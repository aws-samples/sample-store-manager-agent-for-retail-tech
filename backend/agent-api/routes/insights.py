"""
Insights機能のAPIルート定義
"""

from datetime import date
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Path, Depends
from routes.schema.insights import (
    InsightGenerateRequest,
    InsightSaveRequest,
    InsightFeedbackRequest,
    InsightResponse,
    InsightHistoryResponse,
    InsightHistoryItem,
    InsightGenerateResponse,
    InsightUpdateResponse,
)
from routes.schema.common import APIError
from utils.insights_service import InsightsService
from utils.exceptions import NotFoundException, ValidationException
from utils.auth import get_current_user, CurrentUser

router = APIRouter(prefix="/api/insights", tags=["insights"])

insights_service = InsightsService()


@router.get(
    "/daily",
    response_model=InsightResponse,
    responses={
        200: {"description": "Daily insights retrieved successfully"},
        400: {"description": "Bad request", "model": APIError},
        401: {"description": "Unauthorized", "model": APIError},
        404: {"description": "Insights not found", "model": APIError},
        422: {"description": "Validation error"},
    },
)
async def get_daily_insights(
    current_user: CurrentUser = Depends(get_current_user),
    report_date: date = Query(..., description="レポート対象日"),
):
    """
    日次Insights取得

    指定された条件に一致する日次Insightsを取得します。
    """
    try:
        insight = insights_service.get_daily_insights(current_user, report_date)

        if not insight:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "NOT_FOUND",
                        "message": "指定された条件のInsightsが見つかりません",
                    }
                },
            )

        return InsightResponse(**insight)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": f"Insights取得中にエラーが発生しました: {str(e)}",
                }
            },
        )


@router.post(
    "/daily/generate",
    response_model=InsightGenerateResponse,
    responses={
        200: {"description": "Daily insights generated successfully"},
        400: {"description": "Bad request", "model": APIError},
        401: {"description": "Unauthorized", "model": APIError},
        422: {"description": "Validation error"},
    },
)
async def generate_daily_insights(
    request: InsightGenerateRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    日次Insights生成

    指定された条件で新しい日次Insightsを生成します。
    """
    try:
        result = insights_service.generate_daily_insights(
            current_user,
            request.agent_type,
            request.prompt,
            request.session_id,
            request.report_date,
        )

        return InsightGenerateResponse(
            response=result["response"],
            agent_type=result["agent_type"],
            session_id=result["session_id"],
            actor_id=result["actor_id"],
            summary_id=result["summary_id"],
        )

    except ValidationException as e:
        raise HTTPException(
            status_code=409,
            detail={"error": {"code": "ALREADY_EXISTS", "message": str(e)}},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": f"Insights生成中にエラーが発生しました: {str(e)}",
                }
            },
        )


@router.put(
    "/daily/{insight_id}",
    response_model=InsightUpdateResponse,
    responses={
        200: {"description": "Daily insights saved successfully"},
        400: {"description": "Bad request", "model": APIError},
        401: {"description": "Unauthorized", "model": APIError},
        404: {"description": "Insights not found", "model": APIError},
        422: {"description": "Validation error"},
    },
)
async def save_daily_insights(
    insight_id: str = Path(..., description="Insights ID"),
    request: InsightSaveRequest = None,
    current_user: CurrentUser = Depends(get_current_user)
):
    """
    日次Insights保存・更新

    指定されたInsightsの内容を保存・更新します。
    """
    try:
        insight = insights_service.save_daily_insights(
            current_user,
            insight_id,
            request.report_date,
            request.status,
            request.report_text,
            request.session_id,
        )

        return InsightUpdateResponse(message="Insightsを保存しました")

    except NotFoundException as e:
        raise HTTPException(
            status_code=404, detail={"error": {"code": "NOT_FOUND", "message": str(e)}}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": f"Insights保存中にエラーが発生しました: {str(e)}",
                }
            },
        )


@router.put(
    "/daily/{insight_id}/feedback",
    response_model=InsightUpdateResponse,
    responses={
        200: {"description": "Feedback saved successfully"},
        400: {"description": "Bad request", "model": APIError},
        404: {"description": "Insights not found", "model": APIError},
        422: {"description": "Validation error"},
    },
)
async def save_feedback(
    insight_id: str = Path(..., description="Insights ID"),
    request: InsightFeedbackRequest = None,
):
    """
    フィードバック保存

    指定されたInsightsにフィードバックを保存します。
    """
    try:
        insight = insights_service.save_feedback(insight_id, request.user_feedback)

        return InsightUpdateResponse(message="フィードバックを保存しました")

    except NotFoundException as e:
        raise HTTPException(
            status_code=404, detail={"error": {"code": "NOT_FOUND", "message": str(e)}}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": f"フィードバック保存中にエラーが発生しました: {str(e)}",
                }
            },
        )


@router.get(
    "/daily/history",
    response_model=InsightHistoryResponse,
    responses={
        200: {"description": "Insights history retrieved successfully"},
        400: {"description": "Bad request", "model": APIError},
        401: {"description": "Unauthorized", "model": APIError},
        422: {"description": "Validation error"},
    },
)
async def get_insights_history(
    current_user: CurrentUser = Depends(get_current_user),
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(30, ge=1, le=100, description="1ページあたりの件数"),
):
    """
    Insights履歴取得

    Insightsの履歴を取得します。
    """
    try:
        insights, total_count, total_pages = insights_service.get_insights_history(
            current_user, page, limit
        )

        insight_items = [
            InsightHistoryItem(
                id=insight["id"],
                report_date=insight["report_date"].strftime("%Y-%m-%d"),
                user_cd=insight["user_cd"],
                str_cd=insight["str_cd"],
                created_at=insight["created_at"],
                updated_at=insight["updated_at"],
            )
            for insight in insights
        ]

        return InsightHistoryResponse(
            insights=insight_items,
            total_count=total_count,
            current_page=page,
            total_pages=total_pages,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": f"Insights履歴取得中にエラーが発生しました: {str(e)}",
                }
            },
        )


@router.get(
    "/daily/{insight_id}",
    response_model=InsightResponse,
    responses={
        200: {"description": "Insight detail retrieved successfully"},
        404: {"description": "Insights not found", "model": APIError},
        422: {"description": "Validation error"},
    },
)
async def get_insight_detail(insight_id: str = Path(..., description="Insights ID")):
    """
    Insights詳細取得

    指定されたIDのInsights詳細情報を取得します。
    """
    try:
        insight = insights_service.get_insight_by_id(insight_id)

        return InsightResponse(**insight)

    except NotFoundException as e:
        raise HTTPException(
            status_code=404, detail={"error": {"code": "NOT_FOUND", "message": str(e)}}
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": f"Insights詳細取得中にエラーが発生しました: {str(e)}",
                }
            },
        )
