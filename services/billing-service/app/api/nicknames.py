"""
Nicknames (Sender IDs) API endpoints
Manages sender IDs with approval workflow
"""

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Account, Nickname
from ..schemas_enterprise import (
    NicknameCreate,
    NicknameModerate,
    NicknameResponse,
    NicknameUpdate,
)

router = APIRouter(prefix="/v1/nicknames", tags=["nicknames"])


@router.post("", response_model=NicknameResponse, status_code=201)
async def create_nickname(
    account_id: uuid.UUID,
    nickname_data: NicknameCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create new nickname (sender ID) for account

    **Required fields:**
    - nickname: Alphanumeric sender ID (max 11 characters)
    - category: Optional category (e.g., "transactional", "marketing")
    - description: Optional description

    **Status:** New nicknames start with "pending" status and require admin approval

    **Returns:** Created nickname
    """
    # Check if account exists
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Check if nickname already exists for this account
    existing = await db.execute(
        select(Nickname).where(Nickname.account_id == account_id, Nickname.nickname == nickname_data.nickname)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400, detail=f"Nickname '{nickname_data.nickname}' already exists for this account"
        )

    # Create nickname
    nickname = Nickname(
        account_id=account_id,
        nickname=nickname_data.nickname,
        category=nickname_data.category,
        description=nickname_data.description,
        status="pending",
    )

    db.add(nickname)
    await db.commit()
    await db.refresh(nickname)

    return nickname


@router.get("", response_model=List[NicknameResponse])
async def list_nicknames(
    account_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    List nicknames with optional filters

    **Query parameters:**
    - account_id: Filter by account ID
    - status: Filter by status (pending, approved, rejected)
    - limit: Maximum number of results (default: 100)
    - offset: Pagination offset (default: 0)

    **Returns:** List of nicknames
    """
    query = select(Nickname)

    if account_id:
        query = query.where(Nickname.account_id == account_id)
    if status:
        query = query.where(Nickname.status == status)

    query = query.order_by(desc(Nickname.created_at)).limit(limit).offset(offset)

    result = await db.execute(query)
    nicknames = result.scalars().all()

    return nicknames


@router.get("/{nickname_id}", response_model=NicknameResponse)
async def get_nickname(
    nickname_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get nickname by ID

    **Returns:** Nickname details including approval status
    """
    result = await db.execute(select(Nickname).where(Nickname.id == nickname_id))
    nickname = result.scalar_one_or_none()

    if not nickname:
        raise HTTPException(status_code=404, detail="Nickname not found")

    return nickname


@router.put("/{nickname_id}", response_model=NicknameResponse)
async def update_nickname(
    nickname_id: uuid.UUID,
    nickname_data: NicknameUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update nickname metadata

    **Updatable fields:**
    - category: Nickname category
    - description: Nickname description

    **Note:** Cannot update nickname text or status via this endpoint.
    Use moderation endpoint for status changes.

    **Returns:** Updated nickname
    """
    result = await db.execute(select(Nickname).where(Nickname.id == nickname_id))
    nickname = result.scalar_one_or_none()

    if not nickname:
        raise HTTPException(status_code=404, detail="Nickname not found")

    # Update fields
    update_data = nickname_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(nickname, field, value)

    await db.commit()
    await db.refresh(nickname)

    return nickname


@router.delete("/{nickname_id}", status_code=204)
async def delete_nickname(
    nickname_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete nickname

    **Returns:** 204 No Content on success
    """
    result = await db.execute(select(Nickname).where(Nickname.id == nickname_id))
    nickname = result.scalar_one_or_none()

    if not nickname:
        raise HTTPException(status_code=404, detail="Nickname not found")

    await db.delete(nickname)
    await db.commit()


@router.post("/{nickname_id}/moderate", response_model=NicknameResponse)
async def moderate_nickname(
    nickname_id: uuid.UUID,
    moderation_data: NicknameModerate,
    admin_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Moderate nickname (admin only)

    **Required fields:**
    - status: "approved" or "rejected"
    - rejection_reason: Required if status is "rejected"

    **Admin ID:** Must be provided in request (typically from JWT token)

    **Returns:** Updated nickname with moderation details
    """
    # Check if admin exists
    result = await db.execute(select(Account).where(Account.id == admin_id))
    admin = result.scalar_one_or_none()

    if not admin or admin.type != "admin":
        raise HTTPException(status_code=403, detail="Only admins can moderate nicknames")

    # Get nickname
    result = await db.execute(select(Nickname).where(Nickname.id == nickname_id))
    nickname = result.scalar_one_or_none()

    if not nickname:
        raise HTTPException(status_code=404, detail="Nickname not found")

    # Validate rejection reason
    if moderation_data.status == "rejected" and not moderation_data.rejection_reason:
        raise HTTPException(status_code=400, detail="Rejection reason is required when rejecting nickname")

    # Update nickname
    nickname.status = moderation_data.status
    nickname.approved_by = admin_id
    nickname.approved_at = func.now()
    nickname.rejection_reason = moderation_data.rejection_reason

    await db.commit()
    await db.refresh(nickname)

    return nickname


@router.get("/account/{account_id}/approved", response_model=List[str])
async def get_approved_nicknames(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get list of approved nicknames for account

    **Returns:** List of approved nickname strings (for use in SMS sending)
    """
    # Check if account exists
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Get approved nicknames
    query = select(Nickname.nickname).where(
        Nickname.account_id == account_id, Nickname.status == "approved"
    ).order_by(Nickname.nickname)

    result = await db.execute(query)
    nicknames = result.scalars().all()

    return list(nicknames)

