"""
Application configuration — loads all env vars via pydantic-settings.
Never expose NVIDIA_NIM_API_KEY or SUPABASE_SERVICE_ROLE_KEY in responses or logs.
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- Supabase ---
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str  # NEVER expose
    supabase_jwt_secret: str  # JWT secret for local verification (typically same as service_role_key or from Supabase dashboard)

    # --- Database ---
    database_url: str  # postgresql+asyncpg://...

    # --- NVIDIA NIM ---
    nvidia_nim_api_key: Optional[str] = None  # NEVER expose

    # --- LLM ---
    llm_model: str = "microsoft/phi-4-multimodal-instruct"

    # --- Ollama (local fallback) ---
    ollama_host: Optional[str] = None
    ollama_model: str = "qwen2.5-vl:7b"

    # --- Application ---
    max_upload_size_mb: int = 20
    max_receipts_per_day: int = 20
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def validated_database_url(self) -> str:
        """Ensures the database URL uses the asyncpg driver."""
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def llm_provider(self) -> str:
        if self.ollama_host:
            return "ollama"
        return "nvidia_nim"


settings = Settings()
