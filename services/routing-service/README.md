# Routing Service

Intelligent SMS routing service implementing Least Cost Routing (LCR) for the OTP SMS platform.

## Overview

The routing service determines the optimal SMPP connector for each SMS based on:
- Destination phone number (MCC/MNC prefix matching)
- Operator pricing
- Operator health score
- Priority configuration

## Architecture

**Stack:**
- Go 1.22+
- Gin (HTTP framework)
- PostgreSQL (operator database)
- SQLx (SQL toolkit)

**Database Schema:**
- `operators` - Mobile network operators with pricing and configuration
- `mcc_mnc_prefixes` - Phone number prefix to operator mapping
- `operator_health` - Real-time operator health metrics

## API Endpoints

### POST /v1/routing/decision
Get routing decision for a destination phone number.

**Request:**
```json
{
  "destination_msisdn": "+998901234567",
  "account_id": "uuid",
  "message_parts": 1
}
```

**Response:**
```json
{
  "primary_connector_id": "smpp-beeline-uz",
  "backup_connector_ids": ["smpp-ucell-uz", "smpp-ums-uz"],
  "cost_per_part": 50.00,
  "operator_name": "Beeline"
}
```

### GET /v1/operators
List all active operators.

**Response:**
```json
{
  "operators": [
    {
      "id": 1,
      "name": "Beeline",
      "country": "Uzbekistan",
      "mcc": "434",
      "mnc": "04",
      "smpp_connector_id": "smpp-beeline-uz",
      "status": "active",
      "price_per_sms": 50.00,
      "currency": "UZS",
      "health_score": 95,
      "priority": 1
    }
  ],
  "count": 4
}
```

### GET /v1/operators/:phone
Identify operator from phone number.

**Example:** GET /v1/operators/+998901234567

**Response:**
```json
{
  "phone": "+998901234567",
  "operator": "Beeline",
  "connector_id": "smpp-beeline-uz",
  "price": 50.00
}
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "service": "routing",
  "status": "ok"
}
```

## Database Setup

Run the initial migration to create tables and populate Uzbekistan operators:

```bash
psql -U otp -d otp -f migrations/001_initial_schema.sql
```

**Initial Operators:**
- **Beeline** (prefixes: 90, 91) - 50 UZS/SMS
- **Ucell** (prefixes: 93, 94, 95, 97) - 55 UZS/SMS
- **UMS** (prefixes: 88, 98, 99) - 60 UZS/SMS
- **Perfectum Mobile** (prefixes: 33, 77) - 65 UZS/SMS

## Configuration

Environment variables:

- `ROUTING_DB_URL` - PostgreSQL connection string (default: postgres://otp:otp-secret@postgres:5432/otp?sslmode=disable)
- `PORT` - HTTP server port (default: 8080)
- `GIN_MODE` - Gin mode: debug, release, test (default: release)

## Development

**Build:**
```bash
go build -o routing-service ./cmd/server
```

**Run:**
```bash
export ROUTING_DB_URL="postgres://otp:otp-secret@localhost:5432/otp?sslmode=disable"
export PORT=8082
./routing-service
```

**Docker:**
```bash
docker build -t routing-service .
docker run -p 8082:8082 \
  -e ROUTING_DB_URL="postgres://otp:otp-secret@postgres:5432/otp?sslmode=disable" \
  routing-service
```

## Routing Logic (Phase 1)

Current implementation: **Static routing by prefix**

1. Extract country code and prefix from MSISDN
2. Lookup operator in `mcc_mnc_prefixes` table (longest match)
3. Return primary connector ID and pricing
4. Provide backup connectors sorted by price + health score

**Future enhancements (Phase 2+):**
- Dynamic routing based on real-time metrics
- A/B testing of operators
- Traffic shaping and load balancing
- Cost optimization algorithms
- Failover automation

## Integration with API Gateway

The API Gateway calls the routing service before sending each SMS:

```python
# In api-gateway/app/services/sms_service.py
route = await self.routing_client.get_route(
    phone=request.mobile_phone,
    account_id=account_id,
)
# Use route["smpp_connector_id"] to send via correct operator
```

## Monitoring

Metrics exposed at `/metrics` endpoint (Prometheus format):
- Request latency histograms
- Routing decision counts
- Database query performance
- Error rates

## License

Part of Jasmin OTP SMS Platform
