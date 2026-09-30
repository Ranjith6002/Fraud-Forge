import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api import dashboard, rules, transactions
from app.config import get_settings
from app.database import engine, init_db
from app.utils.log_config import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(get_settings().log_level)
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Pluggable fraud rule engine with a reviewer console API.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=False,
        allow_methods=["*"], allow_headers=["*"],
    )
    app.include_router(transactions.router)
    app.include_router(dashboard.router)
    app.include_router(rules.router)

    @app.get("/", tags=["health"], summary="API health/status")
    def health():
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            db_status = "ok"
        except Exception:
            db_status = "unavailable"
        return {"service": settings.app_name, "version": settings.app_version, "status": "ok",
                "database": db_status, "docs": "/docs"}

    @app.get("/api/health/database", tags=["health"], summary="Database status and dialect check")
    def db_health():
        try:
            db_type = engine.dialect.name
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return {
                "status": "connected",
                "database_type": "PostgreSQL" if "postgres" in db_type.lower() else db_type,
                "driver": engine.driver,
                "pool_status": "active"
            }
        except Exception as exc:
            return {
                "status": "error",
                "detail": str(exc)
            }


    @app.exception_handler(SQLAlchemyError)
    async def db_error_handler(request: Request, exc: SQLAlchemyError):
        logger.exception("Database error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "A database error occurred."})

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "Internal server error."})

    return app


app = create_app()
