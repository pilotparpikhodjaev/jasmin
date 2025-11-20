from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import authenticate_request
from ..clients import BillingClient
from ..dependencies import get_billing_client
from ..exceptions import BillingError
from ..schemas import AuthContext

router = APIRouter()


@router.get("/balance", summary="Get current account balance")
async def get_balance(
    auth: AuthContext = Depends(authenticate_request),
    billing_client: BillingClient = Depends(get_billing_client),
) -> dict:
    try:
        return await billing_client.get_balance(str(auth.account_id))
    except BillingError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.get("/messages/{message_id}", summary="Get message status")
async def get_message_status(
    message_id: str,
    auth: AuthContext = Depends(authenticate_request),
    billing_client: BillingClient = Depends(get_billing_client),
) -> dict:
    try:
        record = await billing_client.get_message(message_id)
    except BillingError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    if record.get("account_id") != str(auth.account_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Message not owned by account.")

    return record


@router.get("/profile", response_model=AuthContext, summary="Get authenticated account profile")
async def get_profile(auth: AuthContext = Depends(authenticate_request)) -> AuthContext:
    return auth

