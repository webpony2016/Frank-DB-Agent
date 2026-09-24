from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .config import Settings
from .db import make_engine, initialize
from .errors import DomainError
from .api import router


def create_app(database_url=None, origin=None):
    settings = Settings.load(database_url, origin)
    engine = make_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(app):
        initialize(engine)
        yield
        engine.dispose()

    application = FastAPI(title="Frank Operations Desk · Sample Demo", lifespan=lifespan, docs_url=None, redoc_url=None)
    application.state.engine = engine
    application.state.settings = settings
    application.add_middleware(TrustedHostMiddleware, allowed_hosts=[urlparse(settings.origin).hostname])

    @application.exception_handler(DomainError)
    async def domain_error(request, exc):
        return JSONResponse({"detail": exc.message}, status_code=exc.status)

    @application.middleware("http")
    async def guard(request: Request, call_next):
        if request.method not in {"GET", "HEAD", "OPTIONS"}:
            if request.headers.get("origin") != settings.origin:
                return JSONResponse({"detail": "This action requires the demo's own origin."}, status_code=403)
            size = 0
            parts = []
            async for chunk in request.stream():
                size += len(chunk)
                if size > 65536:
                    return JSONResponse({"detail": "Request too large (64 KiB maximum)."}, status_code=413)
                parts.append(chunk)
            request._body = b"".join(parts)
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store" if request.url.path.startswith("/api") else "no-cache"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "same-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        return response

    @application.get("/health")
    def health():
        return {"status": "ok", "mode": "sample", "schema_version": 1}

    application.include_router(router)
    return application


app = create_app()
