from app.services.ai_lab_plan_validator import LabPlanValidator


def valid_plan() -> dict:
    return {
        "lab_name": "valid-linux",
        "title": "Valid Linux",
        "description": "A safe lab",
        "category": "Linux",
        "difficulty": "Easy",
        "estimated_cpu": 1,
        "estimated_memory_mb": 512,
        "estimated_duration_minutes": 30,
        "nodes": [{"name": "host1", "kind": "linux", "role": "host", "image": "alpine:latest"}],
        "links": [],
        "addressing": [],
        "protocols": {
            "static_routes": [],
            "ospf": {"enabled": False, "area": "0", "nodes": []},
            "bgp": {"enabled": False, "sessions": []},
        },
        "startup_configs": [],
        "verification_rules": [
            {
                "name": "Check uname",
                "target_node": "host1",
                "command": "uname",
                "parser_type": "SIMPLE_TEXT",
                "assertion_type": "CONTAINS",
                "expected_value": "Linux",
                "timeout_seconds": 10,
                "is_active": True,
            }
        ],
        "student_instructions": "Run verification.",
        "hints": "Use uname.",
        "safety_notes": [],
    }


def test_invalid_lab_plan_is_rejected() -> None:
    outcome = LabPlanValidator().validate_raw({"lab_name": "bad"})

    assert outcome.is_valid is False
    assert outcome.errors


def test_unsupported_image_rejected() -> None:
    plan = valid_plan()
    plan["nodes"][0]["image"] = "evil/image:latest"
    outcome = LabPlanValidator().validate_raw(plan)

    assert outcome.is_valid is False
    assert any("Unsupported image" in error for error in outcome.errors)


def test_too_many_nodes_rejected() -> None:
    plan = valid_plan()
    plan["nodes"] = [
        {"name": f"h{i}", "kind": "linux", "role": "host", "image": "alpine:latest"}
        for i in range(7)
    ]
    outcome = LabPlanValidator().validate_raw(plan)

    assert outcome.is_valid is False


def test_too_many_links_rejected() -> None:
    plan = valid_plan()
    plan["nodes"].append({"name": "host2", "kind": "linux", "role": "host", "image": "alpine:latest"})
    plan["links"] = [{"endpoints": ["host1:eth1", "host2:eth1"]} for _ in range(11)]
    outcome = LabPlanValidator().validate_raw(plan)

    assert outcome.is_valid is False


def test_unsupported_command_rejected() -> None:
    plan = valid_plan()
    plan["verification_rules"][0]["command"] = "curl http://example.com"
    outcome = LabPlanValidator().validate_raw(plan)

    assert outcome.is_valid is False
    assert any("Unsupported AI-generated verification command" in error for error in outcome.errors)
