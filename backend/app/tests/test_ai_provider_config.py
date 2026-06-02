from app.adapters.ai_provider import build_ai_provider_config
from app.core.config import Settings


def test_provider_status_config_uses_mock_defaults() -> None:
    settings = Settings(
        AI_LAB_BUILDER_ENABLED=True,
        AI_PROVIDER="mock",
        AI_MODEL="mock",
        POSTGRES_PASSWORD="test",
        JWT_SECRET_KEY="test-secret-key-with-enough-length",
        INITIAL_ADMIN_PASSWORD="TestingAdminPassword123!",
    )

    config = build_ai_provider_config(settings)

    assert config.enabled is True
    assert config.provider == "mock"
    assert config.model == "mock"
    assert config.base_url_host_only is None
    assert config.has_api_key is False


def test_gemini_preset_applies_safe_defaults_without_key_exposure() -> None:
    settings = Settings(
        AI_LAB_BUILDER_ENABLED=True,
        AI_PROVIDER="gemini_openai_compatible",
        AI_API_KEY="server-only-key",
        AI_MODEL=None,
        AI_API_BASE_URL=None,
        POSTGRES_PASSWORD="test",
        JWT_SECRET_KEY="test-secret-key-with-enough-length",
        INITIAL_ADMIN_PASSWORD="TestingAdminPassword123!",
    )

    config = build_ai_provider_config(settings)

    assert config.provider == "gemini_openai_compatible"
    assert config.model == "gemini-2.5-flash-lite"
    assert config.base_url_host_only == "generativelanguage.googleapis.com"
    assert config.has_api_key is True


def test_explicit_base_url_overrides_provider_preset() -> None:
    settings = Settings(
        AI_LAB_BUILDER_ENABLED=True,
        AI_PROVIDER="groq",
        AI_API_BASE_URL="https://proxy.example/v1",
        AI_API_KEY="server-only-key",
        AI_MODEL=None,
        POSTGRES_PASSWORD="test",
        JWT_SECRET_KEY="test-secret-key-with-enough-length",
        INITIAL_ADMIN_PASSWORD="TestingAdminPassword123!",
    )

    config = build_ai_provider_config(settings)

    assert config.model == "llama-3.3-70b-versatile"
    assert config.base_url_host_only == "proxy.example"
