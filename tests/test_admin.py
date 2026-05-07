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


# ── Bulk import ──────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_admin_import_page_unauthed(client):
    """Import page should 401 for unauthenticated users."""
    response = await client.get("/admin/import", follow_redirects=False)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_import_page_loads(authed_client):
    """Import page should render for authenticated users."""
    response = await authed_client.get("/admin/import", follow_redirects=False)
    assert response.status_code == 200
    assert "Bulk Import" in response.text


@pytest.mark.asyncio
async def test_admin_import_valid_csv(authed_client):
    """Import valid CSV data creates redirects."""
    from app.database import lookup_key

    csv_data = "42,/devices/powerspec_g757\nnas,/devices/gtk_nas\n"
    response = await authed_client.post(
        "/admin/import",
        data={"csv": csv_data},
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert "2 redirect(s) imported" in response.text

    assert await lookup_key("42") == "/devices/powerspec_g757"
    assert await lookup_key("nas") == "/devices/gtk_nas"


@pytest.mark.asyncio
async def test_admin_import_with_header(authed_client):
    """Import CSV with a header row skips it."""
    from app.database import lookup_key

    csv_data = "key,path\n42,/devices/powerspec_g757\n"
    response = await authed_client.post(
        "/admin/import",
        data={"csv": csv_data},
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert "1 redirect(s) imported" in response.text
    assert await lookup_key("42") == "/devices/powerspec_g757"


@pytest.mark.asyncio
async def test_admin_import_partial_invalid(authed_client):
    """Import with some invalid rows skips bad rows and reports errors."""
    from app.database import lookup_key

    csv_data = (
        "valid_key,/good/path\n"
        "bad_path_key,http://evil.com\n"
        "another_valid,/another/path\n"
    )
    response = await authed_client.post(
        "/admin/import",
        data={"csv": csv_data},
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert "2 redirect(s) imported" in response.text
    assert "must not contain a URI scheme" in response.text

    assert await lookup_key("valid_key") == "/good/path"
    assert await lookup_key("another_valid") == "/another/path"
    assert await lookup_key("bad_path_key") is None


@pytest.mark.asyncio
async def test_admin_import_updates_existing(authed_client):
    """Import with existing keys updates their paths."""
    from app.database import lookup_key, upsert_key

    await upsert_key("existing", "/old/path")

    csv_data = "existing,/new/path\n"
    response = await authed_client.post(
        "/admin/import",
        data={"csv": csv_data},
        follow_redirects=False,
    )
    assert response.status_code == 200
    assert "1 redirect(s) imported" in response.text
    assert await lookup_key("existing") == "/new/path"


# ── Delete from listing page ──────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_admin_delete_from_list(authed_client):
    """Delete button on admin list page deletes a redirect."""
    from app.database import lookup_key, upsert_key

    await upsert_key("del-key", "/some/path")

    response = await authed_client.post(
        "/admin/del-key/delete",
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["location"].endswith("/admin")

    path = await lookup_key("del-key")
    assert path is None


@pytest.mark.asyncio
async def test_admin_delete_nonexistent(authed_client):
    """Delete a key that does not exist returns 404."""
    response = await authed_client.post(
        "/admin/nonexistent-key/delete",
        follow_redirects=False,
    )
    assert response.status_code == 404
