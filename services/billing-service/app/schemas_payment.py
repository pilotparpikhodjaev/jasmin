"""
Payment models for billing-service.
This defines Click and Payme payment schemas.
"""

from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PaymentProvider(str, Enum):
    CLICK = "click"
    PAYME = "payme"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentInitiateRequest(BaseModel):
    account_id: UUID
    amount: Decimal = Field(..., gt=0)
    currency: str = "UZS"
    provider: PaymentProvider
    return_url: Optional[str] = None


class PaymentInitiateResponse(BaseModel):
    transaction_id: str
    redirect_url: str
    provider_transaction_id: Optional[str] = None


# --- Click Specific Schemas ---
class ClickCallbackRequest(BaseModel):
    click_trans_id: int
    service_id: int
    click_paydoc_id: int
    merchant_trans_id: str
    amount: float
    action: int
    error: int
    error_note: Optional[str] = None
    sign_time: str
    sign_string: str


class ClickCallbackResponse(BaseModel):
    click_trans_id: int
    merchant_trans_id: str
    merchant_prepare_id: Optional[int] = None
    merchant_confirm_id: Optional[int] = None
    error: int
    error_note: str


# --- Payme Specific Schemas ---
class PaymeCallbackRequest(BaseModel):
    method: str
    params: dict
    id: int


class PaymeCallbackResponse(BaseModel):
    result: Optional[dict] = None
    error: Optional[dict] = None
    id: int


class OperatorRate(BaseModel):
    operator_id: int
    operator_name: str
    price: Decimal
    currency: str = "UZS"
    mcc: Optional[str] = None
    mnc: Optional[str] = None


class RateUpdateRequest(BaseModel):
    price: Decimal

