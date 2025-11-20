from datetime import datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import schemas, services
from ..database import get_session
from ..exceptions import NotFoundError
from ..models import Account, Operator, SmsCdr
from ..schemas_enterprise import (
    DashboardDailyCount,
    DashboardDailyRevenue,
    DashboardMessage,
    DashboardStatsResponse,
    DashboardTopAccount,
)

router = APIRouter()


@router.get(
    "/api-keys/{token}",
    response_model=schemas.ApiKeyResolveResponse,
)
async def resolve_api_key(
    token: str,
    session: AsyncSession = Depends(get_session),
) -> schemas.ApiKeyResolveResponse:
    try:
        api_key = await services.resolve_api_key(session, token)
    except NotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    account = api_key.account
    balance = account.balance
    rate_limit = None
    if account.profile:
        rate_limit = account.profile.get("rate_limit_rps")

    return schemas.ApiKeyResolveResponse(
        account_id=account.id,
        account_name=account.name,
        status=account.status,
        currency=account.currency,
        balance=balance.balance if balance else 0,
        credit_limit=balance.credit_limit if balance else 0,
        rate_limit_rps=rate_limit,
        allowed_ips=api_key.allowed_ips,
    )



def _map_cdr_status_to_dashboard(status: str) -> str:
    """Map internal CDR status values to dashboard-friendly statuses."""
    if status == "submitted":
        return "sent"
    if status in {"delivered", "failed", "pending"}:
        return status
    return "pending"


@router.get(
    "/stats/overview",
    response_model=DashboardStatsResponse,
)
async def get_dashboard_overview_stats(
    session: AsyncSession = Depends(get_session),
) -> DashboardStatsResponse:
    """Return aggregated statistics for the admin dashboard."""
    now = datetime.utcnow()
    today = now.date()
    start_of_today = datetime.combine(today, time.min)

    # Total accounts
    result = await session.execute(select(func.count(Account.id)))
    total_accounts = int(result.scalar() or 0)

    # Messages and revenue today
    result = await session.execute(
        select(
            func.count(SmsCdr.id),
            func.coalesce(func.sum(SmsCdr.price), 0),
        ).where(SmsCdr.submit_at >= start_of_today)
    )
    total_messages_today, total_revenue_today_raw = result.one()
    total_messages_today = int(total_messages_today or 0)
    total_revenue_today = float(total_revenue_today_raw or 0)

    # Active operators
    result = await session.execute(
        select(func.count(Operator.id)).where(Operator.status == "active")
    )
    active_operators = int(result.scalar() or 0)

    # Trends for last 7 days (including today)
    start_range_date = today - timedelta(days=6)
    start_range = datetime.combine(start_range_date, time.min)

    day_trunc = func.date_trunc("day", SmsCdr.submit_at)
    trend_query = (
        select(
            day_trunc.label("day"),
            func.count(SmsCdr.id).label("count"),
            func.coalesce(func.sum(SmsCdr.price), 0).label("revenue"),
        )
        .where(SmsCdr.submit_at >= start_range)
        .group_by(day_trunc)
        .order_by(day_trunc)
    )
    result = await session.execute(trend_query)
    trend_rows = result.all()

    messages_per_day: list[DashboardDailyCount] = []
    revenue_per_day: list[DashboardDailyRevenue] = []
    for row in trend_rows:
        day = row.day
        day_str = day.date().isoformat() if isinstance(day, datetime) else str(day)
        messages_per_day.append(
            DashboardDailyCount(date=day_str, count=int(row.count or 0))
        )
        revenue_per_day.append(
            DashboardDailyRevenue(date=day_str, amount=float(row.revenue or 0))
        )

    # Top accounts by message volume (overall)
    top_query = (
        select(
            SmsCdr.account_id,
            func.count(SmsCdr.id).label("usage"),
            func.max(Account.name).label("name"),
        )
        .join(Account, SmsCdr.account_id == Account.id)
        .group_by(SmsCdr.account_id)
        .order_by(func.count(SmsCdr.id).desc())
        .limit(10)
    )
    result = await session.execute(top_query)
    top_accounts = [
        DashboardTopAccount(
            id=row.account_id,
            name=row.name,
            usage=int(row.usage or 0),
        )
        for row in result.all()
        if row.account_id is not None
    ]

    # Recent messages
    recent_query = (
        select(
            SmsCdr.message_id,
            SmsCdr.msisdn,
            SmsCdr.sender,
            SmsCdr.status,
            SmsCdr.account_id,
            SmsCdr.submit_at,
            SmsCdr.delivery_at,
            SmsCdr.message_text,
        )
        .order_by(SmsCdr.submit_at.desc())
        .limit(10)
    )
    result = await session.execute(recent_query)
    recent_messages_rows = result.all()
    recent_messages: list[DashboardMessage] = []
    for row in recent_messages_rows:
        if not row.message_id:
            continue
        recent_messages.append(
            DashboardMessage(
                id=row.message_id,
                from_=row.sender or "",
                to=row.msisdn,
                content=row.message_text or "",
                status=_map_cdr_status_to_dashboard(row.status or ""),
                operator_id=None,
                account_id=str(row.account_id),
                created_at=row.submit_at,
                delivered_at=row.delivery_at,
            )
        )

    return DashboardStatsResponse(
        total_accounts=total_accounts,
        total_messages_today=total_messages_today,
        total_revenue_today=total_revenue_today,
        active_operators=active_operators,
        messages_per_day=messages_per_day,
        revenue_per_day=revenue_per_day,
        top_accounts=top_accounts,
        recent_messages=recent_messages,
    )


