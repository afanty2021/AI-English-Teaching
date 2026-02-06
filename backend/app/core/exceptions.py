"""
统一异常处理模块 - AI英语教学系统

提供完整的业务异常体系：
- BaseException: 所有业务异常的基类
- AuthenticationError: 认证异常
- BusinessError: 业务异常
- ResourceNotFoundError: 资源不存在异常
- ValidationError: 数据验证异常
- TokenExpiredError: Token过期异常
- PermissionError: 权限异常
"""
from fastapi import HTTPException, status
from typing import Any, Optional


class BaseException(HTTPException):
    """
    业务异常基类

    所有业务异常都应继承此类，提供统一的错误响应格式。
    支持 HTTP 状态码、错误代码和详细消息。

    Attributes:
        status_code: HTTP 状态码
        detail: 错误详情消息
        error_code: 错误代码（默认使用类名）
        headers: 额外的响应头
    """

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_message: str = "服务器内部错误"
    error_code: str = "INTERNAL_ERROR"

    def __init__(
        self,
        detail: str = "",
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        headers: Optional[dict] = None
    ):
        self.status_code = status_code or self.status_code
        self.detail = detail or self.default_message
        self.error_code = error_code or self.error_code
        self.headers = headers
        super().__init__(status_code=self.status_code, detail=self.detail, headers=headers)

    def to_dict(self) -> dict:
        """
        将异常转换为字典格式

        Returns:
            包含错误代码、消息和详细信息的字典
        """
        return {
            "success": False,
            "error": {
                "code": self.error_code,
                "message": self.detail,
            }
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(code={self.error_code}, message={self.detail})>"


class AuthenticationError(BaseException):
    """
    认证异常

    用于用户认证失败的场景，如密码错误、账号不存在等。
    HTTP 状态码: 401 Unauthorized
    """
    status_code = status.HTTP_401_UNAUTHORIZED
    default_message = "认证失败"
    error_code = "AUTHENTICATION_ERROR"


class TokenExpiredError(AuthenticationError):
    """
    Token 过期异常

    用于访问令牌或刷新令牌过期的情况。
    HTTP 状态码: 401 Unauthorized
    """
    default_message = "登录已过期，请重新登录"
    error_code = "TOKEN_EXPIRED"


class InvalidTokenError(AuthenticationError):
    """
    无效 Token 异常

    用于 Token 格式错误或签名验证失败的情况。
    HTTP 状态码: 401 Unauthorized
    """
    default_message = "无效的认证令牌"
    error_code = "INVALID_TOKEN"


class InvalidCredentialsError(AuthenticationError):
    """
    凭证无效异常

    用于用户名密码不匹配的情况。
    HTTP 状态码: 401 Unauthorized
    """
    default_message = "用户名或密码错误"
    error_code = "INVALID_CREDENTIALS"


class BusinessError(BaseException):
    """
    业务异常

    用于业务逻辑验证失败的场景，如参数不合法、业务规则不满足等。
    HTTP 状态码: 400 Bad Request
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_message = "业务处理失败"
    error_code = "BUSINESS_ERROR"


class ValidationError(BusinessError):
    """
    数据验证异常

    用于请求数据验证失败的场景。
    HTTP 状态码: 400 Bad Request
    """
    default_message = "数据验证失败"
    error_code = "VALIDATION_ERROR"


class ResourceNotFoundError(BusinessError):
    """
    资源不存在异常

    用于请求的资源不存在的场景，如用户不存在、题目不存在等。
    HTTP 状态码: 404 Not Found
    """
    status_code = status.HTTP_404_NOT_FOUND
    default_message = "请求的资源不存在"
    error_code = "RESOURCE_NOT_FOUND"


class UserNotFoundError(ResourceNotFoundError):
    """
    用户不存在异常

    用于查找的用户不存在的场景。
    HTTP 状态码: 404 Not Found
    """
    default_message = "用户不存在"
    error_code = "USER_NOT_FOUND"


class StudentNotFoundError(ResourceNotFoundError):
    """
    学生不存在异常

    用于查找的学生档案不存在的场景。
    HTTP 状态码: 404 Not Found
    """
    default_message = "学生档案不存在"
    error_code = "STUDENT_NOT_FOUND"


class PracticeNotFoundError(ResourceNotFoundError):
    """
    练习记录不存在异常

    用于查找的练习记录不存在的场景。
    HTTP 状态码: 404 Not Found
    """
    default_message = "练习记录不存在"
    error_code = "PRACTICE_NOT_FOUND"


class MistakeNotFoundError(ResourceNotFoundError):
    """
    错题不存在异常

    用于查找的错题记录不存在的场景。
    HTTP 状态码: 404 Not Found
    """
    default_message = "错题记录不存在"
    error_code = "MISTAKE_NOT_FOUND"


class ContentNotFoundError(ResourceNotFoundError):
    """
    教学内容不存在异常

    用于查找的教学内容不存在的场景。
    HTTP 状态码: 404 Not Found
    """
    default_message = "教学内容不存在"
    error_code = "CONTENT_NOT_FOUND"


class PermissionError(BaseException):
    """
    权限异常

    用于用户权限不足的场景。
    HTTP 状态码: 403 Forbidden
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_message = "权限不足"
    error_code = "PERMISSION_ERROR"


class ForbiddenError(PermissionError):
    """
    禁止访问异常

    用于用户被明确禁止访问某资源的场景。
    HTTP 状态码: 403 Forbidden
    """
    default_message = "您没有权限执行此操作"
    error_code = "FORBIDDEN"


class RateLimitError(BaseException):
    """
    速率限制异常

    用于请求频率超限的场景。
    HTTP 状态码: 429 Too Many Requests
    """
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_message = "请求过于频繁，请稍后再试"
    error_code = "RATE_LIMIT_ERROR"

    def __init__(
        self,
        detail: str = "请求过于频繁，请稍后再试",
        retry_after: int = 60,
        headers: Optional[dict] = None
    ):
        headers = headers or {}
        headers["Retry-After"] = str(retry_after)
        super().__init__(detail=detail, headers=headers)
        self.retry_after = retry_after


class FileOperationError(BaseException):
    """
    文件操作异常

    用于文件上传、下载、删除等操作失败的场景。
    HTTP 状态码: 500 Internal Server Error
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_message = "文件操作失败"
    error_code = "FILE_OPERATION_ERROR"


class PDFRenderError(FileOperationError):
    """
    PDF 渲染异常

    用于 PDF 导出时渲染失败的场景。
    HTTP 状态码: 500 Internal Server Error
    """
    default_message = "PDF 生成失败"
    error_code = "PDF_RENDER_ERROR"


class AIServiceError(BaseException):
    """
    AI 服务异常

    用于调用 AI 服务（如 OpenAI、Anthropic）失败的场景。
    HTTP 状态码: 503 Service Unavailable
    """
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_message = "AI 服务暂时不可用，请稍后再试"
    error_code = "AI_SERVICE_ERROR"


class DatabaseError(BaseException):
    """
    数据库异常

    用于数据库操作失败的场景。
    HTTP 状态码: 500 Internal Server Error
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_message = "数据库操作失败"
    error_code = "DATABASE_ERROR"


class CacheError(BaseException):
    """
    缓存异常

    用于缓存服务（如 Redis）操作失败的场景。
    HTTP 状态码: 500 Internal Server Error
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_message = "缓存服务异常"
    error_code = "CACHE_ERROR"
