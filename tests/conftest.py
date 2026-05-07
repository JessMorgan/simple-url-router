import os
import tempfile
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ["BASE_URL"] = "https://example.com"
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "testpassword"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing"

_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_db_path = _db_file.name
_db_file.close()
os.environ["DB_PATH"] = _db_path


@pytest_asyncio.fixture(autouse=True)
async def reset_db():
    """Ensure a clean DB for each test by removing and re-initializing."""
    if os.path.exists(_db_path):
        os.unlink(_db_path)
    for wal in (_db_path + "-wal", _db_path + "-shm"):
        if os.path.exists(wal):
            os.unlink(wal)

    from app.auth import hash_password
    from app.database import init_db
    from app.config import settings

    await init_db()
    # httpx ASGITransport does not trigger lifespan events, so we must
    # ensure the admin password is hashed manually in tests.
    if not settings.admin_password.startswith("$2"):
        settings.admin_password = hash_password(settings.admin_password)
    yield


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://example.com") as c:
        yield c


@pytest_asyncio.fixture
async def authed_client(client: AsyncClient) -> AsyncGenerator[AsyncClient, None]:
    response = await client.post(
        "/login",
        data={"username": "admin", "password": "testpassword"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    cookies = response.cookies
    client.cookies.update(cookies)
    yield client
