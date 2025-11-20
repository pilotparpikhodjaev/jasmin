"""Account-related response models for the API gateway.

These are tailored for the admin-web dashboard and intentionally mirror the
shape returned by the billing-service internal endpoints.
"""

from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class AdminAccountListItem(BaseModel):
    """Account summary used in the admin dashboard accounts table."""

    id: UUID
    name: str
    email: Optional[EmailStr] = None
    type: Literal["admin", "reseller", "client"]
    status: Literal["active", "suspended", "inactive"]
    balance: Decimal
    sms_count: int
    created_at: datetime
    updated_at: datetime

