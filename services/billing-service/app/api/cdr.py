from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas, services
from ..database import get_session
from ..exceptions import NotFoundError

router = APIRouter()


@router.get(
    "/{message_id}",
    response_model=schemas.SmsCdrResponse,
)
async def get_message(
    message_id: str,
    session: AsyncSession = Depends(get_session),
) -> schemas.SmsCdrResponse:
    try:
        cdr = await services.get_cdr_by_message(session, message_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return schemas.SmsCdrResponse.model_validate(cdr)


@router.patch(
    "/{message_id}",
    response_model=schemas.SmsCdrResponse,
)
async def update_message_status(
    message_id: str,
    payload: schemas.MessageStatusUpdate,
    session: AsyncSession = Depends(get_session),
) -> schemas.SmsCdrResponse:
    async with session.begin():
        try:
            cdr = await services.update_message_status(session, message_id, payload)
        except NotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return schemas.SmsCdrResponse.model_validate(cdr)

