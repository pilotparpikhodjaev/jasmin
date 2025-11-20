"""
Dispatches API endpoints
Manages batch SMS tracking and status
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Dispatch, SmsCdr
from ..schemas_enterprise import (
    DispatchCreate,
    DispatchResponse,
    DispatchStatusResponse,
    DispatchUpdate,
)

router = APIRouter(prefix="/v1/dispatches", tags=["dispatches"])


@router.post("", response_model=DispatchResponse, status_code=201)
async def create_dispatch(
    dispatch_data: DispatchCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create new dispatch for batch SMS tracking

    **Required fields:**
    - dispatch_id: Unique dispatch identifier
    - account_id: Account ID
    - total_messages: Total number of messages in batch
    - currency: Currency code

    **Returns:** Created dispatch
    """
    # Check if dispatch_id already exists
    existing = await db.execute(select(Dispatch).where(Dispatch.dispatch_id == dispatch_data.dispatch_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"Dispatch with ID '{dispatch_data.dispatch_id}' already exists")

    # Create dispatch
    dispatch = Dispatch(
        dispatch_id=dispatch_data.dispatch_id,
        account_id=dispatch_data.account_id,
        total_messages=dispatch_data.total_messages,
        currency=dispatch_data.currency,
        metadata=dispatch_data.metadata,
        status="processing",
    )

    db.add(dispatch)
    await db.commit()
    await db.refresh(dispatch)

    return dispatch


@router.get("", response_model=List[DispatchResponse])
async def list_dispatches(
    account_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    List dispatches with optional filters

    **Query parameters:**
    - account_id: Filter by account ID
    - status: Filter by status (processing, completed, failed, cancelled)
    - limit: Maximum number of results (default: 100)
    - offset: Pagination offset (default: 0)

    **Returns:** List of dispatches
    """
    query = select(Dispatch)

    if account_id:
        query = query.where(Dispatch.account_id == account_id)
    if status:
        query = query.where(Dispatch.status == status)

    query = query.order_by(desc(Dispatch.created_at)).limit(limit).offset(offset)

    result = await db.execute(query)
    dispatches = result.scalars().all()

    return dispatches


@router.get("/{dispatch_id}", response_model=DispatchResponse)
async def get_dispatch(
    dispatch_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get dispatch by dispatch_id

    **Returns:** Dispatch details including counters
    """
    result = await db.execute(select(Dispatch).where(Dispatch.dispatch_id == dispatch_id))
    dispatch = result.scalar_one_or_none()

    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch not found")

    return dispatch


@router.put("/{dispatch_id}", response_model=DispatchResponse)
async def update_dispatch(
    dispatch_id: str,
    dispatch_data: DispatchUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update dispatch counters

    **Updatable fields:**
    - submitted_count: Number of submitted messages
    - delivered_count: Number of delivered messages
    - failed_count: Number of failed messages
    - pending_count: Number of pending messages
    - total_cost: Total cost of dispatch
    - status: Dispatch status

    **Returns:** Updated dispatch
    """
    result = await db.execute(select(Dispatch).where(Dispatch.dispatch_id == dispatch_id))
    dispatch = result.scalar_one_or_none()

    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch not found")

    # Update fields
    update_data = dispatch_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dispatch, field, value)

    # Auto-update status based on counters
    if dispatch.submitted_count + dispatch.delivered_count + dispatch.failed_count >= dispatch.total_messages:
        if dispatch.failed_count == dispatch.total_messages:
            dispatch.status = "failed"
        else:
            dispatch.status = "completed"

    await db.commit()
    await db.refresh(dispatch)

    return dispatch


@router.get("/{dispatch_id}/status", response_model=DispatchStatusResponse)
async def get_dispatch_status(
    dispatch_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get dispatch status summary

    **Returns:** Aggregated status counts from CDR records
    """
    # Get dispatch
    result = await db.execute(select(Dispatch).where(Dispatch.dispatch_id == dispatch_id))
    dispatch = result.scalar_one_or_none()

    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch not found")

    # Aggregate status from CDR
    stats_query = select(
        func.count(SmsCdr.id).label("total"),
        func.sum(func.case((SmsCdr.status == "submitted", 1), else_=0)).label("submitted"),
        func.sum(func.case((SmsCdr.status == "delivered", 1), else_=0)).label("delivered"),
        func.sum(func.case((SmsCdr.status == "failed", 1), else_=0)).label("failed"),
        func.sum(func.case((SmsCdr.status.in_(["pending", "submitted"]), 1), else_=0)).label("pending"),
        func.sum(SmsCdr.price).label("total_cost"),
    ).where(SmsCdr.dispatch_id == dispatch_id)

    result = await db.execute(stats_query)
    stats = result.one()

    # Update dispatch counters
    dispatch.submitted_count = stats.submitted or 0
    dispatch.delivered_count = stats.delivered or 0
    dispatch.failed_count = stats.failed or 0
    dispatch.pending_count = stats.pending or 0
    dispatch.total_cost = stats.total_cost or 0

    # Auto-update status
    if dispatch.submitted_count + dispatch.delivered_count + dispatch.failed_count >= dispatch.total_messages:
        if dispatch.failed_count == dispatch.total_messages:
            dispatch.status = "failed"
        else:
            dispatch.status = "completed"

    await db.commit()

    return DispatchStatusResponse(
        dispatch_id=dispatch_id,
        total=stats.total or 0,
        submitted=stats.submitted or 0,
        delivered=stats.delivered or 0,
        failed=stats.failed or 0,
        pending=stats.pending or 0,
        status=dispatch.status,
        total_cost=dispatch.total_cost,
        currency=dispatch.currency,
    )


@router.get("/{dispatch_id}/messages", response_model=List[dict])
async def get_dispatch_messages(
    dispatch_id: str,
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Get messages for dispatch

    **Query parameters:**
    - status: Filter by message status
    - limit: Maximum number of results (default: 100)
    - offset: Pagination offset (default: 0)

    **Returns:** List of CDR records for this dispatch
    """
    # Check if dispatch exists
    result = await db.execute(select(Dispatch).where(Dispatch.dispatch_id == dispatch_id))
    dispatch = result.scalar_one_or_none()

    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch not found")

    # Get messages
    query = select(SmsCdr).where(SmsCdr.dispatch_id == dispatch_id)

    if status:
        query = query.where(SmsCdr.status == status)

    query = query.order_by(desc(SmsCdr.created_at)).limit(limit).offset(offset)

    result = await db.execute(query)
    messages = result.scalars().all()

    # Convert to dict
    return [
        {
            "message_id": msg.message_id,
            "msisdn": msg.msisdn,
            "sender": msg.sender,
            "status": msg.status,
            "parts": msg.parts,
            "price": float(msg.price) if msg.price else None,
            "currency": msg.currency,
            "submit_at": msg.submit_at.isoformat(),
            "delivery_at": msg.delivery_at.isoformat() if msg.delivery_at else None,
            "error_code": msg.error_code,
        }
        for msg in messages
    ]


@router.delete("/{dispatch_id}", status_code=204)
async def delete_dispatch(
    dispatch_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete dispatch

    **Note:** This does NOT delete associated CDR records.
    CDR records will remain but dispatch_id will be set to NULL.

    **Returns:** 204 No Content on success
    """
    result = await db.execute(select(Dispatch).where(Dispatch.dispatch_id == dispatch_id))
    dispatch = result.scalar_one_or_none()

    if not dispatch:
        raise HTTPException(status_code=404, detail="Dispatch not found")

    await db.delete(dispatch)
    await db.commit()

