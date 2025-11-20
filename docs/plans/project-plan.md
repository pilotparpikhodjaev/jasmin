# Enterprise SMS Gateway Architecture Enhancement: Jasmin Adaptation Plan

### 1. Executive Summary

Transforming an existing Jasmin SMS Gateway into an enterprise-grade B2B SMS aggregation platform for banking OTP/transactional traffic is feasible without rewriting the SMPP/HTTP core. Jasmin already provides a solid foundation: SMPP 3.4 server/client (`SMPPServerFactory`, `SMPPClientFactory`), routing via `RouterPB` and `MORoutingTable/MTRoutingTable`, asynchronous processing using RabbitMQ and Redis, and basic HTTP APIs. These components are sufficient to act as a high-performance SMS “engine” in a larger architecture.

The primary architectural approach is to keep Jasmin as the core SMS transport and routing engine and wrap it with new microservices for **billing, routing intelligence, API gateway, and web UIs**. Jasmin continues to handle SMPP and low-level message flows, while PostgreSQL-backed services provide authoritative billing, multi-tenant account models, LCR routing, and rich administration/analytics. Integration points are primarily AMQP (RabbitMQ), HTTP/REST, and Redis for shared counters.

The critical path for **Phase 1 (OTP MVP, 12 weeks)** is: stand up PostgreSQL and k8s platform; implement a minimal but correct Billing Service; introduce an API Gateway with secure REST endpoints; tune Jasmin integration to use the new billing flows; and deliver first versions of the Admin Dashboard and Client Portal for account management and visibility. This yields a production-ready OTP platform capable of ~500 msg/s with proper CDRs, balances, and basic multi-tenant support.

Overall effort for the 3-phase plan is **12–15 months**, with approximately **$130k–200k** in engineering cost for a compact team (2 backend, 1 frontend, 0.5 DevOps, 0.5 telecom). Phase 1 delivers a usable OTP service in ~3 months, Phase 2 upgrades it to an enterprise platform with LCR and advanced billing, and Phase 3 adds USSD/IVR, campaign tools, and multi-region resilience.

---

### 2. Jasmin Capabilities Assessment

#### SMPP Gateway Core [✓ ~75% coverage]

- Production-ready SMPP 3.4 server and clients (`jasmin/protocols/smpp/factory.py`, `SMPPServerFactory`, `SMPPClientFactory`) with support for bind TX/RX/TRX, enquire_link, TLVs, long/Unicode SMS, and reconnects.
- Asynchronous architecture using Twisted and RabbitMQ for pushing messages into outbound SMPP connectors and handling DLRs.
- Per-user throttling and basic quotas integrated via `RouterPB` and user configuration.
- **Missing:** centralized per-account TPS limits and cluster-wide quotas (current limits are mostly local to an instance).
- **Missing:** SMPP v5.0 and advanced flow control (not essential for OTP, but a limit for some carriers).

#### Routing Engine [✓ ~60% coverage]

- `MORoutingTable`, `MTRoutingTable`, and multiple route types (Static, RandomRoundrobin, Failover) already implemented in `jasmin/routing`.
- Filters (by user, group, prefix, time, content) and interceptors (`Interceptors.py`) allow flexible matching and custom logic.
- **Missing:** Least Cost Routing (LCR) with MCC/MNC lookup, longest-prefix matching, and centralized route pricing.
- **Missing:** quality-based routing (DLR rate, latency) and automated operator disablement based on SLA.

#### Billing System [✓ ~35–40% coverage]

- In-memory billing engine in `jasmin/routing/Bills.py` with `SubmitSmBill` and `SubmitSmRespBill` used by `RouterPB` to charge per-message.
- Support for basic balances and SMS count quotas, with early decrementing and adjustment upon responses/DLRs.
- **Missing:** PostgreSQL-backed persistent billing store, CDR history, multi-currency tariffs, and integration with payment systems.
- **Missing:** ACID guarantees on balances and reconciliation processes; current pickle-based persistence is not enterprise-grade.

#### API Layer [✓ ~55–60% coverage]

- Existing HTTP API (`jasmin/protocols/http/server.py`) supports sending SMS, querying balance, and basic metrics, authenticated via simple credentials.
- SMPP server interface available to clients for direct SMPP connectivity.
- **Missing:** modern REST design with resource-oriented endpoints, versioning, OpenAPI docs, OAuth2/JWT, IP whitelisting, and robust rate limiting.
- **Missing:** WebSocket support for real-time delivery status updates and campaign monitoring.

#### Web UI [✓ ~10% coverage]

- jCli telnet console for administrative operations (users, groups, connectors, routes).
- Minimal REST for some operations; no proper web UI.
- **Missing:** web-based admin console with RBAC, multi-tenant views, operator management, and route visualization.
- **Missing:** client-facing portal with self-service balance, usage stats, API keys, and webhook configuration.

#### Infrastructure & DevOps [✓ ~50% coverage]

- Dockerfiles, `docker-compose.yml`, Prometheus metrics, and Grafana dashboards already present; some Kubernetes manifests exist.
- Logging handled by rotating file handlers; metrics for HTTP and SMPP components available.
- **Missing:** full Kubernetes deployment architecture with Helm, HPA, secrets management, and automated backups.
- **Missing:** CI/CD pipeline for services, structured logging with correlation IDs, and documented DR procedures.

---

### 3. Critical Gaps & Priorities

#### High Priority (Phase 1 blockers)

- **PostgreSQL-backed Billing Service** with authoritative balances, CDRs, and account transactions.
- **API Gateway** providing REST endpoints for send/status/balance with API keys, IP whitelisting, and rate limiting.
- **Basic Multi-Tenant Model** (accounts, resellers, clients) in the billing/store layer.
- **Admin Dashboard v1** for managing clients, operators, and basic routes.
- **Client Portal v1** for viewing balance, history, and managing API keys.
- **Jasmin Integration with Billing & Gateway** (AMQP events for submit_sm/resp/DLR to billing, HTTP/AMQP integration from gateway).

#### Medium Priority (Phase 2)

- **Routing Service with LCR** (MCC/MNC, longest-prefix routing, operator cost/quality scoring).
- **Billing Service v2** with multi-currency, tariff plans, invoice generation, and taxation support.
- **Advanced Admin UI** for LCR configuration, operator health dashboards, and SLA monitoring.
- **OAuth2/JWT** for API gateway and admin portal plus audit logging.
- **SLA-based Operator Health Monitoring** with auto-failover and route disablement.

#### Low Priority (Phase 3)

- **USSD Gateway Integration** (external stack or managed service).
- **IVR/Voice Integration** using Asterisk/FreeSWITCH or CPaaS providers.
- **White-label / Reseller UI** with branding and multi-tenant theming.
- **Campaign Manager** (bulk sends, A/B testing, segmentation).

---

### 4. Layered Enhancement Architecture

#### Architectural Overview

```text
                    +---------------------------+
                    |   Banking / Fintech CLI   |
                    |   & Applications          |
                    +-------------+-------------+
                                  |
                         HTTPS (REST/WebSocket)
                                  |
                         +--------v---------+
                         |   API Gateway   |
                         | (FastAPI/Go)    |
                         +---+--------+----+
                             |        |
                 REST/Admin  |        |  REST/Billing
                             |        |
                +------------v--+   +-v----------------+
                | Admin &       |   |  Billing Service |
                | Client SPA    |   |  (PostgreSQL)    |
                +---------------+   +--------+---------+
                                            |
                                   SQL / Events / CDR
                                            |
                    +-----------------------v----------------------+
                    |                 Routing Service             |
                    |   (LCR, MCC/MNC, Operator Health)           |
                    +-----------------+---------------------------+
                                      |
                                LCR Decisions
                                      |
         +----------------------------v-----------------------------+
         |                    RabbitMQ / Redis                      |
         | (submit queues, DLR queues, rate limits, cache, locks)  |
         +----------------------------+-----------------------------+
                                      |
                       +--------------v-------------------+
                       |       Jasmin Cluster             |
                       | SMPP Server/Clients, RouterPB,   |
                       | Interceptors, HTTP API           |
                       +--------------+-------------------+
                                      |
                            SMPP Links to Operators
                            (BeeLine, Ucell, UMS)
```

#### Component Responsibilities

- **Jasmin Cluster**: SMPP/HTTP transport, session handling, basic routing, and DLR processing; exposes metrics and integrates with internal services via RabbitMQ/HTTP.
- **API Gateway**: Exposes public REST/WS APIs, handles authentication, authorization, rate limiting, and traffic shaping, and orchestrates calls to routing and billing before enqueuing messages for Jasmin.
- **Billing Service**: Maintains account hierarchy, balances, tariffs, CDRs, and transactions; receives events from Jasmin via AMQP and from Gateway via REST; drives invoice and reporting pipelines.
- **Routing Service**: Maintains operator/route definitions, MCC/MNC ranges, LCR strategies, and operator health metrics; provides route decisions via REST/GRPC.
- **Admin & Client SPA**: React application used by admins and clients for configuration, monitoring, and self-service (fronted by API Gateway).
- **RabbitMQ & Redis**: Provide durable messaging queues between services, with Redis used for counters, caching, and distributed locks.

#### SMS Send Data Flow (OTP Use Case)

1. **Client → API Gateway**: Banking client issues `POST /v1/sms/send` with message payload, API key, and optional metadata (OTP template, ref ID).
2. **Gateway Auth & Limits**: API Gateway authenticates API key, verifies IP whitelist, checks per-account rate limits using Redis counters.
3. **Route Decision**: Gateway calls `Routing Service` (`POST /route/decision`) with `msisdn`, `sender`, `account_id`, and optional context. Routing Service returns target operator/connector ID (plus failover list).
4. **Pre-Charge**: Gateway calls `Billing Service` (`POST /charges`) with account, operator, estimated parts, and correlation ID for the upcoming message. Billing Service authoritatively checks balance and reserves the amount (pending charge).
5. **Enqueue to Jasmin**: Gateway publishes message to RabbitMQ (`submit.sm.<shard>`) with metadata: account_id, operator_id, reserved_charge_id, and routing hints.
6. **Jasmin Processing**: Jasmin’s `RouterPB` consumes messages, applies local filters/interceptors, uses provided connector hint (or asks Routing Service again if necessary), and sends `submit_sm` via appropriate SMPP connector.
7. **Submit Response**: On `submit_sm_resp`, Jasmin publishes an event to RabbitMQ (`submit.sm.resp`) including message_id, status, and the reserved charge reference.
8. **Billing Finalization**: Billing Service consumes `submit.sm.resp` events, finalizes the reserved charge (confirm or rollback), and inserts a `cdr_sms` record.
9. **DLR Handling**: Upon DLR receipt, Jasmin emits DLR events via RabbitMQ; Billing Service updates `cdr_sms.delivery_time/status`, while API Gateway notifies clients via webhook and/or WebSocket push.
10. **Client Status Query**: Client can query `GET /v1/sms/{message_id}`; API Gateway federates from Billing/Analytics storage.

#### Integration Patterns

- **AMQP (RabbitMQ)**: Used for decoupling Jasmin from Billing and Routing; events for submit_sm, submit_sm_resp, DLRs, and operator metrics.
- **REST/HTTP**: Used between API Gateway, Billing Service, Routing Service, and admin/client SPA; OpenAPI-documented interfaces.
- **PostgreSQL**: Shared data backbone for billing, CDRs, routing configuration, account metadata, and operator metrics.
- **Redis**: Shared cache for rate limiting, access tokens, LCR cache (MCC/MNC → route mapping), and other high-frequency lookups.

---

### 5. Service Specifications

#### 5.1 API Gateway

**Service Name & Purpose**

- `api-gateway`: Public-facing REST and WebSocket front door for clients and admin UI, enforcing auth, rate limits, and orchestration.

**Key Responsibilities**

- Authenticate clients via API keys (Phase 1) and OAuth2/JWT (Phase 2).
- Enforce per-client rate limiting and quotas using Redis.
- Orchestrate route decisions and billing pre-charges before placing messages into AMQP queues.
- Expose WebSocket channels for DLR and status events (Phase 2+).
- Provide admin endpoints for configuration and management (scoped by RBAC).

**Technology Stack**

- Language: Python
- Framework: `FastAPI`
- Auth: API keys + IP whitelists (Phase 1), OAuth2/JWT with `fastapi-users` or custom implementation (Phase 2)
- Storage: Redis (rate limits), PostgreSQL (sessions/audit if needed)

**REST API Endpoints (key)**

- `POST /v1/sms/send`: Submit OTP/transactional SMS (single recipient; bulk added later).
- `GET /v1/sms/{message_id}`: Get message status (via CDR store).
- `GET /v1/balance`: Get current balance for authenticated account.
- `POST /v1/webhooks`: Register/update DLR webhook URL.
- `GET /v1/account/profile`: Retrieve account metadata (name, contact, limits).
- Admin (separate scopes):
  - `POST /admin/accounts`: Create account or reseller.
  - `POST /admin/api-keys`: Create/revoke API keys.
  - `GET /admin/stats/tps`: Aggregate TPS by account/operator.

**Data Model (uses shared DB)**

- Primarily interacts with `accounts`, `account_balances`, `api_keys`, `cdr_sms`, and `account_transactions`.

**Integration with Jasmin**

- Publishes messages to RabbitMQ queues consumed by Jasmin (`submit.sm.*`).
- Receives DLR and status updates indirectly via Billing Service and message store.
- For SMPP clients, may manage credentials stored in Jasmin’s user configs via admin API (Phase 2).

**Development Effort**

- Phase 1 core: 3–4 weeks.
- Phase 2 enhancements (OAuth2, WebSocket, advanced admin endpoints): 3–4 weeks.

---

#### 5.2 Billing Service

**Service Name & Purpose**

- `billing-service`: Authoritative system for accounts, balances, tariffs, CDRs, and transactions.

**Key Responsibilities**

- Manage account hierarchy and balance state with ACID guarantees.
- Apply tariffs based on route/operator and message characteristics.
- Record all SMS CDRs and account transactions for audit and reporting.
- Provide APIs for charges, balance queries, and CDR export.
- Support reconciliation between Jasmin events and stored CDRs.

**Technology Stack**

- Language: Python
- Framework: `FastAPI` (or Flask) + SQLAlchemy / Alembic for migrations
- Database: PostgreSQL (primary), with read replicas in Phase 3
- Messaging: RabbitMQ (consume events from Jasmin and Gateway)

**REST API Endpoints (key)**

- `POST /charges`: Reserve or finalize a charge (idempotent, keyed by `external_id`).
- `GET /balances/{account_id}`: Fetch current balance and credit limit.
- `GET /cdr`: Filterable CDR search (account, operator, time range, status).
- `POST /accounts`: Create/update accounts (admin use).
- `GET /accounts/{id}`: Retrieve account with hierarchy info.
- `GET /transactions`: List account transactions with pagination.

**Data Model (core tables)**

- `accounts`, `account_balances`, `operators`, `tariff_routes`, `cdr_sms`, `account_transactions`.

**Integration with Jasmin**

- Subscribes to AMQP topics: `submit.sm`, `submit.sm.resp`, `dlr.*`.
- Uses message metadata to calculate price and finalize reserved charges.
- Optionally provides billing decisions to Jasmin via Interceptor (Phase 2) for advanced scenarios.

**Development Effort**

- Phase 1 (schema v1 + core APIs): 3–4 weeks.
- Phase 2 (multi-currency, tariffs, invoices): 4–6 additional weeks.

---

#### 5.3 Routing Service

**Service Name & Purpose**

- `routing-service`: Central brain for route selection, LCR, and operator health management.

**Key Responsibilities**

- Maintain MCC/MNC and prefix-based routing rules.
- Compute least-cost and quality-aware routes for each message.
- Track operator health metrics (DLR rate, latency, error rate) from `operator_metrics`.
- Expose an API for route decisions and operator management.
- Push updated routing decisions into cache (Redis) for low-latency lookups.

**Technology Stack**

- Language: Go (for performance and concurrency) or Python (FastAPI) depending on team.
- Database: PostgreSQL (for rules), Redis (for cached route tables).
- Metrics: Prometheus integration for internal performance.

**REST API Endpoints (key)**

- `POST /route/decision`: Inputs `msisdn`, `sender`, `account_id`, returns chosen operator/connector and fallback list.
- `GET /operators`: List operators and statuses.
- `PATCH /operators/{id}`: Enable/disable operator, adjust weights.
- `POST /mccmnc`: Manage MCC/MNC mappings.
- `POST /tariff-routes`: Define/update route tariffs and precedence.

**Data Model (core tables)**

- `operators`, `operator_metrics`, `tariff_routes`.

**Integration with Jasmin**

- API Gateway calls `route/decision` before enqueuing messages.
- Jasmin or billing emits operator performance metrics to RabbitMQ; routing-service ingests and updates `operator_metrics`.
- Optionally, Jasmin’s Interceptors can call routing-service for routing hints.

**Development Effort**

- Phase 2 core (LCR v1, metrics ingestion): 4–6 weeks.

---

#### 5.4 Admin Dashboard (React)

**Service Name & Purpose**

- `admin-web`: React SPA for operations team to manage clients, operators, routes, and monitor health.

**Key Responsibilities**

- Provide CRUD UI for accounts, operators, tariffs, routes.
- Display dashboards for TPS, DLR rates, error rates, and operator health.
- Offer configuration screens for API keys, IP whitelists, sender IDs.
- Enforce RBAC (Super Admin, NOC, Finance, Sales, etc.) with scoped views.

**Technology Stack**

- React + TypeScript
- UI Library: MUI or Ant Design
- Build: Vite or Create React App
- Deployed as static assets behind Nginx or API Gateway

**Core UI Modules**

- Accounts & Resellers
- Operators & Connectors (SMPP endpoints, status toggles)
- Routes & LCR Policies
- Monitoring (Grafana links + embedded charts)
- Security (user management, roles)

**Integration with Jasmin**

- Indirect via API Gateway and admin APIs (no direct connection).
- Operator status changes propagate to routing-service and Jasmin configurations.

**Development Effort**

- v1 (accounts, operators, basic stats): 4–5 weeks.
- v2 (LCR editor, SLA dashboards): 6–8 additional weeks.

---

#### 5.5 Client Portal (React)

**Service Name & Purpose**

- `client-portal`: React SPA for end customers (banks/fintechs) to manage balance, keys, and view usage.

**Key Responsibilities**

- Show balances, transaction history, and SMS statistics.
- Manage API keys and IP whitelists.
- Configure webhooks (DLR callbacks).
- Provide basic dashboards for usage, DLR, and spending.

**Technology Stack**

- React + TypeScript
- Shared component library with `admin-web`
- Auth via API Gateway (JWT-based sessions)

**Core UI Modules**

- Dashboard (balance, TPS summary, DLR rate)
- API Keys & Webhooks
- Message History (via `cdr_sms`)
- Account Settings

**Integration with Jasmin**

- Indirect via API Gateway → Billing/Routing/CDR data.
- No direct communication with Jasmin.

**Development Effort**

- v1 aligned with Phase 1 OTP: 3–4 weeks (leveraging admin-web components).
- v2 with advanced analytics: 4–6 additional weeks.

---

### 6. PostgreSQL Schema Design

```sql
-- Multi-tenant account hierarchy
CREATE TABLE accounts (
    id              BIGSERIAL PRIMARY KEY,
    parent_id       BIGINT REFERENCES accounts(id),
    type            TEXT NOT NULL CHECK (type IN ('admin', 'reseller', 'client')),
    name            TEXT NOT NULL,
    external_ref    TEXT, -- Bank ID / CRM key
    status          TEXT NOT NULL CHECK (status IN ('active', 'suspended')),
    currency        TEXT NOT NULL, -- ISO 4217 (e.g., 'USD', 'UZS')
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_accounts_parent ON accounts(parent_id);
CREATE INDEX idx_accounts_status ON accounts(status);

-- Real-time balances per account
CREATE TABLE account_balances (
    account_id      BIGINT PRIMARY KEY REFERENCES accounts(id),
    balance         NUMERIC(18,6) NOT NULL DEFAULT 0,
    credit_limit    NUMERIC(18,6) NOT NULL DEFAULT 0,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Operator registry (per SMPP connector/operator)
CREATE TABLE operators (
    id                  BIGSERIAL PRIMARY KEY,
    name                TEXT NOT NULL,
    mcc                 TEXT, -- e.g., '434'
    mnc                 TEXT, -- e.g., '04'
    smpp_connector_id   TEXT NOT NULL, -- maps to Jasmin connector ID
    status              TEXT NOT NULL CHECK (status IN ('active', 'suspended')),
    default_cost        NUMERIC(18,6) NOT NULL,
    currency            TEXT NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_operators_mcc_mnc ON operators(mcc, mnc);
CREATE INDEX idx_operators_status ON operators(status);

-- Operator health metrics (aggregated, e.g., per 5-minute window)
CREATE TABLE operator_metrics (
    id              BIGSERIAL PRIMARY KEY,
    operator_id     BIGINT NOT NULL REFERENCES operators(id),
    window_start    TIMESTAMPTZ NOT NULL,
    window_end      TIMESTAMPTZ NOT NULL,
    messages_sent   BIGINT NOT NULL,
    dlr_success     BIGINT NOT NULL,
    dlr_fail        BIGINT NOT NULL,
    avg_latency_ms  NUMERIC(10,2),
    error_count     BIGINT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_operator_metrics_window ON operator_metrics(operator_id, window_start, window_end);

-- Tariff routes (pricing per MCC/MNC/prefix/account)
CREATE TABLE tariff_routes (
    id              BIGSERIAL PRIMARY KEY,
    account_id      BIGINT REFERENCES accounts(id), -- NULL: global default
    operator_id     BIGINT REFERENCES operators(id),
    mcc             TEXT,
    mnc             TEXT,
    prefix          TEXT, -- longest prefix match for msisdn
    price_per_sms   NUMERIC(18,6) NOT NULL,
    currency        TEXT NOT NULL,
    valid_from      TIMESTAMPTZ NOT NULL DEFAULT now(),
    valid_to        TIMESTAMPTZ,
    priority        INT NOT NULL DEFAULT 100, -- lower = higher precedence
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_tariff_routes_mcc_mnc_prefix
    ON tariff_routes(mcc, mnc, prefix);
CREATE INDEX idx_tariff_routes_account
    ON tariff_routes(account_id);

-- Immutable SMS CDR (audit trail)
CREATE TABLE cdr_sms (
    id              BIGSERIAL PRIMARY KEY,
    account_id      BIGINT NOT NULL REFERENCES accounts(id),
    operator_id     BIGINT REFERENCES operators(id),
    external_message_id TEXT, -- ID from client
    jasmin_message_id   TEXT, -- ID from Jasmin/SMSC
    msisdn          TEXT NOT NULL,
    sender          TEXT,
    submit_time     TIMESTAMPTZ NOT NULL,
    delivery_time   TIMESTAMPTZ,
    status          TEXT NOT NULL, -- e.g., 'SUBMITTED','DELIVERED','FAILED','EXPIRED'
    error_code      TEXT,
    price           NUMERIC(18,6),
    currency        TEXT,
    parts           INT NOT NULL DEFAULT 1,
    country         TEXT, -- resolved from MCC
    extra_meta      JSONB, -- optional: campaign_id, tags
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_cdr_sms_account_time ON cdr_sms(account_id, submit_time);
CREATE INDEX idx_cdr_sms_msisdn_time ON cdr_sms(msisdn, submit_time);
CREATE INDEX idx_cdr_sms_status ON cdr_sms(status);

-- Account transactions (billing events)
CREATE TABLE account_transactions (
    id              BIGSERIAL PRIMARY KEY,
    account_id      BIGINT NOT NULL REFERENCES accounts(id),
    cdr_id          BIGINT REFERENCES cdr_sms(id),
    direction       TEXT NOT NULL CHECK (direction IN ('debit', 'credit')),
    amount          NUMERIC(18,6) NOT NULL,
    currency        TEXT NOT NULL,
    reason          TEXT NOT NULL, -- 'sms_charge','refund','topup'
    external_ref    TEXT, -- payment ref, reconciliation ID
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_account_transactions_account_time
    ON account_transactions(account_id, created_at);

-- Optional: API keys
CREATE TABLE api_keys (
    id              BIGSERIAL PRIMARY KEY,
    account_id      BIGINT NOT NULL REFERENCES accounts(id),
    name            TEXT NOT NULL,
    key_hash        TEXT NOT NULL, -- hashed API key
    ip_whitelist    TEXT[], -- list of CIDRs
    status          TEXT NOT NULL CHECK (status IN ('active', 'revoked')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    revoked_at      TIMESTAMPTZ
);

CREATE INDEX idx_api_keys_account ON api_keys(account_id);
```

---

### 7. Development Roadmap

#### Phase 1: OTP MVP (Weeks 1–12) | ~$30k–50k

**Weeks 1–2: Foundation (PostgreSQL, k8s, CI/CD)**

- [ ] Provision PostgreSQL (single instance + basic backup) in target environment.
- [ ] Deploy Redis and RabbitMQ clusters in Kubernetes.
- [ ] Define base Helm charts for core services (Jasmin, Billing, Gateway, SPA).
- [ ] Set up CI/CD (GitHub Actions/GitLab CI) with build, test, and deploy pipelines.
- Dependencies: none; this is platform groundwork.

**Weeks 2–5: Billing Service Development (in parallel with infra)**

- [ ] Implement PostgreSQL schema (`accounts`, `account_balances`, `cdr_sms`, `account_transactions`, `operators`, `tariff_routes`).
- [ ] Implement `billing-service` with `POST /charges`, `GET /balances/{id}`, `GET /cdr`.
- [ ] Implement basic tariff resolution logic (account + operator + MCC/MNC).
- [ ] Build AMQP consumers for placeholder events (mock Jasmin events in dev).
- Dependencies: PostgreSQL ready.

**Weeks 4–7: API Gateway Development**

- [ ] Initialize `api-gateway` FastAPI project with OpenAPI docs.
- [ ] Implement API key auth + IP whitelist using `api_keys` table and Redis caching.
- [ ] Implement `POST /v1/sms/send`, `GET /v1/sms/{id}`, `GET /v1/balance`.
- [ ] Integrate with Billing Service (`/charges`, `/balances`) and mock Routing decisions (static for Phase 1).
- [ ] Implement per-account rate limiting (Redis counters with sliding window).
- Dependencies: Billing Service v1 available.

**Weeks 6–9: Admin Dashboard v1**

- [ ] Initialize React/TypeScript monorepo for `admin-web` and `client-portal`.
- [ ] Implement admin authentication (API key-bound sessions or basic login).
- [ ] Build UI for:
  - [ ] Account listing & creation.
  - [ ] Operator listing & basic config (status, basic tariffs).
  - [ ] Simple dashboards (TPS, error rate) using Prometheus/Grafana links.
- Dependencies: API Gateway admin endpoints for accounts/operators.

**Weeks 8–10: Client Portal v1**

- [ ] Implement client login (API key pairing or JWT from Gateway).
- [ ] Build pages:
  - [ ] Balance overview.
  - [ ] Message history (paged `cdr_sms` view).
  - [ ] API key management (`api_keys`).
  - [ ] Webhook configuration.
- Dependencies: Gateway endpoints for balance, CDR, API keys.

**Weeks 9–11: Jasmin Integration**

- [ ] Extend Jasmin configuration to publish billing events to RabbitMQ (`submit.sm`, `submit.sm.resp`, `dlr.*`).
- [ ] Wire Billing Service consumers to real RabbitMQ topics.
- [ ] Validate end-to-end flow: `POST /v1/sms/send` → Jasmin → Operator Simulator → DLR → Billing/CDR.
- Dependencies: Billing Service & API Gateway functional.

**Weeks 10–12: Testing & Launch**

- [ ] Build load-test scenario (locust/k6) to reach 500 msg/s.
- [ ] Execute SMPP interoperability tests with each operator (BeeLine, Ucell, UMS) in a lab setup.
- [ ] Smoke test admin and client UI flows.
- [ ] Prepare runbooks, on-call responsibilities, and monitoring alerts.
- [ ] Launch to first pilot banking client with guarded traffic.

---

#### Phase 2: Enterprise Features (Weeks 13–27) | ~$60k–90k

**Focus Areas**

- [ ] LCR-capable Routing Service (MCC/MNC, cost & quality-based routing).
- [ ] Billing Service v2 (multi-currency, invoices, discounting).
- [ ] Admin Dashboard v2 (LCR editor, advanced dashboards).
- [ ] OAuth2/JWT security and audit logging.

Workstreams:

- Weeks 13–18:
  - [ ] Implement Routing Service API and data model (operators, operator_metrics, tariff_routes).
  - [ ] Integrate Routing Service into API Gateway send flow.
  - [ ] Begin collecting operator metrics from Billing/Jasmin (DLR, latency).

- Weeks 16–22:
  - [ ] Extend Billing Service for multi-currency, currency conversion, tariff plans.
  - [ ] Implement invoice generation (PDF/CSV) and reporting endpoints.

- Weeks 19–24:
  - [ ] Implement OAuth2/JWT provider in API Gateway.
  - [ ] Implement audit logging of admin actions to PostgreSQL.
  - [ ] Upgrade Admin UI with LCR management and operator health visualization.

- Weeks 23–27:
  - [ ] Throttling per account/route in Jasmin (or via Gateway + Routing).
  - [ ] SLA rule engine and operator auto-disable thresholds.
  - [ ] Hardening and performance tuning to reach 5,000 msg/s via horizontal scaling.

---

#### Phase 3: Complete Platform (Weeks 28–39) | ~$40k–60k

- [ ] Integrate USSD Gateway (external stack + REST interface).
- [ ] Integrate IVR/Voice provider (Asterisk/FreeSWITCH or CPaaS).
- [ ] Implement Campaign Manager (bulk sends, scheduling, segmentation).
- [ ] Build white-label/reseller UI features and branding options.
- [ ] Implement multi-region HA with cross-region replication and DR drills.

---

### 8. Technology Stack Decisions

| Component        | Option A            | Option B           | Recommendation | Rationale |
|-----------------|---------------------|--------------------|----------------|-----------|
| API Gateway     | FastAPI (Python)    | Go + Gin           | FastAPI        | Strong ecosystem, easy integration with existing Python/Jasmin, built-in OpenAPI. |
| Billing Service | FastAPI + SQLAlchemy| Go + sqlc          | FastAPI        | Rich ORM, simpler business logic coding, shared Python tooling with Gateway. |
| Routing Service | FastAPI (Python)    | Go + Gin           | Go + Gin       | Compute-heavy, latency-sensitive LCR; Go offers better concurrency and CPU efficiency. |
| Admin UI        | React + MUI         | Vue + Vuetify      | React + MUI    | Wider talent pool, strong charting libs, shared components with client portal. |
| Client Portal   | React + MUI         | Angular            | React + MUI    | Shared code with admin-web, faster iteration. |
| Database        | PostgreSQL          | MySQL              | PostgreSQL     | Strong support for JSONB, partitioning, complex queries; standard for billing/CDR. |
| Cache           | Redis Cluster       | Memcached          | Redis Cluster  | Rich data structures, atomic increment ops for rate limiting. |
| Message Broker  | RabbitMQ            | Kafka              | RabbitMQ       | Already in use, suits OTP flows; Kafka can be added later for analytics. |
| Auth            | OAuth2/JWT self-host| External IDP (Keycloak/Auth0) | OAuth2/JWT in Gateway + optional external IDP | Start simple; integrate IDP later for SSO and governance. |
| Deployment      | Kubernetes + Helm   | Docker Swarm       | Kubernetes     | Industry standard for HA, HPA, and multi-region deployments. |
| Observability   | Prometheus + Grafana| Datadog            | Prometheus/Grafana | Already partially in place; cost-efficient and flexible. |

---

### 9. Kubernetes Deployment Architecture

#### Deployments

- `jasmin-core`:
  - Role: SMPP server/clients, RouterPB, HTTP API.
  - Replicas: 2–4 initially; scale horizontally based on TPS.
  - Resources: CPU/memory requests & limits tuned by load tests.
- `api-gateway`:
  - Role: External API handling.
  - Replicas: 2–4; HPA based on CPU and RPS.
- `billing-service`:
  - Replicas: 2 (for availability); HPA by CPU/latency.
- `routing-service`:
  - Replicas: 2–3; HPA by CPU and request rate.
- `admin-web` & `client-portal`:
  - Deployed as static assets served by Nginx.
  - Replicas: 2–3.

#### StatefulSets

- `postgresql`:
  - One primary, 1–2 replicas.
  - PersistentVolumeClaims for data.
- `redis-cluster`:
  - 3 master + 3 replica nodes in cluster mode.
- `rabbitmq-cluster`:
  - 3-node cluster with mirrored queues.

#### Services & Ingress

- `api-gateway-svc`: LoadBalancer/Ingress entry with TLS termination and WAF (if available).
- `admin-web-svc` and `client-portal-svc`: Exposed via Ingress behind `api-gateway` or separate domain.
- Internal `ClusterIP` services for `billing-service`, `routing-service`, `jasmin-core`, `postgresql`, `redis`, `rabbitmq`.

#### ConfigMaps & Secrets

- ConfigMaps:
  - Jasmin configs (connectors, routes where appropriate).
  - API Gateway and service configs (timeouts, rate limits).
- Secrets:
  - SMPP credentials, DB passwords, JWT signing keys, TLS certificates.
  - Managed via Kubernetes Secrets with optional integration to a secret manager (Vault, AWS/GCP secret manager).

#### Scaling Strategy

- `jasmin-core`:
  - HPA triggered by CPU, queue lag metrics (RabbitMQ) and TPS.
  - Shard routing via RabbitMQ routing keys (e.g., by account shard or destination prefix).
- `api-gateway`:
  - HPA by RPS and latency; autoscale to keep p99 latency <500 ms.
- `billing-service`:
  - HPA by CPU and DB latency; heavy batch reporting may need separate worker deployments.
- `postgresql`:
  - Vertical scaling and partitioning on `cdr_sms` by date; read replicas for analytics.
- `redis` & `rabbitmq`:
  - Monitor memory and queue depths; scale nodes within clusters.

#### Monitoring

- Prometheus scrape targets:
  - `jasmin-core` HTTP `/metrics` (SMPP, HTTP, internal queues).
  - `api-gateway`, `billing-service`, `routing-service`.
  - `postgresql` via `postgres_exporter`.
  - `redis_exporter`, `rabbitmq_exporter`.
- Grafana dashboards:
  - TPS per client and operator.
  - DLR success and latency.
  - Error and timeout rates.
  - Queue depth and DB performance.
- Logging:
  - Structured logs shipped via Fluent Bit/Fluentd to Loki/Elasticsearch.
  - Correlation using `correlation_id`/`message_id` across services.

---

### 10. Risk Assessment & Mitigation

| Risk                                  | Probability | Impact | Mitigation Strategy |
|---------------------------------------|-------------|--------|---------------------|
| Python/Twisted TPS limits in Jasmin   | High        | High   | Use horizontal scaling for Jasmin; tune SMPP window size, TCP settings, and ensure sufficient hardware; offload heavy logic to Gateway/Routing in Go. |
| SMPP compatibility issues with operators | Medium   | High   | Maintain lab with SMPP simulators; use protocol analyzers (Wireshark); support per-operator config overrides; implement fallback routes. |
| Billing accuracy bugs (over/under charge) | Medium  | High   | Implement idempotent charges with unique external IDs; dual-logging of CDRs; reconciliation jobs comparing Jasmin events and billing records; comprehensive unit/integration tests. |
| PostgreSQL performance degradation with large CDR volumes | Medium | High | Partition `cdr_sms` by date (e.g., monthly); separate OLTP and reporting workloads; archive old data to cheaper storage. |
| Security vulnerabilities (API, web UI, SMPP) | Medium | High | Conduct security review and penetration testing; enforce TLS for all external traffic; rate-limit management endpoints; use WAF; ensure secure coding practices and dependency updates. |
| Operator outages or poor quality (DLR < 95%) | Medium | Medium | Use Routing Service to track operator metrics; implement SLA-based auto-failover; maintain multiple operators per destination. |
| Team lacks telecom/SMPP expertise        | Medium  | Medium | Engage telecom expert part-time; document standard SMPP flows and error handling; create operator-specific integration guides. |
| Project scope creep (USSD/IVR too early) | Medium  | Medium | Strictly enforce phase boundaries; lock Phase 1 and Phase 2 MVP scope and track change requests; prioritize OTP and core platform first. |

---

### 11. Team & Budget

- **Team Composition**
  - 2 Backend Engineers (Python/Go) – core services (Gateway, Billing, Routing).
  - 1 Frontend Engineer (React) – Admin and Client SPAs.
  - 0.5 DevOps Engineer – Kubernetes, CI/CD, observability, infra.
  - 0.5 Telecom Engineer – SMPP integration, operator onboarding, performance tuning.

- **Total Cost & Phases**
  - Phase 1 (Weeks 1–12): ~$30k–50k (OTP MVP).
  - Phase 2 (Weeks 13–27): ~$60k–90k (Enterprise features).
  - Phase 3 (Weeks 28–39): ~$40k–60k (Complete platform).
  - **Total:** ~$130k–200k over 9–15 months depending on team seniority and region.

- **Timeline**
  - MVP (OTP for first banks): ~3 months.
  - Enterprise-ready (LCR, billing v2, UI v2, OAuth2): ~9 months.
  - Full platform (USSD/IVR, white-label, multi-region): ~12–15 months.

---

### 12. Success Metrics & KPIs

#### Technical KPIs

- **Uptime**: ≥ 99.9% for API Gateway and Jasmin cluster.
- **Throughput**:
  - Phase 1: Sustained 500 msg/s with <1% error.
  - Phase 2: Sustained 5,000 msg/s across scaled cluster.
- **Latency**:
  - API: p99 < 500 ms for `POST /v1/sms/send`.
  - DLR: p99 < 5 seconds end-to-end.
- **Error/Timeout Rate**: < 0.5% for submit_sm and HTTP send operations.

#### Business KPIs

- **Client Count**: Number of active banking/fintech accounts onboarded.
- **MRR (Monthly Recurring Revenue)**: Total billing from SMS traffic and subscriptions.
- **Churn Rate**: Monthly percentage of clients leaving the platform.
- **ARPU**: Average revenue per client per month.

#### Operational KPIs

- **MTTR (Mean Time To Recovery)**: < 30 minutes for critical incidents.
- **Deployment Frequency**: At least weekly safe deployments to production.
- **Change Failure Rate**: < 10% of deployments causing incidents.
- **Alert Fatigue**: Measured via actionable vs. noisy alerts ratio; target >80% actionable.

---

### 13. Next Steps & Immediate Actions

#### 7-Day Kickoff Plan

- **Day 1–2**
  - Finalize PostgreSQL schema (`accounts`, `account_balances`, `operators`, `tariff_routes`, `cdr_sms`, `account_transactions`, `api_keys`).
  - Review schema with telecom and finance stakeholders to confirm billing granularity and reporting needs.

- **Day 2–3**
  - Bootstrap `billing-service` and `api-gateway` FastAPI projects with base structure, health endpoints, and CI pipelines.
  - Set up shared Python tooling (linting, testing, logging libraries).

- **Day 3–4**
  - Stand up initial Kubernetes cluster (dev/staging) with PostgreSQL, Redis, RabbitMQ.
  - Deploy Jasmin in this cluster using existing Docker images and configure Prometheus scrape.

- **Day 5–7**
  - Implement `POST /charges` and `GET /balances/{id}` in Billing Service with test data.
  - Implement `POST /v1/sms/send` in API Gateway with stub integrations to Billing and static routing.
  - Begin building basic admin UI skeleton for accounts and operators.

#### Phase 1 Target Milestones

- **End of Week 4**: Billing Service v1 deployed to staging; Gateway basic flow working end-to-end with mocks.
- **End of Week 8**: Admin and Client SPAs v1 functional; real Jasmin integration in staging.
- **End of Week 12**: OTP MVP in production with first bank sending real traffic at up to 500 msg/s.

This enhancement plan provides a concrete, implementable path from a single Jasmin SMS Gateway deployment to a robust, enterprise-grade SMS aggregation platform suitable for demanding banking and fintech clients.

