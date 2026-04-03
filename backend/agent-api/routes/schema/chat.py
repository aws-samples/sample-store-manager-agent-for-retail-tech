"""
AIチャット機能スキーマ定義
AIチャットメッセージ送信とセッション保存機能のリクエスト/レスポンススキーマ
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from routes.schema.common import (
    AgentType,
    create_id_field,
    create_text_field,
    create_optional_text_field,
)


# チャットメッセージリクエスト
class ChatMessageRequest(BaseModel):
    """AIチャットメッセージリクエスト"""

    agent_type: AgentType = Field(..., description="AIエージェントタイプ")
    prompt: str = create_text_field("プロンプト", 2000)
    session_id: str = create_id_field("セッションID")
    survey_id: str = create_text_field("サーベイ回答ID", 100)

    model_config = {
        "json_schema_extra": {
            "required": [
                "agent_type",
                "prompt",
                "session_id",
                "survey_id",
            ]
        }
    }


# チャットメッセージレスポンス
class ChatMessageResponse(BaseModel):
    """AIチャットメッセージレスポンス"""

    response: str = Field(..., description="AI応答")
    agent_type: AgentType = Field(..., description="AIエージェントタイプ")
    session_id: str = Field(..., description="セッションID")
    actor_id: str = Field(..., description="アクターID")


# チャットセッション保存リクエスト
class ChatSessionSaveRequest(BaseModel):
    """チャットセッション保存リクエスト"""

    survey_id: str = create_id_field("サーベイID")
    session_id: str = create_id_field("セッションID")

    model_config = {
        "json_schema_extra": {
            "required": ["survey_id", "session_id"]
        }
    }


# チャットセッション保存レスポンス
class ChatSessionSaveResponse(BaseModel):
    """チャットセッション保存レスポンス"""

    message: str = Field(..., description="保存結果メッセージ")


# メッセージ履歴項目
class MessageHistoryItem(BaseModel):
    """メッセージ履歴項目"""

    role: str = Field(..., description="メッセージの役割 (user/assistant)")
    content: str = Field(..., description="メッセージ内容")
    timestamp: datetime = Field(..., description="メッセージ送信時刻")
    agent_type: Optional[AgentType] = Field(
        None, description="AIエージェントタイプ（assistantの場合）"
    )


# チャットセッション詳細レスポンス
class ChatSessionResponse(BaseModel):
    """チャットセッション詳細レスポンス"""

    session_id: str = Field(..., description="セッションID")
    survey_id: str = Field(..., description="サーベイID")
    user_cd: str = Field(..., description="ユーザーコード")
    str_cd: str = Field(..., description="店舗コード")
    messages: List[MessageHistoryItem] = Field(..., description="会話履歴")
    created_at: datetime = Field(..., description="作成日時")
