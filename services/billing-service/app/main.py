import asyncio
import logging

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from .api import api_router
from .config import get_settings
from .consumers import BillingEventsConsumer, DLREventsConsumer
from .database import init_models

settings = get_settings()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OTP Billing Service",
    version="0.1.0",
)

app.include_router(api_router)
Instrumentator().instrument(app).expose(app, include_in_schema=False)

# AMQP consumers (global state for lifecycle management)
billing_consumer: BillingEventsConsumer | None = None
dlr_consumer: DLREventsConsumer | None = None


@app.on_event("startup")
async def startup_event() -> None:
    global billing_consumer, dlr_consumer

    # Initialize database
    await init_models()

    # Build AMQP URL from config
    amqp_url = (
        f"amqp://{settings.jasmin_amqp_user}:{settings.jasmin_amqp_password}@"
        f"{settings.jasmin_amqp_host}:{settings.jasmin_amqp_port}{settings.jasmin_amqp_vhost}"
    )

    # Initialize and start AMQP consumers
    try:
        # Billing events consumer
        billing_consumer = BillingEventsConsumer(amqp_url)
        await billing_consumer.connect()
        asyncio.create_task(billing_consumer.start(billing_consumer.process_message))
        logger.info("Billing events consumer started")

        # DLR events consumer
        dlr_consumer = DLREventsConsumer(amqp_url)
        await dlr_consumer.connect()
        asyncio.create_task(dlr_consumer.start(dlr_consumer.process_message))
        logger.info("DLR events consumer started")

    except Exception as e:
        logger.exception("Failed to start AMQP consumers: %s", e)
        raise


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Gracefully close AMQP connections."""
    global billing_consumer, dlr_consumer

    logger.info("Shutting down AMQP consumers...")

    if billing_consumer:
        await billing_consumer.close()

    if dlr_consumer:
        await dlr_consumer.close()

    logger.info("AMQP consumers closed")


@app.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    return {"service": "billing", "status": "ok"}

