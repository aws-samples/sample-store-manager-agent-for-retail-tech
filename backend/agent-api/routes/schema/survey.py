"""
サーベイ機能スキーマ定義
サーベイ回答の保存・取得・更新機能のリクエスト/レスポンススキーマ
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


# サーベイ回答データ
class AnswerData(BaseModel):
    """回答データ"""

    question_id: str = create_id_field("質問ID")
    question_text: str = Field(..., description="質問内容")
    question_type: QuestionType = Field(..., description="質問タイプ")
    answer_value: Optional[str] = Field(None, description="回答値")
    options: Optional[str] = Field(
        None, description="選択肢（choice/ratingタイプの場合）"
    )


# サーベイ回答リクエスト
class SurveyAnswerRequest(BaseModel):
    """サーベイ回答保存リクエスト"""

    survey_id: str = create_id_field("サーベイID")
    answers: List[AnswerData] = Field(..., description="回答データリスト")

    model_config = {
        "json_schema_extra": {"required": ["survey_id", "answers"]}
    }


class SurveyAnswerUpdateRequest(BaseModel):
    """サーベイ回答更新リクエスト"""

    answers: Optional[List[AnswerData]] = Field(None, description="回答データリスト")


# サーベイ回答レスポンス
class SurveyAnswerResponse(BaseModel):
    """サーベイ回答レスポンス"""

    model_config = {"use_enum_values": True}

    survey_id: str = Field(..., description="サーベイID")
    user_cd: str = Field(..., description="ユーザーコード")
    str_cd: str = Field(..., description="店舗コード")
    answers: List[AnswerData] = Field(..., description="回答データリスト")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


class SurveyAnswerListItem(BaseModel):
    """サーベイ回答リスト項目"""

    survey_id: str = Field(..., description="サーベイID")
    user_cd: str = Field(..., description="ユーザーコード")
    str_cd: str = Field(..., description="店舗コード")
    answer_count: int = Field(..., description="回答数")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


class SurveyAnswerListResponse(BaseModel):
    """サーベイ回答履歴レスポンス"""

    answers: List[SurveyAnswerListItem] = Field(..., description="サーベイリスト")
    total_count: int = Field(..., description="総件数")
    current_page: int = Field(..., description="現在のページ番号")
    total_pages: int = Field(..., description="総ページ数")
    limit: int = Field(..., description="1ページあたりの件数")


# 操作レスポンス
class SurveyOperationResponse(BaseModel):
    """サーベイ操作レスポンス"""

    message: str = Field(..., description="操作結果メッセージ")
    survey_id: str = Field(..., description="サーベイID")
