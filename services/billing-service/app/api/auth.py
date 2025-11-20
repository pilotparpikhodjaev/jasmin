"""
Authentication API endpoints
Handles user login, registration, password management
"""

import uuid
from datetime import datetime, timedelta

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Account, AccountBalance, AccountCredential
from ..schemas_enterprise import (
    LoginRequest,
    LoginResponse,
    PasswordChangeRequest,
    PasswordResetRequest,
    RegisterRequest,
)

router = APIRouter(prefix="/v1/auth", tags=["authentication"])


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


@router.post("/register", response_model=LoginResponse, status_code=201)
async def register(
    register_data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Register new account

    **Required fields:**
    - name: Account name
    - email: Email address (must be unique)
    - password: Password (min 8 characters)
    - currency: Currency code (default: UZS)

    **Returns:** Created account details
    """
    # Check if email already exists
    existing = await db.execute(select(AccountCredential).where(AccountCredential.email == register_data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create account
    account = Account(
        name=register_data.name,
        type=register_data.type,
        status="active",
        currency=register_data.currency,
        profile={},
    )
    db.add(account)
    await db.flush()

    # Create credentials
    credentials = AccountCredential(
        account_id=account.id,
        email=register_data.email,
        password_hash=hash_password(register_data.password),
        email_verified=False,
    )
    db.add(credentials)

    # Create balance
    balance = AccountBalance(
        account_id=account.id,
        balance=0,
        credit_limit=0,
        currency=register_data.currency,
    )
    db.add(balance)

    await db.commit()
    await db.refresh(account)
    await db.refresh(balance)

    return LoginResponse(
        account_id=account.id,
        email=credentials.email,
        name=account.name,
        type=account.type,
        status=account.status,
        balance=balance.balance,
        currency=balance.currency,
        created_at=account.created_at,
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Login with email and password

    **Required fields:**
    - email: Email address
    - password: Password

    **Returns:** Account details including balance

    **Error codes:**
    - 401: Invalid credentials
    - 403: Account locked or suspended
    """
    # Get credentials
    result = await db.execute(select(AccountCredential).where(AccountCredential.email == login_data.email))
    credentials = result.scalar_one_or_none()

    if not credentials:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Check if account is locked
    if credentials.locked_until and credentials.locked_until > datetime.utcnow():
        raise HTTPException(
            status_code=403,
            detail=f"Account is locked until {credentials.locked_until.isoformat()}",
        )

    # Verify password
    if not verify_password(login_data.password, credentials.password_hash):
        # Increment failed login attempts
        credentials.failed_login_attempts += 1

        # Lock account after 5 failed attempts
        if credentials.failed_login_attempts >= 5:
            credentials.locked_until = datetime.utcnow() + timedelta(minutes=30)
            await db.commit()
            raise HTTPException(
                status_code=403,
                detail="Account locked due to too many failed login attempts. Try again in 30 minutes.",
            )

        await db.commit()
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Get account
    result = await db.execute(select(Account).where(Account.id == credentials.account_id))
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    # Check if account is suspended
    if account.status == "suspended":
        raise HTTPException(status_code=403, detail="Account is suspended")

    # Get balance
    result = await db.execute(select(AccountBalance).where(AccountBalance.account_id == account.id))
    balance = result.scalar_one_or_none()

    if not balance:
        raise HTTPException(status_code=500, detail="Account balance not found")

    # Reset failed login attempts and update last login
    credentials.failed_login_attempts = 0
    credentials.locked_until = None
    credentials.last_login_at = datetime.utcnow()
    await db.commit()

    return LoginResponse(
        account_id=account.id,
        email=credentials.email,
        name=account.name,
        type=account.type,
        status=account.status,
        balance=balance.balance,
        currency=balance.currency,
        created_at=account.created_at,
    )


@router.post("/change-password", status_code=204)
async def change_password(
    account_id: uuid.UUID,
    password_data: PasswordChangeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Change account password

    **Required fields:**
    - old_password: Current password
    - new_password: New password (min 8 characters)

    **Returns:** 204 No Content on success
    """
    # Get credentials
    result = await db.execute(select(AccountCredential).where(AccountCredential.account_id == account_id))
    credentials = result.scalar_one_or_none()

    if not credentials:
        raise HTTPException(status_code=404, detail="Account credentials not found")

    # Verify old password
    if not verify_password(password_data.old_password, credentials.password_hash):
        raise HTTPException(status_code=401, detail="Invalid current password")

    # Update password
    credentials.password_hash = hash_password(password_data.new_password)
    await db.commit()


@router.post("/reset-password", status_code=202)
async def reset_password(
    reset_data: PasswordResetRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Request password reset

    **Required fields:**
    - email: Email address

    **Returns:** 202 Accepted (always returns success for security)

    **Note:** In production, this should send a password reset email.
    For now, it just validates the email exists.
    """
    # Check if email exists (but don't reveal if it doesn't for security)
    result = await db.execute(select(AccountCredential).where(AccountCredential.email == reset_data.email))
    credentials = result.scalar_one_or_none()

    if credentials:
        # TODO: Send password reset email
        # For now, just log it
        print(f"Password reset requested for {reset_data.email}")

    # Always return success for security (don't reveal if email exists)
    return {"message": "If the email exists, a password reset link has been sent"}


@router.get("/verify-email/{account_id}", status_code=204)
async def verify_email(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify email address

    **Note:** In production, this should require a verification token.
    For now, it just marks the email as verified.

    **Returns:** 204 No Content on success
    """
    # Get credentials
    result = await db.execute(select(AccountCredential).where(AccountCredential.account_id == account_id))
    credentials = result.scalar_one_or_none()

    if not credentials:
        raise HTTPException(status_code=404, detail="Account credentials not found")

    # Mark email as verified
    credentials.email_verified = True
    credentials.email_verified_at = datetime.utcnow()
    await db.commit()

