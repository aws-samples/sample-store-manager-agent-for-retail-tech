"""
共通スキーマ定義
Store Daily QA System API で使用する共通のPydanticスキーマを定義
"""

from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from enum import Enum


# 列挙型定義
class QuestionType(str, Enum):
    """質問タイプ"""

    TEXT = "text"
    CHOICE = "choice"
    RATING = "rating"
    NUMBER = "number"


class AgentType(str, Enum):
    """AIエージェントタイプ"""

    HEARING = "hearing"
    COACHING = "coaching"
    ANALYSIS = "analysis"
    DAILY_SUMMARY = "daily_summary"


class Status(str, Enum):
    """ステータス"""

    PENDING = "pending"
    COMPLETED = "completed"


# エラーレスポンススキーマ
class ErrorDetail(BaseModel):
    """エラー詳細情報"""

    field: Optional[str] = Field(None, description="エラーが発生したフィールド名")
    reason: str = Field(..., description="エラーの理由")


class ErrorResponse(BaseModel):
    """エラーレスポンス"""

    code: str = Field(..., description="エラーコード")
    message: str = Field(..., description="エラーメッセージ")
    details: Optional[Any] = Field(None, description="エラー詳細")


class APIError(BaseModel):
    """API エラーレスポンス"""

    error: ErrorResponse


# 共通レスポンススキーマ
class SuccessResponse(BaseModel):
    """成功レスポンス"""

    message: str = Field(..., description="成功メッセージ")
    data: Optional[Any] = Field(None, description="レスポンスデータ")


class PaginationInfo(BaseModel):
    """ページネーション情報"""

    total_count: int = Field(..., description="総件数")
    current_page: int = Field(..., description="現在のページ番号")
    total_pages: int = Field(..., description="総ページ数")
    per_page: int = Field(..., description="1ページあたりの件数")


class PaginatedResponse(BaseModel):
    """ページネーション対応レスポンス"""

    data: List[Any] = Field(..., description="データリスト")
    pagination: PaginationInfo = Field(..., description="ページネーション情報")


# 共通バリデーション関数
def validate_string_length(
    value: str, min_length: int = 1, max_length: int = 1000
) -> str:
    """文字列長バリデーション"""
    if len(value) < min_length:
        raise ValueError(f"文字列は{min_length}文字以上である必要があります")
    if len(value) > max_length:
        raise ValueError(f"文字列は{max_length}文字以下である必要があります")
    return value


def validate_required_field(value: Any, field_name: str) -> Any:
    """必須フィールドバリデーション"""
    if value is None or (isinstance(value, str) and value.strip() == ""):
        raise ValueError(f"{field_name}は必須フィールドです")
    return value


# 共通フィールド定義
def create_id_field(description: str) -> Field:
    """ID フィールド作成"""
    return Field(..., description=description, min_length=1, max_length=100)


def create_text_field(description: str, max_length: int = 1000) -> Field:
    """テキストフィールド作成"""
    return Field(..., description=description, min_length=1, max_length=max_length)


def create_optional_text_field(description: str, max_length: int = 1000) -> Field:
    """オプショナルテキストフィールド作成"""
    return Field(None, description=description, max_length=max_length)


def create_datetime_field(description: str) -> Field:
    """日時フィールド作成"""
    return Field(..., description=description)
