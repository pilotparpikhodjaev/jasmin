import secrets
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from . import models, schemas
from .exceptions import DuplicateMessageError, InsufficientBalanceError, NotFoundError


async def create_account(session: AsyncSession, payload: schemas.AccountCreate) -> models.Account:
    account = models.Account(
        name=payload.name,
        currency=payload.currency.upper(),
        type=payload.type,
        status=payload.status,
        parent_id=payload.parent_id,
    )
    balance = models.AccountBalance(
        account=account,
        balance=payload.initial_balance,
        credit_limit=payload.credit_limit,
        currency=payload.currency.upper(),
    )
    session.add_all([account, balance])
    await session.flush()
    return account


async def create_api_key(session: AsyncSession, payload: schemas.ApiKeyCreate) -> tuple[models.ApiKey, str]:
    token = secrets.token_urlsafe(32)
    key = models.ApiKey(
        account_id=payload.account_id,
        token=token,
        label=payload.label,
        allowed_ips=[str(ip) for ip in payload.allowed_ips] if payload.allowed_ips else None,
    )
    session.add(key)
    await session.flush()
    await session.refresh(key)
    return key, token


async def resolve_api_key(session: AsyncSession, token: str) -> models.ApiKey:
    stmt: Select[tuple[models.ApiKey]] = (
        select(models.ApiKey)
        .options(selectinload(models.ApiKey.account).selectinload(models.Account.balance))
        .where(models.ApiKey.token == token, models.ApiKey.revoked_at.is_(None))
    )
    result = await session.execute(stmt)
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise NotFoundError("API key not found")
    api_key.last_used_at = datetime.utcnow()
    await session.flush()
    return api_key


async def get_balance(session: AsyncSession, account_id: uuid.UUID) -> models.AccountBalance:
    balance = await session.get(models.AccountBalance, account_id)
    if balance is None:
        raise NotFoundError("Account balance not found")
    return balance


async def apply_charge(
    session: AsyncSession, payload: schemas.ChargeRequest
) -> tuple[models.SmsCdr, Decimal, uuid.UUID]:
    amount = payload.price_per_part * payload.parts

    balance_stmt = (
        select(models.AccountBalance).where(models.AccountBalance.account_id == payload.account_id).with_for_update()
    )
    balance = (await session.execute(balance_stmt)).scalar_one_or_none()
    if balance is None:
        raise NotFoundError("Account balance not found")

    available = Decimal(balance.balance) + Decimal(balance.credit_limit)
    if available < amount:
        raise InsufficientBalanceError("Insufficient balance or credit limit.")

    # Ensure message id uniqueness
    existing_stmt = select(models.SmsCdr).where(models.SmsCdr.message_id == payload.message_id)
    existing = (await session.execute(existing_stmt)).scalar_one_or_none()
    if existing:
        raise DuplicateMessageError("Duplicate message_id charge attempt.")

    balance.balance = Decimal(balance.balance) - amount

    ledger_entry = models.BalanceLedger(
        account_id=payload.account_id,
        amount=amount,
        currency=payload.currency.upper(),
        direction="debit",
        reason="sms_charge",
        reference=payload.message_id,
    )

    cdr = models.SmsCdr(
        account_id=payload.account_id,
        message_id=payload.message_id,
        msisdn=payload.msisdn,
        sender=payload.sender,
        connector_id=payload.connector_id,
        status="submitted",
        parts=payload.parts,
        price=amount,
        currency=payload.currency.upper(),
    )

    session.add_all([ledger_entry, cdr])
    await session.flush()

    return cdr, balance.balance, ledger_entry.id


async def get_cdr_by_message(session: AsyncSession, message_id: str) -> models.SmsCdr:
    stmt = select(models.SmsCdr).where(models.SmsCdr.message_id == message_id)
    result = await session.execute(stmt)
    cdr = result.scalar_one_or_none()
    if cdr is None:
        raise NotFoundError("Message not found")
    return cdr


async def update_message_status(
    session: AsyncSession, message_id: str, payload: schemas.MessageStatusUpdate
) -> models.SmsCdr:
    cdr = await get_cdr_by_message(session, message_id)
    cdr.status = payload.status
    cdr.delivery_at = payload.delivery_at or cdr.delivery_at
    cdr.error_code = payload.error_code
    cdr.dlr_payload = payload.dlr_payload
    await session.flush()
    return cdr


async def create_template(
    session: AsyncSession, account_id: uuid.UUID, payload: schemas.TemplateCreate
) -> models.Template:
    template = models.Template(
        account_id=account_id,
        name=payload.name,
        channel=payload.channel,
        category=payload.category,
        content=payload.content,
        variables=payload.variables,
        status=models.TemplateStatus.pending,
        last_submitted_at=datetime.utcnow(),
    )
    session.add(template)
    await session.flush()
    return template


async def list_templates_for_account(session: AsyncSession, account_id: uuid.UUID) -> list[models.Template]:
    stmt = (
        select(models.Template)
        .where(models.Template.account_id == account_id)
        .order_by(models.Template.updated_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def list_templates_for_review(
    session: AsyncSession, status: models.TemplateStatus | None = None
) -> list[models.Template]:
    stmt = select(models.Template).join(models.Account)
    if status:
        stmt = stmt.where(models.Template.status == status)
    stmt = stmt.order_by(models.Template.last_submitted_at.asc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def decide_template(
    session: AsyncSession,
    template_id: uuid.UUID,
    status: models.TemplateStatus,
    comment: Optional[str],
) -> models.Template:
    template = await session.get(models.Template, template_id)
    if template is None:
        raise NotFoundError("Template not found")

    template.status = status
    template.admin_comment = comment
    template.approved_at = datetime.utcnow() if status == models.TemplateStatus.approved else None
    template.updated_at = datetime.utcnow()
    await session.flush()
    return template

