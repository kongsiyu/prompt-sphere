"""API端点包和路由架构。

该模块提供：
- API路由组织和版本控制
- 请求/响应模型统一规范
- API文档和验证集成
- 中间件和错误处理集成
"""

from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.core.config import get_settings
from app.core.dependencies import get_system_health

# 配置日志
logger = logging.getLogger(__name__)

# 全局API配置
API_TITLE = "AI系统提示词生成器 API"
API_DESCRIPTION = """
## AI系统提示词生成器 API

该API提供强大的AI系统提示词生成和管理功能。

### 主要特性

* **提示词管理** - 创建、编辑、版本控制提示词
* **模板系统** - 可重用的提示词模板
* **AI集成** - 支持多种AI模型（DashScope、OpenAI等）
* **用户管理** - 用户认证和权限控制
* **缓存优化** - Redis缓存提升性能
* **健康监控** - 系统健康状态监控

### API版本

当前API版本：v1

所有API端点都使用 `/api/v1` 前缀。

### 认证方式

API使用JWT Bearer Token进行认证：

```
Authorization: Bearer <your_token>
```

### 响应格式

所有API响应都遵循统一的JSON格式：

```json
{
    "success": true,
    "data": {...},
    "message": "操作成功",
    "timestamp": "2023-01-01T00:00:00Z",
    "request_id": "uuid"
}
```

错误响应格式：

```json
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "错误描述",
        "details": {...}
    },
    "timestamp": "2023-01-01T00:00:00Z",
    "request_id": "uuid"
}
```

### 状态码

* `200` - 操作成功
* `201` - 资源创建成功
* `400` - 请求参数错误
* `401` - 未授权
* `403` - 权限不足
* `404` - 资源不存在
* `409` - 资源冲突
* `422` - 数据验证失败
* `500` - 服务器内部错误
* `503` - 服务不可用

### 限流

API实现了基于用户的限流策略：

* 每分钟最多100个请求
* 每小时最多1000个请求
* 每天最多10000个请求

### 缓存

部分查询接口实现了智能缓存：

* 模板列表缓存 - 5分钟
* 用户信息缓存 - 10分钟
* 系统配置缓存 - 30分钟
"""

API_VERSION = "1.0.0"
API_CONTACT = {
    "name": "API Support",
    "url": "https://github.com/kongsiyu/prompt-sphere",
    "email": "support@prompt-sphere.com"
}
API_LICENSE = {
    "name": "MIT",
    "url": "https://opensource.org/licenses/MIT"
}

# 全局API路由器
main_router = APIRouter()


class APIResponse:
    """标准API响应格式。"""

    @staticmethod
    def success(
        data: Any = None,
        message: str = "操作成功",
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建成功响应。

        Args:
            data: 响应数据
            message: 响应消息
            request_id: 请求ID

        Returns:
            标准成功响应格式
        """
        return {
            "success": True,
            "data": data,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id
        }

    @staticmethod
    def error(
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建错误响应。

        Args:
            code: 错误代码
            message: 错误消息
            details: 错误详情
            request_id: 请求ID

        Returns:
            标准错误响应格式
        """
        return {
            "success": False,
            "error": {
                "code": code,
                "message": message,
                "details": details or {}
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id
        }

    @staticmethod
    def paginated(
        items: list,
        total: int,
        page: int,
        size: int,
        message: str = "查询成功",
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建分页响应。

        Args:
            items: 数据列表
            total: 总数量
            page: 当前页码
            size: 每页大小
            message: 响应消息
            request_id: 请求ID

        Returns:
            标准分页响应格式
        """
        total_pages = (total + size - 1) // size  # 向上取整

        return {
            "success": True,
            "data": {
                "items": items,
                "pagination": {
                    "total": total,
                    "page": page,
                    "size": size,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            },
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": request_id
        }


def create_api_router() -> APIRouter:
    """
    创建主API路由器。

    Returns:
        配置好的API路由器
    """
    router = APIRouter()

    # 根路径信息
    @router.get(
        "/",
        summary="API根信息",
        description="获取API基本信息和状态",
        tags=["系统"]
    )
    async def api_root():
        """API根端点，返回基本信息。"""
        settings = get_settings()
        return APIResponse.success({
            "name": API_TITLE,
            "version": API_VERSION,
            "description": "AI系统提示词生成器 API",
            "docs_url": "/docs" if settings.debug else None,
            "redoc_url": "/redoc" if settings.debug else None,
            "health_url": "/health",
            "api_prefix": settings.api_v1_prefix,
            "environment": "development" if settings.debug else "production",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    # API信息端点
    @router.get(
        "/info",
        summary="API详细信息",
        description="获取API详细配置信息",
        tags=["系统"]
    )
    async def api_info():
        """获取API详细信息。"""
        settings = get_settings()
        return APIResponse.success({
            "api": {
                "title": API_TITLE,
                "version": API_VERSION,
                "description": API_DESCRIPTION,
                "contact": API_CONTACT,
                "license": API_LICENSE
            },
            "server": {
                "host": settings.host,
                "port": settings.port,
                "debug": settings.debug,
                "cors_origins": settings.cors_origins
            },
            "features": {
                "authentication": True,
                "caching": True,
                "rate_limiting": True,
                "api_docs": settings.debug,
                "health_check": True
            },
            "endpoints": {
                "v1_prefix": settings.api_v1_prefix,
                "health": "/health",
                "docs": "/docs" if settings.debug else None,
                "redoc": "/redoc" if settings.debug else None
            }
        })

    return router


def setup_api_middleware(app: FastAPI) -> None:
    """
    设置API中间件。

    Args:
        app: FastAPI应用实例
    """
    settings = get_settings()

    # CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Gzip压缩中间件
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    logger.info("API middleware configured")


def setup_exception_handlers(app: FastAPI) -> None:
    """
    设置全局异常处理器。

    Args:
        app: FastAPI应用实例
    """

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        """404错误处理。"""
        return JSONResponse(
            status_code=404,
            content=APIResponse.error(
                code="NOT_FOUND",
                message="请求的资源不存在",
                details={"path": str(request.url.path)}
            )
        )

    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc):
        """500错误处理。"""
        logger.error(f"Internal server error: {exc}")
        return JSONResponse(
            status_code=500,
            content=APIResponse.error(
                code="INTERNAL_ERROR",
                message="服务器内部错误",
                details={"path": str(request.url.path)}
            )
        )

    logger.info("Exception handlers configured")


def create_openapi_schema(app: FastAPI) -> Dict[str, Any]:
    """
    创建自定义OpenAPI架构。

    Args:
        app: FastAPI应用实例

    Returns:
        OpenAPI架构字典
    """
    return get_openapi(
        title=API_TITLE,
        version=API_VERSION,
        description=API_DESCRIPTION,
        routes=app.routes,
        contact=API_CONTACT,
        license_info=API_LICENSE,
        servers=[
            {
                "url": "/",
                "description": "Current server"
            }
        ],
        tags=[
            {
                "name": "系统",
                "description": "系统相关端点（健康检查、信息查询等）"
            },
            {
                "name": "认证",
                "description": "用户认证和授权"
            },
            {
                "name": "提示词",
                "description": "提示词管理（CRUD操作）"
            },
            {
                "name": "模板",
                "description": "提示词模板管理"
            },
            {
                "name": "AI服务",
                "description": "AI模型集成（DashScope、OpenAI等）"
            },
            {
                "name": "用户",
                "description": "用户管理"
            }
        ]
    )


def configure_api_docs(app: FastAPI) -> None:
    """
    配置API文档。

    Args:
        app: FastAPI应用实例
    """
    settings = get_settings()

    if not settings.debug:
        # 生产环境隐藏文档
        app.openapi_url = None
        app.docs_url = None
        app.redoc_url = None
        return

    # 自定义OpenAPI架构
    app.openapi = lambda: create_openapi_schema(app)

    # 自定义文档页面
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        """自定义Swagger UI。"""
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{API_TITLE} - Swagger UI",
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css",
        )

    @app.get("/redoc", include_in_schema=False)
    async def custom_redoc_html():
        """自定义ReDoc。"""
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=f"{API_TITLE} - ReDoc",
            redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js",
        )

    logger.info("API documentation configured")


# 导出主要组件
__all__ = [
    "main_router",
    "APIResponse",
    "create_api_router",
    "setup_api_middleware",
    "setup_exception_handlers",
    "configure_api_docs",
    "API_TITLE",
    "API_VERSION",
    "API_DESCRIPTION"
]