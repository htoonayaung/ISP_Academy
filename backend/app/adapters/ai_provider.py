import json
from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.core.config import Settings


AI_LAB_BUILDER_SYSTEM_PROMPT = """You generate safe ISP Academy training labs.
Return strict JSON only. Do not include markdown.
Supported node kinds: linux, frr.
Allowed images: alpine:latest, frrouting/frr:latest.
Maximum nodes: 6. Maximum links: 10. Maximum verification rules: 10.
Do not use host mounts, privileged containers, host network, external networks, shell scripts, SSH targets, production IP targets, or unsupported vendors.
Supported labs: basic Linux connectivity, static routing, OSPF single area, eBGP two-router, iBGP.
Verification parser_type must be SIMPLE_TEXT.
Allowed assertion_type values: CONTAINS, NOT_CONTAINS, EQUALS, EXIT_CODE_ZERO, BGP_NEIGHBOR_ESTABLISHED, ROUTE_EXISTS.
Use beginner-friendly names and instructions."""


class AIProvider(ABC):
    @abstractmethod
    async def generate_lab_plan(self, prompt: str) -> dict[str, Any]:
        raise NotImplementedError


class DisabledAIProvider(AIProvider):
    async def generate_lab_plan(self, prompt: str) -> dict[str, Any]:
        raise RuntimeError("AI Lab Builder is disabled")


class MockAIProvider(AIProvider):
    async def generate_lab_plan(self, prompt: str) -> dict[str, Any]:
        lower_prompt = prompt.lower()
        if "bgp" in lower_prompt:
            return _mock_bgp_plan()
        if "ospf" in lower_prompt:
            return _mock_ospf_plan()
        return _mock_linux_plan()


class OpenAICompatibleProvider(AIProvider):
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def generate_lab_plan(self, prompt: str) -> dict[str, Any]:
        if not self.settings.ai_api_base_url or not self.settings.ai_api_key or not self.settings.ai_model:
            raise RuntimeError("AI provider is not configured")

        payload = {
            "model": self.settings.ai_model,
            "messages": [
                {"role": "system", "content": AI_LAB_BUILDER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": self.settings.ai_max_tokens,
            "response_format": {"type": "json_object"},
        }
        async with httpx.AsyncClient(timeout=self.settings.ai_request_timeout_seconds) as client:
            response = await client.post(
                f"{self.settings.ai_api_base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {self.settings.ai_api_key}"},
                json=payload,
            )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)


def build_ai_provider(settings: Settings) -> AIProvider:
    if not settings.ai_lab_builder_enabled:
        return DisabledAIProvider()
    if settings.ai_provider == "mock":
        return MockAIProvider()
    return OpenAICompatibleProvider(settings)


def _mock_linux_plan() -> dict[str, Any]:
    return {
        "lab_name": "basic-linux-ai",
        "title": "AI Basic Linux Connectivity",
        "description": "One Alpine host lab generated as a safe AI preview.",
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
                "name": "Check Linux kernel",
                "target_node": "host1",
                "command": "uname",
                "parser_type": "SIMPLE_TEXT",
                "assertion_type": "CONTAINS",
                "expected_value": "Linux",
                "timeout_seconds": 10,
                "is_active": True,
            }
        ],
        "student_instructions": "Start the lab and run verification.",
        "hints": "The uname command should include Linux.",
        "safety_notes": ["Uses one allowlisted Alpine Linux node."],
    }


def _mock_bgp_plan() -> dict[str, Any]:
    plan = _mock_linux_plan()
    plan.update(
        {
            "lab_name": "basic-ebgp-ai",
            "title": "AI Two Router eBGP",
            "description": "Two FRR routers connected by one eBGP link.",
            "category": "BGP",
            "nodes": [
                {"name": "r1", "kind": "frr", "role": "router", "image": "frrouting/frr:latest"},
                {"name": "r2", "kind": "frr", "role": "router", "image": "frrouting/frr:latest"},
            ],
            "links": [{"endpoints": ["r1:eth1", "r2:eth1"], "subnet": "10.0.12.0/30"}],
            "addressing": [
                {"node": "r1", "interface": "eth1", "ipv4": "10.0.12.1/30"},
                {"node": "r2", "interface": "eth1", "ipv4": "10.0.12.2/30"},
            ],
            "protocols": {
                "static_routes": [],
                "ospf": {"enabled": False, "area": "0", "nodes": []},
                "bgp": {
                    "enabled": True,
                    "sessions": [
                        {"local_node": "r1", "local_as": 65001, "peer_node": "r2", "peer_as": 65002},
                        {"local_node": "r2", "local_as": 65002, "peer_node": "r1", "peer_as": 65001},
                    ],
                },
            },
            "verification_rules": [
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
            ],
        }
    )
    return plan


def _mock_ospf_plan() -> dict[str, Any]:
    plan = _mock_bgp_plan()
    plan["lab_name"] = "basic-ospf-ai"
    plan["title"] = "AI Basic OSPF"
    plan["category"] = "OSPF"
    plan["protocols"]["bgp"] = {"enabled": False, "sessions": []}
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
    return plan
