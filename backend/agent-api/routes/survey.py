"""
サーベイ機能APIルート
サーベイ回答の保存・取得・更新エンドポイント
"""

from fastapi import APIRouter, Query, Depends
from typing import Optional
from routes.schema.survey import (
    SurveyAnswerRequest,
    SurveyAnswerUpdateRequest,
    SurveyAnswerResponse,
    SurveyAnswerListResponse,
    SurveyOperationResponse,
)
from routes.schema.common import APIError
from utils.survey_service import survey_service
from utils.logger import get_logger
from utils.auth import get_current_user, CurrentUser

logger = get_logger("survey-routes")

router = APIRouter(prefix="/api/survey", tags=["survey"])


@router.post(
    "/answers",
    response_model=SurveyOperationResponse,
    responses={
        200: {"description": "Survey answer saved successfully"},
        400: {"description": "Bad request", "model": APIError},
        401: {"description": "Unauthorized", "model": APIError},
        422: {"description": "Validation error"},
    },
)
async def save_survey_answer(
    request: SurveyAnswerRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """サーベイ回答保存"""
    result = survey_service.save_survey_answer(request, current_user)
    return SurveyOperationResponse(**result)


@router.put(
    "/answers/{survey_id}",
    response_model=SurveyOperationResponse,
    responses={
        200: {"description": "Survey answer updated successfully"},
        400: {"description": "Bad request", "model": APIError},
        404: {"description": "Survey not found", "model": APIError},
        422: {"description": "Validation error"},
    },
)
async def update_survey_answer(survey_id: str, request: SurveyAnswerUpdateRequest):
    """サーベイ回答更新"""
    result = survey_service.update_survey_answer(survey_id, request)
    return SurveyOperationResponse(**result)


@router.get(
    "/answers",
    response_model=SurveyAnswerListResponse,
    responses={
        200: {"description": "Survey answers retrieved successfully"},
        400: {"description": "Bad request", "model": APIError},
        401: {"description": "Unauthorized", "model": APIError},
        422: {"description": "Validation error"},
    },
)
async def get_survey_answers(
    current_user: CurrentUser = Depends(get_current_user),
    page: int = Query(1, ge=1, description="ページ番号"),
    limit: int = Query(30, ge=1, le=100, description="1ページあたりの件数"),
):
    """サーベイ回答履歴取得"""
    logger.info(
        f"Survey answers request - page: {page}, limit: {limit}"
    )

    result = survey_service.get_survey_answers(current_user, page=page, limit=limit)

    logger.info(
        f"Survey answers response - total_count: {result.get('total_count', 0)}, answers_count: {len(result.get('answers', []))}"
    )
    logger.debug(f"Survey answers full response: {result}")

    return SurveyAnswerListResponse(**result)


@router.get(
    "/answers/{survey_id}",
    response_model=SurveyAnswerResponse,
    responses={
        200: {"description": "Survey answer retrieved successfully"},
        404: {"description": "Survey not found", "model": APIError},
        422: {"description": "Validation error"},
    },
)
async def get_survey_answer(survey_id: str):
    """サーベイ回答詳細取得"""
    return survey_service.get_survey_answer(survey_id)
