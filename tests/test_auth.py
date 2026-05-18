import pytest


@pytest.mark.asyncio
async def test_login_success(client):
    """Valid credentials should set a session cookie and redirect."""
    response = await client.post(
        "/login",
        data={"username": "admin", "password": "testpassword"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert "session" in response.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    """Invalid password should return login page."""
    response = await client.post(
        "/login",
        data={"username": "admin", "password": "wrongpassword"},
        follow_redirects=False,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_login_wrong_username(client):
    """Invalid username should return login page."""
    response = await client.post(
        "/login",
        data={"username": "hacker", "password": "testpassword"},
        follow_redirects=False,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_logout_clears_session(authed_client):
    """Logout should clear the session cookie."""
    response = await authed_client.get("/logout", follow_redirects=False)
    assert response.status_code == 302
    set_cookie = response.headers.get("set-cookie", "")
    assert "session=;" in set_cookie or "session=\"\";" in set_cookie or "Max-Age=0" in set_cookie
