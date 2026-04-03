"""
カスタム例外とエラーハンドリング
Store Daily QA System API で使用する例外クラスとエラーハンドラー
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from utils.logger import get_logger

logger = get_logger("exceptions")


class APIException(Exception):
    """API基底例外クラス"""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500,
        field: Optional[str] = None,
        reason: Optional[str] = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.field = field
        self.reason = reason
        super().__init__(self.message)


class ValidationException(APIException):
    """バリデーション例外"""

    def __init__(
        self, message: str, field: Optional[str] = None, reason: Optional[str] = None
    ):
        super().__init__(
            code="VALIDATION_ERROR",
            message=message,
            status_code=400,
            field=field,
            reason=reason,
        )


class NotFoundException(APIException):
    """リソース未発見例外"""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            code="NOT_FOUND",
            message=f"{resource_type} not found",
            status_code=404,
            reason=f"{resource_type} with ID '{resource_id}' does not exist",
        )


class AlreadyExistsException(APIException):
    """リソース重複例外"""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            code="ALREADY_EXISTS",
            message=f"{resource_type} already exists",
            status_code=409,
            reason=f"{resource_type} with ID '{resource_id}' already exists",
        )


class UnauthorizedException(APIException):
    """認証例外"""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(code="UNAUTHORIZED", message=message, status_code=401)


class ForbiddenException(APIException):
    """権限例外"""

    def __init__(self, message: str = "Access forbidden"):
        super().__init__(code="FORBIDDEN", message=message, status_code=403)


class InternalServerException(APIException):
    """内部サーバーエラー例外"""

    def __init__(self, message: str = "Internal server error"):
        super().__init__(code="INTERNAL_ERROR", message=message, status_code=500)


def create_error_response(
    code: str,
    message: str,
    status_code: int,
    field: Optional[str] = None,
    reason: Optional[str] = None,
) -> JSONResponse:
    """エラーレスポンス作成"""
    error_data = {"error": {"code": code, "message": message}}

    # 詳細情報がある場合は追加
    if field or reason:
        error_data["error"]["details"] = {}
        if field:
            error_data["error"]["details"]["field"] = field
        if reason:
            error_data["error"]["details"]["reason"] = reason

    return JSONResponse(status_code=status_code, content=error_data)


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """API例外ハンドラー"""
    logger.error(f"API Exception: {exc.code} - {exc.message}")

    return create_error_response(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        field=exc.field,
        reason=exc.reason,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """バリデーション例外ハンドラー"""
    logger.error(f"Validation Error: {exc.errors()}")

    # 最初のエラーを取得
    first_error = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(loc) for loc in first_error.get("loc", []))
    reason = first_error.get("msg", "Validation failed")

    return create_error_response(
        code="VALIDATION_ERROR",
        message="Request validation failed",
        status_code=400,
        field=field,
        reason=reason,
    )


async def pydantic_validation_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Pydanticバリデーション例外ハンドラー"""
    logger.error(f"Pydantic Validation Error: {exc.errors()}")

    # 最初のエラーを取得
    first_error = exc.errors()[0] if exc.errors() else {}
    field = ".".join(str(loc) for loc in first_error.get("loc", []))
    reason = first_error.get("msg", "Validation failed")

    return create_error_response(
        code="VALIDATION_ERROR",
        message="Data validation failed",
        status_code=400,
        field=field,
        reason=reason,
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP例外ハンドラー"""
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")

    # HTTPステータスコードに基づいてエラーコードを決定
    error_code_mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        500: "INTERNAL_ERROR",
    }

    error_code = error_code_mapping.get(exc.status_code, "UNKNOWN_ERROR")

    return create_error_response(
        code=error_code, message=str(exc.detail), status_code=exc.status_code
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """一般例外ハンドラー"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)

    return create_error_response(
        code="INTERNAL_ERROR", message="An unexpected error occurred", status_code=500
    )


# エラーハンドラー登録用の辞書
EXCEPTION_HANDLERS = {
    APIException: api_exception_handler,
    RequestValidationError: validation_exception_handler,
    ValidationError: pydantic_validation_exception_handler,
    HTTPException: http_exception_handler,
    Exception: general_exception_handler,
}
