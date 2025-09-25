"""JWT处理器实现，负责令牌的生成、验证和管理"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Union

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from pydantic import BaseModel

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class JWTPayload(BaseModel):
    """JWT负载数据模型"""
    sub: str  # 用户ID (subject)
    exp: int  # 过期时间 (expiration time)
    iat: int  # 签发时间 (issued at)
    jti: str  # JWT ID，用于令牌标识
    scope: str = "access"  # 令牌作用域 (access/refresh)
    user_id: str
    username: str
    roles: list[str] = []


class JWTHandler:
    """JWT令牌处理器"""

    def __init__(self):
        self.settings = get_settings()
        self._private_key: Optional[bytes] = None
        self._public_key: Optional[bytes] = None
        self._algorithm = "RS256"

        # 初始化密钥对
        self._load_or_generate_keys()

    def _load_or_generate_keys(self) -> None:
        """加载或生成RSA密钥对"""
        try:
            # 尝试从配置加载密钥
            if hasattr(self.settings, 'JWT_PRIVATE_KEY') and self.settings.JWT_PRIVATE_KEY:
                self._private_key = self.settings.JWT_PRIVATE_KEY.encode()
                # 从私钥提取公钥
                private_key_obj = serialization.load_pem_private_key(
                    self._private_key, password=None
                )
                self._public_key = private_key_obj.public_key().public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
                logger.info("JWT keys loaded from configuration")
                return
        except Exception as e:
            logger.warning(f"Failed to load JWT keys from config: {e}")

        # 生成新的密钥对
        self._generate_key_pair()

    def _generate_key_pair(self) -> None:
        """生成新的RSA密钥对"""
        try:
            # 生成2048位RSA密钥对
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )

            # 序列化私钥
            self._private_key = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )

            # 序列化公钥
            self._public_key = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            logger.warning("Generated new JWT key pair - consider saving to configuration")

        except Exception as e:
            logger.error(f"Failed to generate JWT key pair: {e}")
            raise RuntimeError("Cannot initialize JWT handler without valid keys")

    def generate_tokens(
        self,
        user_id: str,
        username: str,
        roles: list[str] = None
    ) -> Dict[str, str]:
        """生成访问令牌和刷新令牌对"""
        if roles is None:
            roles = []

        now = datetime.utcnow()

        # 生成唯一的JTI
        import uuid
        access_jti = str(uuid.uuid4())
        refresh_jti = str(uuid.uuid4())

        # 访问令牌 (15分钟过期)
        access_payload = JWTPayload(
            sub=user_id,
            exp=int((now + timedelta(minutes=15)).timestamp()),
            iat=int(now.timestamp()),
            jti=access_jti,
            scope="access",
            user_id=user_id,
            username=username,
            roles=roles
        )

        # 刷新令牌 (7天过期)
        refresh_payload = JWTPayload(
            sub=user_id,
            exp=int((now + timedelta(days=7)).timestamp()),
            iat=int(now.timestamp()),
            jti=refresh_jti,
            scope="refresh",
            user_id=user_id,
            username=username,
            roles=roles
        )

        try:
            access_token = jwt.encode(
                access_payload.model_dump(),
                self._private_key,
                algorithm=self._algorithm
            )

            refresh_token = jwt.encode(
                refresh_payload.model_dump(),
                self._private_key,
                algorithm=self._algorithm
            )

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": 900,  # 15分钟
                "access_jti": access_jti,
                "refresh_jti": refresh_jti
            }

        except Exception as e:
            logger.error(f"Failed to generate JWT tokens: {e}")
            raise RuntimeError("Failed to generate authentication tokens")

    def verify_token(self, token: str) -> Optional[JWTPayload]:
        """验证JWT令牌并返回负载数据"""
        try:
            # 解码令牌
            payload = jwt.decode(
                token,
                self._public_key,
                algorithms=[self._algorithm],
                options={"verify_exp": True, "verify_iat": True}
            )

            # 转换为数据模型
            return JWTPayload(**payload)

        except jwt.ExpiredSignatureError:
            logger.debug("JWT token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.debug(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to verify JWT token: {e}")
            return None

    def decode_token_unsafe(self, token: str) -> Optional[Dict[str, Any]]:
        """不安全地解码令牌（不验证签名），用于获取过期令牌的信息"""
        try:
            payload = jwt.decode(
                token,
                options={"verify_signature": False, "verify_exp": False}
            )
            return payload
        except Exception as e:
            logger.error(f"Failed to decode JWT token: {e}")
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """使用刷新令牌生成新的访问令牌"""
        # 验证刷新令牌
        payload = self.verify_token(refresh_token)
        if not payload or payload.scope != "refresh":
            logger.debug("Invalid or expired refresh token")
            return None

        # 生成新的访问令牌
        now = datetime.utcnow()
        access_jti = str(__import__('uuid').uuid4())

        access_payload = JWTPayload(
            sub=payload.user_id,
            exp=int((now + timedelta(minutes=15)).timestamp()),
            iat=int(now.timestamp()),
            jti=access_jti,
            scope="access",
            user_id=payload.user_id,
            username=payload.username,
            roles=payload.roles
        )

        try:
            access_token = jwt.encode(
                access_payload.model_dump(),
                self._private_key,
                algorithm=self._algorithm
            )

            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": 900,
                "access_jti": access_jti
            }

        except Exception as e:
            logger.error(f"Failed to refresh access token: {e}")
            return None

    def get_token_claims(self, token: str) -> Optional[Dict[str, Any]]:
        """获取令牌的声明信息（不验证过期时间）"""
        try:
            payload = jwt.decode(
                token,
                self._public_key,
                algorithms=[self._algorithm],
                options={"verify_exp": False}
            )
            return payload
        except Exception as e:
            logger.debug(f"Failed to get token claims: {e}")
            return None

    @property
    def public_key_pem(self) -> str:
        """获取PEM格式的公钥"""
        return self._public_key.decode() if self._public_key else ""

    @property
    def private_key_pem(self) -> str:
        """获取PEM格式的私钥（仅用于备份/配置）"""
        return self._private_key.decode() if self._private_key else ""


# 全局JWT处理器实例
_jwt_handler: Optional[JWTHandler] = None


def get_jwt_handler() -> JWTHandler:
    """获取JWT处理器实例（单例模式）"""
    global _jwt_handler
    if _jwt_handler is None:
        _jwt_handler = JWTHandler()
    return _jwt_handler