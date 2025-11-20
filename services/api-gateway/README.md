# API Gateway - Jasmin SMS Gateway

Enterprise-grade SMS Gateway API compatible with Eskiz.uz API specification.

## Features

✅ **Authentication**
- JWT Bearer token authentication (30-day validity)
- Refresh token support
- API key authentication
- Token revocation

✅ **SMS Operations**
- Single SMS sending
- Batch SMS sending (up to 10,000 messages)
- International SMS support
- Message normalization
- Pre-send SMS checking (parts, encoding, pricing)
- Message status tracking

✅ **Reporting & Analytics**
- Message history with filters
- Dispatch tracking
- Monthly totals by status
- CSV export

✅ **Template Management**
- Template creation with variables
- Moderation workflow
- Template-based sending

✅ **Admin Features**
- Operator management (CRUD)
- Dynamic SMPP connector creation
- Health monitoring
- Operator statistics

## API Endpoints

### Authentication
```
POST   /api/auth/login          - Login with email/password
PATCH  /api/auth/refresh        - Refresh access token
GET    /api/auth/user           - Get current user info
POST   /api/auth/logout         - Logout (revoke token)
```

### SMS
```
POST   /api/message/sms/send              - Send single SMS
POST   /api/message/sms/send-batch        - Send batch SMS
POST   /api/message/sms/send-global       - Send international SMS
POST   /api/message/sms/get-user-messages - Get message history
POST   /api/message/sms/get-user-messages-by-dispatch - Get messages by dispatch
POST   /api/message/sms/get-dispatch-status - Get dispatch status
POST   /api/message/sms/normalizer        - Normalize SMS
GET    /api/message/sms/check             - Check SMS
GET    /api/message/sms/{message_id}      - Get message status
```

### User
```
GET    /api/user/get-limit      - Get balance
GET    /api/nick/me             - Get sender IDs
POST   /api/user/totals         - Get monthly totals
POST   /api/user/export-csv     - Export CSV
```

### Templates
```
POST   /api/user/template                 - Create template
GET    /api/user/templates                - Get templates
GET    /api/user/template/{id}            - Get template by ID
PUT    /api/user/template/{id}            - Update template
DELETE /api/user/template/{id}            - Delete template
POST   /api/user/template/{id}/send       - Send with template
```

### Admin
```
POST   /api/admin/operators                    - Create operator
GET    /api/admin/operators                    - List operators
GET    /api/admin/operators/{id}               - Get operator
PUT    /api/admin/operators/{id}               - Update operator
DELETE /api/admin/operators/{id}               - Delete operator
GET    /api/admin/operators/{id}/health        - Get operator health
POST   /api/admin/operators/{id}/connect       - Connect operator
POST   /api/admin/operators/{id}/disconnect    - Disconnect operator
GET    /api/admin/operators/{id}/stats         - Get operator stats
POST   /api/admin/templates/{id}/moderate      - Moderate template
```

## Quick Start

### 1. Install Dependencies

```bash
cd services/api-gateway
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file:

```env
# Server
API_GATEWAY_PORT=8080
ENVIRONMENT=development

# Jasmin
API_GATEWAY_JASMIN_HTTP_URL=http://localhost:8990
API_GATEWAY_JASMIN_JCLI_URL=http://localhost:8991
API_GATEWAY_JASMIN_USER=admin
API_GATEWAY_JASMIN_PASSWORD=password

# Billing Service
API_GATEWAY_BILLING_URL=http://localhost:8081

# Routing Service
API_GATEWAY_ROUTING_URL=http://localhost:8082

# Redis
API_GATEWAY_REDIS_HOST=localhost
API_GATEWAY_REDIS_PORT=6379
API_GATEWAY_REDIS_DB=0

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_DAYS=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=90

# Defaults
API_GATEWAY_DEFAULT_CURRENCY=UZS
API_GATEWAY_DEFAULT_PRICE_PER_SMS=50.0
API_GATEWAY_RATE_LIMIT_RPS=50
```

### 3. Run Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### 4. Access API Documentation

- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

## Usage Examples

### 1. Login

```bash
curl -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

Response:
```json
{
  "token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 2592000,
  "refresh_token": "abc123..."
}
```

### 2. Send SMS

```bash
curl -X POST http://localhost:8080/api/message/sms/send \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mobile_phone": "998901234567",
    "message": "Your OTP code is 123456",
    "from": "MyCompany",
    "callback_url": "https://example.com/dlr"
  }'
```

Response:
```json
{
  "request_id": "uuid",
  "message_id": "jasmin-msg-id",
  "status": "ACCEPTED",
  "sms_count": 1,
  "price": 50.00,
  "currency": "UZS",
  "balance_after": 9950.00
}
```

### 3. Get Balance

```bash
curl -X GET http://localhost:8080/api/user/get-limit \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response:
```json
{
  "balance": 1000000.00,
  "currency": "UZS",
  "credit_limit": 0.00,
  "available_balance": 1000000.00
}
```

### 4. Create Operator (Admin)

```bash
curl -X POST http://localhost:8080/api/admin/operators \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Ucell Uzbekistan",
    "code": "UZ_UCELL",
    "country": "UZ",
    "mcc": "434",
    "mnc": "05",
    "price_per_sms": 50.00,
    "currency": "UZS",
    "smpp_config": {
      "host": "smpp.ucell.uz",
      "port": 2775,
      "system_id": "username",
      "password": "password",
      "bind_mode": "transceiver",
      "submit_sm_throughput": 100
    },
    "priority": 100,
    "weight": 100,
    "status": "active"
  }'
```

## Architecture

```
┌─────────────────┐
│   Client App    │
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────┐
│  API Gateway    │◄──── JWT Auth
│   (FastAPI)     │◄──── Rate Limiting
└────────┬────────┘
         │
    ┌────┴────┬────────────┬──────────┐
    ▼         ▼            ▼          ▼
┌────────┐ ┌──────┐ ┌──────────┐ ┌────────┐
│Billing │ │Jasmin│ │ Routing  │ │ Redis  │
│Service │ │ HTTP │ │ Service  │ │        │
└────────┘ └──────┘ └──────────┘ └────────┘
```

## Development

### Project Structure

```
services/api-gateway/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── config.py            # Settings
│   ├── dependencies.py      # Dependency injection
│   ├── clients.py           # HTTP clients
│   ├── rate_limiter.py      # Rate limiting
│   ├── exceptions.py        # Custom exceptions
│   ├── models/              # Pydantic models
│   │   ├── auth.py
│   │   ├── sms.py
│   │   ├── user.py
│   │   ├── operator.py
│   │   └── template.py
│   ├── services/            # Business logic
│   │   ├── auth_service.py
│   │   ├── sms_service.py
│   │   └── operator_service.py
│   └── api/                 # API routes
│       └── v1/
│           ├── auth.py
│           ├── sms.py
│           ├── user.py
│           ├── templates.py
│           └── admin.py
├── requirements.txt
├── Dockerfile
└── README.md
```

## Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

## Docker

```bash
# Build image
docker build -t jasmin-api-gateway .

# Run container
docker run -p 8080:8080 \
  -e JWT_SECRET_KEY=your-secret \
  -e API_GATEWAY_BILLING_URL=http://billing:8081 \
  jasmin-api-gateway
```

## License

MIT

