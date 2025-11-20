"""
Authentication models - JWT token system like Eskiz.uz
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login request with email and password"""
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class TokenData(BaseModel):
    """JWT token payload data"""
    account_id: UUID
    email: str
    account_type: str  # 'admin', 'reseller', 'client'
    account_name: str
    exp: datetime
    iat: datetime
    jti: str  # JWT ID for token revocation


class TokenResponse(BaseModel):
    """Token response - similar to Eskiz.uz format"""
    token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until expiration
    refresh_token: Optional[str] = None


class UserResponse(BaseModel):
    """User data response - similar to Eskiz.uz /api/auth/user"""
    id: UUID
    email: EmailStr
    name: str
    role: str  # 'admin', 'reseller', 'client'
    status: str  # 'active', 'suspended', 'pending'
    balance: float
    currency: str
    sms_count: int  # Total SMS sent
    created_at: datetime
    
    # Additional fields
    parent_id: Optional[UUID] = None
    rate_limit_rps: Optional[int] = None
    allowed_ips: Optional[list[str]] = None
    api_key: Optional[str] = None  # Masked API key


class PasswordChangeRequest(BaseModel):
    """Change password request"""
    old_password: str
    new_password: str = Field(min_length=8, max_length=128)


class APIKeyCreateRequest(BaseModel):
    """Create new API key"""
    name: str = Field(max_length=100)
    expires_in_days: Optional[int] = Field(default=365, ge=1, le=3650)
    ip_whitelist: Optional[list[str]] = None


class APIKeyResponse(BaseModel):
    """API key response"""
    id: UUID
    name: str
    key: str  # Only shown once during creation
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    ip_whitelist: Optional[list[str]] = None

