"""
Pydantic schemas模块
定义所有API的请求和响应Schema
"""
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    AuthResponse,
    RefreshTokenRequest,
    ChangePasswordRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
)

from app.schemas.recommendation import (
    StudentProfile,
    ReadingRecommendation,
    ExerciseRecommendation,
    SpeakingRecommendation,
    DailyContentResponse,
    ContentDetailResponse,
    CompleteContentRequest,
    CompleteContentResponse,
    RecommendationFilter,
)

__all__ = [
    # Auth schemas
    "RegisterRequest",
    "LoginRequest",
    "TokenResponse",
    "UserResponse",
    "AuthResponse",
    "RefreshTokenRequest",
    "ChangePasswordRequest",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    # Recommendation schemas
    "StudentProfile",
    "ReadingRecommendation",
    "ExerciseRecommendation",
    "SpeakingRecommendation",
    "DailyContentResponse",
    "ContentDetailResponse",
    "CompleteContentRequest",
    "CompleteContentResponse",
    "RecommendationFilter",
]
