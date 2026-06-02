import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import Settings


SUPPORTED_REAL_PROVIDERS = {
    "openai_compatible",
    "gemini_openai_compatible",
    "openrouter",
    "groq",
}

PROVIDER_PRESETS = {
    "gemini_openai_compatible": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "model": "gemini-2.5-flash-lite",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "model": "openrouter/free",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "model": "llama-3.3-70b-versatile",
    },
}

AI_LAB_BUILDER_SYSTEM_PROMPT = """You generate safe ISP Academy training labs.
Return JSON only. Do not use markdown fences. Do not include explanations outside JSON.
The JSON keys must match the LabPlan schema exactly.
Supported categories: Linux, BGP, OSPF.
Supported difficulty values: Easy, Medium, Hard.
Supported node kinds: linux, frr.
Allowed images: alpine:latest, frrouting/frr:latest.
Maximum nodes: 6. Maximum links: 10. Maximum verification rules: 10.
Do not use host mounts, privileged containers, host network, external networks, shell scripts, SSH targets, production IP targets, unsupported vendors, or vrnetlab images.
Supported labs: basic Linux connectivity, static routing, OSPF single area, eBGP two-router, iBGP.
Verification parser_type must be SIMPLE_TEXT.
Allowed assertion_type values: CONTAINS, NOT_CONTAINS, EQUALS, EXIT_CODE_ZERO, BGP_NEIGHBOR_ESTABLISHED, ROUTE_EXISTS.
Use only these verification commands when possible: uname, show bgp summary, show ip bgp summary, show ip ospf neighbor, show ip route, ip route.
Include beginner-friendly student_instructions and hints.
If the request is unsupported, return a valid minimal supported LabPlan JSON and explain the limitation in safety_notes."""


class AIProviderConfigurationError(RuntimeError):
    pass


class AIProviderResponseError(RuntimeError):
    pass


@dataclass(frozen=True)
class AIProviderConfig:
    enabled: bool
    provider: str
    model: str | None
    base_url: str | None
    api_key: str | None
    request_timeout_seconds: int
    max_tokens: int
    provider_test_enabled: bool
    daily_preview_limit_per_user: int
    real_provider_confirmation_required: bool

    @property
    def is_real_provider(self) -> bool:
        return self.provider in SUPPORTED_REAL_PROVIDERS

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key)

    @property
    def base_url_host_only(self) -> str | None:
        if not self.base_url:
            return None
        parsed = urlparse(self.base_url)
        return parsed.netloc or None


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
    def __init__(self, config: AIProviderConfig) -> None:
        self.config = config

    async def generate_lab_plan(self, prompt: str) -> dict[str, Any]:
        self._validate_config()
        payload = {
            "model": self.config.model,
            "messages": [
                {"role": "system", "content": AI_LAB_BUILDER_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": self.config.max_tokens,
            "response_format": {"type": "json_object"},
        }
        async with httpx.AsyncClient(timeout=self.config.request_timeout_seconds) as client:
            response = await client.post(
                f"{self.config.base_url.rstrip('/')}/chat/completions",  # type: ignore[union-attr]
                headers={"Authorization": f"Bearer {self.config.api_key}"},
                json=payload,
            )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        try:
            return parse_ai_json_response(content)
        except ValueError as exc:
            raise AIProviderResponseError(str(exc)) from exc

    def _validate_config(self) -> None:
        missing = []
        if not self.config.base_url:
            missing.append("AI_API_BASE_URL")
        if not self.config.api_key:
            missing.append("AI_API_KEY")
        if not self.config.model:
            missing.append("AI_MODEL")
        if missing:
            raise AIProviderConfigurationError(f"AI provider is missing required config: {', '.join(missing)}")


def build_ai_provider_config(settings: Settings) -> AIProviderConfig:
    provider = (settings.ai_provider or "mock").strip().lower()
    if not settings.ai_lab_builder_enabled:
        provider = "disabled"
    if provider not in {"disabled", "mock", *SUPPORTED_REAL_PROVIDERS}:
        provider = "disabled"

    preset = PROVIDER_PRESETS.get(provider, {})
    base_url = settings.ai_api_base_url or preset.get("base_url")
    model = settings.ai_model or preset.get("model")
    api_key = settings.ai_api_key
    if provider == "mock":
        base_url = None
        model = model or "mock"
        api_key = None

    return AIProviderConfig(
        enabled=settings.ai_lab_builder_enabled,
        provider=provider,
        model=model,
        base_url=base_url,
        api_key=api_key,
        request_timeout_seconds=settings.ai_request_timeout_seconds,
        max_tokens=settings.ai_max_tokens,
        provider_test_enabled=settings.ai_provider_test_enabled,
        daily_preview_limit_per_user=settings.ai_daily_preview_limit_per_user,
        real_provider_confirmation_required=settings.ai_real_provider_confirmation_required,
    )


def build_ai_provider(settings: Settings) -> AIProvider:
    config = build_ai_provider_config(settings)
    if not config.enabled or config.provider == "disabled":
        return DisabledAIProvider()
    if config.provider == "mock":
        return MockAIProvider()
    return OpenAICompatibleProvider(config)


def parse_ai_json_response(content: str) -> dict[str, Any]:
    candidates = [content.strip()]
    fenced = re.search(r"```(?:json)?\s*(.*?)```", content, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        candidates.insert(0, fenced.group(1).strip())
    extracted = _extract_json_object(content)
    if extracted:
        candidates.append(extracted)

    seen: set[str] = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        cleaned = _remove_trailing_commas(candidate)
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    raise ValueError("AI provider returned invalid JSON")


def _extract_json_object(content: str) -> str | None:
    start = content.find("{")
    if start < 0:
        return None
    depth = 0
    in_string = False
    escaped = False
    for index, char in enumerate(content[start:], start=start):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return content[start : index + 1]
    return None


def _remove_trailing_commas(content: str) -> str:
    return re.sub(r",\s*([}\]])", r"\1", content)


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
