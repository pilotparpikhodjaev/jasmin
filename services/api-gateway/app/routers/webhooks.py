from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse

from ..clients import BillingClient
from ..dependencies import get_billing_client
from ..exceptions import BillingError

router = APIRouter()


def _map_status(message_status: str) -> str:
    normalized = message_status.upper()
    if normalized in {"DELIVRD", "DELIVERED", "ESME_ROK"}:
        return "delivered"
    if normalized in {"ENROUTE", "ACCEPTD", "PENDING"}:
        return "submitted"
    return "failed"


def _parse_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%y%m%d%H%M").isoformat()
    except ValueError:
        return None


@router.api_route("/webhooks/dlr", methods=["GET", "POST"], include_in_schema=False)
async def dlr_webhook(
    request: Request,
    billing_client: BillingClient = Depends(get_billing_client),
) -> PlainTextResponse:
    if request.method == "GET":
        payload = dict(request.query_params)
    else:
        try:
            form = await request.form()
            payload = {key: value for key, value in form.multi_items()}
        except Exception:
            payload = await request.json()

    message_id = payload.get("id")
    if not message_id:
        return PlainTextResponse("ACK/Jasmin")

    status = _map_status(payload.get("message_status", "unknown"))
    delivery_at = _parse_date(payload.get("donedate"))

    update = {
        "status": status,
        "delivery_at": delivery_at,
        "error_code": payload.get("err"),
        "dlr_payload": payload,
    }

    try:
        await billing_client.update_message_status(message_id, update)
    except BillingError:
        # We still ACK to prevent replays; errors are logged on the billing service.
        pass

    return PlainTextResponse("ACK/Jasmin")

