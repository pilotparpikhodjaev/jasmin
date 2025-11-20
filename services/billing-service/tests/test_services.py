import asyncio
from decimal import Decimal
import uuid

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import models, schemas, services
from app.database import Base


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as sess:
        yield sess
    await engine.dispose()


@pytest.mark.asyncio
async def test_apply_charge_and_update_status(session):
    account_payload = schemas.AccountCreate(
        name="Test OTP",
        currency="USD",
        initial_balance=Decimal("1.00"),
        credit_limit=Decimal("1.00"),
    )
    async with session.begin():
        account = await services.create_account(session, account_payload)

    charge_payload = schemas.ChargeRequest(
        account_id=account.id,
        message_id="test-message",
        msisdn="+998901234567",
        sender="TEST",
        connector_id="mtn_primary",
        parts=1,
        price_per_part=Decimal("0.02"),
        currency="USD",
    )

    async with session.begin():
        cdr, remaining, ledger_id = await services.apply_charge(session, charge_payload)

    assert cdr.message_id == "test-message"
    assert Decimal(remaining) == Decimal("0.98")
    assert ledger_id is not None

    status_payload = schemas.MessageStatusUpdate(status="delivered")
    async with session.begin():
        updated = await services.update_message_status(session, cdr.message_id, status_payload)

    assert updated.status == "delivered"


@pytest.mark.asyncio
async def test_template_workflow(session):
    account_payload = schemas.AccountCreate(name="Client A", currency="USD")
    async with session.begin():
        account = await services.create_account(session, account_payload)

    template_payload = schemas.TemplateCreate(
        name="OTP Alert",
        channel="sms",
        category="security",
        content="Your OTP is {{code}}",
        variables=["code"],
    )

    async with session.begin():
        template = await services.create_template(session, account.id, template_payload)

    assert template.status.value == "pending"

    templates = await services.list_templates_for_account(session, account.id)
    assert len(templates) == 1

    async with session.begin():
        decided = await services.decide_template(
            session, template.id, models.TemplateStatus.approved, "Looks good"
        )

    assert decided.status == models.TemplateStatus.approved

