from app.services.ai_lab_plan_validator import LabPlanValidator
from app.services.ai_prompt_interpreter import NaturalLanguagePromptInterpreter


def test_plain_ospf_prompt_scaffold_is_valid() -> None:
    interpreter = NaturalLanguagePromptInterpreter()
    plan, errors = interpreter.normalize(
        "Create a two-router FRR OSPF lab with one area 0 link and an OSPF neighbor verification rule.",
        {},
    )
    outcome = LabPlanValidator().validate_raw(plan)

    assert errors == []
    assert outcome.is_valid is True
    assert outcome.lab_plan is not None
    assert outcome.lab_plan.category == "OSPF"
    assert outcome.lab_plan.verification_rules[0].command == "show ip ospf neighbor"


def test_plain_bgp_prompt_scaffold_is_valid() -> None:
    plan, errors = NaturalLanguagePromptInterpreter().normalize(
        "Create a two-router FRR eBGP lab with a neighbor verification rule.",
        {},
    )
    outcome = LabPlanValidator().validate_raw(plan)

    assert errors == []
    assert outcome.is_valid is True
    assert outcome.lab_plan is not None
    assert outcome.lab_plan.category == "BGP"


def test_plain_linux_prompt_scaffold_is_valid() -> None:
    plan, errors = NaturalLanguagePromptInterpreter().normalize(
        "Create a basic Linux lab with uname verification.",
        {},
    )
    outcome = LabPlanValidator().validate_raw(plan)

    assert errors == []
    assert outcome.is_valid is True
    assert outcome.lab_plan is not None
    assert outcome.lab_plan.nodes[0].image == "alpine:latest"


def test_unclear_prompt_stays_invalid_with_friendly_message() -> None:
    plan, errors = NaturalLanguagePromptInterpreter().normalize("Make something interesting", {})

    assert plan == {}
    assert errors
    assert "could not be safely interpreted" in errors[0]


def test_unsupported_image_is_not_replaced_by_fallback() -> None:
    plan, errors = NaturalLanguagePromptInterpreter().normalize(
        "Create a Cisco IOSv OSPF lab.",
        {"nodes": [{"name": "r1", "kind": "frr", "role": "router", "image": "vrnetlab/iosv:latest"}]},
    )
    outcome = LabPlanValidator().validate_raw(plan)

    assert errors
    assert outcome.is_valid is False


def test_privileged_or_host_mount_request_is_not_interpreted() -> None:
    plan, errors = NaturalLanguagePromptInterpreter().normalize(
        "Create a Linux lab with privileged containers and host mount.",
        {},
    )

    assert plan == {}
    assert errors
    assert "unsafe" in errors[0]
