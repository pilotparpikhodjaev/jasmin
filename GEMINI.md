# Gemini Context for Jasmin SMS Gateway

This file provides essential context for the Gemini AI agent when working with the Jasmin SMS Gateway repository.

## 1. Project Overview

**Name:** Jasmin
**Description:** An open-source SMS Gateway built with Python and the Twisted framework. It features SMPP and HTTP support, advanced routing, billing, and high-performance message queuing.
**Core Technologies:**
*   **Language:** Python 3 (Twisted framework)
*   **Messaging:** AMQP (RabbitMQ)
*   **Storage:** Redis (In-memory DLR tracking and billing)
*   **Protocols:** SMPP 3.4, HTTP/REST
*   **Architecture:** Microservices-style daemons interacting via AMQP.

## 2. Architecture

Jasmin is composed of several key daemons that interact asynchronously:

*   **`jasmind.py`:** The main daemon. Hosts the SMPP Server, HTTP API, CLI (jCli), and the Router.
*   **`interceptord.py`:** Handles message interception logic (modifying/blocking messages).
*   **`dlrd.py`:** Manages Delivery Receipts (DLR), tracking status in Redis.
*   **`dlrlookupd.py`:** Provides an HTTP service for querying DLR status.

**Key Directories:**
*   `jasmin/` - Source code root.
    *   `bin/` - Entry points for daemons (`jasmind.py`, etc.).
    *   `routing/` - Core routing logic (`RouterPB`, tables, filters).
    *   `protocols/` - Protocol implementations (SMPP, HTTP, CLI).
    *   `managers/` - Client connection managers.
    *   `queues/` - AMQP factory and configuration.
*   `misc/` - Configuration templates (`config/`), documentation (`doc/`), and scripts.
*   `tests/` - Unit and integration tests.
*   `docker/` - Dockerfiles and related scripts.

## 3. Build and Run

### Docker (Recommended for Development)
The project uses `docker-compose` to orchestrate Jasmin, RabbitMQ, and Redis.

```bash
# Start all services
docker-compose up

# Start specific configurations
docker-compose -f docker-compose.restapi.yml up
docker-compose -f docker-compose.grafana.yml up
```

### Local Python Environment
**Prerequisites:** RabbitMQ and Redis must be running.

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    pip install -e .
    ```

2.  **Run Daemons:**
    ```bash
    # Main Daemon
    python jasmin/bin/jasmind.py -c misc/config/jasmin.cfg
    
    # Interceptor
    python jasmin/bin/interceptord.py -c misc/config/interceptor.cfg
    
    # DLR Manager
    python jasmin/bin/dlrd.py -c misc/config/dlr.cfg
    ```

3.  **Management Console (jCli):**
    ```bash
    telnet localhost 1401
    # Default credentials: jcliadmin / jclipwd
    ```

## 4. Testing

Jasmin uses the **Twisted Trial** framework for asynchronous testing.

### Running Tests
```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests with coverage
coverage run --source=jasmin -m twisted.trial tests

# Run a specific test module
python -m twisted.trial tests.routing.test_router

# Run a specific test case
python -m twisted.trial tests.routing.test_router.RouterTestCase.test_add_user
```

### Code Quality
```bash
# Run pylint
pylint jasmin/ --rcfile=.pylintrc
```

## 5. Development Conventions

*   **Async First:** All I/O operations must be non-blocking. Use `Twisted`'s `Deferred` and `@defer.inlineCallbacks`.
*   **Perspective Broker (PB):** Used for RPC between components.
*   **Configuration:**
    *   Static config: `.cfg` files (parsed via `ConfigParser`).
    *   Dynamic config: Managed via `jCli` and persisted as Python `pickle` files in `/etc/jasmin/store` (or configured path).
*   **Logging:** Use the component-specific loggers (e.g., `self.log.info()`). Do not use `print`.
*   **Standards:** Follow PEP 8 where possible, but respect Twisted coding styles (camelCase for methods is common in Twisted).

## 6. Documentation

Project documentation source is in `docs/` and `misc/doc/`.

*   **Build Docs:**
    ```bash
    cd misc/doc
    make html
    ```
*   **View:** Open `misc/doc/build/html/index.html`.
