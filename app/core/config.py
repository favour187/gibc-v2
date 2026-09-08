from __future__ import annotations
import os
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

_TRUE = {"1", "true", "yes", "on", "y"}
_FALSE = {"0", "false", "no", "off", "n"}


def _env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    return default if value is None or value == "" else value


def _env_int(name: str, default: int) -> int:
    value = _env(name)
    return int(value) if value is not None else default


def _env_float(name: str, default: float) -> float:
    value = _env(name)
    return float(value) if value is not None else default


def _env_bool(name: str, default: bool = False) -> bool:
    value = _env(name)
    if value is None:
        return default
    return value.strip().lower() in _TRUE


def _env_list(name: str, default: tuple[str, ...] = ()) -> tuple[str, ...]:
    value = _env(name)
    if value is None:
        return default
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    app_name: str = "Hackathon App"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = False
    database_url: str = "sqlite:///./data/app.db"
    db_echo: bool = False
    auto_create_tables: bool = True
    secret_key: str = "dev-only-secret-change-me"
    password_iterations: int = 600_000
    session_ttl_hours: int = 72
    ai_mode: str = "auto"
    ai_base_url: str = "https://api.openai.com/v1"
    ai_api_key: str = ""
    ai_model: str = "gpt-4o-mini"
    ai_timeout_seconds: float = 25.0
    ai_max_retries: int = 2
    ai_cache_ttl_seconds: int = 300
    ai_cache_max_entries: int = 256
    api_prefix: str = "/api"
    cors_origins: tuple[str, ...] = ("*",)
    rate_limit_per_minute: int = 120
    trusted_proxy_headers: bool = False
    static_dir: str | None = None
    data_dir: str = "./data"
    seed_demo_user: bool = False

    @classmethod
    def from_env(cls, **overrides: Any) -> "Settings":
        kwargs = dict(
            app_name=_env("APP_NAME", cls.app_name) or cls.app_name,
            app_version=_env("APP_VERSION", cls.app_version) or cls.app_version,
            environment=_env("ENVIRONMENT", cls.environment) or cls.environment,
            debug=_env_bool("DEBUG", cls.debug),
            database_url=_env("DATABASE_URL", cls.database_url) or cls.database_url,
            db_echo=_env_bool("DB_ECHO", cls.db_echo),
            auto_create_tables=_env_bool("AUTO_CREATE_TABLES", cls.auto_create_tables),
            secret_key=_env("SECRET_KEY", cls.secret_key) or cls.secret_key,
            password_iterations=_env_int(
                "PASSWORD_ITERATIONS", cls.password_iterations
            ),
            session_ttl_hours=_env_int("SESSION_TTL_HOURS", cls.session_ttl_hours),
            ai_mode=_env("AI_MODE", cls.ai_mode) or cls.ai_mode,
            ai_base_url=_env("AI_BASE_URL", cls.ai_base_url) or cls.ai_base_url,
            ai_api_key=_env("AI_API_KEY", "") or "",
            ai_model=_env("AI_MODEL", cls.ai_model) or cls.ai_model,
            ai_timeout_seconds=_env_float("AI_TIMEOUT_SECONDS", cls.ai_timeout_seconds),
            ai_max_retries=_env_int("AI_MAX_RETRIES", cls.ai_max_retries),
            ai_cache_ttl_seconds=_env_int(
                "AI_CACHE_TTL_SECONDS", cls.ai_cache_ttl_seconds
            ),
            ai_cache_max_entries=_env_int(
                "AI_CACHE_MAX_ENTRIES", cls.ai_cache_max_entries
            ),
            api_prefix=_env("API_PREFIX", cls.api_prefix) or cls.api_prefix,
            cors_origins=_env_list("CORS_ORIGINS", cls.cors_origins),
            rate_limit_per_minute=_env_int(
                "RATE_LIMIT_PER_MINUTE", cls.rate_limit_per_minute
            ),
            trusted_proxy_headers=_env_bool(
                "TRUSTED_PROXY_HEADERS", cls.trusted_proxy_headers
            ),
            static_dir=_env("STATIC_DIR"),
            data_dir=_env("DATA_DIR", cls.data_dir) or cls.data_dir,
            seed_demo_user=_env_bool("SEED_DEMO_USER", cls.seed_demo_user),
        )
        return cls(**{**kwargs, **overrides})

    def with_overrides(self, **overrides: Any) -> "Settings":
        return replace(self, **overrides)

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def ai_remote_configured(self) -> bool:
        return bool(self.ai_api_key)

    def ensure_data_dir(self) -> Path:
        path = Path(self.data_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path
