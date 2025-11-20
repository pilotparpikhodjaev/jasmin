"""
API routes
"""

from fastapi import APIRouter

from .v1 import auth, sms, user, templates, admin, stats, operators, accounts

# Main API router
api_router = APIRouter(prefix="/api")

# V1 routes
v1_router = APIRouter()

# Public routes (no auth required)
v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Protected routes (auth required)
v1_router.include_router(sms.router, prefix="/message/sms", tags=["SMS"])
v1_router.include_router(user.router, prefix="/user", tags=["User"])
v1_router.include_router(templates.router, prefix="/user", tags=["Templates"])

# Admin routes (admin auth required)
v1_router.include_router(admin.router, prefix="/admin", tags=["Admin"])

# Public admin-facing resources (still require admin auth)
v1_router.include_router(operators.router, prefix="/operators", tags=["Operators"])
v1_router.include_router(accounts.router, prefix="/accounts", tags=["Accounts"])

# Stats routes (admin auth required)
v1_router.include_router(stats.router, prefix="/stats", tags=["Stats"])

# Include v1 router
api_router.include_router(v1_router)

__all__ = ["api_router"]

