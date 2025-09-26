"""认证API端点实现

该模块提供完整的DingTalk OAuth 2.0认证流程，包括：
- 用户登录和注册
- OAuth回调处理
- JWT令牌生成和管理
- 用户会话管理
- 安全的登出功能
"""

import logging
from typing import Any, Dict, Optional, Union
from datetime import datetime, timedelta
import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field, EmailStr

from app.auth.dingtalk import DingTalkOAuthClient
from app.auth.jwt import get_jwt_handler, JWTPayload
from app.auth.exceptions import (
    OAuthError,
    AccessDeniedError,
    InvalidStateError,
    TokenInvalidError,
    UserInfoError
)
from app.core.config import get_settings
from app.core.redis import get_redis_client
from app.services.user import get_user_service, UserService
from app.models.user import (
    UserCreateRequest,
    UserResponse,
    LoginResponse,
    TokenRefreshResponse,
    UserDetailResponse
)
from app.middleware.rate_limiter import RateLimiter

# 配置日志
logger = logging.getLogger(__name__)

# 创建API路由器
router = APIRouter(prefix="/auth", tags=["authentication"])

# 获取应用设置
settings = get_settings()

# 速率限制器配置
rate_limiter = RateLimiter(
    calls=10,  # 10次请求
    period=300,  # 5分钟内
    scope="auth"
)


# 已从 app.models.user 导入所需模型类


class AuthState(BaseModel):
    """OAuth状态信息"""
    state: str
    redirect_uri: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# OAuth客户端依赖
async def get_dingtalk_client() -> DingTalkOAuthClient:
    """获取DingTalk OAuth客户端实例"""
    # 这些配置应该从环境变量或配置文件中读取
    client_id = getattr(settings, 'DINGTALK_CLIENT_ID', None)
    client_secret = getattr(settings, 'DINGTALK_CLIENT_SECRET', None)

    if not client_id or not client_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="DingTalk OAuth配置未完成"
        )

    # 构建回调URI
    redirect_uri = f"{getattr(settings, 'BASE_URL', 'http://localhost:8000')}/api/v1/auth/callback"

    return DingTalkOAuthClient(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope="openid"
    )


# Redis状态管理
async def save_oauth_state(state: str, redirect_uri: Optional[str] = None) -> None:
    """保存OAuth状态到Redis"""
    redis = await get_redis_client()
    auth_state = AuthState(state=state, redirect_uri=redirect_uri)

    # 状态信息保存15分钟
    await redis.setex(
        f"oauth_state:{state}",
        900,  # 15分钟
        auth_state.model_dump_json()
    )


async def get_oauth_state(state: str) -> Optional[AuthState]:
    """从Redis获取OAuth状态"""
    redis = await get_redis_client()
    state_data = await redis.get(f"oauth_state:{state}")

    if not state_data:
        return None

    return AuthState.model_validate_json(state_data)


async def delete_oauth_state(state: str) -> None:
    """删除OAuth状态"""
    redis = await get_redis_client()
    await redis.delete(f"oauth_state:{state}")


# 会话管理
async def save_user_session(user_id: str, session_data: Dict[str, Any]) -> str:
    """保存用户会话信息"""
    redis = await get_redis_client()
    session_id = str(uuid.uuid4())

    # 会话保存7天
    await redis.setex(
        f"user_session:{session_id}",
        7 * 24 * 3600,  # 7天
        str(session_data)
    )

    # 关联用户ID和会话ID
    await redis.setex(
        f"user_sessions:{user_id}",
        7 * 24 * 3600,
        session_id
    )

    return session_id


async def invalidate_user_sessions(user_id: str) -> None:
    """失效用户的所有会话"""
    redis = await get_redis_client()

    # 获取用户的会话ID
    session_id = await redis.get(f"user_sessions:{user_id}")
    if session_id:
        # 删除会话数据
        await redis.delete(f"user_session:{session_id}")
        await redis.delete(f"user_sessions:{user_id}")


# JWT令牌黑名单管理
async def blacklist_token(jti: str, exp: int) -> None:
    """将令牌加入黑名单"""
    redis = await get_redis_client()

    # 计算令牌剩余有效时间
    now = datetime.utcnow().timestamp()
    ttl = max(0, int(exp - now))

    if ttl > 0:
        await redis.setex(f"token_blacklist:{jti}", ttl, "1")


async def is_token_blacklisted(jti: str) -> bool:
    """检查令牌是否在黑名单中"""
    redis = await get_redis_client()
    result = await redis.get(f"token_blacklist:{jti}")
    return result is not None


@router.post("/login")
@rate_limiter
async def login(
    request: Request,
    redirect_uri: Optional[str] = Query(None, description="登录成功后的重定向地址"),
    dingtalk_client: DingTalkOAuthClient = Depends(get_dingtalk_client)
) -> Dict[str, str]:
    """
    发起DingTalk OAuth登录流程

    返回DingTalk授权URL，用户需要在浏览器中打开此URL进行授权
    """
    try:
        # 生成授权URL和状态参数
        auth_url, state = dingtalk_client.build_authorize_url()

        # 保存状态信息到Redis
        await save_oauth_state(state, redirect_uri)

        logger.info(f"OAuth login initiated with state: {state}")

        return {
            "authorization_url": auth_url,
            "state": state,
            "message": "请在浏览器中打开授权URL完成DingTalk登录"
        }

    except Exception as e:
        logger.error(f"Failed to initiate OAuth login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录流程启动失败: {str(e)}"
        )


@router.get("/callback")
async def oauth_callback(
    request: Request,
    code: Optional[str] = Query(None, description="OAuth授权码"),
    state: Optional[str] = Query(None, description="OAuth状态参数"),
    error: Optional[str] = Query(None, description="OAuth错误代码"),
    error_description: Optional[str] = Query(None, description="错误描述"),
    dingtalk_client: DingTalkOAuthClient = Depends(get_dingtalk_client),
    user_service: UserService = Depends(get_user_service)
) -> Union[LoginResponse, RedirectResponse]:
    """
    处理DingTalk OAuth回调

    接收授权码，交换访问令牌，获取用户信息，生成JWT令牌
    """
    try:
        # 处理OAuth错误
        if error:
            logger.warning(f"OAuth callback error: {error} - {error_description}")
            dingtalk_client.handle_error_callback(error, error_description)

        # 验证必需参数
        if not code or not state:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少授权码或状态参数"
            )

        # 验证状态参数
        auth_state = await get_oauth_state(state)
        if not auth_state:
            raise InvalidStateError("无效的状态参数，可能已过期")

        # 清理状态信息
        await delete_oauth_state(state)

        # 使用授权码交换访问令牌
        logger.info(f"Exchanging code for token with state: {state}")
        token_response = await dingtalk_client.exchange_code_for_token(
            code, state, auth_state.state
        )

        # 获取用户信息
        user_info = await dingtalk_client.get_user_info(token_response.access_token)
        logger.info(f"Retrieved user info for: {user_info.name}")

        # 查找或创建用户
        # 首先尝试通过钉钉unionid查找用户
        existing_user_dict = None
        if hasattr(user_info, 'unionid') and user_info.unionid:
            # 这里需要实现通过钉钉ID查找用户的逻辑
            # 暂时通过email查找
            if user_info.email:
                existing_user_dict = await user_service.get_user_by_email(user_info.email)

        if existing_user_dict:
            # 更新现有用户信息
            update_data = {
                "full_name": user_info.name,
                "is_active": True  # 成功登录说明用户是活跃的
            }
            user_dict = await user_service.update_user(existing_user_dict["id"], **update_data)

            # 更新用户偏好中的钉钉信息
            dingtalk_preferences = {
                "dingtalk_userid": user_info.id,
                "dingtalk_unionid": getattr(user_info, 'unionid', None),
                "dingtalk_openid": getattr(user_info, 'openid', None),
                "avatar_url": user_info.avatar,
                "mobile": getattr(user_info, 'mobile', None),
                "last_dingtalk_sync": datetime.utcnow().isoformat()
            }
            await user_service.update_user_preferences(existing_user_dict["id"], dingtalk_preferences)

            logger.info(f"Updated existing user: {user_info.name}")
        else:
            # 创建新用户 - 需要使用现有的用户服务接口
            user_dict = await user_service.create_user(
                email=user_info.email or f"{user_info.id}@dingtalk.user",  # 如果没有email，使用占位符
                password="dingtalk_oauth_user",  # OAuth用户使用占位符密码
                full_name=user_info.name,
                role="user",  # 默认角色
                preferences={
                    "dingtalk_userid": user_info.id,
                    "dingtalk_unionid": getattr(user_info, 'unionid', None),
                    "dingtalk_openid": getattr(user_info, 'openid', None),
                    "avatar_url": user_info.avatar,
                    "mobile": getattr(user_info, 'mobile', None),
                    "created_via": "dingtalk_oauth",
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            logger.info(f"Created new user: {user_info.name}")

        user_dict = user_dict or existing_user_dict

        # 生成JWT令牌
        jwt_handler = get_jwt_handler()
        tokens = jwt_handler.generate_tokens(
            user_id=user_dict["id"],
            username=user_dict["full_name"],
            roles=[user_dict.get("role", "user")]
        )

        # 保存用户会话
        session_data = {
            "user_id": user_dict["id"],
            "username": user_dict["full_name"],
            "login_time": datetime.utcnow().isoformat(),
            "access_jti": tokens["access_jti"],
            "refresh_jti": tokens["refresh_jti"]
        }
        session_id = await save_user_session(user_dict["id"], session_data)

        # 构建用户响应对象
        user_response = UserResponse(
            id=user_dict["id"],
            email=user_dict["email"],
            full_name=user_dict["full_name"],
            role=user_dict.get("role", "user"),
            is_active=user_dict.get("is_active", True),
            email_verified=user_dict.get("email_verified", False),
            created_at=user_dict.get("created_at", datetime.utcnow()),
            updated_at=user_dict.get("updated_at", datetime.utcnow()),
            last_login_at=user_dict.get("last_login_at")
        )

        # 构建登录响应
        login_response = LoginResponse(
            user=user_response,
            session_id=session_id,
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            expires_in=tokens["expires_in"],
            expires_at=datetime.utcnow() + timedelta(seconds=tokens["expires_in"])
        )

        logger.info(f"User {user_dict['full_name']} logged in successfully")

        # 如果有重定向地址，返回重定向响应
        if auth_state.redirect_uri:
            # 在实际应用中，你可能希望将令牌作为URL片段或通过安全的方式传递
            redirect_url = f"{auth_state.redirect_uri}?login=success"
            return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)

        return login_response

    except (AccessDeniedError, InvalidStateError) as e:
        logger.warning(f"OAuth callback validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except UserInfoError as e:
        logger.error(f"Failed to get user info: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"获取用户信息失败: {str(e)}"
        )
    except OAuthError as e:
        logger.error(f"OAuth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth认证失败: {str(e)}"
        )
    except Exception as e:
        logger.error(f"OAuth callback error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录处理失败: {str(e)}"
        )


# JWT依赖项：验证访问令牌
async def get_current_user(
    request: Request,
    user_service: UserService = Depends(get_user_service)
) -> Dict[str, Any]:
    """验证JWT令牌并返回当前用户字典"""
    # 从Authorization头获取令牌
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少或无效的Authorization头",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = authorization[7:]  # 移除 "Bearer " 前缀

    try:
        # 验证JWT令牌
        jwt_handler = get_jwt_handler()
        payload = jwt_handler.verify_token(token)

        if not payload or payload.scope != "access":
            raise TokenInvalidError("无效的访问令牌")

        # 检查令牌是否在黑名单中
        if await is_token_blacklisted(payload.jti):
            raise TokenInvalidError("令牌已失效")

        # 获取用户信息
        user_dict = await user_service.get_user(payload.user_id)
        if not user_dict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )

        return user_dict

    except TokenInvalidError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌验证失败",
            headers={"WWW-Authenticate": "Bearer"}
        )


@router.post("/refresh")
@rate_limiter
async def refresh_token(
    request: Request,
    refresh_token: str = Query(..., description="刷新令牌")
) -> TokenRefreshResponse:
    """
    使用刷新令牌获取新的访问令牌
    """
    try:
        jwt_handler = get_jwt_handler()

        # 验证刷新令牌
        payload = jwt_handler.verify_token(refresh_token)
        if not payload or payload.scope != "refresh":
            raise TokenInvalidError("无效的刷新令牌")

        # 检查令牌是否在黑名单中
        if await is_token_blacklisted(payload.jti):
            raise TokenInvalidError("刷新令牌已失效")

        # 生成新的访问令牌
        new_tokens = jwt_handler.refresh_access_token(refresh_token)
        if not new_tokens:
            raise TokenInvalidError("刷新令牌失败")

        logger.info(f"Access token refreshed for user: {payload.username}")

        return TokenRefreshResponse(
            access_token=new_tokens["access_token"],
            expires_in=new_tokens["expires_in"]
        )

    except TokenInvalidError as e:
        logger.warning(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="令牌刷新失败"
        )


@router.post("/logout")
async def logout(
    current_user: Dict[str, Any] = Depends(get_current_user),
    request: Request = None
) -> Dict[str, str]:
    """
    用户登出，使令牌失效
    """
    try:
        # 从请求头获取当前令牌
        authorization = request.headers.get("Authorization", "")
        if authorization.startswith("Bearer "):
            token = authorization[7:]

            # 解码令牌获取JTI和过期时间
            jwt_handler = get_jwt_handler()
            claims = jwt_handler.get_token_claims(token)
            if claims:
                await blacklist_token(claims.get("jti"), claims.get("exp", 0))

        # 失效用户的所有会话
        await invalidate_user_sessions(current_user["id"])

        logger.info(f"User {current_user['full_name']} logged out")

        return {"message": "登出成功"}

    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登出失败"
        )


@router.get("/profile")
async def get_profile(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> UserDetailResponse:
    """
    获取当前用户资料
    """
    return UserDetailResponse.from_user_dict(current_user)


@router.get("/qr-login")
@rate_limiter
async def qr_login(
    request: Request,
    redirect_uri: Optional[str] = Query(None, description="登录成功后的重定向地址"),
    dingtalk_client: DingTalkOAuthClient = Depends(get_dingtalk_client)
) -> Dict[str, str]:
    """
    生成DingTalk扫码登录URL

    返回二维码登录URL，适用于PC端扫码登录场景
    """
    try:
        # 生成二维码登录URL
        qr_url, state = dingtalk_client.build_qr_login_url()

        # 保存状态信息
        await save_oauth_state(state, redirect_uri)

        logger.info(f"QR code login initiated with state: {state}")

        return {
            "qr_login_url": qr_url,
            "state": state,
            "message": "请使用DingTalk APP扫描二维码登录"
        }

    except Exception as e:
        logger.error(f"Failed to generate QR login URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"二维码登录URL生成失败: {str(e)}"
        )


# 受保护路由示例
@router.get("/protected")
async def protected_route(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    受保护的路由示例

    需要有效的JWT访问令牌才能访问
    """
    return {
        "message": f"Hello, {current_user['full_name']}!",
        "user_id": current_user["id"],
        "role": current_user.get("role", "user"),
        "timestamp": datetime.utcnow().isoformat()
    }