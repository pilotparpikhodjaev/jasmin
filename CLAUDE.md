# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Jasmin is an enterprise-class open source SMS Gateway built on Python and the Twisted framework. It provides SMPP Client/Server and HTTP Client/Server capabilities with advanced message routing, filtering, and delivery receipt (DLR) tracking.

**Core Technologies:**
- Python 3.8-3.12
- Twisted (async event-driven networking)
- RabbitMQ (AMQP message broker for store-and-forward)
- Redis (in-memory DLR tracking and billing)
- SMPP 3.4 protocol
- HTTP/REST APIs

## Development Commands

### Running Tests
```bash
# Run all tests with coverage (Twisted Trial framework)
coverage run --source=jasmin -m twisted.trial tests

# Run specific test module
python -m twisted.trial tests.routing.test_router

# Run specific test class
python -m twisted.trial tests.routing.test_router.RouterTestCase

# Run specific test method
python -m twisted.trial tests.routing.test_router.RouterTestCase.test_add_user
```

### Code Quality
```bash
# Run pylint checks
./misc/pylint/run.sh

# Or run pylint directly
pylint jasmin/

# Format check (project uses .pylintrc for configuration)
pylint --rcfile=.pylintrc jasmin/
```

### Building Documentation
```bash
cd misc/doc
make html
# Output: misc/doc/build/html/
```

### Running Services

**Using Docker Compose (recommended for development):**
```bash
# Start all services (Jasmin, RabbitMQ, Redis)
docker-compose up

# Start with REST API
docker-compose -f docker-compose.restapi.yml up

# Start with Grafana monitoring
docker-compose -f docker-compose.grafana.yml up
```

**Running daemons directly:**
```bash
# Main Jasmin daemon (SMPP, HTTP, CLI, Router)
python jasmin/bin/jasmind.py -c /etc/jasmin/jasmin.cfg

# Interceptor daemon
python jasmin/bin/interceptord.py -c /etc/jasmin/interceptor.cfg

# DLR daemon (Delivery Receipt tracking)
python jasmin/bin/dlrd.py -c /etc/jasmin/dlr.cfg

# DLR Lookup daemon
python jasmin/bin/dlrlookupd.py -c /etc/jasmin/dlrlookup.cfg
```

### Installation & Setup
```bash
# Install production dependencies
pip install -r requirements.txt

# Install test dependencies
pip install -r requirements-test.txt

# Install in development mode
pip install -e .

# Setup required directories (for local development)
sudo mkdir -p /var/log/jasmin /etc/jasmin/resource /etc/jasmin/store
sudo cp misc/config/*.cfg /etc/jasmin/
sudo cp misc/config/resource/* /etc/jasmin/resource/
sudo chmod -R 777 /var/log/jasmin /etc/jasmin/store
```

## Architecture

### High-Level Components

**Four Main Daemons:**
1. **jasmind** - Main daemon containing:
   - SMPP Server (port 2775)
   - HTTP API Server (port 8990)
   - CLI Management Console (jCli, port 1401)
   - Router (message routing engine)
   - AMQP connection for message queuing

2. **interceptord** - Message interception daemon
   - Intercepts MO/MT messages for modification/blocking
   - Runs interception scripts

3. **dlrd** - Delivery Receipt daemon
   - Tracks message delivery receipts
   - Updates DLR status in Redis

4. **dlrlookupd** - DLR Lookup daemon
   - HTTP service for DLR status queries

### Core Subsystems

**Routing (`jasmin/routing/`):**
- `router.py` - Central RouterPB class, manages routing tables and AMQP queues
- `Routes.py` - Route definitions (StaticMORoute, StaticMTRoute, DefaultRoute, etc.)
- `RoutingTables.py` - MORoutingTable, MTRoutingTable for route management
- `Filters.py` - Message filtering (UserFilter, GroupFilter, ConnectorFilter, etc.)
- `InterceptionTables.py` - MO/MT interception table management
- `Routables.py` - Routable message types (RoutableSubmitSm, RoutableDeliverSm)
- `throwers.py` - deliverSmThrower, DLRThrower for message delivery

**Protocols (`jasmin/protocols/`):**
- `smpp/` - SMPP protocol implementation (client/server)
  - `factory.py` - SMPPServerFactory, SMPPClientFactory
  - `pb.py` - SMPPServerPB (Perspective Broker for SMPP)
  - `configs.py` - SMPP server/client configuration
- `http/` - HTTP API server
  - `server.py` - HTTPApi (Falcon-based REST API)
  - `configs.py` - HTTP API configuration
- `cli/` - Telnet-based CLI (jCli)
  - `jcli.py` - Main CLI interface
  - `usersm.py`, `groupsm.py`, `smppccm.py`, `httpccm.py` - Management modules
  - `morouterm.py`, `mtrouterm.py` - Route management
  - `mointerceptorm.py`, `mtinterceptorm.py` - Interception management
- `rest/` - REST API extensions

**Managers (`jasmin/managers/`):**
- `clients.py` - SMPPClientManagerPB for managing SMPP client connections
- `dlr.py` - DLRLookup for delivery receipt tracking

**Queues (`jasmin/queues/`):**
- `factory.py` - AmqpFactory for RabbitMQ connections
- AMQP exchanges: `messaging` (topic), `billing` (topic)
- Routing keys: `deliver.sm.*`, `submit.sm.*`, `dlr.*`, `bill_request.*`

**Redis (`jasmin/redis/`):**
- `client.py` - Redis connection with configuration
- Used for: DLR tracking, billing counters, message metadata

**Tools (`jasmin/tools/`):**
- `cred/` - Authentication (portal, checkers)
- `spread/pb.py` - Perspective Broker utilities
- `migrations/` - Configuration migration utilities
- `stats.py` - Statistics and metrics

### Message Flow

**MT (Mobile Terminated - outbound SMS):**
1. HTTP/SMPP client → HTTP API / SMPP Server
2. Router applies MT filters and routing rules
3. Message queued to AMQP (`submit.sm.*`)
4. deliverSmThrower delivers to SMPP connector
5. DLR tracked in Redis

**MO (Mobile Originated - inbound SMS):**
1. SMPP connector receives deliver_sm
2. Router applies MO filters and routing rules
3. Message queued to AMQP (`deliver.sm.*`)
4. Delivered to HTTP client via callback or SMPP client

**Interception:**
- MO/MT messages can be intercepted before routing
- Interception scripts can modify or reject messages
- Configured via CLI interception tables

## Key Configuration Files

**Locations (default):**
- `/etc/jasmin/jasmin.cfg` - Main daemon config
- `/etc/jasmin/interceptor.cfg` - Interceptor config
- `/etc/jasmin/dlr.cfg` - DLR daemon config
- `/etc/jasmin/dlrlookup.cfg` - DLR lookup config
- `/etc/jasmin/resource/` - AMQP/Redis connection configs
- `/etc/jasmin/store/` - Persistent storage (users, groups, routes)

**Environment Variables:**
- `CONFIG_PATH` - Override config directory (default: `/etc/jasmin/`)
- `REDIS_CLIENT_HOST` - Redis hostname (default: localhost)
- `AMQP_BROKER_HOST` - RabbitMQ hostname (default: localhost)

## Testing Guidelines

**Framework:** Twisted Trial (async test framework)

**Test Structure:**
```
tests/
├── routing/      # Router, filters, routes tests
├── protocols/    # SMPP, HTTP, CLI tests
├── managers/     # Client manager tests
├── queues/       # AMQP tests
├── redis/        # Redis client tests
└── interceptor/  # Interception tests
```

**Key Testing Patterns:**
- Use `@defer.inlineCallbacks` for async tests
- Mock AMQP/Redis connections in unit tests
- Use `TestCase.addCleanup()` for resource cleanup
- Store test configs in `tests/` directory

**Coverage Target:** Maintain existing coverage levels (check CI for current baseline)

## CLI Management Console

The jCli (Jasmin CLI) is a telnet-based console for runtime configuration:

**Access:**
```bash
telnet localhost 1401
# Default credentials: jcliadmin/jclipwd
```

**Key Management Areas:**
- `user` - User management (add, update, list, remove)
- `group` - Group management
- `smppccm` - SMPP Client Connector management
- `httpccm` - HTTP Client Connector management
- `morouter` - MO routing configuration
- `mtrouter` - MT routing configuration
- `mointerceptor` - MO interception scripts
- `mtinterceptor` - MT interception scripts
- `filter` - Filter management
- `stats` - Statistics and metrics

**Persistence:** Changes made via jCli are persisted to `/etc/jasmin/store/` as pickle files.

## Important Design Patterns

**Perspective Broker (PB):**
- Twisted's RPC mechanism used throughout
- `RouterPB`, `SMPPServerPB`, `SMPPClientManagerPB` are PB Avatars
- Authentication via `RouterAuthChecker`, `SmppsRealm`

**Deferred/Callbacks:**
- All I/O is non-blocking (Twisted Deferreds)
- Use `@defer.inlineCallbacks` and `yield` for sequential async operations
- Add errbacks for error handling

**Logging:**
- Per-component loggers (e.g., `LOG_CATEGORY = "jasmin-router"`)
- Configured in config files (log level, rotation, format)
- Avoid `print()`, use `self.log.info/debug/error()`

**Configuration:**
- Config classes in `*/configs.py` files
- Use `ConfigParser` for .cfg files
- Runtime config changes via jCli (persisted to pickle)

**Pickle Protocol:**
- Users, groups, routes stored as pickle files
- Protocol version configurable (default: highest available)
- Migration utilities in `jasmin/tools/migrations/`

## Common Ports

- **2775** - SMPP Server
- **8990** - HTTP API
- **1401** - jCli (Management Console)
- **5672** - AMQP (RabbitMQ)
- **6379** - Redis
- **8080** - REST API (when enabled)

## Dependencies & External Services

**Required Services:**
- RabbitMQ (AMQP broker) - critical for message queuing
- Redis - critical for DLR tracking and billing

**Python Dependencies:**
- `Twisted` - Core async framework
- `txAMQP3` - AMQP protocol implementation
- `smpp.pdu3`, `smpp.twisted3` - SMPP protocol
- `txredisapi` - Redis async client
- `falcon` - HTTP API framework
- `celery` - Task queue (for background jobs)

**Testing Dependencies:**
- `testfixtures` - Test utilities
- `coverage` - Code coverage
- `pylint` - Linting
