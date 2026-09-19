import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import (
    alerts,
    datasets,
    experiments,
    health,
    models,
    pcap,
    predict,
    preprocessing,
    reports,
    traffic,
)
from app.core.config import settings
from app.database.base import Base
from app.database.session import engine
from app.utils.errors import AppError

# Import ORM models here so Base.metadata is aware of every table before create_all runs.
from app.models import (  # noqa: F401
    dataset,
    experiment,
    ml_model,
    prediction,
    report,
    security_alert,
    traffic_flow,
)

logger = logging.getLogger("netguard")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.resolve_path(settings.model_storage_path)
    settings.resolve_path(settings.upload_path)
    settings.resolve_path(settings.reports_path)
    Base.metadata.create_all(bind=engine)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description="AI-Based Network Traffic Classification & Threat Detection Platform",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.exception_handler(Exception)
    def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error while processing %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={"detail": "An unexpected server error occurred."})

    app.include_router(health.router, prefix=settings.api_prefix)
    app.include_router(datasets.router, prefix=settings.api_prefix)
    app.include_router(preprocessing.router, prefix=settings.api_prefix)
    app.include_router(models.router, prefix=settings.api_prefix)
    app.include_router(experiments.router, prefix=settings.api_prefix)
    app.include_router(predict.router, prefix=settings.api_prefix)
    app.include_router(pcap.router, prefix=settings.api_prefix)
    app.include_router(traffic.router, prefix=settings.api_prefix)
    app.include_router(alerts.router, prefix=settings.api_prefix)
    app.include_router(reports.router, prefix=settings.api_prefix)

    return app


app = create_app()
