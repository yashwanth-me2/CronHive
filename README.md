# CronHive

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![Redis](https://img.shields.io/badge/Redis-7-red)

A reliable, multi-tenant webhook and job scheduling service built with Python.

## Architecture

CronHive uses a Clean/Hexagonal Architecture to separate domain logic from infrastructure details.

- **FastAPI** handles the HTTP layer (Gateways).
- **PostgreSQL** stores tenants, jobs, and execution history.
- **Redis (Sorted Sets)** acts as a lock-free priority queue for job execution.
- **Async Workers** poll Redis and execute HTTP requests with a built-in Circuit Breaker.

## Features

- **At-Least-Once Delivery**: Jobs are guaranteed to execute.
- **Circuit Breaker**: Prevents hammering failing downstream services.
- **Exponential Backoff & Jitter**: Smart retries for failed webhooks.
- **Multi-Tenancy**: Isolated namespaces with API key & JWT authentication.
- **Sliding Window Rate Limiting**: Per-tenant rate limits backed by Redis.

## Quick Start

```bash
# Start the entire stack (API, Worker, Postgres, Redis)
make up

# Run database migrations (requires python environment)
# OR run inside docker: docker-compose exec api alembic upgrade head
make migrate
```

## API Reference
- `POST /api/v1/auth/register` - Register a tenant
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/jobs` - Create a scheduled job
- `GET /api/v1/jobs` - List jobs
- `POST /api/v1/jobs/{id}/pause` - Pause a job
