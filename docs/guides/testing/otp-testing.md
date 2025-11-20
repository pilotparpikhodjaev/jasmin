# OTP Stack Testing & Load Validation

## 1. Billing service unit tests

```bash
cd services/billing-service
python -m pip install -r requirements.txt -r requirements-test.txt
pytest -q tests
```

The suite provisions an in-memory SQLite database and exercises the core billing flows:

- Account creation with initial balance + credit limit
- Charging + ledger writes (`apply_charge`)
- Status updates fed by DLR callbacks (`update_message_status`)

## 2. API gateway contract test (FastAPI)

Use `fastapi`'s built-in Swagger (`http://localhost:8080/docs`) or run a simple health check:

```bash
curl -H "X-API-Key: <client-key>" http://localhost:8080/v1/balance
```

## 3. k6 load test for OTP flow

```bash
cd loadtests
API_BASE=http://localhost:8080/v1 \
API_KEY=<client-key> \
K6_VUS=200 \
K6_DURATION=5m \
k6 run otp_flow.js
```

Targets:

- <1% HTTP failures
- p95 latency < 800 ms for `/v1/otp/send`
- Sustained 200 VUs ≈ 200 TPS OTP workload

Update `API_KEY` with a real client key before running in staging and monitor Grafana (`http://localhost:3000`) for saturation signals (Jasmin queue depth, RabbitMQ, CPU).

