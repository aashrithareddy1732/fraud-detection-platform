import logging
from dataclasses import dataclass
from os import getenv

from dotenv import load_dotenv

load_dotenv(override=True)

logger = logging.getLogger(__name__)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        import json

        payload = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        return json.dumps(payload)


def _get_bool(name: str, default: bool = False) -> bool:
    value = getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    app_env: str = getenv("APP_ENV", "development")
    debug: bool = _get_bool("DEBUG", True)
    database_url: str = getenv("DATABASE_URL", "sqlite:///./fraud_detection.db")
    openai_api_key: str = getenv("OPENAI_API_KEY", "")
    openai_model: str = getenv("OPENAI_MODEL", "gpt-4.1-mini")
    app_version: str = getenv("APP_VERSION", "0.2.0")
    model_version: str = getenv("MODEL_VERSION", "synthetic-rf-v1")
    cors_origins: tuple[str, ...] = tuple(
        origin.strip() for origin in getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if origin.strip()
    )

    @property
    def openai_enabled(self) -> bool:
        return bool(self.openai_api_key)


settings = Settings()


def validate_startup_config() -> None:
    if not settings.openai_enabled:
        logger.warning(
            "OPENAI_API_KEY is missing. Falling back to local investigation explanations."
        )


def configure_logging() -> None:
    """Use JSON-shaped logs so local output remains easy to ship to a log platform later."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.DEBUG if settings.debug else logging.INFO, handlers=[handler], force=True)
