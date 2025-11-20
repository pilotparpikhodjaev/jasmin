"""Accounts endpoints used by the admin-web dashboard.

These routes are mounted under `/api/accounts` and provide a simple
representation of accounts with balance and SMS usage information.

Currently only listing is required by the frontend:

- GET /api/accounts -> list accounts for admin dashboard

All endpoints require an authenticated admin user.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ...clients import BillingClient
from ...dependencies import get_billing_client, get_current_user
from ...models.account import AdminAccountListItem

router = APIRouter()


def require_admin(current_user: dict = Depends(get_current_user)):
    """Dependency to require admin role for account management."""

    if current_user["account_type"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


@router.get("", response_model=list[AdminAccountListItem])
async def list_accounts(
    type: Optional[str] = Query(None, description="Filter by account type", alias="type"),
    filter_status: Optional[str] = Query(None, description="Filter by status", alias="status"),
    search: Optional[str] = Query(None, description="Free text search"),
    current_user: dict = Depends(require_admin),
    billing_client: BillingClient = Depends(get_billing_client),
) -> list[AdminAccountListItem]:
    """List accounts for the admin dashboard.

    This proxies to the billing-service /v1/accounts endpoint which already
    returns the flattened structure consumed by the Next.js admin-web app.
    """

    try:
        accounts = await billing_client.list_accounts(
            account_type=type,
            status=filter_status,
            search=search,
        )
        # billing-service already returns the correct shape; FastAPI will
        # validate it against AdminAccountListItem.
        return accounts
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to list accounts from billing service: {exc}",
        )

