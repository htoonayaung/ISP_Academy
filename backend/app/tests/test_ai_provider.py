import pytest
import httpx

from app.adapters.ai_provider import (
    AIProviderConfig,
    AIProviderResponseError,
    MockAIProvider,
    OpenAICompatibleProvider,
)


class FakeAsyncClient:
    next_response: httpx.Response

    def __init__(self, timeout: int) -> None:
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        return None

    async def post(self, url: str, headers: dict, json: dict) -> httpx.Response:
        return self.next_response


@pytest.mark.parametrize(
    ("prompt", "expected_category", "expected_kind"),
    [
        ("Create a basic Linux lab", "Linux", "linux"),
        ("Create a BGP lab", "BGP", "frr"),
        ("Create an OSPF lab", "OSPF", "frr"),
    ],
)
async def test_mock_ai_provider_returns_supported_lab_plan(
    prompt: str,
    expected_category: str,
    expected_kind: str,
) -> None:
    plan = await MockAIProvider().generate_lab_plan(prompt)

    assert plan["category"] == expected_category
    assert plan["nodes"][0]["kind"] == expected_kind
    assert len(plan["nodes"]) <= 6
    assert len(plan["links"]) <= 10
    assert len(plan["verification_rules"]) <= 10


async def test_openai_compatible_provider_rejects_missing_choices(monkeypatch) -> None:
    FakeAsyncClient.next_response = httpx.Response(
        200,
        json={"id": "bad-response", "object": "chat.completion"},
    )
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    provider = OpenAICompatibleProvider(
        AIProviderConfig(
            enabled=True,
            provider="openrouter",
            model="test-model",
            base_url="https://provider.test/v1",
            api_key="test-key",
            request_timeout_seconds=5,
            max_tokens=100,
            provider_test_enabled=True,
            daily_preview_limit_per_user=20,
            real_provider_confirmation_required=True,
        )
    )

    with pytest.raises(AIProviderResponseError, match="did not include choices"):
        await provider.generate_lab_plan("Create a Linux lab")


async def test_openai_compatible_provider_reports_rate_limit(monkeypatch) -> None:
    FakeAsyncClient.next_response = httpx.Response(
        status_code=429,
        json={
            "error": {
                "message": "model is temporarily rate-limited upstream",
                "metadata": {"retry_after_seconds": 17},
            }
        },
    )
    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)
    provider = OpenAICompatibleProvider(
        AIProviderConfig(
            enabled=True,
            provider="openrouter",
            model="test-model",
            base_url="https://provider.test/v1",
            api_key="test-key",
            request_timeout_seconds=5,
            max_tokens=100,
            provider_test_enabled=True,
            daily_preview_limit_per_user=20,
            real_provider_confirmation_required=True,
        )
    )

    with pytest.raises(AIProviderResponseError, match="rate limit"):
        await provider.generate_lab_plan("Create a Linux lab")
