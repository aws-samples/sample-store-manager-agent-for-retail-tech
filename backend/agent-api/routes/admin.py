"""
管理者機能APIルート
定型質問とお知らせ管理のエンドポイント
"""

from fastapi import APIRouter, Query, Depends
from typing import Optional
from utils.auth import get_current_user, CurrentUser
from routes.schema.admin import (
    QuestionCreateRequest,
    QuestionUpdateRequest,
    QuestionListResponse,
    QuestionResponse,
    MessageCreateRequest,
    MessageUpdateRequest,
    MessageListResponse,
    MessageResponse,
    QuestionOperationResponse,
    MessageOperationResponse,
    AdminOperationResponse,
)
from routes.schema.common import APIError
from utils.admin_service import admin_service

router = APIRouter(prefix="/api/admin", tags=["admin"])


# 定型質問管理エンドポイント
@router.get(
    "/survey/questions",
    response_model=QuestionListResponse,
    responses={
        200: {"description": "Questions retrieved successfully"},
        400: {"description": "Bad request", "model": APIError},
        422: {"description": "Validation error"},
    },
)
async def get_questions(
    is_active: bool = Query(True, description="アクティブな質問のみ取得"),
    limit: int = Query(30, ge=1, le=100, description="取得件数上限"),
):
    """定型質問一覧取得"""
    result = admin_service.get_questions(active_only=is_active, limit=limit)
    return QuestionListResponse(**result)


@router.get(
    "/survey/questions/{admin_survey_id}",
    response_model=QuestionResponse,
    responses={
        200: {"description": "Question retrieved successfully"},
        404: {"description": "Question not found", "model": APIError},
        422: {"description": "Validation error"},
    },
)
async def get_question(admin_survey_id: str):
    """定型質問詳細取得"""
    return admin_service.get_question(admin_survey_id)


@router.post(
    "/survey/questions",
    response_model=QuestionOperationResponse,
    responses={
        200: {"description": "Question created successfully"},
        400: {"description": "Bad request", "model": APIError},
        422: {"description": "Validation error"},
    },
)
async def create_question(
    request: QuestionCreateRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """定型質問作成"""
    result = admin_service.create_question(request, current_user)
    return QuestionOperationResponse(**result)


@router.put(
    "/survey/questions/{admin_survey_id}",
    response_model=AdminOperationResponse,
    responses={
        200: {"description": "Question updated successfully"},
        400: {"description": "Bad request", "model": APIError},
        404: {"description": "Question not found", "model": APIError},
        422: {"description": "Validation error"},
    },
)
async def update_question(admin_survey_id: str, request: QuestionUpdateRequest):
    """定型質問更新"""
    result = admin_service.update_question(admin_survey_id, request)
    return AdminOperationResponse(**result)


@router.delete(
    "/survey/questions/{admin_survey_id}",
    response_model=AdminOperationResponse,
    responses={
        200: {"description": "Question deleted successfully"},
        404: {"description": "Question not found", "model": APIError},
        422: {"description": "Validation error"},
    },
)
async def delete_question(admin_survey_id: str):
    """定型質問削除"""
    result = admin_service.delete_question(admin_survey_id)
    return AdminOperationResponse(**result)


# お知らせ管理エンドポイント
@router.get(
    "/messages",
    response_model=MessageListResponse,
    responses={
        200: {"description": "Messages retrieved successfully"},
        400: {"description": "Bad request", "model": APIError},
        422: {"description": "Validation error"},
    },
)
async def get_messages(
    is_active: bool = Query(True, description="アクティブなお知らせのみ取得"),
    limit: int = Query(30, ge=1, le=200, description="取得件数上限"),
):
    """お知らせ一覧取得"""
    result = admin_service.get_messages(active_only=is_active, limit=limit)
    return MessageListResponse(**result)


@router.get(
    "/messages/{admin_messages_id}",
    response_model=MessageResponse,
    responses={
        200: {"description": "Message retrieved successfully"},
        404: {"description": "Message not found", "model": APIError},
        422: {"description": "Validation error"},
    },
)
async def get_message(admin_messages_id: str):
    """お知らせ詳細取得"""
    return admin_service.get_message(admin_messages_id)


@router.post(
    "/messages",
    response_model=MessageOperationResponse,
    responses={
        200: {"description": "Message created successfully"},
        400: {"description": "Bad request", "model": APIError},
        422: {"description": "Validation error"},
    },
)
async def create_message(
    request: MessageCreateRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """お知らせ作成"""
    result = admin_service.create_message(request, current_user)
    return MessageOperationResponse(**result)


@router.put(
    "/messages/{admin_messages_id}",
    response_model=AdminOperationResponse,
    responses={
        200: {"description": "Message updated successfully"},
        400: {"description": "Bad request", "model": APIError},
        404: {"description": "Message not found", "model": APIError},
        422: {"description": "Validation error"},
    },
)
async def update_message(admin_messages_id: str, request: MessageUpdateRequest):
    """お知らせ更新"""
    result = admin_service.update_message(admin_messages_id, request)
    return AdminOperationResponse(**result)


@router.delete(
    "/messages/{admin_messages_id}",
    response_model=AdminOperationResponse,
    responses={
        200: {"description": "Message deleted successfully"},
        404: {"description": "Message not found", "model": APIError},
        422: {"description": "Validation error"},
    },
)
async def delete_message(admin_messages_id: str):
    """お知らせ削除"""
    result = admin_service.delete_message(admin_messages_id)
    return AdminOperationResponse(**result)
