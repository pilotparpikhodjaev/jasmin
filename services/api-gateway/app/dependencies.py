from fastapi import Request, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from redis.asyncio import Redis

from .clients import BillingClient, JasminHttpClient, RoutingClient
from .rate_limiter import RateLimiter
from .services.auth_service import AuthService
from .services.sms_service import SMSService
from .services.operator_service import OperatorService

security = HTTPBearer()


def get_billing_client(request: Request) -> BillingClient:
    return request.app.state.billing_client


def get_jasmin_client(request: Request) -> JasminHttpClient:
    return request.app.state.jasmin_client


def get_routing_client(request: Request) -> RoutingClient:
    return request.app.state.routing_client


def get_rate_limiter(request: Request) -> RateLimiter:
    return request.app.state.rate_limiter


def get_redis(request: Request) -> Redis:
    return request.app.state.redis


def get_auth_service(redis: Redis = Depends(get_redis)) -> AuthService:
    """Get auth service instance"""
    return AuthService(redis)


def get_sms_service(
    jasmin_client: JasminHttpClient = Depends(get_jasmin_client),
    billing_client: BillingClient = Depends(get_billing_client),
    routing_client: RoutingClient = Depends(get_routing_client),
) -> SMSService:
    """Get SMS service instance"""
    return SMSService(jasmin_client, billing_client, routing_client)


def get_operator_service(
    jasmin_client: JasminHttpClient = Depends(get_jasmin_client),
    billing_client: BillingClient = Depends(get_billing_client),
    routing_client: RoutingClient = Depends(get_routing_client),
    redis: Redis = Depends(get_redis),
) -> OperatorService:
    """Get operator service instance"""
    return OperatorService(jasmin_client, billing_client, routing_client, redis)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    """
    Dependency to get current authenticated user from JWT token

    Returns dict with:
    - account_id: UUID
    - email: str
    - account_type: str (admin, reseller, client)
    - account_name: str
    """
    try:
        token = credentials.credentials
        token_data = auth_service.decode_token(token)

        # Check if token is revoked
        if await auth_service.is_token_revoked(token_data.jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return {
            "account_id": token_data.account_id,
            "email": token_data.email,
            "account_type": token_data.account_type,
            "account_name": token_data.account_name,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

