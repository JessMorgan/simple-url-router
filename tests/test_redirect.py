import pytest


@pytest.mark.asyncio
async def test_redirect_found(client):
    """A key that exists in the DB should 302 to the correct URL."""
    from app.database import upsert_key

    await upsert_key("42", "/devices/powerspec_g757")

    response = await client.get("/42", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "https://example.com/devices/powerspec_g757"


@pytest.mark.asyncio
async def test_redirect_missing_unauthed(client):
    """A missing key for an unauthenticated user should 404 with login link."""
    response = await client.get("/999999", follow_redirects=False)
    assert response.status_code == 404
    body = response.text
    assert "999999" in body
    assert "/login" in body


@pytest.mark.asyncio
async def test_redirect_missing_authed(authed_client):
    """A missing key for an authenticated user should 404 with creation form."""
    await authed_client.post("/admin/999999", data={"path": "/new/path"}, follow_redirects=False)

    response = await authed_client.get("/999999", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "https://example.com/new/path"


@pytest.mark.asyncio
async def test_redirect_invalid_key(client):
    """A key with invalid characters should 422."""
    response = await client.get("/key%20with%20spaces", follow_redirects=False)
    assert response.status_code == 422

    response = await client.get("/key<script>", follow_redirects=False)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_redirect_long_key(client):
    """A key exceeding length limits should 422."""
    long_key = "a" * 300
    response = await client.get(f"/{long_key}", follow_redirects=False)
    assert response.status_code == 422
