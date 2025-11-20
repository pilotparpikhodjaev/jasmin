"""
Operators API endpoints
Manages SMPP operators, health monitoring, and statistics
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Operator, OperatorHealthMetric, SmsCdr
from ..schemas_enterprise import (
    OperatorCreate,
    OperatorHealthMetricsResponse,
    OperatorResponse,
    OperatorStatsResponse,
    OperatorUpdate,
)

router = APIRouter(prefix="/v1/operators", tags=["operators"])


@router.post("", response_model=OperatorResponse, status_code=201)
async def create_operator(
    operator_data: OperatorCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create new SMPP operator

    **Required fields:**
    - name: Operator name (e.g., "Ucell Uzbekistan")
    - code: Unique operator code (e.g., "UZ_UCELL")
    - country: ISO 3166-1 alpha-2 country code (e.g., "UZ")
    - mcc: Mobile Country Code (e.g., "434")
    - mnc: Mobile Network Code (e.g., "05")
    - price_per_sms: Price per SMS in specified currency
    - smpp_config: SMPP connection configuration

    **Returns:** Created operator with ID
    """
    # Check if operator code already exists
    existing = await db.execute(select(Operator).where(Operator.code == operator_data.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Operator with code '{operator_data.code}' already exists")

    # Create operator
    operator = Operator(
        name=operator_data.name,
        code=operator_data.code,
        country=operator_data.country,
        mcc=operator_data.mcc,
        mnc=operator_data.mnc,
        price_per_sms=operator_data.price_per_sms,
        currency=operator_data.currency,
        priority=operator_data.priority,
        weight=operator_data.weight,
        status=operator_data.status,
        health_check_enabled=operator_data.health_check_enabled,
        health_check_interval=operator_data.health_check_interval,
        smpp_config=operator_data.smpp_config.model_dump(),
        metadata=operator_data.metadata,
    )

    db.add(operator)
    await db.commit()
    await db.refresh(operator)

    return operator


@router.get("", response_model=List[OperatorResponse])
async def list_operators(
    country: Optional[str] = Query(None, min_length=2, max_length=2),
    status: Optional[str] = Query(None),
    mcc: Optional[str] = Query(None, min_length=3, max_length=3),
    mnc: Optional[str] = Query(None, min_length=2, max_length=3),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    List operators with optional filters

    **Query parameters:**
    - country: Filter by country code (e.g., "UZ")
    - status: Filter by status (active, inactive, maintenance)
    - mcc: Filter by Mobile Country Code
    - mnc: Filter by Mobile Network Code
    - limit: Maximum number of results (default: 100)
    - offset: Pagination offset (default: 0)

    **Returns:** List of operators
    """
    query = select(Operator)

    if country:
        query = query.where(Operator.country == country)
    if status:
        query = query.where(Operator.status == status)
    if mcc:
        query = query.where(Operator.mcc == mcc)
    if mnc:
        query = query.where(Operator.mnc == mnc)

    query = query.order_by(desc(Operator.created_at)).limit(limit).offset(offset)

    result = await db.execute(query)
    operators = result.scalars().all()

    return operators


@router.get("/{operator_id}", response_model=OperatorResponse)
async def get_operator(
    operator_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Get operator by ID

    **Returns:** Operator details including SMPP configuration
    """
    result = await db.execute(select(Operator).where(Operator.id == operator_id))
    operator = result.scalar_one_or_none()

    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")

    return operator


@router.put("/{operator_id}", response_model=OperatorResponse)
async def update_operator(
    operator_id: int,
    operator_data: OperatorUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update operator configuration

    **Updatable fields:**
    - name: Operator name
    - price_per_sms: Price per SMS
    - priority: Routing priority (0-1000)
    - weight: Routing weight (0-100)
    - status: Operator status
    - health_check_enabled: Enable/disable health monitoring
    - health_check_interval: Health check interval in seconds
    - smpp_config: SMPP connection configuration
    - metadata: Additional metadata

    **Returns:** Updated operator
    """
    result = await db.execute(select(Operator).where(Operator.id == operator_id))
    operator = result.scalar_one_or_none()

    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")

    # Update fields
    update_data = operator_data.model_dump(exclude_unset=True)
    if "smpp_config" in update_data and update_data["smpp_config"]:
        update_data["smpp_config"] = update_data["smpp_config"].model_dump()

    for field, value in update_data.items():
        setattr(operator, field, value)

    await db.commit()
    await db.refresh(operator)

    return operator


@router.delete("/{operator_id}", status_code=204)
async def delete_operator(
    operator_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete operator

    **Warning:** This will also delete all associated health metrics.
    CDR records will remain but operator_id will be set to NULL.

    **Returns:** 204 No Content on success
    """
    result = await db.execute(select(Operator).where(Operator.id == operator_id))
    operator = result.scalar_one_or_none()

    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")

    await db.delete(operator)
    await db.commit()


@router.get("/{operator_id}/health", response_model=OperatorHealthMetricsResponse)
async def get_operator_health(
    operator_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get latest health metrics for operator

    **Returns:** Latest health metrics including:
    - Connection status
    - Submit/delivery rates
    - Latency statistics (avg, p95, p99)
    - Health score (0-100)
    - Recent errors
    """
    # Check if operator exists
    result = await db.execute(select(Operator).where(Operator.id == operator_id))
    operator = result.scalar_one_or_none()

    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")

    # Get latest health metrics
    query = (
        select(OperatorHealthMetric)
        .where(OperatorHealthMetric.operator_id == operator_id)
        .order_by(desc(OperatorHealthMetric.measured_at))
        .limit(1)
    )

    result = await db.execute(query)
    health = result.scalar_one_or_none()

    if not health:
        raise HTTPException(status_code=404, detail="No health metrics available for this operator")

    return health


@router.get("/{operator_id}/stats", response_model=OperatorStatsResponse)
async def get_operator_stats(
    operator_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get operator statistics

    **Returns:** Aggregated statistics including:
    - Total messages sent
    - Delivery/failure counts
    - Delivery rate
    - Total revenue
    - Average latency
    """
    # Check if operator exists
    result = await db.execute(select(Operator).where(Operator.id == operator_id))
    operator = result.scalar_one_or_none()

    if not operator:
        raise HTTPException(status_code=404, detail="Operator not found")

    # Aggregate statistics from CDR
    stats_query = select(
        func.count(SmsCdr.id).label("total_messages"),
        func.sum(func.case((SmsCdr.status == "delivered", 1), else_=0)).label("delivered_messages"),
        func.sum(func.case((SmsCdr.status == "failed", 1), else_=0)).label("failed_messages"),
        func.sum(func.case((SmsCdr.status.in_(["submitted", "pending"]), 1), else_=0)).label("pending_messages"),
        func.sum(SmsCdr.price).label("total_revenue"),
        func.max(SmsCdr.submit_at).label("last_message_at"),
    ).where(SmsCdr.operator_id == operator_id)

    result = await db.execute(stats_query)
    stats = result.one()

    total_messages = stats.total_messages or 0
    delivered_messages = stats.delivered_messages or 0
    failed_messages = stats.failed_messages or 0
    pending_messages = stats.pending_messages or 0
    total_revenue = stats.total_revenue or 0
    last_message_at = stats.last_message_at

    # Calculate delivery rate
    delivery_rate = (delivered_messages / total_messages * 100) if total_messages > 0 else 0

    # Get average latency from health metrics
    health_query = (
        select(func.avg(OperatorHealthMetric.avg_submit_latency_ms))
        .where(OperatorHealthMetric.operator_id == operator_id)
        .where(OperatorHealthMetric.avg_submit_latency_ms > 0)
    )
    result = await db.execute(health_query)
    avg_latency = result.scalar() or 0

    return OperatorStatsResponse(
        operator_id=operator_id,
        operator_name=operator.name,
        total_messages=total_messages,
        delivered_messages=delivered_messages,
        failed_messages=failed_messages,
        pending_messages=pending_messages,
        delivery_rate=round(delivery_rate, 2),
        total_revenue=total_revenue,
        currency=operator.currency,
        avg_latency_ms=round(avg_latency, 2),
        last_message_at=last_message_at,
    )
