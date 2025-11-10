# FastAPI Education Backend

Self-contained backend core that powers registration, RBAC, courses, invites, chat, notifications, and storage links for an education platform.

## Stack
- FastAPI + Uvicorn
- PostgreSQL via SQLAlchemy + Alembic
- Redis (rate limiting, pub/sub, RQ queues)
- MinIO for object storage (S3-compatible)
- SMTP (MailHog in dev) for templated emails

## Getting Started
1. Copy `.env.example` to `.env` and adjust secrets (note the async driver in `DATABASE_URL`, e.g. `postgresql+asyncpg://...`).
2. Build/run with Docker Compose:
   ```bash
   docker-compose up --build
   ```
3. API runs on http://localhost:8000 with interactive docs at `/docs`.

### Services in Docker Compose
- `db`: PostgreSQL 15 (port 5432)
- `redis`: Redis 7 (port 6379)
- `minio`: MinIO gateway (S3 API on port 9000, console 9090)
- `mailhog`: SMTP sink/UI (SMTP 1025, UI http://localhost:8025)
- `worker`: RQ worker that processes queued email jobs

## Migrations
```bash
alembic upgrade head   # apply latest
alembic downgrade -1   # rollback one revision
```

## Example Requests
```bash
# register/login
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secretpass"}'

curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secretpass"}'

# create invite (admin token required)
curl -X POST http://localhost:8000/admin/invites \
  -H "Authorization: Bearer <ADMIN_ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"role_to_grant":"member","expires_at":"2024-12-01T00:00:00Z"}'

# redeem invite
curl -X POST http://localhost:8000/invites/redeem \
  -H "Authorization: Bearer <USER_ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"code":"INV123"}'

# member-only courses
curl -H "Authorization: Bearer <MEMBER_TOKEN>" http://localhost:8000/courses?visibility=member

# request signed URL for lesson asset (requires authenticated user)
curl -H "Authorization: Bearer <TOKEN>" \
  'http://localhost:8000/storage/sign?key=lessons/video.mp4'

# websocket chat
websocat "ws://localhost:8000/ws/channels/hq?token=<ACCESS_TOKEN>"
```

## API Reference

Looking for the full list of routes, payloads, and roles? See [API_REFERENCE.md](API_REFERENCE.md).

## Frontend Console

A minimal client lives in `frontend/` for exercising the backend without Postman/cURL:

1. Run the backend (e.g., `docker-compose up`).
2. Open `frontend/index.html` in your browser (no build step required).
3. Set the API base URL (defaults to `http://localhost:8000`).
4. Use the panels to register/login, browse courses, mark progress, manage invites, request signed URLs, or join chat channels.

Tokens are stored in `localStorage`, and each panel shows the raw JSON returned by the API for quick inspection.

## Tests & Coverage
```bash
pytest --cov=app
```

Unit tests cover auth hashing/JWT, invites, storage signing, and chat lifecycle with mocked Redis. Integration tests ensure course listing/detail and idempotent progress updates.

## Definition of Done
- JWT auth (access/refresh) with hashed passwords
- RBAC-protected admin endpoints
- Courses + lessons CRUD, visibility filtering, idempotent progress
- MinIO signed URLs for secure asset access
- Redis-powered rate limits and WebSocket chat pub/sub
- Invite lifecycle with audit logs
- SMTP notifications via templated emails
- Alembic migrations + 70%+ coverage on critical subsystems
