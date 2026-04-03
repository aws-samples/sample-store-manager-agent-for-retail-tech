"""
AIチャット機能APIルート
AIチャットメッセージ送信とセッション保存エンドポイント
"""

from fastapi import APIRouter, HTTPException, Depends
from routes.schema.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSessionSaveRequest,
    ChatSessionSaveResponse,
    ChatSessionResponse,
)
from routes.schema.common import APIError
from utils.chat_service import chat_service
from utils.auth import get_current_user, CurrentUser

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post(
    "/message",
    response_model=ChatMessageResponse,
    responses={
        200: {"description": "Chat message sent successfully"},
        400: {"description": "Bad request", "model": APIError},
        401: {"description": "Unauthorized", "model": APIError},
        422: {"description": "Validation error"},
    },
)
async def send_chat_message(
    request: ChatMessageRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """AIチャットメッセージ送信"""
    return chat_service.send_message(request, current_user)


@router.post(
    "/session/save",
    response_model=ChatSessionSaveResponse,
    responses={
        200: {"description": "Chat session saved successfully"},
        400: {"description": "Bad request", "model": APIError},
        401: {"description": "Unauthorized", "model": APIError},
        422: {"description": "Validation error"},
    },
)
async def save_chat_session(
    request: ChatSessionSaveRequest,
    current_user: CurrentUser = Depends(get_current_user)
):
    """チャットセッション保存"""
    result = chat_service.save_chat_session(request, current_user)
    return ChatSessionSaveResponse(**result)


@router.get(
    "/session",
    response_model=ChatSessionResponse,
    responses={
        200: {"description": "Chat session retrieved successfully"},
        400: {"description": "Bad request", "model": APIError},
        404: {"description": "Chat session not found", "model": APIError},
        422: {"description": "Validation error"},
    },
)
async def get_chat_session_by_survey(survey_id: str):
    """サーベイIDからチャットセッション取得"""
    session = chat_service.get_chat_session_by_survey(survey_id)

    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    return session
