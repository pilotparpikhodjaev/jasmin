# Repository Guidelines

## Project Structure & Module Organization
Core SMS gateway code resides in `jasmin/`, split into purpose-driven modules such as `managers/` (SMPP/HTTP clients), `protocols/` (wire logic), `queues/` (AMQP glue), and `routing/` (billing, filtering, DLR rules). The `tests/` tree mirrors this layout; when you add `jasmin/routing/new_rule.py`, place coverage in `tests/routing/test_new_rule.py`. Deployment assets live in `docker/`, `kubernetes/`, and `misc/` (docs, installers), while executable entry points are under `jasmin/bin/` and referenced by `setup.py`.

## Build, Test, and Development Commands
Install dependencies with:
- `python -m pip install -r requirements.txt`
- `python -m pip install -r requirements-test.txt`
- `python -m pip install -e .` (editable dev mode)

`trial tests` runs the Twisted Trial suite; scope to a subpackage (`trial tests.protocols`) for faster loops. Bring up Redis, RabbitMQ, and the daemon locally via `docker-compose up jasmin`, which mounts the repo into the container built from `docker/Dockerfile.dev`.

## Coding Style & Naming Conventions
Target Python 3 with 4-space indentation, snake_case functions, and CapWords classes consistent with existing types (`SubmitSmBill`, `RouterPB`). Many modules execute inside Twisted reactors, so avoid blocking APIs inside callbacks and prefer Deferred-based flows. `pylint` is configured by `.pylintrc`; run `pylint jasmin tests` before pushing and treat warnings as bugs.

## Testing Guidelines
Trial is the canonical framework. Use `@defer.inlineCallbacks` and helper coroutines like `waitFor` just as `tests/managers/test_managers.py` does, and always stop any listener/reactor resources during `tearDown`. Name files `test_<feature>.py`, keep fixtures per namespace (`tests/protocols/smpp`), and stub external dependencies (AMQP, Redis) unless an integration test explicitly requires them. Validate both success and failure paths because routers maintain complex state.

## Commit & Pull Request Guidelines
Recent history (`git log -5`) shows short, imperative subjects (“bumping dependencies”), so follow that format and keep summaries under 72 characters. Reference issues in commit bodies, mention env/port/protocol changes, and document migrations. PRs should include: a scope overview, manual + automated test commands (`trial tests.routing`, `docker-compose up --build`), and screenshots/logs for operator-facing adjustments. Ensure CI and linters are green before requesting review and consult `SECURITY.md` for responsible disclosure language.

## Security & Configuration Tips
Do not commit credentials; `docker-compose.yml` wires `REDIS_CLIENT_HOST` and `AMQP_BROKER_HOST`, so override them via local env or `.env` files ignored by Git. Keep both `requirements.txt` and `requirements-test.txt` current because they feed Docker builds and NFPM packages. Report vulnerabilities privately through the process described in `SECURITY.md` before any public issue.
