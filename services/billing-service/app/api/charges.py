from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas, services
from ..database import get_session
from ..exceptions import DuplicateMessageError, InsufficientBalanceError, NotFoundError

router = APIRouter()


@router.post(
    "/",
    response_model=schemas.ChargeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_charge(
    payload: schemas.ChargeRequest,
    session: AsyncSession = Depends(get_session),
) -> schemas.ChargeResponse:
    try:
        async with session.begin():
            cdr, remaining_balance, ledger_id = await services.apply_charge(session, payload)
    except InsufficientBalanceError as exc:
        raise HTTPException(status_code=status.HTTP_402_PAYMENT_REQUIRED, detail=str(exc)) from exc
    except DuplicateMessageError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return schemas.ChargeResponse(
        charge_id=ledger_id,
        message_id=cdr.message_id,
        account_id=cdr.account_id,
        debited_amount=cdr.price,
        remaining_balance=remaining_balance,
        currency=cdr.currency,
    )

