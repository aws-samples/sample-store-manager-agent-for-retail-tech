"""
管理者機能スキーマ定義
定型質問とお知らせ管理のリクエスト/レスポンススキーマ
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from routes.schema.common import (
    QuestionType,
    create_id_field,
    create_text_field,
    create_optional_text_field,
)


# 定型質問管理スキーマ
class QuestionCreateRequest(BaseModel):
    """定型質問作成リクエスト"""

    question_text: str = create_text_field("質問内容", 500)
    question_type: QuestionType = Field(..., description="質問タイプ")
    options: Optional[List[str]] = Field(
        None, description="選択肢(choiceタイプの場合)"
    )
    is_active: bool = Field(True, description="アクティブ状態")


class QuestionUpdateRequest(BaseModel):
    """定型質問更新リクエスト"""

    question_text: Optional[str] = create_optional_text_field("質問内容", 500)
    question_type: Optional[QuestionType] = Field(None, description="質問タイプ")
    options: Optional[List[str]] = Field(
        None, description="選択肢(choiceタイプの場合)"
    )
    is_active: Optional[bool] = Field(None, description="アクティブ状態")


class QuestionResponse(BaseModel):
    """定型質問レスポンス"""

    admin_survey_id: str = create_id_field("質問ID")
    question_text: str = Field(..., description="質問内容")
    question_type: QuestionType = Field(..., description="質問タイプ")
    options: Optional[List[str]] = Field(None, description="選択肢")
    is_active: bool = Field(..., description="アクティブ状態")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


class QuestionListResponse(BaseModel):
    """定型質問一覧レスポンス"""

    questions: List[QuestionResponse] = Field(..., description="質問リスト")


# お知らせ管理スキーマ
class MessageCreateRequest(BaseModel):
    """お知らせ作成リクエスト"""

    title: str = create_text_field("タイトル", 200)
    content: str = create_text_field("内容", 2000)
    is_active: bool = Field(True, description="アクティブ状態")


class MessageUpdateRequest(BaseModel):
    """お知らせ更新リクエスト"""

    title: Optional[str] = create_optional_text_field("タイトル", 200)
    content: Optional[str] = create_optional_text_field("内容", 2000)
    is_active: Optional[bool] = Field(None, description="アクティブ状態")


class MessageResponse(BaseModel):
    """お知らせレスポンス"""

    admin_messages_id: str = create_id_field("お知らせID")
    title: str = Field(..., description="タイトル")
    content: str = Field(..., description="内容")
    is_active: bool = Field(..., description="アクティブ状態")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


class MessageListResponse(BaseModel):
    """お知らせ一覧レスポンス"""

    messages: List[MessageResponse] = Field(..., description="お知らせリスト")


# 共通レスポンス
class QuestionOperationResponse(BaseModel):
    """質問操作レスポンス"""

    admin_survey_id: str = Field(..., description="作成/更新された質問ID")
    message: str = Field(..., description="操作結果メッセージ")


class MessageOperationResponse(BaseModel):
    """メッセージ操作レスポンス"""

    admin_messages_id: str = Field(..., description="作成/更新されたメッセージID")
    message: str = Field(..., description="操作結果メッセージ")


class AdminOperationResponse(BaseModel):
    """管理者操作レスポンス"""

    message: str = Field(..., description="操作結果メッセージ")
