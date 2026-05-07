# simple-url-router

Key-based HTTP redirector. Given a short key, redirects to a configured path on a fixed base URL. Built-in single-admin auth, SQLite storage, Docker-first deployment.

## Quick start

```bash
# 1. Create .env with a secret key (required)
echo "SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')" > .env

# 2. Start the service
docker compose up -d

# 3. Visit http://localhost:8000 — you'll see the admin list (empty)
#    Log in at /login with admin / changeme (or whatever you set)
```

## How it works

- A request to `GET /<key>` looks up `key` in the SQLite database
- If found, responds with **HTTP 302** to `{BASE_URL}{path}` — e.g. key `42` → path `/devices/powerspec_g757` → redirects to `http://example.com/devices/powerspec_g757`
- If **not found** and the user is **unauthenticated**: 404 page with a link to `/login`
- If **not found** and the user is **authenticated**: 404 page with a creation form to add the key on the spot

Keys can be integers, UUIDs/GUIDs, or arbitrary alphanumeric strings (with hyphens and underscores). Redirect values must be absolute paths (starting with `/`) — not full URLs.

## Configuration

All config is via environment variables. Create a `.env` file:

```bash
# Required — used to sign session cookies. Generate with:
#   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=your-long-random-secret

# Optional with defaults
BASE_URL=http://localhost:8000         # base for redirect URLs
ADMIN_USERNAME=admin                   # single admin login
ADMIN_PASSWORD=changeme                # single admin password
```

### All environment variables

| Variable         | Required | Default                        | Description                                 |
|------------------|----------|--------------------------------|---------------------------------------------|
| `SECRET_KEY`     | **Yes**  | — (compose fails if unset)     | Signs session cookies. Long random string.  |
| `BASE_URL`       | No       | `http://localhost:8000`        | Redirect target base. No trailing slash.    |
| `ADMIN_USERNAME` | No       | `admin`                        | Admin login username.                       |
| `ADMIN_PASSWORD` | No       | `changeme`                     | Admin login password.                       |
| `DB_PATH`        | No       | `data/redirects.db`            | SQLite database path (inside container).    |

## Deploying via Docker Compose

### Prerequisites

- Docker Engine 24+ with Compose plugin (or `docker-compose` v2)

### Step-by-step

```bash
# 1. Clone the repository
git clone <repo-url> simple-url-router
cd simple-url-router

# 2. Generate a secret key
echo "SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')" >> .env

# 3. Optionally override defaults
echo "ADMIN_PASSWORD=my-strong-password" >> .env

# 4. Build and start
docker compose up -d

# 5. Check it's healthy
docker compose ps
# NAME                IMAGE                       STATUS
# simple-url-router   simple-url-router:latest    Up (healthy)

# 6. View logs
docker compose logs -f

# 7. Stop
docker compose down
```

The database persists in a named Docker volume (`redirects_data`) mapped to `/app/data` inside the container. Your data survives container restarts and rebuilds.

### Production tweaks

```yaml
# docker-compose.override.yml (or edit docker-compose.yml)
services:
  app:
    ports:
      - "127.0.0.1:8000:8000"       # listen only on localhost behind reverse proxy
    environment:
      - BASE_URL=https://your-domain.com
```

## Docker image details

- **Base**: `python:3.12-slim`
- **User**: runs as non-root `app` user (UID not exposed, internal only)
- **Filesystem**: read-only root (`read_only: true` in compose), writes DB via a Docker volume at `/app/data`, uses `tmpfs` for `/tmp`
- **Health check**: hits `GET /health` every 30s — container status shows `(healthy)` when ready

## Running tests

```bash
# With a local venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run all tests
python -m pytest

# Run with coverage report (requires pytest-cov: pip install pytest-cov)
python -m pytest --cov=app tests/

# Run a specific test file
python -m pytest tests/test_redirect.py -v

# Run via Docker (requires Dockerfile to be built first)
docker build -t simple-url-router:latest .
docker run --rm simple-url-router:latest python -m pytest tests/
```

Tests use a temporary SQLite database (not the production path) and httpx's `ASGITransport` for in-process requests. No external services or network access required.

## Development without Docker

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export SECRET_KEY=dev-key
export ADMIN_PASSWORD=admin
uvicorn app.main:app --reload
```
