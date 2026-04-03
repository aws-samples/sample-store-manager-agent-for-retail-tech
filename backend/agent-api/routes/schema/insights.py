"""
Insights機能のリクエスト/レスポンススキーマ定義
"""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field
from routes.schema.common import Status


class InsightGenerateRequest(BaseModel):
    """日次Insights生成リクエスト"""

    agent_type: str = Field(
        default="daily_summary", description="エージェントタイプ", min_length=1
    )
    prompt: str = Field(..., description="生成指示", min_length=1)
    session_id: str = Field(
        ..., description="セッションID", min_length=1, max_length=100
    )
    report_date: date = Field(..., description="レポート対象日")

    model_config = {
        "json_schema_extra": {
            "required": [
                "agent_type",
                "prompt",
                "session_id",
                "report_date",
            ]
        }
    }


class InsightSaveRequest(BaseModel):
    """日次Insights保存リクエスト"""

    report_date: datetime = Field(..., description="レポート対象日")
    status: str = Field(..., description="セッション状態")
    report_text: str = Field(..., description="レポートテキスト")
    session_id: str = Field(..., description="会話セッションID")

    model_config = {
        "json_schema_extra": {
            "required": [
                "report_date",
                "status",
                "report_text",
                "session_id",
            ]
        }
    }


class InsightFeedbackRequest(BaseModel):
    """フィードバック保存リクエスト"""

    user_feedback: str = Field(..., description="ユーザーフィードバック")

    model_config = {"json_schema_extra": {"required": ["user_feedback"]}}


class InsightResponse(BaseModel):
    """日次Insightsレスポンス"""

    id: str = Field(..., description="Insights ID")
    user_cd: str = Field(..., description="ユーザーコード")
    str_cd: str = Field(..., description="店舗コード")
    report_date: datetime = Field(..., description="レポート対象日")
    status: str = Field(..., description="ステータス")
    report_text: str = Field(..., description="レポートテキスト")
    session_id: str = Field(..., description="会話セッションID")
    actor_id: str = Field(..., description="ユーザー/アクターID")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")
    user_feedback: Optional[str] = Field(
        default=None, description="ユーザーフィードバック"
    )


class InsightHistoryItem(BaseModel):
    """Insights履歴項目"""

    id: str = Field(..., description="Insights ID")
    report_date: str = Field(..., description="レポート対象日")
    user_cd: str = Field(..., description="ユーザーコード")
    str_cd: str = Field(..., description="店舗コード")
    created_at: datetime = Field(..., description="作成日時")
    updated_at: datetime = Field(..., description="更新日時")


class InsightHistoryResponse(BaseModel):
    """Insights履歴レスポンス"""

    insights: List[InsightHistoryItem] = Field(..., description="Insights一覧")
    total_count: int = Field(..., description="総件数")
    current_page: int = Field(..., description="現在のページ")
    total_pages: int = Field(..., description="総ページ数")


class InsightGenerateResponse(BaseModel):
    """Insights生成レスポンス"""

    response: str = Field(..., description="生成されたInsightsテキスト")
    agent_type: str = Field(..., description="エージェントタイプ")
    session_id: str = Field(..., description="セッションID")
    actor_id: str = Field(..., description="アクターID")
    summary_id: str = Field(..., description="サマリーID")


class InsightUpdateResponse(BaseModel):
    """Insights更新レスポンス"""

    message: str = Field(..., description="更新結果メッセージ")
