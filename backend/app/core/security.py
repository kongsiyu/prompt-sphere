"""安全配置和RSA密钥管理"""
import logging
import os
import secrets
from typing import Optional, Dict, Any

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet
import base64

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class SecurityManager:
    """安全管理器，负责密钥生成和加密操作"""

    def __init__(self):
        self.settings = get_settings()
        self._master_key: Optional[bytes] = None
        self._fernet: Optional[Fernet] = None
        self._initialize_encryption()

    def _initialize_encryption(self) -> None:
        """初始化加密系统"""
        try:
            # 从环境变量或配置获取主密钥盐
            salt = getattr(self.settings, 'SECURITY_SALT', 'default_salt_change_in_production').encode()

            # 生成或获取主密钥
            secret_key = getattr(self.settings, 'SECRET_KEY', self._generate_secret_key())

            # 使用PBKDF2派生加密密钥
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(secret_key.encode()))
            self._fernet = Fernet(key)

            logger.info("Encryption system initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise RuntimeError("Cannot initialize security system")

    def _generate_secret_key(self) -> str:
        """生成安全的密钥"""
        return secrets.token_urlsafe(32)

    def encrypt_data(self, data: str) -> str:
        """加密数据"""
        try:
            if not self._fernet:
                raise RuntimeError("Encryption not initialized")

            encrypted = self._fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()

        except Exception as e:
            logger.error(f"Failed to encrypt data: {e}")
            raise

    def decrypt_data(self, encrypted_data: str) -> str:
        """解密数据"""
        try:
            if not self._fernet:
                raise RuntimeError("Encryption not initialized")

            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self._fernet.decrypt(encrypted_bytes)
            return decrypted.decode()

        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            raise

    def hash_password(self, password: str, salt: Optional[str] = None) -> Dict[str, str]:
        """哈希密码"""
        import hashlib
        import secrets

        if salt is None:
            salt = secrets.token_hex(32)

        # 使用PBKDF2进行密码哈希
        pwdhash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000  # 迭代次数
        )

        return {
            'hash': pwdhash.hex(),
            'salt': salt
        }

    def verify_password(self, password: str, stored_hash: str, salt: str) -> bool:
        """验证密码"""
        try:
            computed_hash = self.hash_password(password, salt)
            return secrets.compare_digest(computed_hash['hash'], stored_hash)
        except Exception as e:
            logger.error(f"Failed to verify password: {e}")
            return False

    def generate_rsa_key_pair(self) -> Dict[str, str]:
        """生成RSA密钥对"""
        try:
            # 生成2048位RSA密钥对
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )

            # 序列化私钥
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )

            # 序列化公钥
            public_pem = private_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )

            return {
                'private_key': private_pem.decode(),
                'public_key': public_pem.decode()
            }

        except Exception as e:
            logger.error(f"Failed to generate RSA key pair: {e}")
            raise

    def encrypt_with_rsa(self, data: str, public_key_pem: str) -> str:
        """使用RSA公钥加密数据"""
        try:
            public_key = serialization.load_pem_public_key(public_key_pem.encode())

            encrypted = public_key.encrypt(
                data.encode(),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            return base64.b64encode(encrypted).decode()

        except Exception as e:
            logger.error(f"Failed to encrypt with RSA: {e}")
            raise

    def decrypt_with_rsa(self, encrypted_data: str, private_key_pem: str) -> str:
        """使用RSA私钥解密数据"""
        try:
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode(),
                password=None
            )

            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            decrypted = private_key.decrypt(
                encrypted_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            return decrypted.decode()

        except Exception as e:
            logger.error(f"Failed to decrypt with RSA: {e}")
            raise

    def generate_csrf_token(self) -> str:
        """生成CSRF令牌"""
        return secrets.token_urlsafe(32)

    def generate_api_key(self) -> str:
        """生成API密钥"""
        return secrets.token_urlsafe(48)

    def validate_token_format(self, token: str) -> bool:
        """验证令牌格式"""
        try:
            # 基本长度检查
            if len(token) < 20:
                return False

            # 检查是否为有效的base64url格式
            try:
                base64.urlsafe_b64decode(token + '==')  # 添加填充
                return True
            except Exception:
                # 可能是JWT格式
                parts = token.split('.')
                return len(parts) == 3

        except Exception:
            return False

    def sanitize_input(self, data: str, max_length: int = 1000) -> str:
        """清理输入数据"""
        if not isinstance(data, str):
            return ""

        # 限制长度
        data = data[:max_length]

        # 移除潜在的危险字符
        import re
        # 移除控制字符但保留基本的空白字符
        data = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', data)

        return data.strip()

    def generate_session_id(self) -> str:
        """生成会话ID"""
        return secrets.token_urlsafe(64)

    def constant_time_compare(self, a: str, b: str) -> bool:
        """常量时间字符串比较，防止时序攻击"""
        return secrets.compare_digest(a, b)


class SecurityConfig:
    """安全配置类"""

    # 令牌过期时间（秒）
    ACCESS_TOKEN_EXPIRE_MINUTES = 15
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    SESSION_EXPIRE_HOURS = 24

    # 密码复杂性要求
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBERS = True
    REQUIRE_SPECIAL_CHARS = False

    # 速率限制
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_ATTEMPT_WINDOW_MINUTES = 15

    # CORS配置
    ALLOWED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
    ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS = ["*"]

    # 安全头
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }

    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """验证密码强度"""
        errors = []

        if len(password) < SecurityConfig.MIN_PASSWORD_LENGTH:
            errors.append(f"密码至少需要{SecurityConfig.MIN_PASSWORD_LENGTH}个字符")

        if len(password) > SecurityConfig.MAX_PASSWORD_LENGTH:
            errors.append(f"密码不能超过{SecurityConfig.MAX_PASSWORD_LENGTH}个字符")

        if SecurityConfig.REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            errors.append("密码必须包含大写字母")

        if SecurityConfig.REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            errors.append("密码必须包含小写字母")

        if SecurityConfig.REQUIRE_NUMBERS and not any(c.isdigit() for c in password):
            errors.append("密码必须包含数字")

        if SecurityConfig.REQUIRE_SPECIAL_CHARS:
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if not any(c in special_chars for c in password):
                errors.append("密码必须包含特殊字符")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }


# 全局安全管理器实例
_security_manager: Optional[SecurityManager] = None


def get_security_manager() -> SecurityManager:
    """获取安全管理器实例（单例模式）"""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager


def get_security_config() -> SecurityConfig:
    """获取安全配置实例"""
    return SecurityConfig()