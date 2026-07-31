from functools import lru_cache
from typing import Annotated, Self
from uuid import uuid4

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = Field(default="development", alias="APP_ENV")
    app_name: str = Field(default="Minfy Resolve", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    web_url: str = Field(default="http://localhost:5173", alias="WEB_URL")
    api_url: str = Field(default="http://localhost:8000", alias="API_URL")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    database_url: str = Field(alias="DATABASE_URL")

    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=60, ge=5, le=1440, alias="JWT_EXPIRE_MINUTES")
    jwt_issuer: str = Field(default="knowledge-platform-api", alias="JWT_ISSUER")
    jwt_audience: str = Field(default="knowledge-platform-web", alias="JWT_AUDIENCE")

    # AI provider selection. `nvidia` is the zero-infrastructure local/demo path;
    # Legacy provider fields remain supported for older local environment files.
    ai_provider: str = Field(default="disabled", alias="AI_PROVIDER")

    aws_region: str = Field(default="", alias="AWS_REGION")
    aws_profile: str = Field(default="", alias="AWS_PROFILE")
    bedrock_embedding_model_id: str = Field(default="", alias="BEDROCK_EMBEDDING_MODEL_ID")
    bedrock_embedding_provider: str = Field(default="auto", alias="BEDROCK_EMBEDDING_PROVIDER")
    bedrock_embedding_dimensions: int | None = Field(default=None, ge=1, le=4096, alias="BEDROCK_EMBEDDING_DIMENSIONS")
    bedrock_embeddings_enabled: bool = Field(default=False, alias="BEDROCK_EMBEDDINGS_ENABLED")
    bedrock_chat_model_id: str = Field(default="", alias="BEDROCK_CHAT_MODEL_ID")
    bedrock_generation_max_tokens: int = Field(default=500, ge=64, le=4096, alias="BEDROCK_GENERATION_MAX_TOKENS")

    nvidia_api_key: str = Field(default="", alias="NVIDIA_API_KEY")
    nvidia_chat_url: str = Field(default="https://integrate.api.nvidia.com/v1/chat/completions", alias="NVIDIA_CHAT_URL")
    nvidia_chat_model: str = Field(default="openai/gpt-oss-120b", alias="NVIDIA_CHAT_MODEL")
    nvidia_embedding_url: str = Field(default="https://integrate.api.nvidia.com/v1/embeddings", alias="NVIDIA_EMBEDDING_URL")
    nvidia_embedding_model: str = Field(default="nvidia/nemotron-3-embed-1b", alias="NVIDIA_EMBEDDING_MODEL")
    nvidia_embedding_dimensions: int | None = Field(default=2048, ge=1, le=8192, alias="NVIDIA_EMBEDDING_DIMENSIONS")
    nvidia_timeout_seconds: float = Field(default=120.0, ge=5.0, le=180.0, alias="NVIDIA_TIMEOUT_SECONDS")
    nvidia_generation_max_tokens: int = Field(default=1024, ge=64, le=4096, alias="NVIDIA_GENERATION_MAX_TOKENS")

    rag_max_context_solutions: int = Field(default=4, ge=1, le=8, alias="RAG_MAX_CONTEXT_SOLUTIONS")
    search_result_limit: int = Field(default=10, ge=1, le=20, alias="SEARCH_RESULT_LIMIT")
    search_result_threshold: float = Field(default=0.42, ge=0, le=1, alias="SEARCH_RESULT_THRESHOLD")
    rag_enabled: bool = Field(default=False, alias="RAG_ENABLED")

    upload_provider: str = Field(default="local", alias="UPLOAD_PROVIDER")
    upload_directory: str = Field(default="/app/uploads", alias="UPLOAD_DIRECTORY")
    max_upload_size_mb: int = Field(default=10, ge=1, le=50, alias="MAX_UPLOAD_SIZE_MB")
    allowed_upload_types: Annotated[list[str], NoDecode] = Field(
        default=["text/plain", "text/markdown", "application/pdf"],
        alias="ALLOWED_UPLOAD_TYPES",
    )

    cors_allowed_origins: Annotated[list[str], NoDecode] = Field(
        default=["http://localhost:5173"],
        alias="CORS_ALLOWED_ORIGINS",
    )
    rate_limit_search_per_minute: int = Field(default=60, ge=1, alias="RATE_LIMIT_SEARCH_PER_MINUTE")
    rate_limit_auth_per_minute: int = Field(default=10, ge=1, alias="RATE_LIMIT_AUTH_PER_MINUTE")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("cors_allowed_origins", "allowed_upload_types", mode="before")
    @classmethod
    def parse_csv(cls, value):
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def validate_required_settings(self) -> Self:
        if self.app_env != "development" and self.jwt_secret.startswith("replace-with"):
            raise ValueError("JWT_SECRET must be changed outside development.")
        if self.ai_provider not in {"disabled", "nvidia", "bedrock"}:
            raise ValueError("AI_PROVIDER must be disabled, nvidia, or bedrock.")
        if self.bedrock_embedding_provider not in {"auto", "amazon_titan", "cohere"}:
            raise ValueError("BEDROCK_EMBEDDING_PROVIDER must be auto, amazon_titan, or cohere.")

        if self.ai_provider == "nvidia" and self.rag_enabled and not self.nvidia_api_key:
            raise ValueError("RAG_ENABLED with AI_PROVIDER=nvidia requires NVIDIA_API_KEY.")

        if self.effective_ai_provider == "bedrock" and self.rag_enabled:
            missing = [
                name
                for name, value in {
                    "AWS_REGION": self.aws_region,
                    "BEDROCK_EMBEDDING_MODEL_ID": self.bedrock_embedding_model_id,
                    "BEDROCK_CHAT_MODEL_ID": self.bedrock_chat_model_id,
                }.items()
                if not value
            ]
            if missing:
                raise ValueError(f"RAG_ENABLED with AI_PROVIDER=bedrock requires: {', '.join(missing)}.")

        if self.rag_enabled and self.effective_ai_provider == "disabled":
            raise ValueError("RAG_ENABLED requires AI_PROVIDER=nvidia or AI_PROVIDER=bedrock.")

        # Backward-compatible validation for existing provider-specific environments.
        if self.bedrock_embeddings_enabled:
            missing = [
                name
                for name, value in {
                    "AWS_REGION": self.aws_region,
                    "BEDROCK_EMBEDDING_MODEL_ID": self.bedrock_embedding_model_id,
                    "BEDROCK_EMBEDDING_DIMENSIONS": self.bedrock_embedding_dimensions,
                }.items()
                if value in {None, ""}
            ]
            if missing:
                raise ValueError(f"BEDROCK_EMBEDDINGS_ENABLED requires: {', '.join(missing)}.")
        return self

    @property
    def effective_ai_provider(self) -> str:
        """Resolve older provider-specific environments without changing their files."""
        if self.ai_provider != "disabled":
            return self.ai_provider
        if self.bedrock_embeddings_enabled or self.bedrock_embedding_model_id or self.bedrock_chat_model_id:
            return "bedrock"
        return "disabled"

    @property
    def embeddings_enabled(self) -> bool:
        if self.effective_ai_provider == "nvidia":
            return bool(self.nvidia_api_key and self.nvidia_embedding_model)
        if self.effective_ai_provider == "bedrock":
            return bool(self.bedrock_embedding_model_id and (self.bedrock_embeddings_enabled or self.rag_enabled))
        return False

    @property
    def embedding_model_id(self) -> str:
        if self.effective_ai_provider == "nvidia":
            return self.nvidia_embedding_model
        if self.effective_ai_provider == "bedrock":
            return self.bedrock_embedding_model_id
        return ""

    @property
    def chat_model_id(self) -> str:
        if self.effective_ai_provider == "nvidia":
            return self.nvidia_chat_model
        if self.effective_ai_provider == "bedrock":
            return self.bedrock_chat_model_id
        return ""

    @property
    def ai_status(self) -> str:
        if not self.rag_enabled:
            return "disabled_until_configured"
        return "configured" if self.embeddings_enabled and self.chat_model_id else "incomplete_configuration"

    @property
    def bedrock_status(self) -> str:
        return self.ai_status

    @property
    def embedding_status(self) -> str:
        return "configured" if self.embeddings_enabled else "disabled_until_configured"

    @staticmethod
    def new_request_id() -> str:
        return str(uuid4())


@lru_cache
def get_settings() -> Settings:
    return Settings()
