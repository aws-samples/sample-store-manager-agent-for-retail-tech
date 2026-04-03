"""
Insights機能のビジネスロジック実装
"""

import uuid
import math
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Tuple
from config import config
from utils.database import (
    execute_query_and_get_results,
    execute_query_with_pyathena,
    get_catalog_info,
    DatabaseException,
)
from utils.exceptions import NotFoundException, ValidationException
from utils.agentcore_client import invoke_agentcore_runtime
from utils.logger import get_logger
from utils.auth import CurrentUser
from routes.schema.common import Status

logger = get_logger("insights-service")


class InsightsService:
    """Insights機能のサービスクラス"""

    def __init__(self):
        pass

    def _parse_agent_response(self, agent_response: Dict[str, Any]) -> str:
        """Agentレスポンスからテキストを抽出"""
        try:
            if not agent_response:
                return ""

            response_data = agent_response.get("response", {})

            if isinstance(response_data, str):
                return response_data

            content = response_data.get("content", [])

            if not content or not isinstance(content, list) or len(content) == 0:
                return ""

            text = content[0].get("text", "")

            return text

        except Exception as e:
            logger.error(f"Error parsing agent response: {e}")
            return ""

    def _get_existing_summary_id(
        self, user_cd: str, str_cd: str, report_date: date
    ) -> Optional[str]:
        """既存のsummary_idを取得"""
        try:
            catalog_info = get_catalog_info()
            catalog_name = catalog_info["catalog_name"]
            database_name = catalog_info["database_name"]

            query = f"""
            SELECT summary_id
            FROM "{catalog_name}"."{database_name}".daily_survey_answers
            WHERE str_cd = ?
              AND DATE(created_at AT TIME ZONE 'Asia/Tokyo') = DATE '{report_date}'
              AND summary_id IS NOT NULL
            LIMIT 1
            """

            results = execute_query_and_get_results(query, [str_cd])

            if not results:
                return None

            return results[0].get("summary_id")

        except DatabaseException as e:
            logger.error(f"Database error in _get_existing_summary_id: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in _get_existing_summary_id: {e}")
            raise

    def _update_existing_summary(
        self,
        summary_id: str,
        report_text: str,
        agentcore_memory_id: str,
        session_id: str,
        actor_id: str,
    ) -> None:
        """既存のdaily_survey_summaryレコードを更新"""
        try:
            catalog_info = get_catalog_info()
            catalog_name = catalog_info["catalog_name"]
            database_name = catalog_info["database_name"]

            query = f"""
            UPDATE "{catalog_name}"."{database_name}".daily_survey_summary
            SET
                report_text = %(report_text)s,
                updated_at = current_timestamp,
                agentcore_memory_id = %(agentcore_memory_id)s,
                session_id = %(session_id)s,
                actor_id = %(actor_id)s
            WHERE id = %(summary_id)s
            """

            params = {
                "report_text": report_text,
                "agentcore_memory_id": agentcore_memory_id,
                "session_id": session_id,
                "actor_id": actor_id,
                "summary_id": summary_id,
            }

            execute_query_with_pyathena(query, params)

        except DatabaseException as e:
            logger.error(f"Database error in _update_existing_summary: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in _update_existing_summary: {e}")
            raise

    def _create_new_summary(
        self,
        user_cd: str,
        str_cd: str,
        report_date: date,
        report_text: str,
        agentcore_memory_id: str,
        session_id: str,
        actor_id: str,
    ) -> str:
        """新規daily_survey_summaryレコードを作成"""
        try:
            catalog_info = get_catalog_info()
            catalog_name = catalog_info["catalog_name"]
            database_name = catalog_info["database_name"]

            new_summary_id = str(uuid.uuid4())

            insert_query = f"""
            INSERT INTO "{catalog_name}"."{database_name}".daily_survey_summary
            (id, user_cd, str_cd, report_date, status, report_text,
             agentcore_memory_id, session_id, actor_id, supplement_comment,
             created_at, updated_at)
            VALUES (%(id)s, %(user_cd)s, %(str_cd)s, TIMESTAMP '{report_date} 00:00:00', 'in_progress', %(report_text)s, %(agentcore_memory_id)s, %(session_id)s, %(actor_id)s, NULL, current_timestamp, current_timestamp)
            """

            params = {
                "id": new_summary_id,
                "user_cd": user_cd,
                "str_cd": str_cd,
                "report_text": report_text,
                "agentcore_memory_id": agentcore_memory_id,
                "session_id": session_id,
                "actor_id": actor_id,
            }

            execute_query_with_pyathena(insert_query, params)

            return new_summary_id

        except DatabaseException as e:
            logger.error(f"Database error in _create_new_summary: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in _create_new_summary: {e}")
            raise

    def _update_answers_summary_id(
        self, summary_id: str, user_cd: str, str_cd: str, report_date: date
    ) -> None:
        """daily_survey_answersのsummary_idを更新"""
        try:
            catalog_info = get_catalog_info()
            catalog_name = catalog_info["catalog_name"]
            database_name = catalog_info["database_name"]

            update_answers_query = f"""
            UPDATE "{catalog_name}"."{database_name}".daily_survey_answers
            SET summary_id = ?
            WHERE str_cd = ?
              AND DATE(created_at AT TIME ZONE 'Asia/Tokyo') = DATE '{report_date}'
              AND summary_id IS NULL
            """

            execution_parameters = [summary_id, str_cd]

            execute_query_and_get_results(update_answers_query, execution_parameters)

        except DatabaseException as e:
            logger.error(f"Database error in _update_answers_summary_id: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in _update_answers_summary_id: {e}")
            raise

    def get_daily_insights(
        self, current_user: CurrentUser, report_date: date
    ) -> Optional[Dict[str, Any]]:
        """日次Insights取得"""
        try:
            user_cd = current_user.user_cd
            str_cd = current_user.str_cd

            catalog_info = get_catalog_info()
            catalog_name = catalog_info["catalog_name"]
            database_name = catalog_info["database_name"]

            query = f"""
            SELECT 
                id,
                user_cd,
                str_cd,
                date_format(report_date AT TIME ZONE 'Asia/Tokyo', '%Y-%m-%d %H:%i:%s') as report_date,
                status,
                report_text,
                session_id,
                actor_id,
                date_format(created_at AT TIME ZONE 'Asia/Tokyo', '%Y-%m-%d %H:%i:%s') as created_at,
                date_format(updated_at AT TIME ZONE 'Asia/Tokyo', '%Y-%m-%d %H:%i:%s') as updated_at,
                user_feedback
            FROM "{catalog_name}"."{database_name}".daily_survey_summary
            WHERE user_cd = ?
                AND str_cd = ?
                AND DATE(report_date AT TIME ZONE 'Asia/Tokyo') = DATE '{report_date}'
            ORDER BY created_at DESC
            LIMIT 1
            """

            results = execute_query_and_get_results(query, [user_cd, str_cd])

            if not results:
                return None

            row = results[0]

            return {
                "id": row["id"],
                "user_cd": row["user_cd"],
                "str_cd": row["str_cd"],
                "report_date": datetime.strptime(
                    row["report_date"], "%Y-%m-%d %H:%M:%S"
                ),
                "status": row["status"],
                "report_text": row["report_text"],
                "session_id": row["session_id"],
                "actor_id": row["actor_id"],
                "created_at": datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S"),
                "updated_at": datetime.strptime(row["updated_at"], "%Y-%m-%d %H:%M:%S"),
                "user_feedback": row.get("user_feedback"),
            }

        except DatabaseException as e:
            logger.error(f"Database error in get_daily_insights: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in get_daily_insights: {e}")
            raise

    def generate_daily_insights(
        self,
        current_user: CurrentUser,
        agent_type: str,
        prompt: str,
        session_id: str,
        report_date: date,
    ) -> Dict[str, Any]:
        """日次Insights生成"""
        try:
            actor_id = current_user.actor_id
            user_cd = current_user.user_cd
            str_cd = current_user.str_cd

            result = invoke_agentcore_runtime(
                agent_type=agent_type,
                prompt=prompt,
                session_id=session_id,
                actor_id=actor_id,
                str_cd=str_cd,
            )

            report_text = self._parse_agent_response(result)

            agentcore_memory_id = config.DAILY_SUMMARY_AGENTCORE_MEMORY_ID

            existing_summary_id = self._get_existing_summary_id(
                user_cd, str_cd, report_date
            )

            if existing_summary_id:
                self._update_existing_summary(
                    summary_id=existing_summary_id,
                    report_text=report_text,
                    agentcore_memory_id=agentcore_memory_id,
                    session_id=session_id,
                    actor_id=actor_id,
                )
                summary_id = existing_summary_id

                self._update_answers_summary_id(
                    summary_id=summary_id,
                    user_cd=user_cd,
                    str_cd=str_cd,
                    report_date=report_date,
                )
            else:
                summary_id = self._create_new_summary(
                    user_cd=user_cd,
                    str_cd=str_cd,
                    report_date=report_date,
                    report_text=report_text,
                    agentcore_memory_id=agentcore_memory_id,
                    session_id=session_id,
                    actor_id=actor_id,
                )

                self._update_answers_summary_id(
                    summary_id=summary_id,
                    user_cd=user_cd,
                    str_cd=str_cd,
                    report_date=report_date,
                )

            return {
                "response": report_text,
                "agent_type": agent_type,
                "session_id": session_id,
                "actor_id": actor_id,
                "summary_id": summary_id,
            }

        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            raise ValidationException("AgentCore Runtime is not configured")
        except DatabaseException as e:
            logger.error(f"Database error in generate_daily_insights: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in generate_daily_insights: {e}")
            raise

    def save_daily_insights(
        self,
        current_user: CurrentUser,
        insight_id: str,
        report_date: datetime,
        status: str,
        report_text: str,
        session_id: str,
    ) -> Dict[str, Any]:
        """日次Insights保存・更新"""
        try:
            actor_id = current_user.actor_id
            user_cd = current_user.user_cd
            str_cd = current_user.str_cd

            existing_insight = self.get_insight_by_id(insight_id)

            agentcore_memory_id = config.DAILY_SUMMARY_AGENTCORE_MEMORY_ID

            catalog_info = get_catalog_info()
            catalog_name = catalog_info["catalog_name"]
            database_name = catalog_info["database_name"]

            query = f"""
            UPDATE "{catalog_name}"."{database_name}".daily_survey_summary
            SET
                user_cd = %(user_cd)s,
                str_cd = %(str_cd)s,
                status = 'completed',
                report_text = %(report_text)s,
                agentcore_memory_id = %(agentcore_memory_id)s,
                session_id = %(session_id)s,
                actor_id = %(actor_id)s,
                updated_at = current_timestamp
            WHERE id = %(insight_id)s
            """

            params = {
                "user_cd": user_cd,
                "str_cd": str_cd,
                "report_text": report_text,
                "agentcore_memory_id": agentcore_memory_id,
                "session_id": session_id,
                "actor_id": actor_id,
                "insight_id": insight_id,
            }

            execute_query_with_pyathena(query, params)

            return self.get_insight_by_id(insight_id)

        except NotFoundException:
            raise
        except DatabaseException as e:
            logger.error(f"Database error in save_daily_insights: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in save_daily_insights: {e}")
            raise

    def save_feedback(self, insight_id: str, user_feedback: str) -> Dict[str, Any]:
        """フィードバック保存"""
        try:
            existing_insight = self.get_insight_by_id(insight_id)

            catalog_info = get_catalog_info()
            catalog_name = catalog_info["catalog_name"]
            database_name = catalog_info["database_name"]

            query = f"""
            UPDATE "{catalog_name}"."{database_name}".daily_survey_summary
            SET 
                user_feedback = ?,
                updated_at = current_timestamp
            WHERE id = ?
            """

            execute_query_and_get_results(query, [user_feedback, insight_id])

            return self.get_insight_by_id(insight_id)

        except NotFoundException:
            raise
        except DatabaseException as e:
            logger.error(f"Database error in save_feedback: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in save_feedback: {e}")
            raise

    def get_insights_history(
        self, current_user: CurrentUser, page: int = 1, limit: int = 30
    ) -> Tuple[List[Dict[str, Any]], int, int]:
        """Insights履歴取得"""
        try:
            str_cd = current_user.str_cd

            catalog_info = get_catalog_info()
            catalog_name = catalog_info["catalog_name"]
            database_name = catalog_info["database_name"]

            where_clause = "WHERE str_cd = ?"
            execution_params = [str_cd]

            count_query = f"""
            SELECT COUNT(*) as total_count
            FROM "{catalog_name}"."{database_name}".daily_survey_summary
            {where_clause}
            """

            count_results = execute_query_and_get_results(count_query, execution_params)
            total_count = int(count_results[0]["total_count"]) if count_results else 0
            total_pages = math.ceil(total_count / limit) if total_count > 0 else 1

            start_row = (page - 1) * limit + 1
            end_row = page * limit

            query = f"""
            WITH ranked_data AS (
                SELECT 
                    id,
                    report_date,
                    user_cd,
                    str_cd,
                    created_at,
                    updated_at,
                    ROW_NUMBER() OVER (ORDER BY created_at DESC) as row_num
                FROM "{catalog_name}"."{database_name}".daily_survey_summary
                {where_clause}
            )
            SELECT 
                id,
                date_format(report_date AT TIME ZONE 'Asia/Tokyo', '%Y-%m-%d %H:%i:%s') as report_date,
                user_cd,
                str_cd,
                date_format(created_at AT TIME ZONE 'Asia/Tokyo', '%Y-%m-%d %H:%i:%s') as created_at,
                date_format(updated_at AT TIME ZONE 'Asia/Tokyo', '%Y-%m-%d %H:%i:%s') as updated_at
            FROM ranked_data
            WHERE row_num BETWEEN {start_row} AND {end_row}
            ORDER BY created_at DESC
            """

            results = execute_query_and_get_results(query, execution_params)

            insights = []
            for row in results:
                insights.append(
                    {
                        "id": row["id"],
                        "report_date": datetime.strptime(
                            row["report_date"], "%Y-%m-%d %H:%M:%S"
                        ),
                        "user_cd": row["user_cd"],
                        "str_cd": row["str_cd"],
                        "created_at": datetime.strptime(
                            row["created_at"], "%Y-%m-%d %H:%M:%S"
                        ),
                        "updated_at": datetime.strptime(
                            row["updated_at"], "%Y-%m-%d %H:%M:%S"
                        ),
                    }
                )

            return insights, total_count, total_pages

        except DatabaseException as e:
            logger.error(f"Database error in get_insights_history: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in get_insights_history: {e}")
            raise

    def get_insight_by_id(self, insight_id: str) -> Dict[str, Any]:
        """Insights詳細取得"""
        try:
            catalog_info = get_catalog_info()
            catalog_name = catalog_info["catalog_name"]
            database_name = catalog_info["database_name"]

            query = f"""
            SELECT 
                id,
                user_cd,
                str_cd,
                date_format(report_date AT TIME ZONE 'Asia/Tokyo', '%Y-%m-%d %H:%i:%s') as report_date,
                status,
                report_text,
                session_id,
                actor_id,
                date_format(created_at AT TIME ZONE 'Asia/Tokyo', '%Y-%m-%d %H:%i:%s') as created_at,
                date_format(updated_at AT TIME ZONE 'Asia/Tokyo', '%Y-%m-%d %H:%i:%s') as updated_at,
                user_feedback
            FROM "{catalog_name}"."{database_name}".daily_survey_summary
            WHERE id = ?
            """

            results = execute_query_and_get_results(query, [insight_id])

            if not results:
                raise NotFoundException("Insight", insight_id)

            row = results[0]

            return {
                "id": row["id"],
                "user_cd": row["user_cd"],
                "str_cd": row["str_cd"],
                "report_date": datetime.fromisoformat(
                    row["report_date"].replace("Z", "+00:00")
                ),
                "status": row["status"],
                "report_text": row["report_text"],
                "session_id": row["session_id"],
                "actor_id": row["actor_id"],
                "created_at": datetime.fromisoformat(
                    row["created_at"].replace("Z", "+00:00")
                ),
                "updated_at": datetime.fromisoformat(
                    row["updated_at"].replace("Z", "+00:00")
                ),
                "user_feedback": row.get("user_feedback"),
            }

        except NotFoundException:
            raise
        except DatabaseException as e:
            logger.error(f"Database error in get_insight_by_id: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in get_insight_by_id: {e}")
            raise
