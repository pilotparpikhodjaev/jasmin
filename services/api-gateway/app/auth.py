from fastapi import Depends, Header, HTTPException, Request, status

from .clients import BillingClient
from .dependencies import get_billing_client
from .exceptions import BillingError
from .schemas import AuthContext
from .config import get_settings


async def authenticate_request(
    request: Request,
    x_api_key: str = Header(..., alias="X-API-Key"),
    billing_client: BillingClient = Depends(get_billing_client),
) -> AuthContext:
    client_ip = request.client.host if request.client else None
    try:
        context = await billing_client.resolve_api_key(x_api_key)
    except BillingError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    if context.allowed_ips and client_ip not in context.allowed_ips:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="IP not allowed for this API key.")

    return context


async def require_admin_token(
    x_admin_token: str = Header(..., alias="X-Admin-Token"),
):
    settings = get_settings()
    if x_admin_token != settings.admin_api_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid admin token")

