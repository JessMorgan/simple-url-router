import pytest


@pytest.mark.asyncio
async def test_admin_list_unauthed(client):
    """Admin list should redirect to login for unauthenticated users."""
    response = await client.get("/admin", follow_redirects=False)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_list_authed(authed_client):
    """Admin list should return 200 for authenticated users."""
    response = await authed_client.get("/admin", follow_redirects=False)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_admin_create_redirect(authed_client):
    """An admin can create a new redirect via POST."""
    response = await authed_client.post(
        "/admin/42",
        data={"path": "/devices/powerspec_g757"},
        follow_redirects=False,
    )
    assert response.status_code == 302

    from app.database import lookup_key

    path = await lookup_key("42")
    assert path == "/devices/powerspec_g757"


@pytest.mark.asyncio
async def test_admin_update_redirect(authed_client):
    """An admin can update an existing redirect."""
    from app.database import lookup_key, upsert_key

    await upsert_key("1", "/devices/old")

    response = await authed_client.post(
        "/admin/1",
        data={"path": "/devices/new"},
        follow_redirects=False,
    )
    assert response.status_code == 302

    path = await lookup_key("1")
    assert path == "/devices/new"


@pytest.mark.asyncio
async def test_admin_delete_redirect(authed_client):
    """An admin can delete a redirect."""
    from app.database import lookup_key, upsert_key

    await upsert_key("99", "/devices/todelete")

    response = await authed_client.post(
        "/admin/99/delete",
        follow_redirects=False,
    )
    assert response.status_code == 302

    path = await lookup_key("99")
    assert path is None


@pytest.mark.asyncio
async def test_admin_create_invalid_path(authed_client):
    """An admin cannot create a redirect with an invalid path."""
    response = await authed_client.post(
        "/admin/43",
        data={"path": "http://evil.com"},
        follow_redirects=False,
    )
    assert response.status_code == 422

    response = await authed_client.post(
        "/admin/44",
        data={"path": "../escape"},
        follow_redirects=False,
    )
    assert response.status_code == 422

    response = await authed_client.post(
        "/admin/45",
        data={"path": "relative/path"},
        follow_redirects=False,
    )
    assert response.status_code == 422
