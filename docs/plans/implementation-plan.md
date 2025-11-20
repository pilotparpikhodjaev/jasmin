# Enterprise SMS Platform Implementation Plan

## Scope & Goals
- Deliver a bank-grade OTP/transactional SMS platform on top of Jasmin within 15 months.
- Phase 1 (M1–M3): ship stable SMPP/HTTP core, PostgreSQL-backed billing, REST API gateway, minimal React admin and client portals, monitoring stack.
- Phase 2 (M4–M9): add LCR/routing intelligence, billing v2 (multi-currency, invoices), SPA v2, OAuth2-security, operator health dashboards.
- Phase 3 (M10–M15): USSD/IVR integrations, campaign tooling, reseller/white-label UI, multi-region HA and observability.

## Deliverable Breakdown
### Core Platform (Jasmin Cluster)
- Harden SMPP server/client configs (timeouts, TLS, bind windows).
- Containerize router/thrower components; helm-ready manifests with ConfigMaps for credentials.
- Metrics: expose Prometheus `/metrics` for SMPP/HTTP, custom TPS counters per connector.

### Billing Service (FastAPI + PostgreSQL)
- Schema v1: `accounts`, `balances`, `operators`, `routes`, `cdr_sms`, `payments`.
- APIs: `POST /charges`, `GET /balances/{id}`, `GET /cdr`.
- Integrations: consume AMQP billing events; reconcile against Jasmin bills nightly.
- Phase 2 upgrades: tariffs per MCC/MNC, multi-currency, invoicing, retention policies.

### API Gateway (REST/WebSocket)
- Stack: FastAPI or Go Gin + Redis + JWT/API-key auth.
- Endpoints v1: `POST /v1/sms/send`, `GET /v1/sms/{id}`, `GET /v1/balance`, webhook registration.
- Controls: IP whitelists, per-client rate limiting, OTP templates.
- v2: OAuth2 provider, WebSocket DLR streaming, OpenAPI spec, audit logging.

### Routing Service
- Phase 1: static routes defined via admin UI (failover via Jasmin FailoverMTRoute).
- Phase 2: MCC/MNC catalogue, LCR computation (price, quality), operator scoring.
- APIs: `POST /route/decision`, `PATCH /operator/{id}/status`, metrics exporter.

### Web Interfaces
- Admin SPA: client/operator CRUD, connector state, live TPS/DLR widgets.
- Client SPA: balance, send history, API key management, webhook config.
- Shared React/TypeScript repo with role-based routing; served via Nginx container.
- Phase 2: advanced analytics, tariff editor, SLA breach alerts; Phase 3: reseller theming.

### Monitoring & DevOps
- Kubernetes baseline: Jasmin, API gateway, billing, routing, SPA, RabbitMQ, Redis, PostgreSQL.
- Helm charts + GitOps pipeline (ArgoCD).
- Observability: Prometheus + Grafana dashboards (TPS, DLR, queue lag, DB load), Loki/Fluent Bit logs, alerting (PagerDuty).
- DR: daily PostgreSQL backups, RabbitMQ shovel for standby region (Phase 3).

## Phase Timeline & Key Milestones
| Month | Milestone | Owner(s) | Acceptance |
| --- | --- | --- | --- |
| M1 | Billing schema & API v1 live in staging | Backend + DB | Charges + balances persisted, unit tests + Trial integration |
| M1 | API Gateway MVP (send/status/balance) | Backend | Auth ok, rate limiting via Redis, OpenAPI draft |
| M2 | Jasmin cluster tuned + integrated with billing | Telecom + Backend | OTP load 1k TPS stable, AMQP billing events mirrored |
| M2 | Admin & Client SPA v1 | Frontend | CRUD clients/operators, balance view, API key lifecycle |
| M3 | Monitoring stack + first bank onboarding | DevOps + All | Grafana dashboards + alerting, pilot bank sending OTP |
| M4–M6 | Routing Service LCR v1 + Billing v2 | Backend | MCC/MNC LCR decisions, invoices generated |
| M7 | SPA v2 + OAuth2 security | Frontend + Backend | RBAC scopes, audit log persisted |
| M8–M9 | Operator health automation + SLA tooling | Telecom + Backend | Auto-disable routes <SLA, dashboards |
| M10–M12 | USSD + IVR integrations | Telecom | End-to-end test flows via SS7/Voice providers |
| M13–M15 | Campaign manager, white-label, multi-region HA | Full team | Campaign uploads, reseller skins, DR drill success |

## Workstreams & Dependencies
1. **Telecom Core**: SMPP connector onboarding, TPS tuning, routing hooks. Depends on API gateway for ingress auth, billing for charging.
2. **Billing & Finance**: DB schema, reconciliation jobs, payment integrations. Requires telecom events for accurate CDR.
3. **API & UI**: Public REST, admin/client SPA, documentation. Relies on billing data and routing decisions.
4. **Routing Intelligence**: LCR engine, operator scoring, failover automations. Needs quality metrics + DLR feeds from Jasmin.
5. **DevOps & SecOps**: Kubernetes, CI/CD, monitoring, security hardening. Supports all other streams.

## Risk Mitigation Actions
- **Performance ceiling**: benchmark every sprint; prepare horizontal scaling playbooks (shard RabbitMQ, spin additional Jasmin pods).
- **Billing accuracy**: implement dual-write (Jasmin + billing service) with reconciliation and idempotency keys.
- **SMPP interoperability**: maintain operator sandbox with Wireshark captures; regression suite using SMPP simulators.
- **Security gaps**: penetration test API gateway before onboarding first bank; enforce secret rotation via Vault.
- **Team capacity**: cross-train backend engineers on telecom specifics; schedule buffer for telecom expert availability.

## Next Steps
1. Approve plan scope & budget; align stakeholders on MVP definition.
2. Draft detailed sprint backlog for Phase 1 (user stories, API contracts, DB ERD).
3. Stand up dev/staging clusters and CI pipeline.
4. Kick off parallel tracks: billing service build, API gateway skeleton, Jasmin tuning.

