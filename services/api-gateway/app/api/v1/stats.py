"""Stats endpoints for admin dashboard.

This module exposes aggregated system statistics consumed by the admin-web
Next.js dashboard at `/admin`.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from ...clients import BillingClient
from ...dependencies import get_billing_client, get_current_user

router = APIRouter()


def require_admin(current_user: dict = Depends(get_current_user)):
    """Dependency to require admin role for stats endpoints."""
    if current_user["account_type"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


@router.get("/overview")
async def get_dashboard_overview(
    current_user: dict = Depends(require_admin),
    billing_client: BillingClient = Depends(get_billing_client),
):
    """Get aggregated system statistics for the admin dashboard.

    This endpoint proxies to the billing-service internal stats endpoint
    `/internal/stats/overview` and simply forwards its JSON response.
    """
    try:
        return await billing_client.get_dashboard_overview()
    except HTTPException:
        # Re-raise FastAPI HTTP errors as-is
        raise
    except Exception as exc:  # pragma: no cover - generic upstream failure
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch dashboard stats from billing service: {exc}",
        )

