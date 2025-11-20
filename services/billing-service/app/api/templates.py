import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas, services
from ..database import get_session

router = APIRouter()


@router.post(
    "/v1/templates",
    response_model=schemas.TemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_template(
    payload: schemas.TemplateCreate,
    account_id: uuid.UUID = Query(...),
    session: AsyncSession = Depends(get_session),
) -> schemas.TemplateResponse:
    async with session.begin():
        template = await services.create_template(session, account_id, payload)
    return schemas.TemplateResponse.model_validate(template)


@router.get(
    "/v1/templates",
    response_model=list[schemas.TemplateResponse],
)
async def list_templates(
    account_id: uuid.UUID = Query(...),
    session: AsyncSession = Depends(get_session),
) -> list[schemas.TemplateResponse]:
    templates = await services.list_templates_for_account(session, account_id)
    return [schemas.TemplateResponse.model_validate(tpl) for tpl in templates]

