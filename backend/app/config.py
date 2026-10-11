import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_BACKEND_DIR / ".env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # Postgres (Alembic + direct DB access)
    database_url: str

    # OpenAI
    openai_api_key: str
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = 1536

    # Server / CORS
    # In .env this is a comma-separated string (e.g. http://localhost:5173).
    # Reading as str avoids pydantic-settings attempting json.loads() on non-JSON strings.
    allowed_origins_raw: str = Field(
        default="http://localhost:5173",
        validation_alias="allowed_origins",
    )

    @property
    def allowed_origins(self) -> list[str]:
        raw = self.allowed_origins_raw.strip()
        if raw.startswith("[") and raw.endswith("]"):
            try:
                import json
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if str(x).strip()]
            except Exception:
                pass
        return [origin.strip() for origin in raw.split(",") if origin.strip()]


settings = Settings()

# Mirror env vars for external SDKs (e.g. OpenAI) that read os.environ directly
os.environ.setdefault("OPENAI_API_KEY", settings.openai_api_key)
