"""
Enterprise-level Pydantic schemas for Billing Service
Includes: Operators, Nicknames, Authentication, Transactions, Dispatches, Audit Logs
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, IPvAnyAddress


# ============================================================================
# OPERATOR SCHEMAS
# ============================================================================


class SMPPConnectionConfig(BaseModel):
    """SMPP connection configuration"""

    host: str
    port: int = Field(ge=1, le=65535)
    system_id: str
    password: str
    system_type: str = ""
    bind_mode: Literal["transmitter", "receiver", "transceiver"] = "transceiver"
    submit_sm_throughput: int = Field(default=100, ge=1, le=10000)
    source_addr_ton: int = Field(default=0, ge=0, le=255)
    source_addr_npi: int = Field(default=0, ge=0, le=255)
    dest_addr_ton: int = Field(default=1, ge=0, le=255)
    dest_addr_npi: int = Field(default=1, ge=0, le=255)
    enquire_link_interval: int = Field(default=30, ge=10, le=300)
    reconnect_delay: int = Field(default=10, ge=1, le=300)


class OperatorCreate(BaseModel):
    """Create new operator"""

    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=64, pattern=r"^[A-Z0-9_]+$")
    country: str = Field(min_length=2, max_length=2, pattern=r"^[A-Z]{2}$")
    mcc: str = Field(min_length=3, max_length=3, pattern=r"^\d{3}$")
    mnc: str = Field(min_length=2, max_length=3, pattern=r"^\d{2,3}$")
    price_per_sms: Decimal = Field(ge=0)
    currency: str = Field(default="UZS", min_length=3, max_length=3)
    priority: int = Field(default=100, ge=0, le=1000)
    weight: int = Field(default=100, ge=0, le=100)
    status: Literal["active", "inactive", "maintenance"] = "active"
    health_check_enabled: bool = True
    health_check_interval: int = Field(default=60, ge=10, le=3600)
    smpp_config: SMPPConnectionConfig
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OperatorUpdate(BaseModel):
    """Update operator"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    price_per_sms: Optional[Decimal] = Field(None, ge=0)
    priority: Optional[int] = Field(None, ge=0, le=1000)
    weight: Optional[int] = Field(None, ge=0, le=100)
    status: Optional[Literal["active", "inactive", "maintenance"]] = None
    health_check_enabled: Optional[bool] = None
    health_check_interval: Optional[int] = Field(None, ge=10, le=3600)
    smpp_config: Optional[SMPPConnectionConfig] = None
    metadata: Optional[Dict[str, Any]] = None


class OperatorHealthMetricsResponse(BaseModel):
    """Operator health metrics"""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str | int
    operator_id: str | int
    is_connected: bool
    last_connected_at: Optional[datetime]
    connection_uptime_seconds: int
    submit_sm_count: int
    submit_sm_resp_count: int
    delivery_count: int
    failure_count: int
    submit_success_rate: Decimal
    delivery_rate: Decimal
    avg_submit_latency_ms: Decimal
    p95_submit_latency_ms: Decimal
    p99_submit_latency_ms: Decimal
    health_score: Decimal
    health_status: Literal["healthy", "degraded", "unhealthy", "unknown"]
    recent_errors: List[Dict[str, Any]]
    measured_at: datetime
    created_at: datetime


class OperatorResponse(BaseModel):
    """Operator response"""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str | int
    name: str
    code: str
    country: str
    mcc: str
    mnc: str
    price_per_sms: Decimal
    currency: str
    priority: int
    weight: int
    status: str
    health_check_enabled: bool
    health_check_interval: int
    smpp_config: Dict[str, Any]
    jasmin_connector_id: Optional[str]
    metadata: Dict[str, Any] = Field(default_factory=dict, alias="metadata_")
    created_at: datetime
    updated_at: datetime


class OperatorStatsResponse(BaseModel):
    """Operator statistics"""

    operator_id: str | int
    operator_name: str
    total_messages: int
    delivered_messages: int
    failed_messages: int
    pending_messages: int
    delivery_rate: Decimal
    total_revenue: Decimal
    currency: str
    avg_latency_ms: Decimal
    last_message_at: Optional[datetime]


# ============================================================================
# NICKNAME (SENDER ID) SCHEMAS
# ============================================================================


class NicknameCreate(BaseModel):
    """Create new nickname"""

    nickname: str = Field(min_length=1, max_length=11, pattern=r"^[A-Za-z0-9]+$")
    category: Optional[str] = Field(None, max_length=64)
    description: Optional[str] = None


class NicknameUpdate(BaseModel):
    """Update nickname"""

    category: Optional[str] = Field(None, max_length=64)
    description: Optional[str] = None


class NicknameModerate(BaseModel):
    """Moderate nickname (admin only)"""

    status: Literal["approved", "rejected"]
    rejection_reason: Optional[str] = None


class NicknameResponse(BaseModel):
    """Nickname response"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    nickname: str
    status: Literal["pending", "approved", "rejected"]
    category: Optional[str]
    description: Optional[str]
    approved_by: Optional[uuid.UUID]
    approved_at: Optional[datetime]
    rejection_reason: Optional[str]
    created_at: datetime
    updated_at: datetime


# ============================================================================
# AUTHENTICATION SCHEMAS
# ============================================================================


class LoginRequest(BaseModel):
    """Login request"""

    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class RegisterRequest(BaseModel):
    """Register new account"""

    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    currency: str = Field(default="UZS", min_length=3, max_length=3)
    type: Literal["client"] = "client"


class LoginResponse(BaseModel):
    """Login response"""

    account_id: uuid.UUID
    email: str
    name: str
    type: str
    status: str
    balance: Decimal
    currency: str
    created_at: datetime


class PasswordChangeRequest(BaseModel):
    """Change password"""

    old_password: str = Field(min_length=6, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class PasswordResetRequest(BaseModel):
    """Request password reset"""

    email: EmailStr


# ============================================================================
# TRANSACTION SCHEMAS
# ============================================================================


class TransactionCreate(BaseModel):
    """Create transaction"""

    account_id: uuid.UUID
    type: Literal["charge", "refund", "topup", "adjustment", "commission"]
    amount: Decimal = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    description: Optional[str] = None
    reference_type: Optional[str] = None
    reference_id: Optional[uuid.UUID] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TransactionResponse(BaseModel):
    """Transaction response"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    type: str
    amount: Decimal
    currency: str
    balance_before: Decimal
    balance_after: Decimal
    description: Optional[str]
    reference_type: Optional[str]
    reference_id: Optional[uuid.UUID]
    metadata: Dict[str, Any]
    created_by: Optional[uuid.UUID]
    created_at: datetime


# ============================================================================
# DISPATCH SCHEMAS
# ============================================================================


class DispatchCreate(BaseModel):
    """Create dispatch"""

    dispatch_id: str = Field(min_length=1, max_length=255)
    account_id: uuid.UUID
    total_messages: int = Field(ge=0)
    currency: str = Field(min_length=3, max_length=3)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DispatchUpdate(BaseModel):
    """Update dispatch counters"""

    submitted_count: Optional[int] = Field(None, ge=0)
    delivered_count: Optional[int] = Field(None, ge=0)
    failed_count: Optional[int] = Field(None, ge=0)
    pending_count: Optional[int] = Field(None, ge=0)
    total_cost: Optional[Decimal] = Field(None, ge=0)
    status: Optional[Literal["processing", "completed", "failed", "cancelled"]] = None


class DispatchResponse(BaseModel):
    """Dispatch response"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    dispatch_id: str
    account_id: uuid.UUID
    total_messages: int
    submitted_count: int
    delivered_count: int
    failed_count: int
    pending_count: int
    total_cost: Decimal
    currency: str
    status: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class DispatchStatusResponse(BaseModel):
    """Dispatch status summary"""

    dispatch_id: str
    total: int
    submitted: int
    delivered: int
    failed: int
    pending: int
    status: str
    total_cost: Decimal
    currency: str




# ============================================================================
# DASHBOARD / STATS SCHEMAS
# ============================================================================


class AdminAccountListItem(BaseModel):
    """Account summary for admin dashboard listing."""

    id: uuid.UUID
    name: str
    email: Optional[EmailStr] = None
    type: Literal["admin", "reseller", "client"]
    status: Literal["active", "suspended", "inactive"]
    balance: Decimal
    sms_count: int
    created_at: datetime
    updated_at: datetime


class DashboardDailyCount(BaseModel):
    """Daily message count"""

    date: str
    count: int


class DashboardDailyRevenue(BaseModel):
    """Daily revenue amount"""

    date: str
    amount: float


class DashboardTopAccount(BaseModel):
    """Top account by message volume"""

    id: uuid.UUID
    name: str
    usage: int


class DashboardMessage(BaseModel):
    """Recent message summary for dashboard"""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    from_: str = Field(alias="from")
    to: str
    content: str
    status: Literal["pending", "sent", "delivered", "failed"]
    operator_id: Optional[str] = Field(default=None, alias="operatorId")
    account_id: str = Field(alias="accountId")
    created_at: datetime = Field(alias="createdAt")
    delivered_at: Optional[datetime] = Field(default=None, alias="deliveredAt")


class DashboardStatsResponse(BaseModel):
    """Aggregated dashboard statistics"""

    total_accounts: int
    total_messages_today: int
    total_revenue_today: float
    active_operators: int
    messages_per_day: List[DashboardDailyCount]
    revenue_per_day: List[DashboardDailyRevenue]
    top_accounts: List[DashboardTopAccount]
    recent_messages: List[DashboardMessage]
