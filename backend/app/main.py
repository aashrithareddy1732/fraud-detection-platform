import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api import analytics, explanations, metrics, operations, predictions, transactions
from app.config import configure_logging, settings, validate_startup_config
from app.database import Base, engine

Base.metadata.create_all(bind=engine)
configure_logging()
validate_startup_config()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI-Powered Credit Card Fraud Detection Platform",
    version=settings.app_version,
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(transactions.router)
app.include_router(predictions.router)
app.include_router(metrics.router)
app.include_router(explanations.router)
app.include_router(analytics.router)
app.include_router(operations.router)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("request_failed", extra={"correlation_id": correlation_id, "path": request.url.path})
        raise
    response.headers["X-Correlation-ID"] = correlation_id
    logger.info(
        "request_completed correlation_id=%s method=%s path=%s status=%s duration_ms=%.2f",
        correlation_id, request.method, request.url.path, response.status_code, (time.perf_counter() - started) * 1000,
    )
    return response


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.app_env, "openai_enabled": settings.openai_enabled}


@app.get("/ready")
def ready():
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
        return {"status": "ready"}
    except Exception as exc:
        return {"status": "not_ready", "detail": str(exc)}


@app.get("/version")
def version():
    return {"app_version": settings.app_version, "model_version": settings.model_version, "environment": settings.app_env}
