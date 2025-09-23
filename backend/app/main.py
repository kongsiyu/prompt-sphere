"""主FastAPI应用模块。

该模块提供：
- FastAPI应用实例创建和配置
- 中间件集成（CORS、Gzip等）
- 路由注册和API版本控制
- 异常处理器配置
- 应用生命周期管理
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.api.health import router as health_router
from app.api import (
    setup_api_middleware,
    setup_exception_handlers,
    configure_api_docs,
    create_api_router,
    API_TITLE,
    API_VERSION,
    API_DESCRIPTION
)
from app.core.config import settings
from app.core.redis import close_redis_client
from app.services.base import register_service
from backend.database.session import session_manager

# 配置日志
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    应用生命周期管理。

    处理应用启动和关闭时的初始化和清理工作。

    Args:
        app: FastAPI应用实例

    Yields:
        None
    """
    # === 应用启动 ===
    logger.info("Starting application...")

    try:
        # 初始化数据库连接池
        logger.info("Initializing database connection pool...")
        # 数据库连接池在第一次使用时自动初始化

        # 初始化Redis连接
        logger.info("Initializing Redis connection...")
        # Redis连接在第一次使用时自动初始化

        # 注册服务
        logger.info("Registering services...")
        # TODO: 在这里注册具体的服务实例
        # 例如：
        # from app.services.prompt_service import PromptService
        # register_service("prompt_service", PromptService())

        # 预热缓存
        logger.info("Warming up caches...")
        # TODO: 可以在这里预加载一些常用数据到缓存

        logger.info("Application startup completed successfully")

    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise

    # === 应用运行 ===
    yield

    # === 应用关闭 ===
    logger.info("Shutting down application...")

    try:
        # 关闭数据库会话
        logger.info("Closing database sessions...")
        await session_manager.close_all_sessions()

        # 关闭Redis连接
        logger.info("Closing Redis connections...")
        await close_redis_client()

        # 清理缓存
        logger.info("Cleaning up caches...")
        # TODO: 可以在这里执行缓存清理

        logger.info("Application shutdown completed successfully")

    except Exception as e:
        logger.error(f"Error during application shutdown: {e}")


def create_application() -> FastAPI:
    """
    创建并配置FastAPI应用实例。

    Returns:
        配置完成的FastAPI应用实例
    """
    logger.info("Creating FastAPI application...")

    # 创建FastAPI应用实例
    app = FastAPI(
        title=API_TITLE,
        version=API_VERSION,
        description=API_DESCRIPTION,
        debug=settings.debug,
        docs_url=None,  # 自定义文档URL
        redoc_url=None,  # 自定义ReDoc URL
        openapi_url="/openapi.json" if settings.debug else None,
        lifespan=lifespan  # 设置生命周期管理
    )

    # 配置API中间件
    logger.info("Setting up API middleware...")
    setup_api_middleware(app)

    # 配置异常处理器
    logger.info("Setting up exception handlers...")
    setup_exception_handlers(app)

    # 配置API文档
    logger.info("Configuring API documentation...")
    configure_api_docs(app)

    # 注册路由
    logger.info("Registering API routes...")

    # 注册根级API路由（/, /info等）
    root_router = create_api_router()
    app.include_router(root_router, tags=["系统"])

    # 注册健康检查路由
    app.include_router(health_router, tags=["健康检查"])

    # 注册v1 API路由
    app.include_router(api_router, prefix=settings.api_v1_prefix)

    # 添加中间件以记录请求信息
    @app.middleware("http")
    async def log_requests(request, call_next):
        """记录HTTP请求信息。"""
        import time
        import uuid

        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # 记录请求开始
        start_time = time.time()
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host if request.client else None
            }
        )

        # 处理请求
        try:
            response = await call_next(request)

            # 记录请求完成
            process_time = time.time() - start_time
            logger.info(
                f"Request completed: {request.method} {request.url.path} - {response.status_code}",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "process_time": process_time
                }
            )

            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            # 记录请求错误
            process_time = time.time() - start_time
            logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "process_time": process_time
                },
                exc_info=True
            )
            raise

    logger.info("FastAPI application created successfully")
    return app


# 创建FastAPI应用实例
app = create_application()

# 导出应用实例
__all__ = ["app", "create_application"]