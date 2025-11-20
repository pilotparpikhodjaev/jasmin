from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import AuthContext, authenticate_request
from ..clients import BillingClient
from ..dependencies import get_billing_client
from ..exceptions import BillingError
from .. import schemas

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=list[schemas.Template])
async def list_templates(
    auth: AuthContext = Depends(authenticate_request),
    billing: BillingClient = Depends(get_billing_client),
):
    try:
        templates = await billing.list_templates(auth.account_id)
    except BillingError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return templates


@router.post("", response_model=schemas.Template, status_code=status.HTTP_201_CREATED)
async def create_template(
    payload: schemas.TemplatePayload,
    auth: AuthContext = Depends(authenticate_request),
    billing: BillingClient = Depends(get_billing_client),
):
    try:
        template = await billing.create_template(auth.account_id, payload.model_dump())
    except BillingError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    return template

