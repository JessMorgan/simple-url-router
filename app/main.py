from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.auth import hash_password
from app.config import settings
from app.database import init_db, list_all
from app.routes import admin, redirect
from app.templates import templates


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    if not settings.admin_password.startswith("$2"):
        settings.admin_password = hash_password(settings.admin_password)
    yield


app = FastAPI(
    title="Simple URL Redirector",
    version="0.1.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def check_redirects(request: Request, call_next):
    """Check if the URL path exists as a redirect key BEFORE route handlers run.

    This prevents explicit routes like /health, /admin, /login, etc. from
    shadowing user-created redirects with the same key.
    """
    if request.method == "GET":
        key = request.url.path.strip("/")
        if key:
            from app.database import lookup_key

            redirect_path = await lookup_key(key)
            if redirect_path is not None:
                redirect_url = f"{settings.base_url.rstrip('/')}{redirect_path}"
                return RedirectResponse(url=redirect_url, status_code=302)
    return await call_next(request)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        context = {"base_url": settings.base_url}
        return templates.TemplateResponse(
            request, "login.html", context, status_code=401
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# Health check must be registered BEFORE the catch-all /{key} redirect route.
@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    redirects = await list_all()
    context = {
        "redirects": redirects,
        "base_url": settings.base_url,
    }
    return templates.TemplateResponse(request, "admin_list.html", context)


@app.get("/admin/new", response_class=HTMLResponse)
async def admin_new_page(request: Request):
    from app.routes.admin import require_admin

    require_admin(request)
    context = {
        "key": "",
        "existing_path": "",
        "is_new": True,
        "base_url": settings.base_url,
    }
    return templates.TemplateResponse(request, "admin.html", context)


# Include admin routes next so specific paths (/admin, /login, /logout)
# take priority over the catch-all /{key} redirect route.
app.include_router(admin.router)
app.include_router(redirect.router)
