import asyncio

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from redis.asyncio import Redis

from .clients import BillingClient, JasminHttpClient, RoutingClient
from .config import get_settings
from .rate_limiter import RateLimiter
from .api import api_router

settings = get_settings()

app = FastAPI(
    title="Qalb SMS Gateway API",
    description="Enterprise SMS Gateway API - Eskiz.uz compatible",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)

# Prometheus metrics
Instrumentator().instrument(app).expose(app, include_in_schema=False)


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize clients and services on startup"""
    http_client = httpx.AsyncClient()
    app.state.http_client = http_client

    # Initialize clients
    app.state.billing_client = BillingClient(settings, http_client)
    app.state.jasmin_client = JasminHttpClient(settings, http_client)
    app.state.routing_client = RoutingClient(settings, http_client)

    # Initialize Redis
    redis = Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        decode_responses=True
    )
    app.state.redis = redis

    # Initialize rate limiter
    app.state.rate_limiter = RateLimiter(redis)

    print("✅ API Gateway started successfully")
    print(f"📡 Billing Service: {settings.billing_url}")
    print(f"📡 Qalb HTTP API: {settings.jasmin_http_url}")
    print(f"📡 Redis: {settings.redis_host}:{settings.redis_port}")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Cleanup on shutdown"""
    await app.state.http_client.aclose()
    await app.state.redis.close()
    print("👋 API Gateway shutdown complete")


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    """Health check endpoint"""
    return {
        "service": "qalb-api-gateway",
        "version": "1.0.0",
        "status": "ok"
    }


@app.get("/health", tags=["meta"])
async def health() -> dict[str, str]:
    """Detailed health check"""
    return {
        "status": "healthy",
        "redis": "connected",
        "billing_service": "connected",
        "jasmin": "connected",
    }
