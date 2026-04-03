"""
AIチャット機能ビジネスロジック
AIチャットメッセージ送信とセッション保存の業務処理
"""

import os
import boto3
import uuid
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from config import config
from utils.exceptions import ValidationException, InternalServerException
from utils.agentcore_client import invoke_agentcore_runtime, get_memory_client
from utils.logger import get_logger
from utils.auth import CurrentUser
from routes.schema.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSessionSaveRequest,
    ChatSessionResponse,
)

logger = get_logger("chat-service")


def _execute_athena_query(
    query: str, execution_parameters: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    region = config.REGION
    workgroup = config.ATHENA_WORKGROUP
    output_location = config.ATHENA_OUTPUT_LOCATION

    athena_client = boto3.client("athena", region_name=region)

    query_params = {
        "QueryString": query,
        "WorkGroup": workgroup,
        "ResultConfiguration": {"OutputLocation": output_location},
    }

    if execution_parameters:
        query_params["ExecutionParameters"] = execution_parameters

    response = athena_client.start_query_execution(**query_params)

    query_execution_id = response["QueryExecutionId"]

    max_attempts = 30
    for _ in range(max_attempts):
        query_status = athena_client.get_query_execution(
            QueryExecutionId=query_execution_id
        )
        status = query_status["QueryExecution"]["Status"]["State"]

        if status == "SUCCEEDED":
            break
        elif status in ["FAILED", "CANCELLED"]:
            reason = query_status["QueryExecution"]["Status"].get(
                "StateChangeReason", "Unknown"
            )
            raise InternalServerException(f"Athena query failed: {reason}")

        time.sleep(1)
    else:
        raise InternalServerException("Athena query timeout")

    result = athena_client.get_query_results(QueryExecutionId=query_execution_id)

    if len(result["ResultSet"]["Rows"]) <= 1:
        return []

    columns = [
        col["Label"] for col in result["ResultSet"]["ResultSetMetadata"]["ColumnInfo"]
    ]
    rows = []

    for row in result["ResultSet"]["Rows"][1:]:
        row_data = {}
        for i, col in enumerate(columns):
            row_data[col] = row["Data"][i].get("VarCharValue", "")
        rows.append(row_data)

    return rows


def _get_table_path() -> str:
    table_bucket_arn = config.TABLE_BUCKET_ARN
    namespace = config.NAMESPACE

    table_bucket_name = table_bucket_arn.split("/")[-1]
    catalog_name = f"s3tablescatalog/{table_bucket_name}"

    return f'"{catalog_name}"."{namespace}"."ai_chat_history"'


class ChatService:
    """AIチャット機能サービスクラス"""

    def __init__(self):
        pass

    def send_message(self, request: ChatMessageRequest, current_user: CurrentUser) -> ChatMessageResponse:
        """AIチャットメッセージ送信"""
        self._validate_chat_request(request)

        actor_id = current_user.actor_id
        str_cd = current_user.str_cd

        try:
            result = invoke_agentcore_runtime(
                agent_type=request.agent_type,
                prompt=request.prompt,
                session_id=request.session_id,
                actor_id=actor_id,
                str_cd=str_cd,
            )

            ai_response = result.get("response", "")

            return ChatMessageResponse(
                response=ai_response,
                agent_type=request.agent_type,
                session_id=request.session_id,
                actor_id=actor_id,
                timestamp=datetime.now(timezone.utc),
            )

        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            raise InternalServerException("AgentCore Runtime is not configured")
        except Exception as e:
            logger.error(f"AgentCore Runtime error: {e}")
            raise InternalServerException(f"Failed to invoke agent: {str(e)}")

    def save_chat_session(self, request: ChatSessionSaveRequest, current_user: CurrentUser) -> Dict[str, Any]:
        """チャットセッション保存"""
        self._validate_session_request(request)

        user_cd = current_user.user_cd

        try:
            table_bucket_arn = config.TABLE_BUCKET_ARN
            namespace = config.NAMESPACE
            workgroup = config.ATHENA_WORKGROUP
            output_location = config.ATHENA_OUTPUT_LOCATION
            region = config.REGION

            memory_id = config.HEARING_AGENTCORE_MEMORY_ID

            logger.info(f"Using AgentCore Memory ID: {memory_id}")

            table_bucket_name = table_bucket_arn.split("/")[-1]
            catalog_name = f"s3tablescatalog/{table_bucket_name}"

            athena_client = boto3.client("athena", region_name=region)

            record_id = str(uuid.uuid4())

            query = f"""
            INSERT INTO "{catalog_name}"."{namespace}"."ai_chat_history" 
            (id, summary_id, survey_id, agentcore_memory_id, session_id, actor_id, created_at)
            VALUES 
            (?, NULL, ?, ?, ?, ?, current_timestamp)
            """

            query_params = {
                "QueryString": query,
                "WorkGroup": workgroup,
                "ResultConfiguration": {"OutputLocation": output_location},
                "ExecutionParameters": [
                    record_id,
                    request.survey_id,
                    memory_id,
                    request.session_id,
                    user_cd,
                ],
            }

            response = athena_client.start_query_execution(**query_params)

            logger.info(
                f"Chat session saved to S3 Tables: {response['QueryExecutionId']}"
            )

            return {"message": "Chat session saved successfully"}

        except Exception as e:
            logger.error(f"Error saving chat session to S3 Tables: {e}")
            raise InternalServerException(f"Failed to save chat session: {str(e)}")

    def get_chat_session_by_survey(
        self, survey_id: str
    ) -> Optional[ChatSessionResponse]:
        try:
            table_bucket_arn = os.environ.get("TABLE_BUCKET_ARN")
            namespace = os.environ.get("NAMESPACE", "store_data")

            if not table_bucket_arn:
                raise InternalServerException("TABLE_BUCKET_ARN is not configured")

            table_bucket_name = table_bucket_arn.split("/")[-1]
            catalog_name = f"s3tablescatalog/{table_bucket_name}"

            query = f"""
                SELECT 
                    h.agentcore_memory_id, 
                    h.session_id, 
                    h.actor_id, 
                    h.survey_id,
                    a.user_cd,
                    a.str_cd,
                    date_format(h.created_at AT TIME ZONE 'Asia/Tokyo', '%Y-%m-%d %H:%i:%s') as created_at,
                    format_datetime(h.created_at AT TIME ZONE 'Asia/Tokyo', 'yyyy-MM-dd HH:mm:ss') as created_at_jst
                FROM "{catalog_name}"."{namespace}"."ai_chat_history" h
                INNER JOIN "{catalog_name}"."{namespace}"."daily_survey_answers" a
                    ON h.survey_id = a.survey_id
                WHERE h.survey_id = ?
                ORDER BY h.created_at DESC
                LIMIT 1
            """

            results = _execute_athena_query(query, [survey_id])

            if not results:
                logger.info(f"Session not found for survey: {survey_id}")
                return None

            metadata = results[0]

            messages = []
            default_timestamp = metadata["created_at_jst"]

            try:
                memory_client = get_memory_client()
                turns = memory_client.get_last_k_turns(
                    memory_id=metadata["agentcore_memory_id"],
                    actor_id=metadata["actor_id"],
                    session_id=metadata["session_id"],
                    k=20,
                )

                for turn in turns:
                    for msg in turn:
                        role = msg["role"].lower()

                        content_data = msg["content"]

                        if isinstance(content_data, dict) and "text" in content_data:
                            text_value = content_data["text"]

                            if isinstance(text_value, str):
                                try:
                                    parsed_text = json.loads(text_value)
                                    if (
                                        isinstance(parsed_text, dict)
                                        and "message" in parsed_text
                                    ):
                                        message_content = parsed_text["message"].get(
                                            "content", []
                                        )
                                        if message_content and isinstance(
                                            message_content, list
                                        ):
                                            text = message_content[0].get("text", "")
                                        else:
                                            text = text_value
                                    else:
                                        text = text_value
                                except json.JSONDecodeError:
                                    text = text_value
                            else:
                                text = str(text_value)
                        elif isinstance(content_data, str):
                            try:
                                content_data = json.loads(content_data)
                                if (
                                    isinstance(content_data, dict)
                                    and "message" in content_data
                                ):
                                    message_content = content_data["message"].get(
                                        "content", []
                                    )
                                    if message_content and isinstance(
                                        message_content, list
                                    ):
                                        text = message_content[0].get("text", "")
                                    else:
                                        text = str(content_data)
                                else:
                                    text = str(content_data)
                            except json.JSONDecodeError:
                                text = content_data
                        else:
                            text = str(content_data)

                        messages.append(
                            {
                                "role": role,
                                "content": text,
                                "timestamp": msg.get("timestamp", default_timestamp),
                            }
                        )
            except Exception as memory_error:
                logger.warning(
                    f"Failed to retrieve messages from AgentCore Memory: {memory_error}"
                )
                logger.warning(f"Returning empty messages for survey_id: {survey_id}")

            messages.reverse()

            return ChatSessionResponse(
                session_id=metadata["session_id"],
                survey_id=metadata["survey_id"],
                user_cd=metadata["user_cd"],
                str_cd=metadata["str_cd"],
                messages=messages,
                created_at=metadata["created_at"],
            )

        except Exception as e:
            logger.error(f"Error retrieving chat session: {e}")
            raise InternalServerException(f"Failed to retrieve chat session: {str(e)}")

    def _validate_chat_request(self, request: ChatMessageRequest):
        if len(request.prompt.strip()) == 0:
            raise ValidationException(
                "Prompt cannot be empty",
                field="prompt",
                reason="Message content is required",
            )

        if len(request.session_id.strip()) == 0:
            raise ValidationException(
                "Session ID cannot be empty",
                field="session_id",
                reason="Valid session ID is required",
            )

    def _validate_session_request(self, request: ChatSessionSaveRequest):
        """セッション保存リクエストバリデーション"""
        # セッションIDの形式チェック
        if len(request.session_id.strip()) == 0:
            raise ValidationException(
                "Session ID cannot be empty",
                field="session_id",
                reason="Valid session ID is required",
            )


# グローバルインスタンス
chat_service = ChatService()
