"""Billing events AMQP consumer for Jasmin submit_sm_resp processing."""

import json
import logging
from typing import Any

from aio_pika import ExchangeType, IncomingMessage
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import async_session
from ..services import apply_charge
from ..schemas import ChargeRequest
from .base import AMQPConsumer


logger = logging.getLogger(__name__)


class BillingEventsConsumer(AMQPConsumer):
    """Consumer for billing exchange events (bill_request.submit_sm_resp.#)."""

    def __init__(self, amqp_url: str):
        super().__init__(
            amqp_url=amqp_url,
            exchange_name="billing",
            exchange_type=ExchangeType.TOPIC,
            queue_name="billing_service.submit_sm_resp",
            routing_keys=["bill_request.submit_sm_resp.#"],
            prefetch_count=10,
        )

    async def process_message(self, message: IncomingMessage) -> None:
        """
        Process billing event from Jasmin.

        Expected message format (from Jasmin Bill publishing):
        {
            "bid": "unique-bill-id",
            "user": {
                "uid": "account-uuid",
                "username": "account-name"
            },
            "amounts": {
                "submit_sm_resp": 0.01
            },
            "message_id": "msg-uuid",
            "connector_id": "smpp-connector-1",
            "status": "ESME_ROK" or "ESME_*"
        }
        """
        async with message.process(ignore_processed=True):
            try:
                body = self._parse_message_body(message)

                # Extract billing information
                bill_id = body.get("bid")
                user = body.get("user", {})
                account_id = user.get("uid")
                amounts = body.get("amounts", {})
                submit_sm_resp_amount = amounts.get("submit_sm_resp", 0.0)
                message_id = body.get("message_id")
                status = body.get("status", "UNKNOWN")

                if not account_id or not message_id:
                    logger.error(
                        "Missing required fields in billing event: bill_id=%s, account_id=%s, message_id=%s",
                        bill_id,
                        account_id,
                        message_id,
                    )
                    await message.reject(requeue=False)
                    return

                logger.info(
                    "Processing billing event: bill_id=%s, account_id=%s, message_id=%s, amount=%.4f, status=%s",
                    bill_id,
                    account_id,
                    message_id,
                    submit_sm_resp_amount,
                    status,
                )

                # Process based on status
                if status == "ESME_ROK":
                    # Success - charge has already been applied by api-gateway
                    # This is confirmation, update CDR if needed
                    logger.debug("Message %s sent successfully (ESME_ROK)", message_id)
                else:
                    # Error - should refund or handle failed submission
                    # This will be implemented in future enhancement
                    logger.warning(
                        "Message %s failed with status %s - refund logic not yet implemented",
                        message_id,
                        status,
                    )

                await message.ack()

            except json.JSONDecodeError as e:
                logger.error("Failed to parse billing event JSON: %s", e)
                await message.reject(requeue=False)
            except Exception as e:
                logger.exception("Error processing billing event: %s", e)
                await message.reject(requeue=True)

    def _parse_message_body(self, message: IncomingMessage) -> dict[str, Any]:
        """Parse message body as JSON."""
        try:
            return json.loads(message.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            # Fallback: try to extract from headers if body is pickle
            # For now, we expect JSON format
            raise json.JSONDecodeError("Invalid message format", message.body, 0)
