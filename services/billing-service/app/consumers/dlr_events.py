"""DLR events AMQP consumer for Jasmin delivery receipt processing."""

import json
import logging
from datetime import datetime
from typing import Any

from aio_pika import ExchangeType, IncomingMessage
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import async_session
from ..services import update_message_status
from ..schemas import MessageStatusUpdate
from .base import AMQPConsumer


logger = logging.getLogger(__name__)


class DLREventsConsumer(AMQPConsumer):
    """Consumer for messaging exchange DLR events (dlr.*)."""

    def __init__(self, amqp_url: str):
        super().__init__(
            amqp_url=amqp_url,
            exchange_name="messaging",
            exchange_type=ExchangeType.TOPIC,
            queue_name="billing_service.dlr",
            routing_keys=["dlr.#"],
            prefetch_count=20,
        )

    async def process_message(self, message: IncomingMessage) -> None:
        """
        Process DLR event from Jasmin.

        Expected message format (from Jasmin DLR publishing):
        {
            "message_id": "msg-uuid",
            "status": "DELIVRD" | "EXPIRED" | "DELETED" | "UNDELIV" | "ACCEPTD" | "UNKNOWN" | "REJECTD" | "ESME_*",
            "pdu_type": "deliver_sm" | "data_sm" | "submit_sm_resp",
            "smpp_msgid": "operator-message-id",
            "dlr_details": {
                "id": "operator-dlr-id",
                "sub": "1",
                "dlvrd": "1",
                "submit_date": "2024-01-01 12:00:00",
                "done_date": "2024-01-01 12:00:05",
                "stat": "DELIVRD",
                "err": "000",
                "text": "Message delivered"
            }
        }
        """
        async with message.process(ignore_processed=True):
            try:
                body = self._parse_message_body(message)

                message_id = body.get("message_id")
                status_raw = body.get("status", "UNKNOWN")
                pdu_type = body.get("pdu_type")
                dlr_details = body.get("dlr_details", {})

                if not message_id:
                    logger.error("Missing message_id in DLR event")
                    await message.reject(requeue=False)
                    return

                # Map Jasmin status to our CDR status
                status = self._map_dlr_status(status_raw)

                logger.info(
                    "Processing DLR event: message_id=%s, status=%s (%s), pdu_type=%s",
                    message_id,
                    status,
                    status_raw,
                    pdu_type,
                )

                # Update CDR in database
                async with async_session() as session:
                    try:
                        await update_message_status(
                            session,
                            message_id,
                            MessageStatusUpdate(
                                status=status,
                                delivery_at=self._parse_delivery_time(dlr_details),
                                error_code=dlr_details.get("err"),
                                dlr_payload=dlr_details if dlr_details else None,
                            ),
                        )
                        await session.commit()
                        logger.debug("Updated CDR for message %s to status %s", message_id, status)

                    except Exception as e:
                        await session.rollback()
                        logger.error("Failed to update CDR for message %s: %s", message_id, e)
                        raise

                await message.ack()

            except json.JSONDecodeError as e:
                logger.error("Failed to parse DLR event JSON: %s", e)
                await message.reject(requeue=False)
            except Exception as e:
                logger.exception("Error processing DLR event: %s", e)
                await message.reject(requeue=True)

    def _parse_message_body(self, message: IncomingMessage) -> dict[str, Any]:
        """Parse message body as JSON."""
        try:
            return json.loads(message.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            # Fallback: try to extract from message properties
            # Jasmin DLR has message-id in properties
            message_id = message.message_id
            status = message.body.decode("utf-8") if message.body else "UNKNOWN"

            return {
                "message_id": message_id,
                "status": status,
                "pdu_type": message.headers.get("type") if message.headers else None,
                "dlr_details": {},
            }

    def _map_dlr_status(self, jasmin_status: str) -> str:
        """
        Map Jasmin DLR status to our CDR status.

        Jasmin statuses (from SMPP spec Table B-2):
        - DELIVRD: Message is delivered to destination
        - EXPIRED: Message validity period has expired
        - DELETED: Message has been deleted
        - UNDELIV: Message is undeliverable
        - ACCEPTD: Message is in accepted state
        - UNKNOWN: Message is in invalid state
        - REJECTD: Message is in a rejected state
        - ESME_*: SMPP error codes from submit_sm_resp
        """
        status_map = {
            "DELIVRD": "delivered",
            "EXPIRED": "expired",
            "DELETED": "failed",
            "UNDELIV": "failed",
            "ACCEPTD": "pending",
            "UNKNOWN": "failed",
            "REJECTD": "rejected",
        }

        # Handle ESME_* error codes
        if jasmin_status.startswith("ESME_"):
            if jasmin_status == "ESME_ROK":
                return "submitted"  # Successfully submitted to operator
            else:
                return "failed"  # Operator rejected

        return status_map.get(jasmin_status, "unknown")

    def _parse_delivery_time(self, dlr_details: dict) -> datetime | None:
        """Parse delivery time from DLR details."""
        done_date = dlr_details.get("done_date") or dlr_details.get("donedate")
        if not done_date:
            return None

        try:
            # Try common formats
            for fmt in ["%y%m%d%H%M", "%Y-%m-%d %H:%M:%S", "%Y%m%d%H%M%S"]:
                try:
                    return datetime.strptime(str(done_date), fmt)
                except ValueError:
                    continue
        except Exception as e:
            logger.warning("Failed to parse delivery time '%s': %s", done_date, e)

        return None
