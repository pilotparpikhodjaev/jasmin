"""
Authentication service - JWT token management
"""

import secrets
import uuid
from datetime import datetime, timedelta
from typing import Optional

import jwt
from jwt import PyJWTError
from passlib.context import CryptContext
from redis.asyncio import Redis

from ..config import get_settings
from ..models.auth import TokenData, TokenResponse

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """JWT authentication service"""
    
    def __init__(self, redis: Redis):
        self.redis = redis
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.access_token_expire_days = settings.jwt_access_token_expire_days
        self.refresh_token_expire_days = settings.jwt_refresh_token_expire_days
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(
        self,
        account_id: uuid.UUID,
        email: str,
        account_type: str,
        account_name: str,
    ) -> TokenResponse:
        """
        Create JWT access token (30 days like Eskiz.uz)
        """
        now = datetime.utcnow()
        expires_delta = timedelta(days=self.access_token_expire_days)
        expire = now + expires_delta
        
        jti = str(uuid.uuid4())  # JWT ID for revocation
        
        token_data = TokenData(
            account_id=account_id,
            email=email,
            account_type=account_type,
            account_name=account_name,
            exp=expire,
            iat=now,
            jti=jti,
        )
        
        # Create JWT
        to_encode = {
            "account_id": str(account_id),
            "email": email,
            "account_type": account_type,
            "account_name": account_name,
            "exp": expire,
            "iat": now,
            "jti": jti,
        }
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        # Create refresh token
        refresh_token = self._create_refresh_token(account_id, jti)
        
        return TokenResponse(
            token=encoded_jwt,
            token_type="bearer",
            expires_in=int(expires_delta.total_seconds()),
            refresh_token=refresh_token,
        )
    
    def _create_refresh_token(self, account_id: uuid.UUID, jti: str) -> str:
        """Create refresh token"""
        refresh_token = secrets.token_urlsafe(32)
        # Store in Redis with expiration
        # Key: refresh_token:{token} -> account_id:jti
        # TTL: refresh_token_expire_days
        return refresh_token
    
    async def store_refresh_token(
        self,
        refresh_token: str,
        account_id: uuid.UUID,
        jti: str,
    ) -> None:
        """Store refresh token in Redis"""
        key = f"refresh_token:{refresh_token}"
        value = f"{account_id}:{jti}"
        ttl = self.refresh_token_expire_days * 24 * 3600  # Convert to seconds
        await self.redis.setex(key, ttl, value)
    
    async def verify_refresh_token(self, refresh_token: str) -> Optional[tuple[uuid.UUID, str]]:
        """Verify refresh token and return (account_id, jti)"""
        key = f"refresh_token:{refresh_token}"
        value = await self.redis.get(key)
        
        if not value:
            return None
        
        try:
            account_id_str, jti = value.split(":", 1)
            return uuid.UUID(account_id_str), jti
        except (ValueError, AttributeError):
            return None
    
    async def revoke_refresh_token(self, refresh_token: str) -> None:
        """Revoke refresh token"""
        key = f"refresh_token:{refresh_token}"
        await self.redis.delete(key)
    
    def decode_token(self, token: str) -> TokenData:
        """Decode and verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            return TokenData(
                account_id=uuid.UUID(payload["account_id"]),
                email=payload["email"],
                account_type=payload["account_type"],
                account_name=payload["account_name"],
                exp=datetime.fromtimestamp(payload["exp"]),
                iat=datetime.fromtimestamp(payload["iat"]),
                jti=payload["jti"],
            )
        except jwt.ExpiredSignatureError:
            raise ValueError("Token has expired")
        except PyJWTError as e:
            raise ValueError(f"Invalid token: {e}")
    
    async def is_token_revoked(self, jti: str) -> bool:
        """Check if token is revoked"""
        key = f"revoked_token:{jti}"
        return await self.redis.exists(key) > 0
    
    async def revoke_token(self, jti: str, ttl_seconds: int) -> None:
        """Revoke token by JTI"""
        key = f"revoked_token:{jti}"
        await self.redis.setex(key, ttl_seconds, "1")
    
    async def revoke_all_user_tokens(self, account_id: uuid.UUID) -> None:
        """Revoke all tokens for a user (e.g., on password change)"""
        # Store revocation timestamp
        key = f"user_tokens_revoked:{account_id}"
        await self.redis.set(key, datetime.utcnow().isoformat())
    
    async def is_user_tokens_revoked(self, account_id: uuid.UUID, token_iat: datetime) -> bool:
        """Check if user's tokens were revoked after token issuance"""
        key = f"user_tokens_revoked:{account_id}"
        revoked_at_str = await self.redis.get(key)
        
        if not revoked_at_str:
            return False
        
        try:
            revoked_at = datetime.fromisoformat(revoked_at_str)
            return token_iat < revoked_at
        except (ValueError, AttributeError):
            return False
    
    def generate_api_key(self) -> str:
        """Generate API key"""
        return f"jasm_{secrets.token_urlsafe(32)}"
    
    async def store_api_key(
        self,
        api_key: str,
        account_id: uuid.UUID,
        expires_at: Optional[datetime] = None,
    ) -> None:
        """Store API key in Redis"""
        key = f"api_key:{api_key}"
        value = str(account_id)
        
        if expires_at:
            ttl = int((expires_at - datetime.utcnow()).total_seconds())
            await self.redis.setex(key, ttl, value)
        else:
            await self.redis.set(key, value)
    
    async def verify_api_key(self, api_key: str) -> Optional[uuid.UUID]:
        """Verify API key and return account_id"""
        key = f"api_key:{api_key}"
        value = await self.redis.get(key)
        
        if not value:
            return None
        
        try:
            return uuid.UUID(value)
        except (ValueError, AttributeError):
            return None
    
    async def revoke_api_key(self, api_key: str) -> None:
        """Revoke API key"""
        key = f"api_key:{api_key}"
        await self.redis.delete(key)
    
    async def update_api_key_last_used(self, api_key: str) -> None:
        """Update API key last used timestamp"""
        key = f"api_key_last_used:{api_key}"
        await self.redis.set(key, datetime.utcnow().isoformat())

