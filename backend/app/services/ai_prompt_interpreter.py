from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from app.lab_runtime.yaml_validator import ALLOWED_IMAGE_PREFIXES, ALLOWED_KINDS


FRR_IMAGE = "frrouting/frr:latest"
LINUX_IMAGE = "alpine:latest"
FRIENDLY_INCOMPLETE_MESSAGE = (
    "The AI provider returned incomplete output and the request could not be safely interpreted. "
    "Try one of the example prompts."
)


@dataclass(frozen=True)
class PromptInterpretation:
    intent: str | None
    scaffold: dict[str, Any] | None
    errors: list[str]


class NaturalLanguagePromptInterpreter:
    def interpret(self, prompt: str, raw_plan: dict[str, Any] | None = None) -> PromptInterpretation:
        lowered = prompt.lower()
        unsafe_errors = self._unsafe_request_errors(lowered, raw_plan or {})
        if unsafe_errors:
            return PromptInterpretation(intent=None, scaffold=None, errors=unsafe_errors)

        if self._is_ospf(lowered):
            return PromptInterpretation("ospf", self.two_router_ospf_plan(), [])
        if self._is_bgp(lowered):
            return PromptInterpretation("bgp", self.two_router_ebgp_plan(), [])
        if self._is_static(lowered):
            return PromptInterpretation("static", self.static_routing_plan(), [])
        if self._is_linux(lowered):
            return PromptInterpretation("linux", self.basic_linux_plan(), [])
        return PromptInterpretation(None, None, [FRIENDLY_INCOMPLETE_MESSAGE])

    def normalize(self, prompt: str, raw_plan: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
        interpretation = self.interpret(prompt, raw_plan)
        if interpretation.errors and interpretation.scaffold is None:
            return raw_plan, interpretation.errors

        if interpretation.scaffold is None:
            return self._normalize_safe_defaults(raw_plan), []

        merged = deepcopy(interpretation.scaffold)
        for key in ("title", "description", "student_instructions", "hints"):
            value = raw_plan.get(key)
            if isinstance(value, str) and value.strip():
                merged[key] = value.strip()
        safety_notes = raw_plan.get("safety_notes")
        if isinstance(safety_notes, list) and safety_notes:
            merged["safety_notes"] = [str(item) for item in safety_notes if str(item).strip()]
        elif isinstance(safety_notes, str) and safety_notes.strip():
            merged["safety_notes"] = [safety_notes.strip()]
        return self._normalize_safe_defaults(merged), []

    @staticmethod
    def basic_linux_plan() -> dict[str, Any]:
        return {
            "lab_name": "basic-linux-uname",
            "title": "Basic Linux Uname Verification Lab",
            "description": "One Alpine Linux host for a simple uname verification exercise.",
            "category": "Linux",
            "difficulty": "Easy",
            "estimated_cpu": 1,
            "estimated_memory_mb": 512,
            "estimated_duration_minutes": 20,
            "nodes": [{"name": "host1", "kind": "linux", "role": "host", "image": LINUX_IMAGE}],
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
                    "name": "Check Linux uname",
                    "target_node": "host1",
                    "command": "uname",
                    "parser_type": "SIMPLE_TEXT",
                    "assertion_type": "CONTAINS",
                    "expected_value": "Linux",
                    "timeout_seconds": 10,
                    "is_active": True,
                }
            ],
            "student_instructions": "Start the lab, wait for the host to be ready, then run verification.",
            "hints": "The uname output should contain Linux.",
            "safety_notes": ["Uses one allowlisted Alpine Linux node and no host mounts."],
        }

    @staticmethod
    def two_router_ospf_plan() -> dict[str, Any]:
        plan = _two_router_base(
            "two-router-frr-ospf-area0",
            "Two Router FRR OSPF Area 0 Lab",
            "Simple FRR OSPF adjacency lab.",
            "OSPF",
        )
        plan["protocols"]["ospf"] = {"enabled": True, "area": "0", "nodes": ["r1", "r2"]}
        plan["verification_rules"] = [
            {
                "name": "Check OSPF neighbor",
                "target_node": "r1",
                "command": "show ip ospf neighbor",
                "parser_type": "SIMPLE_TEXT",
                "assertion_type": "CONTAINS",
                "expected_value": "Full",
                "timeout_seconds": 10,
                "is_active": True,
            }
        ]
        plan["student_instructions"] = "Start the lab and verify that r1 forms an OSPF Full adjacency with r2."
        plan["hints"] = "Use show ip ospf neighbor on r1 and look for Full state."
        plan["safety_notes"] = ["Two allowlisted FRR containers, one private point-to-point link, OSPF area 0."]
        return plan

    @staticmethod
    def two_router_ebgp_plan() -> dict[str, Any]:
        plan = _two_router_base(
            "two-router-frr-ebgp",
            "Two Router FRR eBGP Lab",
            "Simple two-router eBGP neighbor lab.",
            "BGP",
        )
        plan["protocols"]["bgp"] = {
            "enabled": True,
            "sessions": [
                {"local_node": "r1", "local_as": 65001, "peer_node": "r2", "peer_as": 65002},
                {"local_node": "r2", "local_as": 65002, "peer_node": "r1", "peer_as": 65001},
            ],
        }
        plan["verification_rules"] = [
            {
                "name": "Check BGP neighbor",
                "target_node": "r1",
                "command": "show bgp summary",
                "parser_type": "SIMPLE_TEXT",
                "assertion_type": "BGP_NEIGHBOR_ESTABLISHED",
                "expected_value": "Established",
                "timeout_seconds": 10,
                "is_active": True,
            }
        ]
        plan["student_instructions"] = "Start the lab and verify that r1 forms an eBGP session with r2."
        plan["hints"] = "Use show bgp summary on r1 and look for Established."
        plan["safety_notes"] = ["Two allowlisted FRR containers, one private point-to-point link, AS 65001 and 65002."]
        return plan

    @staticmethod
    def static_routing_plan() -> dict[str, Any]:
        plan = _two_router_base(
            "two-router-frr-static-routing",
            "Two Router FRR Static Routing Lab",
            "Simple two-router static route lab using FRR containers.",
            "Linux",
        )
        plan["protocols"]["static_routes"] = [
            {"node": "r1", "prefix": "10.0.2.0/24", "next_hop": "10.0.12.2"},
            {"node": "r2", "prefix": "10.0.1.0/24", "next_hop": "10.0.12.1"},
        ]
        plan["verification_rules"] = [
            {
                "name": "Check static route",
                "target_node": "r1",
                "command": "show ip route",
                "parser_type": "SIMPLE_TEXT",
                "assertion_type": "ROUTE_EXISTS",
                "expected_value": "10.0.2.0/24",
                "timeout_seconds": 10,
                "is_active": True,
            }
        ]
        plan["student_instructions"] = "Start the lab and verify that r1 has a route toward r2's remote subnet."
        plan["hints"] = "Check show ip route on r1 for 10.0.2.0/24."
        plan["safety_notes"] = ["Static routing scaffold uses private addressing and allowlisted FRR images."]
        return plan

    @staticmethod
    def _normalize_safe_defaults(plan: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(plan)
        if "protocols" not in normalized or not isinstance(normalized.get("protocols"), dict):
            normalized["protocols"] = {
                "static_routes": [],
                "ospf": {"enabled": False, "area": "0", "nodes": []},
                "bgp": {"enabled": False, "sessions": []},
            }
        normalized.setdefault("links", [])
        normalized.setdefault("addressing", [])
        normalized.setdefault("startup_configs", [])
        normalized.setdefault("verification_rules", [])
        normalized.setdefault("safety_notes", ["AI output was normalized with safe defaults."])
        normalized.setdefault("difficulty", "Easy")
        normalized.setdefault("estimated_duration_minutes", 30)
        nodes = normalized.get("nodes")
        if isinstance(nodes, list):
            for node in nodes:
                if not isinstance(node, dict):
                    continue
                kind = node.get("kind")
                if kind == "linux" and not node.get("image"):
                    node["image"] = LINUX_IMAGE
                if kind == "frr" and not node.get("image"):
                    node["image"] = FRR_IMAGE
                if not node.get("role"):
                    node["role"] = "router" if kind == "frr" else "host"
        for rule in normalized.get("verification_rules", []):
            if isinstance(rule, dict):
                rule.setdefault("parser_type", "SIMPLE_TEXT")
                rule.setdefault("timeout_seconds", 10)
                rule.setdefault("is_active", True)
        return normalized

    @staticmethod
    def _unsafe_request_errors(lowered_prompt: str, raw_plan: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        unsafe_terms = ["privileged", "host mount", "host path", "/var/run/docker.sock", "external network", "host network"]
        if any(term in lowered_prompt for term in unsafe_terms):
            errors.append("Prompt requests unsafe lab behavior that is not allowed in the MVP.")
        unsupported_terms = ["iosv", "cisco", "mikrotik", "chr", "sonic", "vyos", "vrnetlab"]
        if any(term in lowered_prompt for term in unsupported_terms):
            errors.append("Prompt requests unsupported vendor images or node kinds for the MVP.")
        if _raw_plan_has_unsafe_fields(raw_plan):
            errors.append("AI output included unsupported images, node kinds, privileged mode, mounts, or external networks.")
        return errors

    @staticmethod
    def _is_ospf(lowered: str) -> bool:
        return "ospf" in lowered

    @staticmethod
    def _is_bgp(lowered: str) -> bool:
        return "bgp" in lowered or "ebgp" in lowered or "ibgp" in lowered

    @staticmethod
    def _is_static(lowered: str) -> bool:
        return "static" in lowered and ("route" in lowered or "routing" in lowered)

    @staticmethod
    def _is_linux(lowered: str) -> bool:
        return "linux" in lowered or "alpine" in lowered or "uname" in lowered


def _two_router_base(lab_name: str, title: str, description: str, category: str) -> dict[str, Any]:
    return {
        "lab_name": lab_name,
        "title": title,
        "description": description,
        "category": category,
        "difficulty": "Easy",
        "estimated_cpu": 2,
        "estimated_memory_mb": 512,
        "estimated_duration_minutes": 30,
        "nodes": [
            {"name": "r1", "kind": "frr", "role": "router", "image": FRR_IMAGE},
            {"name": "r2", "kind": "frr", "role": "router", "image": FRR_IMAGE},
        ],
        "links": [{"endpoints": ["r1:eth1", "r2:eth1"], "subnet": "10.0.12.0/30"}],
        "addressing": [
            {"node": "r1", "interface": "eth1", "ipv4": "10.0.12.1/30"},
            {"node": "r2", "interface": "eth1", "ipv4": "10.0.12.2/30"},
        ],
        "protocols": {
            "static_routes": [],
            "ospf": {"enabled": False, "area": "0", "nodes": []},
            "bgp": {"enabled": False, "sessions": []},
        },
        "startup_configs": [],
        "verification_rules": [],
        "student_instructions": "Start the lab and run verification.",
        "hints": "Wait until both FRR nodes are running before verification.",
        "safety_notes": ["Uses allowlisted FRR images and private addressing."],
    }


def _raw_plan_has_unsafe_fields(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            lowered_key = str(key).lower()
            if lowered_key in {"privileged", "mounts", "binds", "host_network", "network-mode"}:
                return True
            if lowered_key == "kind" and isinstance(item, str) and item not in ALLOWED_KINDS:
                return True
            if lowered_key == "image" and isinstance(item, str):
                if not item.startswith(ALLOWED_IMAGE_PREFIXES) or "vrnetlab" in item.lower():
                    return True
            if _raw_plan_has_unsafe_fields(item):
                return True
    if isinstance(value, list):
        return any(_raw_plan_has_unsafe_fields(item) for item in value)
    if isinstance(value, str):
        lowered = value.lower()
        return any(term in lowered for term in ["vrnetlab", "/var/run/docker.sock", "host mount", "privileged: true"])
    return False
