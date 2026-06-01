import pytest

from app.adapters.ai_provider import MockAIProvider


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
