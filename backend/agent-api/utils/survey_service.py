"""
サーベイ機能ビジネスロジック
サーベイ回答の保存・取得・更新の業務処理
"""

import uuid
import json
import math
from datetime import datetime
from typing import List, Optional, Dict, Any
from utils.database import (
    execute_query_and_get_results,
    get_catalog_info,
    DatabaseException,
)
from utils.exceptions import NotFoundException, ValidationException
from utils.logger import get_logger
from utils.auth import CurrentUser
from routes.schema.survey import (
    SurveyAnswerRequest,
    SurveyAnswerUpdateRequest,
    SurveyAnswerResponse,
    SurveyAnswerListItem,
    AnswerData,
)

logger = get_logger("survey-service")


class SurveyService:
    """サーベイ機能サービスクラス"""

    def __init__(self):
        pass

    def save_survey_answer(self, request: SurveyAnswerRequest, current_user: CurrentUser) -> Dict[str, Any]:
        """サーベイ回答保存"""
        try:
            self._validate_survey_request(request)

            user_cd = current_user.user_cd
            str_cd = current_user.str_cd

            catalog_info = get_catalog_info()
            catalog_name = catalog_info["catalog_name"]
            database_name = catalog_info["database_name"]

            values_list = []
            execution_parameters = []

            for answer in request.answers:
                answer_id = str(uuid.uuid4())

                answer_value_cast = (
                    "CAST(? AS varchar)"
                    if answer.answer_value
                    else "CAST(NULL AS varchar)"
                )
                options_cast = (
                    "CAST(? AS varchar)" if answer.options else "CAST(NULL AS varchar)"
                )

                values_list.append(
                    f"(CAST(? AS varchar), CAST(NULL AS varchar), CAST(? AS varchar), CAST(? AS varchar), CAST(? AS varchar), CAST(? AS varchar), CAST(? AS varchar), {answer_value_cast}, {options_cast}, current_timestamp, current_timestamp)"
                )

                params = [
                    answer_id,
                    request.survey_id,
                    str_cd,
                    user_cd,
                    answer.question_text,
                    answer.question_type.value,
                ]

                if answer.answer_value:
                    params.append(answer.answer_value)
                if answer.options:
                    params.append(answer.options)

                execution_parameters.extend(params)

            query = f"""
            INSERT INTO "{catalog_name}"."{database_name}".daily_survey_answers
            (id, summary_id, survey_id, str_cd, user_cd, question_text, question_type, answer_value, options, created_at, updated_at)
            VALUES {", ".join(values_list)}
            """

            execute_query_and_get_results(query, execution_parameters)

            return {
                "message": "Survey answer saved successfully",
                "survey_id": request.survey_id,
            }

        except ValidationException:
            raise
        except DatabaseException as e:
            logger.error(f"Database error in save_survey_answer: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in save_survey_answer: {e}")
            raise

    def update_survey_answer(
        self, survey_id: str, request: SurveyAnswerUpdateRequest
    ) -> Dict[str, Any]:
        """サーベイ回答更新"""
        try:
            catalog_info = get_catalog_info()
            catalog_name = catalog_info["catalog_name"]
            database_name = catalog_info["database_name"]

            find_query = f"""
            SELECT DISTINCT user_cd, str_cd
            FROM "{catalog_name}"."{database_name}".daily_survey_answers
            WHERE survey_id = ?
            LIMIT 1
            """

            results = execute_query_and_get_results(find_query, [survey_id])

            if not results:
                raise NotFoundException("Survey", survey_id)

            if request.answers is not None:
                for answer in request.answers:
                    update_query = f"""
                    UPDATE "{catalog_name}"."{database_name}".daily_survey_answers
                    SET 
                        answer_value = CAST(? AS varchar),
                        updated_at = current_timestamp
                    WHERE "id" = ?
                    """

                    execute_query_and_get_results(
                        update_query, [answer.answer_value, answer.question_id]
                    )

            return {
                "message": "Survey answer updated successfully",
                "survey_id": survey_id,
            }

        except NotFoundException:
            raise
        except ValidationException:
            raise
        except DatabaseException as e:
            logger.error(f"Database error in update_survey_answer: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in update_survey_answer: {e}")
            raise

    def get_survey_answers(
        self, current_user: CurrentUser, page: int = 1, limit: int = 30
    ) -> Dict[str, Any]:
        """サーベイ回答履歴取得"""
        try:
            str_cd = current_user.str_cd
            
            logger.info(
                f"Getting survey answers - str_cd: {str_cd}, page: {page}, limit: {limit}"
            )

            catalog_info = get_catalog_info()
            catalog_name = catalog_info["catalog_name"]
            database_name = catalog_info["database_name"]

            where_clause = "WHERE a.str_cd = ?"
            execution_params = [str_cd]

            count_query = f"""
            SELECT COUNT(DISTINCT a.survey_id) as total_count
            FROM "{catalog_name}"."{database_name}".daily_survey_answers a
            {where_clause}
            """

            count_results = execute_query_and_get_results(count_query, execution_params)
            total_count = int(count_results[0]["total_count"]) if count_results else 0
            total_pages = math.ceil(total_count / limit) if total_count > 0 else 1

            start_row = (page - 1) * limit + 1
            end_row = page * limit

            query = f"""
            WITH ranked_data AS (
                SELECT DISTINCT
                    a.survey_id,
                    a.user_cd,
                    a.str_cd,
                    a.created_at,
                    a.updated_at,
                    COUNT(*) OVER (PARTITION BY a.survey_id) as answer_count,
                    ROW_NUMBER() OVER (PARTITION BY a.survey_id ORDER BY a.created_at DESC) as rn,
                    ROW_NUMBER() OVER (ORDER BY a.created_at DESC) as row_num
                FROM "{catalog_name}"."{database_name}".daily_survey_answers a
                {where_clause}
            )
            SELECT 
                survey_id,
                user_cd,
                str_cd,
                date_format(created_at AT TIME ZONE 'Asia/Tokyo', '%Y-%m-%d %H:%i:%s') as created_at,
                date_format(updated_at AT TIME ZONE 'Asia/Tokyo', '%Y-%m-%d %H:%i:%s') as updated_at,
                answer_count
            FROM ranked_data
            WHERE rn = 1 AND row_num BETWEEN {start_row} AND {end_row}
            ORDER BY created_at DESC
            """

            results = execute_query_and_get_results(query, execution_params)

            answers = []
            for row in results:
                answers.append(
                    SurveyAnswerListItem(
                        survey_id=row["survey_id"],
                        user_cd=row["user_cd"],
                        str_cd=row["str_cd"],
                        answer_count=int(row["answer_count"])
                        if row["answer_count"]
                        else 0,
                        created_at=datetime.fromisoformat(
                            row["created_at"].replace("Z", "+00:00")
                        ),
                        updated_at=datetime.fromisoformat(
                            row["updated_at"].replace("Z", "+00:00")
                        ),
                    )
                )

            result = {
                "answers": answers,
                "total_count": total_count,
                "current_page": page,
                "total_pages": total_pages,
                "limit": limit,
            }

            logger.info(
                f"Returning survey result - total_count: {total_count}, answers_count: {len(answers)}"
            )

            return result

        except DatabaseException as e:
            logger.error(f"Database error in get_survey_answers: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in get_survey_answers: {e}")
            raise

    def get_survey_answer(self, survey_id: str) -> SurveyAnswerResponse:
        """サーベイ回答詳細取得"""
        try:
            catalog_info = get_catalog_info()
            catalog_name = catalog_info["catalog_name"]
            database_name = catalog_info["database_name"]

            summary_query = f"""
            SELECT DISTINCT
                a.survey_id,
                a.user_cd,
                a.str_cd,
                date_format(a.created_at AT TIME ZONE 'Asia/Tokyo', '%Y-%m-%d %H:%i:%s') as created_at,
                date_format(a.updated_at AT TIME ZONE 'Asia/Tokyo', '%Y-%m-%d %H:%i:%s') as updated_at
            FROM "{catalog_name}"."{database_name}".daily_survey_answers a
            WHERE a.survey_id = ?
            LIMIT 1
            """

            summary_results = execute_query_and_get_results(summary_query, [survey_id])

            if not summary_results:
                raise NotFoundException("Survey", survey_id)

            summary_row = summary_results[0]

            answers_query = f"""
            SELECT 
                "id" as question_id,
                question_text,
                question_type,
                answer_value,
                options
            FROM "{catalog_name}"."{database_name}".daily_survey_answers
            WHERE survey_id = ?
            ORDER BY created_at
            """

            answers_results = execute_query_and_get_results(answers_query, [survey_id])

            answers = []
            for answer_row in answers_results:
                question_type_str = answer_row["question_type"]
                if isinstance(question_type_str, str):
                    if "." in question_type_str:
                        question_type_value = question_type_str.split(".")[-1].lower()
                    else:
                        question_type_value = question_type_str.lower()
                else:
                    question_type_value = question_type_str

                answers.append(
                    AnswerData(
                        question_id=answer_row["question_id"],
                        question_text=answer_row["question_text"],
                        question_type=question_type_value,
                        answer_value=answer_row["answer_value"],
                        options=answer_row.get("options"),
                    )
                )

            return SurveyAnswerResponse(
                survey_id=summary_row["survey_id"],
                user_cd=summary_row["user_cd"],
                str_cd=summary_row["str_cd"],
                answers=answers,
                created_at=datetime.fromisoformat(
                    summary_row["created_at"].replace("Z", "+00:00")
                ),
                updated_at=datetime.fromisoformat(
                    summary_row["updated_at"].replace("Z", "+00:00")
                ),
            )

        except NotFoundException:
            raise
        except DatabaseException as e:
            logger.error(f"Database error in get_survey_answer: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in get_survey_answer: {e}")
            raise

    def _validate_survey_request(self, request: SurveyAnswerRequest):
        """サーベイリクエストバリデーション"""
        if not request.answers or len(request.answers) == 0:
            raise ValidationException(
                "At least one answer is required",
                field="answers",
                reason="Survey must have at least one answer",
            )


survey_service = SurveyService()
