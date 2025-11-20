"""
Template models - for message templates and moderation
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field


class TemplateStatus(str, Enum):
    """Template status"""
    PENDING = "pending"
    MODERATION = "moderation"
    APPROVED = "approved"
    REJECTED = "rejected"
    INPROCESS = "inprocess"


class TemplateCategory(str, Enum):
    """Template category"""
    SERVICE = "service"
    TRANSACTIONAL = "transactional"
    OTP = "otp"
    NOTIFICATION = "notification"
    MARKETING = "marketing"


class TemplateCreate(BaseModel):
    """Create template request - /api/user/template"""
    name: str = Field(min_length=1, max_length=100)
    category: TemplateCategory
    content: str = Field(min_length=1, max_length=1600)
    variables: Optional[List[str]] = Field(default=None, description="Variable placeholders like {code}, {name}")
    description: Optional[str] = Field(default=None, max_length=500)


class TemplateUpdate(BaseModel):
    """Update template"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    category: Optional[TemplateCategory] = None
    content: Optional[str] = Field(default=None, min_length=1, max_length=1600)
    variables: Optional[List[str]] = None
    description: Optional[str] = None


class TemplateResponse(BaseModel):
    """Template response"""
    id: UUID
    account_id: UUID
    name: str
    category: str
    content: str
    variables: Optional[List[str]]
    description: Optional[str]
    status: str
    admin_comment: Optional[str]
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime]
    approved_at: Optional[datetime]
    rejected_at: Optional[datetime]


class TemplateListResponse(BaseModel):
    """List of templates - /api/user/templates"""
    total: int
    templates: List[TemplateResponse]


class TemplateDecision(BaseModel):
    """Admin decision on template"""
    status: TemplateStatus = Field(description="approved or rejected")
    comment: Optional[str] = Field(default=None, max_length=500)


class TemplateUsageRequest(BaseModel):
    """Use template for sending SMS"""
    template_id: UUID
    to: str = Field(pattern=r"^\+?998\d{9}$")
    variables: Optional[dict[str, str]] = Field(default=None, description="Variable values")
    callback_url: Optional[str] = None

