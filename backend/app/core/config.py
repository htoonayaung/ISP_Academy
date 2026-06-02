from functools import lru_cache

from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = Field(default="AI-Powered ISP Academy MVP", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    cors_origins: list[str] = Field(
        default=[
            "http://10.0.44.2:3000",
            "http://10.0.44.2:5173",
            "http://localhost:3000",
            "http://localhost:5173",
        ],
        alias="CORS_ORIGINS",
    )

    postgres_host: str = Field(default="postgres", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_user: str = Field(default="isp_academy", alias="POSTGRES_USER")
    postgres_password: str = Field(alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="isp_academy", alias="POSTGRES_DB")

    redis_url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")
    celery_broker_url: str = Field(default="redis://redis:6379/1", alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://redis:6379/2", alias="CELERY_RESULT_BACKEND")

    lab_root: str = Field(default="/opt/isp-academy/lab-storage", alias="LAB_ROOT")
    containerlab_bin: str = Field(default="/usr/bin/containerlab", alias="CONTAINERLAB_BIN")
    containerlab_command_timeout_seconds: int = Field(
        default=120,
        alias="CONTAINERLAB_COMMAND_TIMEOUT_SECONDS",
    )
    lab_event_output_limit: int = Field(default=12000, alias="LAB_EVENT_OUTPUT_LIMIT")

    jwt_secret_key: str = Field(alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=30,
        alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
    )

    initial_admin_email: str = Field(default="admin@example.com", alias="INITIAL_ADMIN_EMAIL")
    initial_admin_username: str = Field(default="admin", alias="INITIAL_ADMIN_USERNAME")
    initial_admin_password: str = Field(alias="INITIAL_ADMIN_PASSWORD")
    initial_admin_full_name: str = Field(default="Initial Admin", alias="INITIAL_ADMIN_FULL_NAME")

    ai_lab_builder_enabled: bool = Field(default=False, alias="AI_LAB_BUILDER_ENABLED")
    ai_provider: str = Field(default="mock", alias="AI_PROVIDER")
    ai_api_base_url: str | None = Field(default=None, alias="AI_API_BASE_URL")
    ai_api_key: str | None = Field(default=None, alias="AI_API_KEY")
    ai_model: str | None = Field(default=None, alias="AI_MODEL")
    ai_request_timeout_seconds: int = Field(default=60, alias="AI_REQUEST_TIMEOUT_SECONDS")
    ai_max_tokens: int = Field(default=4000, alias="AI_MAX_TOKENS")
    ai_daily_preview_limit_per_user: int = Field(default=20, alias="AI_DAILY_PREVIEW_LIMIT_PER_USER")
    ai_provider_test_enabled: bool = Field(default=False, alias="AI_PROVIDER_TEST_ENABLED")
    ai_real_provider_confirmation_required: bool = Field(
        default=True,
        alias="AI_REAL_PROVIDER_CONFIRMATION_REQUIRED",
    )

    demo_setup_enabled: bool = Field(default=True, alias="DEMO_SETUP_ENABLED")
    demo_instructor_username: str = Field(default="demo_instructor", alias="DEMO_INSTRUCTOR_USERNAME")
    demo_instructor_password: str | None = Field(default=None, alias="DEMO_INSTRUCTOR_PASSWORD")
    demo_student_username: str = Field(default="demo_student", alias="DEMO_STUDENT_USERNAME")
    demo_student_password: str | None = Field(default=None, alias="DEMO_STUDENT_PASSWORD")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        return (
            "postgresql+asyncpg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
