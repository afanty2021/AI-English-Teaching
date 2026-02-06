"""
FastAPI主应用
AI英语教学系统后端入口
"""
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    应用生命周期管理

    在应用启动时执行初始化操作，关闭时执行清理操作。
    """
    # 启动时执行
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 启动中...")
    print(f"📊 环境: {settings.ENVIRONMENT}")
    print(f"🔧 调试模式: {settings.DEBUG}")

    yield

    # 关闭时执行
    print(f"👋 {settings.APP_NAME} 关闭中...")


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.APP_NAME,
    description="AI英语教学系统后端API",
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)


# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册路由
app.include_router(api_router, prefix="/api/v1")

# 注册WebSocket路由
from app.websocket.router import router as ws_router
app.include_router(ws_router, prefix="/api/v1", tags=["WebSocket"])

# 注册全局异常处理器
from app.core.exception_handler import setup_exception_handlers
setup_exception_handlers(app)


# 根路径
@app.get("/")
async def root() -> dict[str, str]:
    """
    根路径

    返回API基本信息。
    """
    return {
        "message": f"欢迎使用{settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "docs": "/api/docs",
        "redoc": "/api/redoc",
    }


# 健康检查端点
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> dict[str, Any]:
    """
    健康检查端点

    用于容器编排和负载均衡器检查服务健康状态。

    Returns:
        包含服务状态、版本和环境信息的字典
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


# 数据库健康检查
@app.get("/health/db", status_code=status.HTTP_200_OK)
async def database_health_check() -> dict[str, Any]:
    """
    数据库健康检查

    检查数据库连接是否正常。

    Returns:
        包含数据库连接状态的字典

    Raises:
        HTTPException: 如果数据库连接失败
    """
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine

    try:
        engine = create_async_engine(settings.DATABASE_URL)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()

        return {
            "status": "healthy",
            "database": "connected",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
            },
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )
