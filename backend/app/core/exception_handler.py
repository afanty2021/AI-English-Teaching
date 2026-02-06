"""
全局异常处理器 - AI英语教学系统

提供 FastAPI 全局异常处理中间件，将所有异常转换为统一格式。
"""
import logging
from typing import Any, Union

from fastapi import FastAPI, Request, HTTPException as FastAPIHTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import (
    BaseException,
    AuthenticationError,
    BusinessError,
    ValidationError,
    ResourceNotFoundError,
    PermissionError,
    RateLimitError,
)


logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI) -> None:
    """
    配置 FastAPI 全局异常处理器

    Args:
        app: FastAPI 应用实例
    """

    @app.exception_handler(BaseException)
    async def base_exception_handler(request: Request, exc: BaseException) -> JSONResponse:
        """
        处理所有业务异常

        将业务异常转换为统一的 JSON 响应格式。
        """
        logger.warning(
            f"业务异常: {exc.error_code} - {exc.detail}",
            extra={
                "url": str(request.url),
                "method": request.method,
                "error_code": exc.error_code,
                "error_detail": exc.detail,
            }
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.error_code,
                    "message": exc.detail,
                }
            },
            headers=exc.headers
        )

    @app.exception_handler(AuthenticationError)
    async def authentication_exception_handler(
        request: Request,
        exc: AuthenticationError
    ) -> JSONResponse:
        """
        处理认证异常

        认证失败时返回 401 状态码，包含错误代码和消息。
        """
        logger.warning(
            f"认证失败: {exc.error_code} - {exc.detail}",
            extra={
                "url": str(request.url),
                "method": request.method,
                "error_code": exc.error_code,
            }
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.error_code,
                    "message": exc.detail,
                }
            },
            headers={"WWW-Authenticate": "Bearer"} if not exc.headers else exc.headers
        )

    @app.exception_handler(ResourceNotFoundError)
    async def resource_not_found_handler(
        request: Request,
        exc: ResourceNotFoundError
    ) -> JSONResponse:
        """
        处理资源不存在异常

        返回 404 状态码，包含具体的资源类型信息。
        """
        logger.info(
            f"资源未找到: {exc.error_code} - {exc.detail}",
            extra={
                "url": str(request.url),
                "method": request.method,
                "error_code": exc.error_code,
            }
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.error_code,
                    "message": exc.detail,
                }
            }
        )

    @app.exception_handler(PermissionError)
    async def permission_exception_handler(
        request: Request,
        exc: PermissionError
    ) -> JSONResponse:
        """
        处理权限异常

        返回 403 状态码。
        """
        logger.warning(
            f"权限不足: {exc.error_code} - {exc.detail}",
            extra={
                "url": str(request.url),
                "method": request.method,
                "user_id": getattr(request.state, "user_id", None),
                "error_code": exc.error_code,
            }
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.error_code,
                    "message": exc.detail,
                }
            }
        )

    @app.exception_handler(RateLimitError)
    async def rate_limit_exception_handler(
        request: Request,
        exc: RateLimitError
    ) -> JSONResponse:
        """
        处理速率限制异常

        返回 429 状态码，包含 Retry-After 头。
        """
        logger.warning(
            f"请求频率超限: {exc.error_code}",
            extra={
                "url": str(request.url),
                "method": request.method,
                "retry_after": exc.retry_after,
            }
        )

        headers = exc.headers or {}
        headers["Retry-After"] = str(exc.retry_after)

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.error_code,
                    "message": exc.detail,
                }
            },
            headers=headers
        )

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: ValidationError
    ) -> JSONResponse:
        """
        处理数据验证异常

        返回 400 状态码，包含验证错误详情。
        """
        logger.warning(
            f"数据验证失败: {exc.error_code} - {exc.detail}",
            extra={
                "url": str(request.url),
                "method": request.method,
                "error_code": exc.error_code,
                "detail": exc.detail,
            }
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.error_code,
                    "message": exc.detail,
                }
            }
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(
        request: Request,
        exc: RequestValidationError
    ) -> JSONResponse:
        """
        处理 FastAPI 请求验证异常

        返回 422 状态码，包含详细的验证错误信息。
        """
        errors = []
        for error in exc.errors():
            loc = " -> ".join(str(l) for l in error["loc"])
            msg = error["msg"]
            errors.append(f"{loc}: {msg}")

        logger.warning(
            f"请求验证失败: {errors}",
            extra={
                "url": str(request.url),
                "method": request.method,
                "validation_errors": errors,
            }
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "请求数据验证失败",
                    "details": errors,
                }
            }
        )

    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(
        request: Request,
        exc: StarletteHTTPException
    ) -> JSONResponse:
        """
        处理 Starlette HTTP 异常

        作为后备处理器，处理其他 HTTP 异常。
        """
        logger.info(
            f"HTTP 异常: {exc.status_code} - {exc.detail}",
            extra={
                "url": str(request.url),
                "method": request.method,
                "status_code": exc.status_code,
            }
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": str(exc.detail),
                }
            },
            headers=exc.headers
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        处理所有未捕获的异常

        作为最后的异常处理器，确保所有异常都有响应。
        同时记录详细的错误日志以便排查。
        """
        logger.error(
            f"未捕获的异常: {type(exc).__name__} - {str(exc)}",
            extra={
                "url": str(request.url),
                "method": request.method,
                "exception_type": type(exc).__name__,
                "exception_message": str(exc),
                "traceback": getattr(exc, "__traceback__", None),
            },
            exc_info=True
        )

        # 生产环境不返回具体错误详情
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "服务器内部错误，请稍后再试",
                }
            }
        )
