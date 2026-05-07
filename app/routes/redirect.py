from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.auth import verify_session_token
from app.database import lookup_key
from app.models import KeyParam
from app.templates import templates
from app.config import settings

router = APIRouter()


def _is_authenticated(request: Request) -> bool:
    token = request.cookies.get("session")
    if not token:
        return False
    return verify_session_token(token)


@router.get("/{key}")
async def handle_redirect(key: KeyParam, request: Request):
    path = await lookup_key(key)
    if path is not None:
        redirect_url = f"{settings.base_url.rstrip('/')}{path}"
        return RedirectResponse(url=redirect_url, status_code=302)

    authed = _is_authenticated(request)
    context = {
        "key": key,
        "authenticated": authed,
        "base_url": settings.base_url,
    }
    return templates.TemplateResponse(
        request, "404.html", context, status_code=404
    )
