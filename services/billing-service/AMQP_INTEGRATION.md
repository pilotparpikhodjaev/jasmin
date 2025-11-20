# AMQP Integration for Billing Service

## Overview

The billing service implements AMQP consumers to process real-time events from Jasmin SMS Gateway for billing finalization and delivery receipt (DLR) tracking.

## Architecture

```
Jasmin SMS Gateway
    │
    ├─→ RabbitMQ Exchange: "billing"
    │   │
    │   └─→ Routing Key: bill_request.submit_sm_resp.#
    │       │
    │       └─→ Queue: billing_service.submit_sm_resp
    │           │
    │           └─→ BillingEventsConsumer
    │               └─→ Finalize charges, handle failures
    │
    └─→ RabbitMQ Exchange: "messaging"
        │
        └─→ Routing Key: dlr.#
            │
            └─→ Queue: billing_service.dlr
                │
                └─→ DLREventsConsumer
                    └─→ Update CDR with delivery status
```

## Components

### 1. Jasmin Configuration

**File:** `misc/config/otp/jasmin.cfg`

Key settings:
- `publish_submit_sm_resp = True` - Enables publishing of submit_sm_resp events
- `smpp_receipt_on_success_submit_sm_resp = True` - Sends receipts to SMPP clients

### 2. Base Consumer (`app/consumers/base.py`)

Generic AMQP consumer with:
- Robust connection with auto-reconnect
- QoS prefetch control
- Queue binding with routing keys
- Graceful shutdown

### 3. Billing Events Consumer (`app/consumers/billing_events.py`)

**Exchange:** billing (topic)
**Routing Keys:** `bill_request.submit_sm_resp.#`
**Queue:** billing_service.submit_sm_resp

**Message Format (JSON):**
```json
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
  "status": "ESME_ROK" | "ESME_*"
}
```

**Processing:**
- `ESME_ROK` - Success confirmation (charge already applied by api-gateway)
- `ESME_*` errors - Failed submission (refund logic planned for future)

### 4. DLR Events Consumer (`app/consumers/dlr_events.py`)

**Exchange:** messaging (topic)
**Routing Keys:** `dlr.#`
**Queue:** billing_service.dlr

**Message Format (JSON):**
```json
{
  "message_id": "msg-uuid",
  "status": "DELIVRD" | "EXPIRED" | "UNDELIV" | "REJECTD" | "ESME_*",
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
```

**Status Mapping:**

| Jasmin Status | CDR Status | Description |
|--------------|-----------|-------------|
| DELIVRD | delivered | Successfully delivered to handset |
| EXPIRED | expired | Message validity period expired |
| DELETED | failed | Message was deleted |
| UNDELIV | failed | Undeliverable (invalid number, etc.) |
| ACCEPTD | pending | Accepted by operator, awaiting delivery |
| UNKNOWN | failed | Invalid/unknown state |
| REJECTD | rejected | Rejected by operator |
| ESME_ROK | submitted | Successfully submitted to operator |
| ESME_* | failed | SMPP error codes |

## Startup and Shutdown

### Startup (`main.py`)

1. Initialize database
2. Build AMQP connection URL from config
3. Create and connect billing events consumer
4. Create and connect DLR events consumer
5. Start async tasks for message processing

### Shutdown

1. Gracefully close billing events consumer connection
2. Gracefully close DLR events consumer connection
3. Wait for in-flight messages to complete

## Configuration

**Environment Variables (from docker-compose.otp.yml):**

```yaml
BILLING_JASMIN_AMQP_HOST: rabbitmq
BILLING_JASMIN_AMQP_PORT: 5672
BILLING_JASMIN_AMQP_USER: jasmin
BILLING_JASMIN_AMQP_PASSWORD: jasmin
BILLING_JASMIN_AMQP_VHOST: /
```

## Error Handling

### Message Processing
- JSON parse errors → reject without requeue
- Database errors → reject with requeue
- Unknown errors → reject with requeue

### Connection Failures
- Automatic reconnection with exponential backoff (aio-pika robust connection)
- Connection health monitored via heartbeats

## Queue Configuration

**Billing Queue:**
- Message TTL: 24 hours
- Max length: 100,000 messages
- Prefetch count: 10

**DLR Queue:**
- Message TTL: 24 hours
- Max length: 100,000 messages
- Prefetch count: 20 (DLR typically higher volume)

## Monitoring

Consumers log:
- Connection status (connect, disconnect, reconnect)
- Message processing (success, error, status)
- Queue binding confirmations

**Log Levels:**
- INFO: Startup, shutdown, successful processing
- WARNING: Failed deliveries, refund logic triggers
- ERROR: Parse errors, database errors
- EXCEPTION: Unexpected errors with full stack trace

## Future Enhancements

1. **Refund Logic** - Implement automatic refunds for failed submissions (ESME_* errors)
2. **Pickle Support** - Add support for Jasmin's native pickle serialization
3. **Dead Letter Queue** - Configure DLQ for permanently failed messages
4. **Metrics** - Prometheus metrics for consumer performance (message rate, processing time, errors)
5. **Circuit Breaker** - Prevent cascading failures during database outages

## Testing

See `AMQP_TESTING.md` for integration test scenarios:
- Send SMS → verify billing event consumed → verify charge finalized
- Send SMS → receive DLR → verify CDR updated
- Concurrent message processing
- Consumer restart resilience
- RabbitMQ connection failure recovery

## Troubleshooting

### Consumer Not Starting
- Check RabbitMQ is running: `docker-compose logs rabbitmq`
- Verify AMQP credentials match between Jasmin and billing-service
- Check billing-service logs for connection errors

### Messages Not Being Consumed
- Verify Jasmin config has `publish_submit_sm_resp = True`
- Check RabbitMQ Management UI (http://localhost:15672) for queue bindings
- Verify routing keys match between publisher and consumer
- Check message format (should be JSON)

### DLR Not Updating CDR
- Verify message_id exists in sms_cdr table
- Check DLR message format in RabbitMQ Management UI
- Review billing-service logs for update errors
- Verify database connection is healthy

## References

- [Jasmin AMQP Documentation](https://docs.jasminsms.com/en/latest/messaging/index.html)
- [aio-pika Documentation](https://aio-pika.readthedocs.io/)
- [RabbitMQ Topic Exchange](https://www.rabbitmq.com/tutorials/tutorial-five-python.html)
