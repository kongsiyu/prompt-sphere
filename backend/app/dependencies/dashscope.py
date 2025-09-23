"""DashScope 依赖注入提供者."""

import logging
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.dashscope.config import DashScopeSettings
from app.services.dashscope_service import DashScopeService

logger = logging.getLogger(__name__)


# @lru_cache
def get_dashscope_settings() -> DashScopeSettings:
    """获取 DashScope 配置设置（缓存单例）."""
    try:
        settings = DashScopeSettings()
        logger.info("DashScope settings loaded successfully")
        return settings
    except Exception as e:
        logger.error(f"Failed to load DashScope settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="DashScope 配置加载失败"
        )


# @lru_cache
def get_dashscope_service(
    settings: Annotated[DashScopeSettings, Depends(get_dashscope_settings)]
) -> DashScopeService:
    """获取 DashScope 服务实例（缓存单例）."""
    try:
        # 验证必要的配置
        if not settings.api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="DashScope API 密钥未配置"
            )

        service = DashScopeService(settings)
        logger.info("DashScope service created successfully")
        return service

    except HTTPException:
        # 重新抛出已知的 HTTP 异常
        raise
    except Exception as e:
        logger.error(f"Failed to create DashScope service: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="DashScope 服务初始化失败"
        )


# 依赖注入类型别名，方便在路由中使用
DashScopeServiceDep = Annotated[DashScopeService, Depends(get_dashscope_service)]
DashScopeSettingsDep = Annotated[DashScopeSettings, Depends(get_dashscope_settings)]


async def verify_dashscope_health(
    service: DashScopeServiceDep
) -> DashScopeService:
    """验证 DashScope 服务健康状态的中间件依赖."""
    try:
        health = await service.health_check()
        if health["status"] != "healthy":
            logger.warning(f"DashScope service is unhealthy: {health}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"DashScope 服务不可用: {health.get('error', '未知错误')}"
            )
        return service
    except HTTPException:
        # 重新抛出已知的 HTTP 异常
        raise
    except Exception as e:
        logger.error(f"DashScope health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="DashScope 服务健康检查失败"
        )


# 健康验证依赖的类型别名
HealthyDashScopeServiceDep = Annotated[DashScopeService, Depends(verify_dashscope_health)]