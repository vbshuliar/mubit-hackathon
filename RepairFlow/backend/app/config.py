"""Environment configuration. All secrets are read server-side only."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, model_validator
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"

    data_dir: Path = BACKEND_DIR / "data"
    database_path: Path = BACKEND_DIR / "data" / "repairflow.db"
    recordings_dir: Path = BACKEND_DIR / "data" / "recordings"
    documents_dir: Path = BACKEND_DIR / "data" / "documents"

    operator_username: str = "operator"
    operator_password: str = "repairflow-demo"
    # Toggle, not a removal: flip back to True (the safe default for anyone
    # else running this) before any live/public demo. False just makes
    # require_operator accept every request with no Authorization header.
    # Default OFF since 2026-09-21 (owner decision): this is a localhost
    # prototype and operator sign-in was removed from the UI entirely. It
    # remains a switch rather than a deletion so the capability survives if
    # this is ever exposed -- but the SPA no longer has a login form, so
    # turning it on makes every API call 401 until one is reintroduced.
    # See docs/26 and frontend-fixi/src/lib/auth-context.ts.
    operator_auth_enabled: bool = False

    # Gemini / Pydantic AI
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.8-flash"
    gemini_fallback_model: str = "gemini-3.7-flash"

    coordinator_provider: Literal["auto", "mubit", "gemini", "fixture"] = "auto"
    mubit_api_key: SecretStr | None = None
    mubit_model: str = "claude-haiku-4-5"
    mubit_base_url: str = "https://api.mubit.ai/anthropic"
    mubit_budget_path: Path = BACKEND_DIR / "data" / "mubit-budget.sqlite3"
    mubit_max_runs: int = Field(default=30, ge=0, le=1000)
    mubit_max_tokens_per_run: int = Field(default=60000, ge=1000, le=200000)
    mubit_record: Literal["full", "metadata", "off"] = "full"
    # Additional paid shadow measurement only; never changes the chosen action.
    mubit_report_shadow_enabled: bool = False

    @model_validator(mode="after")
    def _validate_mubit(self) -> "Settings":
        from urllib.parse import urlsplit

        if self.coordinator_provider == "mubit" and not self.mubit_live:
            raise ValueError("MUBIT_API_KEY is required when COORDINATOR_PROVIDER=mubit")
        if self.active_coordinator_provider == "mubit":
            url = urlsplit(self.mubit_base_url)
            if (url.scheme != "https" or not url.hostname or url.username or url.password
                    or url.query or url.fragment or url.path.rstrip("/") != "/anthropic"):
                raise ValueError("MUBIT_BASE_URL must be an HTTPS Anthropic gateway URL ending in /anthropic (no /v1)")
            if not self.mubit_model.startswith("claude-"):
                raise ValueError("MUBIT_MODEL must be a Claude model ID for the Anthropic gateway")
        if self.coordinator_provider == "gemini" and not self.gemini_live:
            raise ValueError("GEMINI_API_KEY is required when COORDINATOR_PROVIDER=gemini")
        return self

    @property
    def mubit_live(self) -> bool:
        return bool(self.mubit_api_key and self.mubit_api_key.get_secret_value().strip())

    @property
    def active_coordinator_provider(self) -> str:
        if self.coordinator_provider != "auto":
            return self.coordinator_provider
        return "mubit" if self.mubit_live else "gemini" if self.gemini_live else "fixture"

    # Earliest day offset MockBookingConnector generates slots at (docs/10).
    # Default 2 (unchanged, "believable" scheduling). For a compressed demo
    # timeline this can be lowered -- but never to 0: a same-day slot's
    # expires_at equals its start_at, so a slot generated after that hour
    # has already expired the instant it's created (see booking.py).
    demo_slot_offset_days: int = 2

    # Largest single upload accepted by the documents endpoint. Bounded
    # because the whole body is buffered to hash and size it before it is
    # written; an unbounded upload is a trivial memory exhaustion.
    max_document_bytes: int = 25 * 1024 * 1024

    # Tavily
    tavily_api_key: str | None = None

    # Public callback base (HTTPS tunnel) used for provider-facing URLs
    public_base_url: str = "http://localhost:8000"

    # Both dev ports. 5174 is what `npm run dev` in frontend-fixi actually
    # binds (vite.config.ts) and what the README tells you to open; 5173 is
    # the older `frontend/` app. Shipping only 5173 meant a fresh clone
    # followed the documented steps and got CORS failures from the only
    # frontend that is actually served -- the local .env had been fixed by
    # hand, so the breakage was invisible on this machine.
    cors_allow_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:5174"]
    )
    # Escape hatch for the one legitimate wildcard case: a deployment that
    # genuinely wants an open, *credential-free* API. It drops credentials
    # rather than keeping them, because the dangerous combination is
    # precisely wildcard + credentials.
    cors_allow_credentials: bool = True

    @model_validator(mode="after")
    def _reject_wildcard_origin_with_credentials(self) -> "Settings":
        """`allow_origins=["*"]` with `allow_credentials=True` is not the
        harmless-looking dev convenience it reads as. Starlette treats a
        wildcard as "echo whatever Origin the request carried", so with
        credentials on, *any* site a signed-in operator visits can call
        this API with their session and read the response. The browser
        does not save you here -- echoing the origin is what makes it
        legal.

        Refuse at construction, so a bad CORS_ALLOW_ORIGINS fails the
        process loudly on boot instead of quietly widening access. The
        wildcard stays available for a genuinely open API, but only with
        CORS_ALLOW_CREDENTIALS=false, because the dangerous thing is the
        combination and not either half.
        """
        if "*" in self.cors_allow_origins and self.cors_allow_credentials:
            raise ValueError(
                "CORS_ALLOW_ORIGINS contains '*' while CORS_ALLOW_CREDENTIALS "
                "is true: that lets any origin call this API as the signed-in "
                "operator. List origins explicitly, or set "
                "CORS_ALLOW_CREDENTIALS=false to opt into an open, "
                "credential-free API."
            )
        return self

    @property
    def gemini_live(self) -> bool:
        return bool(self.gemini_api_key)

    @property
    def tavily_live(self) -> bool:
        return bool(self.tavily_api_key)

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.recordings_dir.mkdir(parents=True, exist_ok=True)
        self.documents_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings
