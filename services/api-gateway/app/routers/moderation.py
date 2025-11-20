import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..auth import require_admin_token
from ..clients import BillingClient
from ..dependencies import get_billing_client
from ..exceptions import BillingError
from .. import schemas
router = APIRouter(prefix="/admin/templates", tags=["admin-templates"])


@router.get(
    "",
    response_model=list[schemas.Template],
    dependencies=[Depends(require_admin_token)],
)
async def list_pending_templates(
    status_filter: str | None = Query(default=None, alias="status"),
    billing: BillingClient = Depends(get_billing_client),
):
    try:
        templates = await billing.list_pending_templates(status_filter)
    except BillingError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return templates


@router.post(
    "/{template_id}/decision",
    response_model=schemas.Template,
    dependencies=[Depends(require_admin_token)],
)
async def decide_template(
    template_id: uuid.UUID,
    payload: schemas.TemplateDecision,
    billing: BillingClient = Depends(get_billing_client),
):
    try:
        template = await billing.decide_template(template_id, payload.model_dump())
    except BillingError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return template

