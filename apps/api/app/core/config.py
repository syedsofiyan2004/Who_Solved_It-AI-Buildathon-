from functools import lru_cache
from typing import Annotated
from typing import Self
from uuid import uuid4

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = Field(default="development", alias="APP_ENV")
    app_name: str = Field(
        default="Technical Knowledge and Expert Discovery Platform",
        alias="APP_NAME",
    )
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    web_url: str = Field(default="http://localhost:5173", alias="WEB_URL")
    api_url: str = Field(default="http://localhost:8000", alias="API_URL")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    database_url: str = Field(alias="DATABASE_URL")

    jwt_secret: str = Field(alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=60, ge=5, le=1440, alias="JWT_EXPIRE_MINUTES")
    jwt_issuer: str = Field(default="knowledge-platform-api", alias="JWT_ISSUER")
    jwt_audience: str = Field(default="knowledge-platform-web", alias="JWT_AUDIENCE")

    aws_region: str = Field(default="", alias="AWS_REGION")
    aws_profile: str = Field(default="", alias="AWS_PROFILE")
    bedrock_embedding_model_id: str = Field(default="", alias="BEDROCK_EMBEDDING_MODEL_ID")
    bedrock_embedding_provider: str = Field(default="auto", alias="BEDROCK_EMBEDDING_PROVIDER")
    bedrock_embedding_dimensions: int | None = Field(default=None, ge=1, le=4096, alias="BEDROCK_EMBEDDING_DIMENSIONS")
    bedrock_embeddings_enabled: bool = Field(default=False, alias="BEDROCK_EMBEDDINGS_ENABLED")
    bedrock_chat_model_id: str = Field(default="", alias="BEDROCK_CHAT_MODEL_ID")
    bedrock_generation_max_tokens: int = Field(default=500, ge=64, le=2048, alias="BEDROCK_GENERATION_MAX_TOKENS")
    rag_max_context_solutions: int = Field(default=3, ge=1, le=5, alias="RAG_MAX_CONTEXT_SOLUTIONS")

    search_result_limit: int = Field(default=10, ge=1, le=20, alias="SEARCH_RESULT_LIMIT")
    search_similarity_threshold: float | None = Field(
        default=0.35,
        ge=0,
        le=1,
        alias="SEARCH_SIMILARITY_THRESHOLD",
    )
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
    rate_limit_search_per_minute: int = Field(default=30, ge=1, alias="RATE_LIMIT_SEARCH_PER_MINUTE")
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

    @field_validator("search_similarity_threshold", mode="before")
    @classmethod
    def parse_optional_float(cls, value):
        if value == "":
            return None
        return value

    @model_validator(mode="after")
    def validate_required_settings(self) -> Self:
        if self.app_env != "development" and self.jwt_secret.startswith("replace-with"):
            raise ValueError("JWT_SECRET must be changed outside development.")

        if self.rag_enabled:
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
                joined = ", ".join(missing)
                raise ValueError(f"RAG_ENABLED requires Bedrock settings: {joined}.")

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
        if self.bedrock_embedding_provider not in {"auto", "amazon_titan", "cohere"}:
            raise ValueError("BEDROCK_EMBEDDING_PROVIDER must be auto, amazon_titan, or cohere.")

        return self

    @property
    def bedrock_status(self) -> str:
        if not self.rag_enabled:
            return "disabled_until_configured"
        return "configured"

    @property
    def embedding_status(self) -> str:
        return "configured" if self.bedrock_embeddings_enabled else "disabled_until_configured"

    @staticmethod
    def new_request_id() -> str:
        return str(uuid4())


@lru_cache
def get_settings() -> Settings:
    return Settings()
