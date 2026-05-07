from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError

from app.auth import (
    create_session_token,
    verify_password,
    verify_session_token,
)
from app.database import delete_key, list_all, lookup_key, upsert_key
from app.models import KeyParam, PathValue
from app.templates import templates
from app.config import settings
from pydantic import TypeAdapter

_path_adapter = TypeAdapter(PathValue)

router = APIRouter()


def require_admin(request: Request) -> None:
    token = request.cookies.get("session")
    if not token or not verify_session_token(token):
        raise HTTPException(status_code=401, detail="Not authenticated")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    context = {"base_url": settings.base_url}
    return templates.TemplateResponse(request, "login.html", context)


@router.post("/login")
async def login(
    request: Request,
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
):
    if username != settings.admin_username:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(password, settings.admin_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_session_token()
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(
        key="session",
        value=token,
        max_age=settings.session_max_age,
        httponly=True,
        samesite="lax",
        secure=False,
    )
    return response


@router.get("/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/login", status_code=302)
    response.set_cookie(key="session", value="", max_age=0)
    return response


@router.get("/admin/{key}", response_class=HTMLResponse)
async def admin_edit_page(request: Request, key: KeyParam):
    require_admin(request)
    existing = await lookup_key(key)
    context = {
        "key": key,
        "existing_path": existing or "",
        "is_new": existing is None,
        "base_url": settings.base_url,
    }
    return templates.TemplateResponse(request, "admin.html", context)


@router.post("/admin/{key}")
async def admin_upsert(
    request: Request,
    key: KeyParam,
    path: str = Form(...),
):
    require_admin(request)
    try:
        validated_path = _path_adapter.validate_python(path)
    except ValidationError as e:
        clean = [{"loc": err.get("loc"), "msg": err.get("msg"), "type": err.get("type")} for err in e.errors()]
        raise HTTPException(status_code=422, detail=clean)
    await upsert_key(key, validated_path)
    return RedirectResponse(url=f"/{key}", status_code=302)


@router.post("/admin/{key}/delete")
async def admin_delete(request: Request, key: KeyParam):
    require_admin(request)
    deleted = await delete_key(key)
    if not deleted:
        raise HTTPException(status_code=404, detail="Key not found")
    return RedirectResponse(url="/admin", status_code=302)


@router.get("/admin", response_class=HTMLResponse)
async def admin_list(request: Request):
    require_admin(request)
    redirects = await list_all()
    context = {
        "redirects": redirects,
        "base_url": settings.base_url,
    }
    return templates.TemplateResponse(request, "admin_list.html", context)
