"""Base AMQP consumer for Jasmin events."""

import asyncio
import logging
from typing import Callable, Optional

import aio_pika
from aio_pika import ExchangeType, IncomingMessage
from aio_pika.abc import AbstractRobustConnection


logger = logging.getLogger(__name__)


class AMQPConsumer:
    """Base class for AMQP consumers."""

    def __init__(
        self,
        amqp_url: str,
        exchange_name: str,
        exchange_type: ExchangeType,
        queue_name: str,
        routing_keys: list[str],
        prefetch_count: int = 10,
    ):
        self.amqp_url = amqp_url
        self.exchange_name = exchange_name
        self.exchange_type = exchange_type
        self.queue_name = queue_name
        self.routing_keys = routing_keys
        self.prefetch_count = prefetch_count

        self.connection: Optional[AbstractRobustConnection] = None
        self.channel = None
        self.exchange = None
        self.queue = None
        self._consumer_task: Optional[asyncio.Task] = None

    async def connect(self) -> None:
        """Establish connection to RabbitMQ."""
        logger.info("Connecting to RabbitMQ at %s", self.amqp_url)

        self.connection = await aio_pika.connect_robust(
            self.amqp_url,
            client_properties={"connection_name": self.queue_name},
        )

        self.channel = await self.connection.channel()
        await self.channel.set_qos(prefetch_count=self.prefetch_count)

        # Declare exchange
        self.exchange = await self.channel.declare_exchange(
            name=self.exchange_name,
            type=self.exchange_type,
            durable=True,
        )

        # Declare queue
        self.queue = await self.channel.declare_queue(
            name=self.queue_name,
            durable=True,
            arguments={
                "x-message-ttl": 86400000,  # 24 hours TTL
                "x-max-length": 100000,  # Max 100k messages
            },
        )

        # Bind queue to exchange with routing keys
        for routing_key in self.routing_keys:
            await self.queue.bind(
                exchange=self.exchange,
                routing_key=routing_key,
            )
            logger.info(
                "Bound queue %s to exchange %s with routing key %s",
                self.queue_name,
                self.exchange_name,
                routing_key,
            )

        logger.info("AMQP consumer %s ready", self.queue_name)

    async def start(self, message_handler: Callable) -> None:
        """Start consuming messages."""
        if not self.queue:
            raise RuntimeError("Consumer not connected. Call connect() first.")

        logger.info("Starting consumer %s", self.queue_name)
        await self.queue.consume(message_handler)

    async def close(self) -> None:
        """Close AMQP connection gracefully."""
        logger.info("Closing AMQP consumer %s", self.queue_name)

        if self.connection and not self.connection.is_closed:
            await self.connection.close()

    async def process_message(self, message: IncomingMessage) -> None:
        """
        Process incoming message. Override in subclass.

        IMPORTANT: Must call message.ack() or message.reject() after processing.
        """
        raise NotImplementedError("Subclass must implement process_message()")
