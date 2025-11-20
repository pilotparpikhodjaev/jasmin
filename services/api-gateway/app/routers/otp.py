from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import authenticate_request
from ..clients import BillingClient, JasminHttpClient
from ..config import get_settings
from ..dependencies import get_billing_client, get_jasmin_client, get_rate_limiter
from ..exceptions import BillingError, RateLimitExceeded, UpstreamError
from ..rate_limiter import RateLimiter
from ..schemas import AuthContext, OtpRequest, OtpResponse
from ..utils import calculate_parts

router = APIRouter()


@router.post(
    "/otp/send",
    response_model=OtpResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a single OTP message",
)
async def send_otp(
    request: OtpRequest,
    auth: AuthContext = Depends(authenticate_request),
    jasmin_client: JasminHttpClient = Depends(get_jasmin_client),
    billing_client: BillingClient = Depends(get_billing_client),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> OtpResponse:
    settings = get_settings()
    limit = auth.rate_limit_rps or settings.rate_limit_rps
    try:
        await rate_limiter.check(str(auth.account_id), limit)
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc

    sender = request.sender or settings.default_sender
    dlr_url = request.dlr_callback_url or settings.default_dlr_callback

    jasmin_payload = {
        "to": request.to,
        "from": sender,
        "content": request.message,
        "coding": "0",
        "dlr": "yes" if dlr_url else "no",
        "dlr-level": "2",
        "dlr-method": "POST",
    }
    if dlr_url:
        jasmin_payload["dlr-url"] = dlr_url

    try:
        message_id = await jasmin_client.send_sms(jasmin_payload)
    except UpstreamError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    parts = calculate_parts(request.message)
    price_per_part = settings.default_price_per_part
    total_price = price_per_part * Decimal(parts)
    currency = auth.currency or settings.default_currency

    charge_payload = {
        "account_id": str(auth.account_id),
        "message_id": message_id,
        "msisdn": request.to,
        "sender": sender,
        "parts": parts,
        "price_per_part": str(price_per_part),
        "currency": currency,
    }

    try:
        await billing_client.charge_message(charge_payload)
    except BillingError as exc:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(exc)) from exc

    return OtpResponse(
        message_id=message_id,
        account_id=auth.account_id,
        price=total_price,
        currency=currency,
    )

