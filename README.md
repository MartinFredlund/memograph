# GraphWeb

A self-hosted photo memory bank and family/social graph. Upload photos, tag the people in them,
and build up a graph of relationships over time.

> Screenshot / demo — _coming soon (Phase 5)_

---

## What it does

- **Upload photos** via drag-and-drop
- **Tag people** by clicking on faces — coordinates are stored, so tags appear in the right place
- **Build a graph** of family and social relationships (parent/child, spouse, friend, colleague…)
- **Browse** by person, event, place, or date
- **Explore** the full relationship web in an interactive graph viewer

Self-hosted. Your data stays on your server.

---

## Prerequisites

| Tool | Version |
|------|---------|
| Docker | 24+ |
| Docker Compose | v2 plugin |
| GNU Make | any |
| A Cloudflare account + tunnel token | for public access (optional for local dev) |

---

## Quickstart (production)

```bash
# 1. Clone the repo
git clone <repo-url> graphweb && cd graphweb

# 2. Copy the environment file and fill in your values
cp .env.example .env
$EDITOR .env

# 3. Start all services
make up

# 4. Open the app
# → http://localhost  (or your configured domain)
# → Default admin credentials are set in .env (ADMIN_USERNAME / ADMIN_PASSWORD)
```

> Never use the default admin password in production. Change it in `.env` before first start.

---

## Development setup

The dev override mounts source code into the containers and enables hot reload for both backend
and frontend.

```bash
# Start in dev mode (no cloudflared, hot reload enabled)
make dev

# Backend runs on  http://localhost:8000
# Frontend runs on http://localhost:5173
# Neo4j browser at http://localhost:7474  (no auth in dev by default)
# MinIO console at http://localhost:9001
```

---

## Environment variables

All variables are defined in `.env` (copy from `.env.example`). **Never commit `.env`.**

| Variable | Description |
|----------|-------------|
| `NEO4J_AUTH` | Neo4j credentials (`neo4j/<password>`) |
| `NEO4J_URI` | Bolt URI for the backend (`bolt://neo4j:7687`) |
| `MINIO_ROOT_USER` | MinIO admin username |
| `MINIO_ROOT_PASSWORD` | MinIO admin password |
| `MINIO_ENDPOINT` | Internal MinIO endpoint (`minio:9000`) |
| `MINIO_BUCKET` | Bucket name for image storage |
| `JWT_SECRET` | Random secret for signing JWTs (generate with `openssl rand -hex 32`) |
| `ADMIN_USERNAME` | Seeded admin username |
| `ADMIN_PASSWORD` | Seeded admin password (change before first run) |
| `CLOUDFLARE_TUNNEL_TOKEN` | Cloudflare tunnel token (production only) |

> See `.env.example` for the full list with comments.

---

## Architecture

```
Internet → Cloudflare (SSL, DDoS protection)
         → cloudflared tunnel (outbound-only, no open ports needed)
         → Traefik (internal routing)
         → /api/*  → FastAPI backend
            /*      → React frontend (nginx)
```

**Services:** `cloudflared`, `traefik`, `neo4j`, `minio`, `backend`, `frontend`

**Data model:** Neo4j graph with `Person`, `Event`, `Place`, `Image`, and `User` nodes.
Relationships are minimal base types (`PARENT_OF`, `SPOUSE_OF`, `FRIEND_OF`, etc.);
derived relationships (grandparent, sibling, in-law) are computed by Cypher traversal queries.

For full architectural detail, data model, and implementation plan, see [plan.md](./plan.md).

---

## Running tests

```bash
# Backend tests (pytest)
make test-backend

# Frontend type-check + lint
make lint-frontend
```

CI runs automatically on every push via GitHub Actions (see `.github/workflows/`).

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, Pydantic v2 |
| Graph database | Neo4j 5 Community Edition |
| Object storage | MinIO (S3-compatible) |
| Frontend | React 18, TypeScript, Ant Design, Cytoscape.js |
| Data fetching | @tanstack/react-query |
| Reverse proxy | Traefik v3 |
| CI/CD | GitHub Actions |
| Build tools | Vite (frontend), uv (backend) |

---

## Contributing

This is a personal project — contributions aren't expected, but issues and suggestions are
welcome. Open an issue to discuss before sending a pull request.

---

## License

MIT
