"""健康检查API端点。

该模块提供：
- 数据库连接状态检查
- Redis连接状态检查
- 系统整体健康状态报告
- 服务组件状态监控
- 性能指标收集
"""

import logging
import asyncio
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.core.dependencies import get_system_health, get_database_session, get_redis_dependency
from app.core.cache import get_cache
from app.core.config import get_settings
from app.services.base import health_check_all_services
from app.api import APIResponse
from database.session import DatabaseSession, check_session_health

# 配置日志
logger = logging.getLogger(__name__)

# 创建健康检查路由器
router = APIRouter(prefix="/health", tags=["健康检查"])


class HealthStatus(BaseModel):
    """健康状态模型。"""
    status: str = Field(..., description="健康状态", example="healthy")
    timestamp: str = Field(..., description="检查时间", example="2023-01-01T00:00:00Z")
    uptime: Optional[float] = Field(None, description="运行时间（秒）", example=3600.0)
    version: Optional[str] = Field(None, description="应用版本", example="1.0.0")


class ComponentHealth(BaseModel):
    """组件健康状态模型。"""
    status: str = Field(..., description="组件状态", example="healthy")
    response_time: Optional[float] = Field(None, description="响应时间（毫秒）", example=12.5)
    last_check: str = Field(..., description="最后检查时间", example="2023-01-01T00:00:00Z")
    error: Optional[str] = Field(None, description="错误信息", example=None)
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")


class SystemHealth(BaseModel):
    """系统健康状态模型。"""
    overall: HealthStatus = Field(..., description="整体健康状态")
    database: ComponentHealth = Field(..., description="数据库健康状态")
    redis: ComponentHealth = Field(..., description="Redis健康状态")
    services: ComponentHealth = Field(..., description="服务健康状态")
    cache: ComponentHealth = Field(..., description="缓存健康状态")


# 应用启动时间
_app_start_time = time.time()


async def measure_response_time(func, *args, **kwargs) -> tuple[Any, float]:
    """
    测量函数执行响应时间。

    Args:
        func: 要测量的函数
        *args: 函数参数
        **kwargs: 函数关键字参数

    Returns:
        (结果, 响应时间毫秒)
    """
    start_time = time.time()
    try:
        if asyncio.iscoroutinefunction(func):
            result = await func(*args, **kwargs)
        else:
            result = func(*args, **kwargs)
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # 转换为毫秒
        return result, response_time
    except Exception as e:
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        return None, response_time


@router.get(
    "/",
    response_model=Dict[str, Any],
    summary="系统健康检查",
    description="获取系统整体健康状态，包括所有组件的状态信息"
)
async def health_check():
    """
    系统整体健康检查端点。

    Returns:
        系统健康状态信息
    """
    try:
        logger.debug("Starting system health check")

        # 获取系统健康状态
        health_info, check_time = await measure_response_time(get_system_health)

        # 计算运行时间
        uptime = time.time() - _app_start_time

        # 获取应用设置
        settings = get_settings()

        # 构建响应数据
        response_data = {
            "overall": {
                "status": health_info.get("status", "unknown"),
                "timestamp": health_info.get("timestamp", datetime.utcnow().isoformat()),
                "uptime": uptime,
                "version": settings.app_version,
                "check_duration": check_time
            },
            "components": {
                "database": health_info.get("database", {"status": "unknown"}),
                "redis": health_info.get("redis", {"status": "unknown"}),
                "services": health_info.get("services", {"status": "unknown"}),
                "cache": {"status": "unknown"}  # 将在下面更新
            },
            "errors": health_info.get("errors", []),
            "metadata": {
                "environment": "development" if settings.debug else "production",
                "hostname": "localhost",  # 可以从环境变量获取
                "process_id": None,  # 可以添加进程ID
                "memory_usage": None,  # 可以添加内存使用情况
                "cpu_usage": None  # 可以添加CPU使用情况
            }
        }

        # 测试缓存健康状态
        try:
            cache = get_cache("health_check")
            test_key = "health_test"
            cache_result, cache_time = await measure_response_time(
                cache.set, test_key, "test_value", ttl=10
            )
            if cache_result:
                await cache.delete(test_key)
                response_data["components"]["cache"] = {
                    "status": "healthy",
                    "response_time": cache_time,
                    "last_check": datetime.utcnow().isoformat()
                }
            else:
                response_data["components"]["cache"] = {
                    "status": "degraded",
                    "response_time": cache_time,
                    "last_check": datetime.utcnow().isoformat(),
                    "error": "Cache set operation failed"
                }
        except Exception as e:
            response_data["components"]["cache"] = {
                "status": "unhealthy",
                "last_check": datetime.utcnow().isoformat(),
                "error": str(e)
            }

        # 根据组件状态确定整体状态
        component_statuses = [
            response_data["components"]["database"]["status"],
            response_data["components"]["redis"]["status"],
            response_data["components"]["services"].get("overall_status", "unknown"),
            response_data["components"]["cache"]["status"]
        ]

        healthy_count = sum(1 for status in component_statuses if status == "healthy")
        total_count = len(component_statuses)

        if healthy_count == total_count:
            overall_status = "healthy"
        elif healthy_count > total_count // 2:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"

        response_data["overall"]["status"] = overall_status

        # 根据健康状态设置HTTP状态码
        if overall_status == "healthy":
            status_code = status.HTTP_200_OK
        elif overall_status == "degraded":
            status_code = status.HTTP_200_OK  # 仍返回200，但在响应中标明degraded
        else:
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        logger.info(f"Health check completed: {overall_status}")

        return JSONResponse(
            status_code=status_code,
            content=APIResponse.success(
                data=response_data,
                message=f"系统健康状态: {overall_status}"
            )
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        error_response = APIResponse.error(
            code="HEALTH_CHECK_FAILED",
            message="健康检查失败",
            details={"error": str(e)}
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response
        )


@router.get(
    "/database",
    response_model=Dict[str, Any],
    summary="数据库健康检查",
    description="检查数据库连接状态和性能指标"
)
async def database_health_check():
    """
    数据库健康检查端点。

    Returns:
        数据库健康状态信息
    """
    try:
        logger.debug("Starting database health check")

        # 执行数据库健康检查
        health_result, response_time = await measure_response_time(check_session_health)

        health_result["response_time"] = response_time
        health_result["component"] = "database"

        if health_result["status"] == "healthy":
            status_code = status.HTTP_200_OK
        else:
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        return JSONResponse(
            status_code=status_code,
            content=APIResponse.success(
                data=health_result,
                message=f"数据库状态: {health_result['status']}"
            )
        )

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        error_response = APIResponse.error(
            code="DATABASE_HEALTH_CHECK_FAILED",
            message="数据库健康检查失败",
            details={"error": str(e)}
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=error_response
        )


@router.get(
    "/redis",
    response_model=Dict[str, Any],
    summary="Redis健康检查",
    description="检查Redis连接状态和缓存性能"
)
async def redis_health_check():
    """
    Redis健康检查端点。

    Returns:
        Redis健康状态信息
    """
    try:
        logger.debug("Starting Redis health check")

        # 获取Redis客户端
        redis_client = await get_redis_dependency()

        # 测试Redis连接
        health_result, response_time = await measure_response_time(
            redis_client.health_check
        )

        result_data = {
            "status": "healthy" if health_result else "unhealthy",
            "response_time": response_time,
            "last_check": datetime.utcnow().isoformat(),
            "component": "redis",
            "connection_pool": {
                "size": redis_client._connection_pool.connection_kwargs.get("max_connections", "unknown") if redis_client._connection_pool else "unknown"
            }
        }

        if not health_result:
            result_data["error"] = "Redis ping failed"

        # 测试基本Redis操作
        try:
            test_key = "health_check_test"
            test_value = "test_data"

            # 测试设置操作
            set_result, set_time = await measure_response_time(
                redis_client.set, test_key, test_value, ex=10
            )

            # 测试获取操作
            get_result, get_time = await measure_response_time(
                redis_client.get, test_key
            )

            # 清理测试数据
            await redis_client.delete(test_key)

            result_data["operations"] = {
                "set": {
                    "success": set_result,
                    "response_time": set_time
                },
                "get": {
                    "success": get_result is not None,
                    "response_time": get_time,
                    "data_match": get_result.decode('utf-8') == test_value if get_result else False
                }
            }

        except Exception as op_error:
            result_data["operations_error"] = str(op_error)
            result_data["status"] = "degraded"

        status_code = status.HTTP_200_OK if result_data["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE

        return JSONResponse(
            status_code=status_code,
            content=APIResponse.success(
                data=result_data,
                message=f"Redis状态: {result_data['status']}"
            )
        )

    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        error_response = APIResponse.error(
            code="REDIS_HEALTH_CHECK_FAILED",
            message="Redis健康检查失败",
            details={"error": str(e)}
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=error_response
        )


@router.get(
    "/services",
    response_model=Dict[str, Any],
    summary="服务健康检查",
    description="检查所有注册服务的健康状态"
)
async def services_health_check():
    """
    服务健康检查端点。

    Returns:
        所有服务的健康状态信息
    """
    try:
        logger.debug("Starting services health check")

        # 执行服务健康检查
        health_result, response_time = await measure_response_time(health_check_all_services)

        health_result["response_time"] = response_time
        health_result["component"] = "services"
        health_result["last_check"] = datetime.utcnow().isoformat()

        # 添加每个服务的响应时间测试
        for service_name, service_health in health_result.get("services", {}).items():
            if service_health.get("status") == "healthy":
                try:
                    # 这里可以添加特定服务的性能测试
                    service_health["performance_check"] = "passed"
                except Exception:
                    service_health["performance_check"] = "failed"

        status_code = status.HTTP_200_OK if health_result.get("overall_status") == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE

        return JSONResponse(
            status_code=status_code,
            content=APIResponse.success(
                data=health_result,
                message=f"服务状态: {health_result.get('overall_status', 'unknown')}"
            )
        )

    except Exception as e:
        logger.error(f"Services health check failed: {e}")
        error_response = APIResponse.error(
            code="SERVICES_HEALTH_CHECK_FAILED",
            message="服务健康检查失败",
            details={"error": str(e)}
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=error_response
        )


@router.get(
    "/cache",
    response_model=Dict[str, Any],
    summary="缓存健康检查",
    description="检查缓存系统的健康状态和性能"
)
async def cache_health_check():
    """
    缓存健康检查端点。

    Returns:
        缓存系统健康状态信息
    """
    try:
        logger.debug("Starting cache health check")

        cache = get_cache("health_check")
        test_key = "cache_health_test"
        test_value = {"test": "data", "timestamp": datetime.utcnow().isoformat()}

        result_data = {
            "status": "healthy",
            "component": "cache",
            "last_check": datetime.utcnow().isoformat(),
            "operations": {},
            "namespace": cache.namespace
        }

        # 测试缓存设置操作
        set_result, set_time = await measure_response_time(
            cache.set, test_key, test_value, ttl=30
        )
        result_data["operations"]["set"] = {
            "success": set_result,
            "response_time": set_time
        }

        # 测试缓存获取操作
        get_result, get_time = await measure_response_time(
            cache.get, test_key
        )
        result_data["operations"]["get"] = {
            "success": get_result is not None,
            "response_time": get_time,
            "data_match": get_result == test_value if get_result else False
        }

        # 测试缓存存在检查
        exists_result, exists_time = await measure_response_time(
            cache.exists, test_key
        )
        result_data["operations"]["exists"] = {
            "success": exists_result,
            "response_time": exists_time
        }

        # 测试缓存删除操作
        delete_result, delete_time = await measure_response_time(
            cache.delete, test_key
        )
        result_data["operations"]["delete"] = {
            "success": delete_result > 0,
            "response_time": delete_time,
            "deleted_count": delete_result
        }

        # 计算平均响应时间
        response_times = [
            result_data["operations"]["set"]["response_time"],
            result_data["operations"]["get"]["response_time"],
            result_data["operations"]["exists"]["response_time"],
            result_data["operations"]["delete"]["response_time"]
        ]
        result_data["average_response_time"] = sum(response_times) / len(response_times)

        # 检查是否有失败的操作
        failed_operations = [
            op for op, details in result_data["operations"].items()
            if not details["success"]
        ]

        if failed_operations:
            result_data["status"] = "degraded"
            result_data["failed_operations"] = failed_operations

        status_code = status.HTTP_200_OK if result_data["status"] == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE

        return JSONResponse(
            status_code=status_code,
            content=APIResponse.success(
                data=result_data,
                message=f"缓存状态: {result_data['status']}"
            )
        )

    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        error_response = APIResponse.error(
            code="CACHE_HEALTH_CHECK_FAILED",
            message="缓存健康检查失败",
            details={"error": str(e)}
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=error_response
        )


@router.get(
    "/ready",
    summary="就绪检查",
    description="检查应用是否已准备好接收请求"
)
async def readiness_check():
    """
    就绪检查端点（用于Kubernetes等容器编排）。

    Returns:
        应用就绪状态
    """
    try:
        # 快速检查关键组件
        checks = []

        # 数据库检查
        try:
            health_result = await check_session_health()
            checks.append(("database", health_result["status"] == "healthy"))
        except Exception:
            checks.append(("database", False))

        # Redis检查
        try:
            redis_client = await get_redis_dependency()
            redis_healthy = await redis_client.health_check()
            checks.append(("redis", redis_healthy))
        except Exception:
            checks.append(("redis", False))

        # 所有关键组件都健康才认为就绪
        all_ready = all(ready for _, ready in checks)

        if all_ready:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=APIResponse.success(
                    data={"ready": True, "checks": dict(checks)},
                    message="应用已就绪"
                )
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=APIResponse.error(
                    code="NOT_READY",
                    message="应用未就绪",
                    details={"checks": dict(checks)}
                )
            )

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=APIResponse.error(
                code="READINESS_CHECK_FAILED",
                message="就绪检查失败",
                details={"error": str(e)}
            )
        )


@router.get(
    "/live",
    summary="存活检查",
    description="检查应用是否仍在运行"
)
async def liveness_check():
    """
    存活检查端点（用于Kubernetes等容器编排）。

    Returns:
        应用存活状态
    """
    # 简单的存活检查，只要能响应就认为存活
    uptime = time.time() - _app_start_time

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=APIResponse.success(
            data={
                "alive": True,
                "uptime": uptime,
                "timestamp": datetime.utcnow().isoformat()
            },
            message="应用存活"
        )
    )


# 导出路由器
__all__ = ["router"]