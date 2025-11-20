"""
Authentication endpoints - matching Eskiz.uz API
POST /api/auth/login - Get token
PATCH /api/auth/refresh - Refresh token
GET /api/auth/user - Get user data
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ...models.auth import (
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
)
from ...services.auth_service import AuthService
from ...dependencies import get_auth_service, get_billing_client, get_current_user
from ...clients import BillingClient

router = APIRouter()
security = HTTPBearer()


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
    billing_client: BillingClient = Depends(get_billing_client),
):
    """
    Login with email and password
    Returns JWT token with 30-day validity (like Eskiz.uz)
    
    Example:
    ```json
    {
        "email": "user@example.com",
        "password": "password123"
    }
    ```
    
    Response:
    ```json
    {
        "token": "eyJhbGc...",
        "token_type": "bearer",
        "expires_in": 2592000,
        "refresh_token": "abc123..."
    }
    ```
    """
    # Authenticate user via billing service
    try:
        user_data = await billing_client.authenticate_user(
            email=request.email,
            password=request.password,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    # Create access token
    token_response = auth_service.create_access_token(
        account_id=user_data["account_id"],
        email=user_data["email"],
        account_type=user_data["type"],
        account_name=user_data["name"],
    )

    # Store refresh token
    await auth_service.store_refresh_token(
        refresh_token=token_response.refresh_token,
        account_id=user_data["account_id"],
        jti=auth_service.decode_token(token_response.token).jti,
    )
    
    return token_response


@router.patch("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
    billing_client: BillingClient = Depends(get_billing_client),
):
    """
    Refresh access token using refresh token
    
    Example:
    ```json
    {
        "refresh_token": "abc123..."
    }
    ```
    """
    # Verify refresh token
    result = await auth_service.verify_refresh_token(request.refresh_token)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    account_id, old_jti = result
    
    # Get user data
    try:
        user_data = await billing_client.get_account(account_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not found",
        )
    
    # Create new access token
    token_response = auth_service.create_access_token(
        account_id=user_data["account_id"],
        email=user_data["email"],
        account_type=user_data["type"],
        account_name=user_data["name"],
    )

    # Revoke old refresh token
    await auth_service.revoke_refresh_token(request.refresh_token)

    # Store new refresh token
    await auth_service.store_refresh_token(
        refresh_token=token_response.refresh_token,
        account_id=user_data["account_id"],
        jti=auth_service.decode_token(token_response.token).jti,
    )
    
    return token_response


@router.get("/user", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    billing_client: BillingClient = Depends(get_billing_client),
):
    """
    Get current authenticated user data
    Similar to Eskiz.uz /api/auth/user
    
    Requires: Bearer token in Authorization header
    
    Response:
    ```json
    {
        "id": "uuid",
        "email": "user@example.com",
        "name": "Company Name",
        "role": "client",
        "status": "active",
        "balance": 1000000.00,
        "currency": "UZS",
        "sms_count": 5000,
        "created_at": "2024-01-01T00:00:00Z"
    }
    ```
    """
    # Get full user data from billing service
    try:
        user_data = await billing_client.get_account(current_user["account_id"])
        balance_data = await billing_client.get_balance(str(current_user["account_id"]))

        # Get SMS count from CDR (optional - may not exist yet)
        sms_count = 0
        try:
            sms_stats = await billing_client.get_account_stats(current_user["account_id"])
            sms_count = sms_stats.get("total_messages", 0)
        except Exception:
            # Stats endpoint doesn't exist yet, default to 0
            pass

        return UserResponse(
            id=user_data["id"],
            email=current_user["email"],  # Use email from JWT token
            name=user_data["name"],
            role=user_data["type"],
            status=user_data["status"],
            balance=float(balance_data["balance"]),
            currency=balance_data["currency"],
            sms_count=sms_count,
            created_at=user_data["created_at"],
            parent_id=user_data.get("parent_id"),
            rate_limit_rps=user_data.get("rate_limit_rps"),
            allowed_ips=user_data.get("allowed_ips"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user data: {str(e)}",
        )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Logout - revoke current token
    """
    try:
        token = credentials.credentials
        token_data = auth_service.decode_token(token)
        
        # Calculate remaining TTL
        remaining_seconds = int((token_data.exp - token_data.iat).total_seconds())
        
        # Revoke token
        await auth_service.revoke_token(token_data.jti, remaining_seconds)
        
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to logout: {str(e)}",
        )

