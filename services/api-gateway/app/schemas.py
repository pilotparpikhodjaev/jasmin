import uuid
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class OtpRequest(BaseModel):
    to: str = Field(pattern=r"^\+?\d{6,16}$")
    message: str = Field(min_length=1, max_length=1600)
    sender: Optional[str] = Field(default=None, max_length=11)
    dlr_callback_url: Optional[HttpUrl] = None
    metadata: Optional[dict] = None


class OtpResponse(BaseModel):
    message_id: str
    account_id: uuid.UUID
    price: Decimal
    currency: str


class AuthContext(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: uuid.UUID
    account_name: str
    currency: str
    balance: Decimal
    credit_limit: Decimal
    rate_limit_rps: Optional[int]
    allowed_ips: Optional[list[str]]


class TemplatePayload(BaseModel):
    name: str
    channel: str = "sms"
    category: Optional[str] = None
    content: str
    variables: Optional[list[str]] = None


class Template(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    name: str
    channel: str
    category: Optional[str]
    content: str
    variables: Optional[list[str]]
    status: str
    admin_comment: Optional[str]
    last_submitted_at: str
    approved_at: Optional[str]
    updated_at: str


class TemplateDecision(BaseModel):
    status: str
    comment: Optional[str] = None

