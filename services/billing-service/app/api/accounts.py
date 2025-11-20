import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models, schemas, services
from ..database import get_session
from ..exceptions import NotFoundError
from ..schemas_enterprise import AdminAccountListItem

router = APIRouter()


@router.get(
    "/",
    response_model=list[AdminAccountListItem],
)
async def list_accounts(
    account_type: str | None = Query(None, alias="type"),
    status: str | None = None,
    search: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[AdminAccountListItem]:
    """List accounts with basic stats for the admin dashboard.

    This endpoint is intended to be called by the API gateway and returns
    a flat structure expected by the admin-web frontend.
    """
    base_query = (
        select(models.Account, models.AccountCredential.email, models.AccountBalance.balance)
        .outerjoin(models.AccountCredential, models.AccountCredential.account_id == models.Account.id)
        .outerjoin(models.AccountBalance, models.AccountBalance.account_id == models.Account.id)
    )

    conditions = []
    if account_type:
        conditions.append(models.Account.type == account_type)
    if status:
        conditions.append(models.Account.status == status)
    if search:
        like = f"%{search.lower()}%"
        conditions.append(
            or_(
                func.lower(models.Account.name).like(like),
                func.lower(models.AccountCredential.email).like(like),
            )
        )

    if conditions:
        base_query = base_query.where(*conditions)

    result = await session.execute(base_query)
    rows = result.all()

    accounts = []
    account_ids: list[uuid.UUID] = []
    for account, email, balance in rows:
        accounts.append((account, email, balance))
        account_ids.append(account.id)

    sms_counts: dict[uuid.UUID, int] = {}
    if account_ids:
        counts_query = (
            select(models.SmsCdr.account_id, func.count(models.SmsCdr.id))
            .where(models.SmsCdr.account_id.in_(account_ids))
            .group_by(models.SmsCdr.account_id)
        )
        result = await session.execute(counts_query)
        for account_id, count in result.all():
            sms_counts[account_id] = int(count or 0)

    items: list[AdminAccountListItem] = []
    for account, email, balance in accounts:
        balance_value = balance or 0
        items.append(
            AdminAccountListItem(
                id=account.id,
                name=account.name,
                email=email,
                type=account.type,
                status=account.status,
                balance=balance_value,
                sms_count=sms_counts.get(account.id, 0),
                created_at=account.created_at,
                updated_at=account.updated_at,
            )
        )

    return items


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=schemas.AccountResponse,
)
async def create_account(
    payload: schemas.AccountCreate, session: AsyncSession = Depends(get_session)
) -> schemas.AccountResponse:
    async with session.begin():
        account = await services.create_account(session, payload)
    return schemas.AccountResponse.model_validate(account)


@router.get(
    "/{account_id}",
    response_model=schemas.AccountResponse,
)
async def get_account(account_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> schemas.AccountResponse:
    account = await session.get(models.Account, account_id)
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return schemas.AccountResponse.model_validate(account)


@router.get(
    "/{account_id}/balance",
    response_model=schemas.BalanceResponse,
)
async def get_account_balance(
    account_id: uuid.UUID, session: AsyncSession = Depends(get_session)
) -> schemas.BalanceResponse:
    try:
        balance = await services.get_balance(session, account_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return schemas.BalanceResponse.model_validate(balance)


@router.post(
    "/{account_id}/api-keys",
    response_model=schemas.ApiKeyResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key(
    account_id: uuid.UUID,
    payload: schemas.ApiKeyCreate,
    session: AsyncSession = Depends(get_session),
) -> schemas.ApiKeyResponse:
    if payload.account_id != account_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="account_id mismatch")

    async with session.begin():
        key, token = await services.create_api_key(session, payload)

    return schemas.ApiKeyResponse(
        id=key.id,
        token=token,
        account_id=key.account_id,
        label=key.label,
        allowed_ips=key.allowed_ips,
        created_at=key.created_at,
    )

