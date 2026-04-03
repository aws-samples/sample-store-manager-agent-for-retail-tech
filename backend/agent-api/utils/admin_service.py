"""
管理者機能ビジネスロジック
定型質問とお知らせ管理の業務処理
"""

import uuid
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from utils.auth import CurrentUser
from utils.database import (
    execute_query_and_get_results,
    get_catalog_info,
    DatabaseException,
)
from utils.exceptions import NotFoundException, ValidationException
from utils.logger import get_logger
from routes.schema.admin import (
    QuestionCreateRequest,
    QuestionUpdateRequest,
    QuestionResponse,
    MessageCreateRequest,
    MessageUpdateRequest,
    MessageResponse,
)

logger = get_logger("admin-service")


class AdminService:
    """管理者機能サービスクラス"""

    def __init__(self):
        pass

    def get_questions(
        self, active_only: bool = True, limit: int = 30
    ) -> Dict[str, Any]:
        """定型質問一覧取得"""
        try:
            catalog_info = get_catalog_info()
            catalog_name = catalog_info["catalog_name"]
            database_name = catalog_info["database_name"]

            where_clause = "WHERE is_active = true" if active_only else ""

            query = f"""
            SELECT 
                id as admin_survey_id,
                question_text,
                question_type,
                options,
                is_active,
                date_format(created_at AT TIME ZONE 'Asia/Tokyo', '%Y-%m-%d %H:%i:%s') as created_at,
                date_format(updated_at AT TIME ZONE 'Asia/Tokyo', '%Y-%m-%d %H:%i:%s') as updated_at
            FROM "{catalog_name}"."{database_name}".admin_survey
            {where_clause}
            ORDER BY created_at DESC
            LIMIT {limit}
            """

            results = execute_query_and_get_results(query)

            questions = []
            for row in results:
                options = None
                if row.get("options"):
                    try:
                        options = json.loads(row["options"])
                    except:
                        options = None

                question_type_str = row["question_type"]
                if isinstance(question_type_str, str):
                    if "." in question_type_str:
                        question_type_value = question_type_str.split(".")[-1].lower()
                    else:
                        question_type_value = question_type_str.lower()
                else:
                    question_type_value = question_type_str

                questions.append(
                    QuestionResponse(
                        admin_survey_id=row["admin_survey_id"],
                        question_text=row["question_text"],
                        question_type=question_type_value,
                        options=options,
                        is_active=row["is_active"] == "true",
                        created_at=datetime.fromisoformat(
                            row["created_at"].replace("Z", "+00:00")
                        ),
                        updated_at=datetime.fromisoformat(
                            row["updated_at"].replace("Z", "+00:00")
                        ),
                    )
                )

            return {"questions": questions}

        except DatabaseException as e:
            logger.error(f"Database error in get_questions: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in get_questions: {e}")
            raise

    def get_question(self, question_id: str) -> QuestionResponse:
        """定型質問詳細取得"""
        try:
            catalog_info = get_catalog_info()
            catalog_name = catalog_info["catalog_name"]
            database_name = catalog_info["database_name"]

            query = f"""
            SELECT 
                id as admin_survey_id,
                question_text,
                question_type,
                options,
                is_active,
                date_format(created_at AT TIME ZONE 'Asia/Tokyo', '%Y-%m-%d %H:%i:%s') as created_at,
                date_format(updated_at AT TIME ZONE 'Asia/Tokyo', '%Y-%m-%d %H:%i:%s') as updated_at
            FROM "{catalog_name}"."{database_name}".admin_survey
            WHERE id = ?
            """

            results = execute_query_and_get_results(query, [question_id])

            if not results:
                raise NotFoundException("Question", question_id)

            row = results[0]
            options = None
            if row.get("options"):
                try:
                    options = json.loads(row["options"])
                except:
                    options = None

            question_type_str = row["question_type"]
            if isinstance(question_type_str, str):
                if "." in question_type_str:
                    question_type_value = question_type_str.split(".")[-1].lower()
                else:
                    question_type_value = question_type_str.lower()
            else:
                question_type_value = question_type_str

            return QuestionResponse(
                admin_survey_id=row["admin_survey_id"],
                question_text=row["question_text"],
                question_type=question_type_value,
                options=options,
                is_active=row["is_active"] == "true",
                created_at=datetime.fromisoformat(
                    row["created_at"].replace("Z", "+00:00")
                ),
                updated_at=datetime.fromisoformat(
                    row["updated_at"].replace("Z", "+00:00")
                ),
            )

        except NotFoundException:
            raise
        except DatabaseException as e:
            logger.error(f"Database error in get_question: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in get_question: {e}")
            raise

    def create_question(self, request: QuestionCreateRequest, current_user: CurrentUser) -> Dict[str, Any]:
        """定型質問作成"""
        try:
            self._validate_question_request(request)

            user_cd = current_user.user_cd

            catalog_info = get_catalog_info()
            catalog_name = catalog_info["catalog_name"]
            database_name = catalog_info["database_name"]

            question_id = str(uuid.uuid4())

            options_value = (
                f"'{json.dumps(request.options, ensure_ascii=False)}'"
                if request.options
                else "NULL"
            )

            query = f"""
            INSERT INTO "{catalog_name}"."{database_name}".admin_survey
            (id, question_text, question_type, options, is_active, created_by, created_at, updated_at)
            VALUES (?, ?, ?, {options_value}, ?, ?, current_timestamp, current_timestamp)
            """

            execution_parameters = [
                question_id,
                request.question_text,
                request.question_type.value,
                str(request.is_active).lower(),
                user_cd,
            ]

            execute_query_and_get_results(query, execution_parameters)

            return {
                "message": "Question created successfully",
                "admin_survey_id": question_id,
            }

        except ValidationException:
            raise
        except DatabaseException as e:
            logger.error(f"Database error in create_question: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in create_question: {e}")
            raise

    def update_question(
        self, question_id: str, request: QuestionUpdateRequest
    ) -> Dict[str, Any]:
        """定型質問更新"""
        try:
            existing_question = self.get_question(question_id)

            set_clauses = []

            set_clauses = []
            params = []

            if request.question_text is not None:
                set_clauses.append("question_text = ?")
                params.append(request.question_text)

            if request.question_type is not None:
                set_clauses.append("question_type = ?")
                params.append(request.question_type.value)

            if request.is_active is not None:
                set_clauses.append("is_active = ?")
                params.append(str(request.is_active).lower())

            if hasattr(request, "options") and request.options is not None:
                set_clauses.append("options = ?")
                params.append(json.dumps(request.options, ensure_ascii=False))

            if not set_clauses:
                return {"message": "No updates provided"}

            set_clauses.append("updated_at = current_timestamp")
            params.append(question_id)

            catalog_info = get_catalog_info()
            catalog_name = catalog_info["catalog_name"]
            database_name = catalog_info["database_name"]

            query = f"""
            UPDATE "{catalog_name}"."{database_name}".admin_survey
            SET {", ".join(set_clauses)}
            WHERE id = ?
            """

            execute_query_and_get_results(query, params)

            return {"message": "Question updated successfully"}

        except NotFoundException:
            raise
        except DatabaseException as e:
            logger.error(f"Database error in update_question: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in update_question: {e}")
            raise

    def delete_question(self, question_id: str) -> Dict[str, Any]:
        """定型質問削除"""
        try:
            existing_question = self.get_question(question_id)

            catalog_info = get_catalog_info()
            catalog_name = catalog_info["catalog_name"]
            database_name = catalog_info["database_name"]

            query = f"""
            UPDATE "{catalog_name}"."{database_name}".admin_survey
            SET is_active = false, updated_at = current_timestamp
            WHERE id = ?
            """

            execute_query_and_get_results(query, [question_id])

            return {"message": "Question deleted successfully"}

        except NotFoundException:
            raise
        except DatabaseException as e:
            logger.error(f"Database error in delete_question: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in delete_question: {e}")
            raise

    def get_messages(self, active_only: bool = True, limit: int = 30) -> Dict[str, Any]:
        """お知らせ一覧取得"""
        try:
            catalog_info = get_catalog_info()
            catalog_name = catalog_info["catalog_name"]
            database_name = catalog_info["database_name"]

            where_clause = "WHERE is_active = true" if active_only else ""

            query = f"""
            SELECT 
                id as admin_messages_id,
                title,
                content,
                is_active,
                date_format(created_at AT TIME ZONE 'Asia/Tokyo', '%Y-%m-%d %H:%i:%s') as created_at,
                date_format(updated_at AT TIME ZONE 'Asia/Tokyo', '%Y-%m-%d %H:%i:%s') as updated_at
            FROM "{catalog_name}"."{database_name}".admin_messages
            {where_clause}
            ORDER BY created_at DESC
            LIMIT {limit}
            """

            results = execute_query_and_get_results(query)

            messages = []
            for row in results:
                messages.append(
                    MessageResponse(
                        admin_messages_id=row["admin_messages_id"],
                        title=row["title"],
                        content=row["content"],
                        is_active=row["is_active"] == "true",
                        created_at=datetime.fromisoformat(
                            row["created_at"].replace("Z", "+00:00")
                        ),
                        updated_at=datetime.fromisoformat(
                            row["updated_at"].replace("Z", "+00:00")
                        ),
                    )
                )

            return {"messages": messages}

        except DatabaseException as e:
            logger.error(f"Database error in get_messages: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in get_messages: {e}")
            raise

    def get_message(self, message_id: str) -> MessageResponse:
        """お知らせ詳細取得"""
        try:
            catalog_info = get_catalog_info()
            catalog_name = catalog_info["catalog_name"]
            database_name = catalog_info["database_name"]

            query = f"""
            SELECT 
                id as admin_messages_id,
                title,
                content,
                is_active,
                date_format(created_at AT TIME ZONE 'Asia/Tokyo', '%Y-%m-%d %H:%i:%s') as created_at,
                date_format(updated_at AT TIME ZONE 'Asia/Tokyo', '%Y-%m-%d %H:%i:%s') as updated_at
            FROM "{catalog_name}"."{database_name}".admin_messages
            WHERE id = ?
            """

            results = execute_query_and_get_results(query, [message_id])

            if not results:
                raise NotFoundException("Message", message_id)

            row = results[0]

            return MessageResponse(
                admin_messages_id=row["admin_messages_id"],
                title=row["title"],
                content=row["content"],
                is_active=row["is_active"] == "true",
                created_at=datetime.fromisoformat(
                    row["created_at"].replace("Z", "+00:00")
                ),
                updated_at=datetime.fromisoformat(
                    row["updated_at"].replace("Z", "+00:00")
                ),
            )

        except NotFoundException:
            raise
        except DatabaseException as e:
            logger.error(f"Database error in get_message: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in get_message: {e}")
            raise

    def create_message(self, request: MessageCreateRequest, current_user: CurrentUser) -> Dict[str, Any]:
        """お知らせ作成"""
        try:
            user_cd = current_user.user_cd

            catalog_info = get_catalog_info()
            catalog_name = catalog_info["catalog_name"]
            database_name = catalog_info["database_name"]

            message_id = str(uuid.uuid4())

            query = f"""
            INSERT INTO "{catalog_name}"."{database_name}".admin_messages
            (id, title, content, is_active, created_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, current_timestamp, current_timestamp)
            """

            execution_parameters = [
                message_id,
                request.title,
                request.content,
                str(request.is_active).lower(),
                user_cd,
            ]

            execute_query_and_get_results(query, execution_parameters)

            return {
                "message": "Message created successfully",
                "admin_messages_id": message_id,
            }

        except DatabaseException as e:
            logger.error(f"Database error in create_message: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in create_message: {e}")
            raise

    def update_message(
        self, message_id: str, request: MessageUpdateRequest
    ) -> Dict[str, Any]:
        """お知らせ更新"""
        try:
            existing_message = self.get_message(message_id)

            set_clauses = []
            params = []

            if request.title is not None:
                set_clauses.append("title = ?")
                params.append(request.title)

            if request.content is not None:
                set_clauses.append("content = ?")
                params.append(request.content)

            if request.is_active is not None:
                set_clauses.append("is_active = ?")
                params.append(str(request.is_active).lower())

            if not set_clauses:
                return {"message": "No updates provided"}

            set_clauses.append("updated_at = current_timestamp")
            params.append(message_id)

            catalog_info = get_catalog_info()
            catalog_name = catalog_info["catalog_name"]
            database_name = catalog_info["database_name"]

            query = f"""
            UPDATE "{catalog_name}"."{database_name}".admin_messages
            SET {", ".join(set_clauses)}
            WHERE id = ?
            """

            execute_query_and_get_results(query, params)

            return {"message": "Message updated successfully"}

        except NotFoundException:
            raise
        except DatabaseException as e:
            logger.error(f"Database error in update_message: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in update_message: {e}")
            raise

    def delete_message(self, message_id: str) -> Dict[str, Any]:
        """お知らせ削除"""
        try:
            existing_message = self.get_message(message_id)

            catalog_info = get_catalog_info()
            catalog_name = catalog_info["catalog_name"]
            database_name = catalog_info["database_name"]

            query = f"""
            UPDATE "{catalog_name}"."{database_name}".admin_messages
            SET is_active = false, updated_at = current_timestamp
            WHERE id = ?
            """

            execute_query_and_get_results(query, [message_id])

            return {"message": "Message deleted successfully"}

        except NotFoundException:
            raise
        except DatabaseException as e:
            logger.error(f"Database error in delete_message: {e}")
            raise
        except Exception as e:
            logger.error(f"Error in delete_message: {e}")
            raise

    def _validate_question_request(self, request: QuestionCreateRequest):
        """定型質問リクエストバリデーション"""
        if request.question_type == "choice" and not request.options:
            raise ValidationException(
                "Options are required for choice type questions",
                field="options",
                reason="Choice questions must have options",
            )

        if request.question_type in ["text", "number", "rating"] and request.options:
            raise ValidationException(
                "Options are not allowed for text, number, and rating type questions",
                field="options",
                reason="Text, number, and rating questions should not have options",
            )


admin_service = AdminService()
