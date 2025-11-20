"""
User and account models
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """User profile information"""
    id: UUID
    email: str
    name: str
    role: str
    status: str
    balance: Decimal
    currency: str
    credit_limit: Decimal
    rate_limit_rps: Optional[int]
    allowed_ips: Optional[list[str]]
    created_at: datetime
    parent_id: Optional[UUID] = None


class BalanceResponse(BaseModel):
    """Balance response - /api/user/get-limit"""
    balance: Decimal
    currency: str
    credit_limit: Decimal
    available_balance: Decimal  # balance + credit_limit


class NicknameResponse(BaseModel):
    """Sender ID (nickname) response - /api/nick/me"""
    nicknames: list[str]


class TotalsRequest(BaseModel):
    """Monthly totals request - /api/user/totals"""
    year: int = Field(ge=2020, le=2100)
    month: int = Field(ge=1, le=12)
    is_global: bool = Field(default=False, description="Include international SMS")


class StatusTotal(BaseModel):
    """Total by status"""
    status: str
    count: int
    total_price: Decimal


class TotalsResponse(BaseModel):
    """Monthly totals response"""
    year: int
    month: int
    total_messages: int
    total_price: Decimal
    currency: str
    by_status: list[StatusTotal]


class ExportCSVRequest(BaseModel):
    """Export CSV request - /api/user/export-csv"""
    start_date: datetime
    end_date: datetime
    status: Optional[str] = None
    is_ad: Optional[bool] = None

