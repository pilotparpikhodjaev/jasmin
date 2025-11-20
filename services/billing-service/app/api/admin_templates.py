import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models, schemas, services
from ..database import get_session
from ..exceptions import NotFoundError

router = APIRouter()


@router.get(
    "/v1/admin/templates",
    response_model=list[schemas.TemplateResponse],
)
async def list_pending_templates(
    status_filter: str | None = Query(default=None, alias="status"),
    session: AsyncSession = Depends(get_session),
) -> list[schemas.TemplateResponse]:
    status_enum = None
    if status_filter:
        try:
            status_enum = models.TemplateStatus(status_filter)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status filter")

    templates = await services.list_templates_for_review(session, status_enum)
    return [schemas.TemplateResponse.model_validate(tpl) for tpl in templates]


@router.post(
    "/v1/admin/templates/{template_id}/decision",
    response_model=schemas.TemplateResponse,
)
async def decide_template(
    template_id: uuid.UUID,
    payload: schemas.TemplateDecisionRequest,
    session: AsyncSession = Depends(get_session),
) -> schemas.TemplateResponse:
    try:
        async with session.begin():
            template = await services.decide_template(
                session, template_id, models.TemplateStatus(payload.status), payload.comment
            )
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return schemas.TemplateResponse.model_validate(template)

