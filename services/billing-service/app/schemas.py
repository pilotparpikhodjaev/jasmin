import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, IPvAnyAddress


class AccountCreate(BaseModel):
    name: str
    currency: str = Field(min_length=3, max_length=3)
    type: Literal["admin", "reseller", "client"] = "client"
    status: Literal["active", "suspended"] = "active"
    parent_id: Optional[uuid.UUID] = None
    credit_limit: Decimal = Decimal("0.0")
    initial_balance: Decimal = Decimal("0.0")


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    currency: str
    type: str
    status: str
    created_at: datetime


class ApiKeyCreate(BaseModel):
    account_id: uuid.UUID
    label: Optional[str] = None
    allowed_ips: Optional[list[IPvAnyAddress]] = None


class ApiKeyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    token: str
    account_id: uuid.UUID
    label: Optional[str]
    allowed_ips: Optional[list[str]]
    created_at: datetime


class BalanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: uuid.UUID
    balance: Decimal
    credit_limit: Decimal
    currency: str
    updated_at: datetime


class ChargeRequest(BaseModel):
    account_id: uuid.UUID
    message_id: str
    msisdn: str
    sender: Optional[str] = None
    connector_id: Optional[str] = None
    parts: int = 1
    price_per_part: Decimal
    currency: str


class ChargeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    charge_id: uuid.UUID
    message_id: str
    account_id: uuid.UUID
    debited_amount: Decimal
    remaining_balance: Decimal
    currency: str


class MessageStatusUpdate(BaseModel):
    status: Literal["submitted", "delivered", "failed"]
    delivery_at: Optional[datetime] = None
    error_code: Optional[str] = None
    dlr_payload: Optional[dict] = None


class SmsCdrResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message_id: str
    account_id: uuid.UUID
    status: str
    price: Optional[Decimal]
    currency: Optional[str]
    submit_at: datetime
    delivery_at: Optional[datetime]
    parts: int
    msisdn: str
    sender: Optional[str]


class ApiKeyResolveResponse(BaseModel):
    account_id: uuid.UUID
    account_name: str
    status: str
    currency: str
    balance: Decimal
    credit_limit: Decimal
    rate_limit_rps: Optional[int] = None
    allowed_ips: Optional[list[str]] = None


class TemplateCreate(BaseModel):
    name: str
    channel: Literal["sms", "email", "voice", "whatsapp"] = "sms"
    category: Optional[str] = None
    content: str
    variables: Optional[list[str]] = None


class TemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    name: str
    channel: str
    category: Optional[str]
    content: str
    variables: Optional[list[str]]
    status: str
    admin_comment: Optional[str]
    last_submitted_at: datetime
    approved_at: Optional[datetime]
    updated_at: datetime


class TemplateDecisionRequest(BaseModel):
    status: Literal["approved", "rejected"]
    comment: Optional[str] = None

