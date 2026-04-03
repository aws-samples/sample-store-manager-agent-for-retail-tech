"""
FastAPI application for Store Daily QA System API
"""

import os
from mangum import Mangum
from utils.logger import get_logger

logger = get_logger("api-main")

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

# ルートのインポート
from routes.admin import router as admin_router
from routes.survey import router as survey_router
from routes.chat import router as chat_router
from routes.insights import router as insights_router

# カスタム例外のインポート
from utils.exceptions import (
    NotFoundException,
    ValidationException as CustomValidationException,
    AlreadyExistsException,
    UnauthorizedException,
    ForbiddenException,
    InternalServerException,
)

app = FastAPI(
    title="Store Daily QA System API",
    description="API for store staff daily QA system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に制限する
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# エラーハンドラー
@app.exception_handler(NotFoundException)
async def not_found_error_handler(request: Request, exc: NotFoundException):
    """404エラーハンドラー"""
    return JSONResponse(
        status_code=404, content={"error": {"code": "NOT_FOUND", "message": str(exc)}}
    )


@app.exception_handler(CustomValidationException)
async def validation_error_handler(request: Request, exc: CustomValidationException):
    """バリデーションエラーハンドラー"""
    return JSONResponse(
        status_code=400,
        content={"error": {"code": "VALIDATION_ERROR", "message": str(exc)}},
    )


@app.exception_handler(AlreadyExistsException)
async def already_exists_error_handler(request: Request, exc: AlreadyExistsException):
    """既存リソースエラーハンドラー"""
    return JSONResponse(
        status_code=409,
        content={"error": {"code": "ALREADY_EXISTS", "message": str(exc)}},
    )


@app.exception_handler(UnauthorizedException)
async def unauthorized_error_handler(request: Request, exc: UnauthorizedException):
    """認証エラーハンドラー"""
    return JSONResponse(
        status_code=401,
        content={"error": {"code": "UNAUTHORIZED", "message": str(exc)}},
    )


@app.exception_handler(ForbiddenException)
async def forbidden_error_handler(request: Request, exc: ForbiddenException):
    """権限エラーハンドラー"""
    return JSONResponse(
        status_code=403, content={"error": {"code": "FORBIDDEN", "message": str(exc)}}
    )


@app.exception_handler(InternalServerException)
async def internal_server_error_handler(request: Request, exc: InternalServerException):
    """内部サーバーエラーハンドラー"""
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "内部サーバーエラーが発生しました",
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(
    request: Request, exc: RequestValidationError
):
    """リクエストバリデーションエラーハンドラー"""
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "リクエストの形式が正しくありません",
                "details": exc.errors(),
            }
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """一般的な例外ハンドラー"""
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "予期しないエラーが発生しました",
            }
        },
    )


# ルートの登録
app.include_router(admin_router)
app.include_router(survey_router)
app.include_router(chat_router)
app.include_router(insights_router)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Store Daily QA System API is running",
        "version": "1.0.0",
        "status": "healthy",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Store Daily QA System API",
        "version": "1.0.0",
    }


@app.get("/api/info")
async def api_info():
    """API情報エンドポイント"""
    return {
        "title": "Store Daily QA System API",
        "description": "店舗スタッフの日次QAシステムAPI",
        "version": "1.0.0",
        "endpoints": {
            "admin": "/api/admin",
            "survey": "/api/survey",
            "chat": "/api/chat",
            "insights": "/api/insights",
        },
        "documentation": {"swagger": "/docs", "redoc": "/redoc"},
    }


def lambda_handler(event, context):
    return Mangum(app)(event, context)


handler = lambda_handler
