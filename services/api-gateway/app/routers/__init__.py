from fastapi import APIRouter

from . import account, moderation, otp, templates, webhooks

api_router = APIRouter(prefix="/v1")
api_router.include_router(otp.router, tags=["otp"])
api_router.include_router(account.router, tags=["account"])
api_router.include_router(webhooks.router, tags=["webhooks"])
api_router.include_router(templates.router)
api_router.include_router(moderation.router)

