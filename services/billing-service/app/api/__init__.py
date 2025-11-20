from fastapi import APIRouter

from . import (
    accounts,
    admin_templates,
    auth,
    cdr,
    charges,
    dispatches,
    health,
    internal,
    nicknames,
    operators,
    templates,
    payment,
)

api_router = APIRouter()

# Health check
api_router.include_router(health.router, tags=["health"])

# Authentication
api_router.include_router(auth.router, tags=["authentication"])

# Core billing
api_router.include_router(accounts.router, prefix="/v1/accounts", tags=["accounts"])
api_router.include_router(charges.router, prefix="/v1/charges", tags=["charges"])
api_router.include_router(cdr.router, prefix="/v1/messages", tags=["cdr"])

# Enterprise features
api_router.include_router(operators.router, tags=["operators"])
api_router.include_router(nicknames.router, tags=["nicknames"])
api_router.include_router(dispatches.router, tags=["dispatches"])

# Templates
api_router.include_router(templates.router, tags=["templates"])
api_router.include_router(admin_templates.router, tags=["admin-templates"])

# Internal
api_router.include_router(internal.router, prefix="/internal", tags=["internal"])

# Payment
api_router.include_router(payment.router, prefix="/v1", tags=["payment"])

