"""
SMS models - matching Eskiz.uz API structure
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, Field, HttpUrl


class SMSSendRequest(BaseModel):
    """Single SMS send request - /api/message/sms/send"""
    mobile_phone: str = Field(pattern=r"^\+?998\d{9}$", description="Phone number in format 998XXXXXXXXX")
    message: str = Field(min_length=1, max_length=1600)
    from_: str = Field(alias="from", max_length=11, description="Sender ID (nickname)")
    callback_url: Optional[HttpUrl] = None
    user_sms_id: Optional[str] = Field(default=None, max_length=100, description="Client's message ID")


class SMSBatchMessage(BaseModel):
    """Single message in batch"""
    mobile_phone: str = Field(pattern=r"^\+?998\d{9}$")
    message: str = Field(min_length=1, max_length=1600)
    user_sms_id: Optional[str] = None


class SMSBatchRequest(BaseModel):
    """Batch SMS send request - /api/message/sms/send-batch"""
    messages: List[SMSBatchMessage] = Field(min_length=1, max_length=10000)
    from_: str = Field(alias="from", max_length=11)
    dispatch_id: Optional[str] = Field(default=None, max_length=100, description="Batch identifier")
    callback_url: Optional[HttpUrl] = None


class SMSGlobalRequest(BaseModel):
    """International SMS send request - /api/message/sms/send-global"""
    mobile_phone: str = Field(pattern=r"^\+?\d{6,16}$")
    message: str = Field(min_length=1, max_length=1600)
    country_code: str = Field(pattern=r"^[A-Z]{2}$", description="ISO 3166-1 alpha-2 country code")
    unicode: bool = Field(default=False, description="Force Unicode encoding")
    from_: Optional[str] = Field(default=None, alias="from", max_length=11)
    callback_url: Optional[HttpUrl] = None


class SMSResponse(BaseModel):
    """SMS send response"""
    request_id: UUID
    message_id: str  # Jasmin message ID
    user_sms_id: Optional[str] = None
    status: str  # 'NEW', 'STORED', 'ACCEPTED'
    sms_count: int  # Number of parts
    price: Decimal
    currency: str
    balance_after: Decimal


class SMSBatchResponse(BaseModel):
    """Batch SMS response"""
    dispatch_id: str
    total_messages: int
    accepted: int
    rejected: int
    total_price: Decimal
    currency: str
    balance_after: Decimal
    messages: List[SMSResponse]


class SMSStatusResponse(BaseModel):
    """Message status response"""
    request_id: UUID
    message_id: str
    user_sms_id: Optional[str]
    status: str  # 'NEW', 'STORED', 'ACCEPTED', 'DELIVRD', 'UNDELIV', 'EXPIRED', 'REJECTD'
    submit_time: datetime
    delivery_time: Optional[datetime]
    error_code: Optional[str]
    operator: Optional[str]
    country: str
    sms_count: int
    price: Decimal


class MessageHistoryRequest(BaseModel):
    """Get message history - /api/message/sms/get-user-messages"""
    start_date: datetime
    to_date: datetime
    page_size: int = Field(default=50, ge=1, le=1000)
    count: int = Field(default=0, ge=0, description="Offset for pagination")
    is_ad: Optional[bool] = Field(default=None, description="Filter by advertising messages")
    status: Optional[str] = None  # Filter by status


class MessageHistoryResponse(BaseModel):
    """Message history response"""
    total: int
    messages: List[SMSStatusResponse]


class DispatchMessagesRequest(BaseModel):
    """Get messages by dispatch ID"""
    dispatch_id: str
    count: int = Field(default=0, ge=0)
    is_ad: Optional[bool] = None
    status: Optional[str] = None


class DispatchStatusResponse(BaseModel):
    """Dispatch status summary"""
    dispatch_id: str
    total_messages: int
    status_breakdown: dict[str, int]  # {'DELIVRD': 100, 'UNDELIV': 5, ...}
    total_price: Decimal
    currency: str


class SMSNormalizerRequest(BaseModel):
    """SMS normalizer request - /api/message/sms/normalizer"""
    message: str


class SMSNormalizerResponse(BaseModel):
    """SMS normalizer response"""
    original_message: str
    normalized_message: str
    original_length: int
    normalized_length: int
    savings_percent: float
    recommendations: List[str]


class SMSCheckRequest(BaseModel):
    """SMS check request - /api/message/sms/check"""
    message: str
    to: Optional[str] = None  # Phone number for operator-specific pricing


class OperatorPricing(BaseModel):
    """Pricing per operator"""
    operator: str
    price_per_sms: Decimal
    currency: str


class SMSCheckResponse(BaseModel):
    """SMS check response"""
    message: str
    length: int
    parts_count: int
    encoding: str  # 'GSM7', 'UCS2'
    is_blacklisted: bool
    blacklist_reason: Optional[str] = None
    pricing: List[OperatorPricing]


class DLRCallback(BaseModel):
    """DLR callback payload - sent to client's callback_url"""
    request_id: UUID
    message_id: str
    user_sms_id: Optional[str]
    country: str
    phone_number: str
    sms_count: int
    status: str  # 'DELIVRD', 'UNDELIV', 'EXPIRED', 'REJECTD'
    status_date: datetime
    error_code: Optional[str] = None

