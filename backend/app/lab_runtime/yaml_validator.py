from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

import yaml

from app.lab_runtime.name_sanitizer import is_safe_interface_name, is_safe_node_name

ALLOWED_KINDS = {"linux", "frr"}
ALLOWED_IMAGE_PREFIXES = (
    "alpine:",
    "busybox:",
    "debian:",
    "ubuntu:",
    "frrouting/frr:",
    "quay.io/frrouting/frr:",
)
FORBIDDEN_NODE_KEYS = {"binds", "mounts", "volumes"}
FORBIDDEN_TOPOLOGY_KEYS = {"kinds"}


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class ContainerlabYamlValidator:
    def validate(self, raw_yaml: str) -> ValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        try:
            document = yaml.safe_load(raw_yaml)
        except yaml.YAMLError as exc:
            return ValidationResult(False, [f"YAML parse error: {exc}"], warnings)

        if not isinstance(document, Mapping):
            return ValidationResult(False, ["Containerlab YAML must be a mapping"], warnings)

        topology = document.get("topology")
        if not isinstance(topology, Mapping):
            errors.append("Missing required topology mapping")
            return ValidationResult(False, errors, warnings)

        if not document.get("name") or not isinstance(document.get("name"), str):
            errors.append("Missing required lab name")

        for key in FORBIDDEN_TOPOLOGY_KEYS:
            if key in topology:
                errors.append(f"Unsupported topology-level key is not allowed in MVP: {key}")

        mgmt = document.get("mgmt")
        if isinstance(mgmt, Mapping):
            if mgmt.get("external-access") is True:
                errors.append("External management access is not allowed")
            if "network" in mgmt:
                warnings.append("Custom management network will be ignored by future runtime policy")

        nodes = topology.get("nodes")
        if not isinstance(nodes, Mapping) or not nodes:
            errors.append("Missing required topology.nodes mapping")
            return ValidationResult(False, errors, warnings)

        node_names = set()
        for node_name, node_data in nodes.items():
            self._validate_node(node_name, node_data, errors)
            if isinstance(node_name, str):
                node_names.add(node_name)

        links = topology.get("links", [])
        if links is not None:
            self._validate_links(links, node_names, errors)

        return ValidationResult(not errors, errors, warnings)

    def _validate_node(self, node_name: Any, node_data: Any, errors: list[str]) -> None:
        if not isinstance(node_name, str) or not is_safe_node_name(node_name):
            errors.append(f"Invalid node name: {node_name}")
            return

        if not isinstance(node_data, Mapping):
            errors.append(f"Node {node_name} must be a mapping")
            return

        kind = node_data.get("kind")
        image = node_data.get("image")

        if kind not in ALLOWED_KINDS:
            errors.append(f"Node {node_name} uses unsupported kind: {kind}")

        if image is not None:
            if not isinstance(image, str):
                errors.append(f"Node {node_name} image must be a string")
            elif not image.startswith(ALLOWED_IMAGE_PREFIXES):
                errors.append(f"Node {node_name} uses non-allowlisted image: {image}")

        if "vrnetlab" in str(image).lower() or "vrnetlab" in str(kind).lower():
            errors.append(f"Node {node_name} uses vrnetlab, which is not allowed in MVP")

        if node_data.get("privileged") is True:
            errors.append(f"Node {node_name} uses privileged mode, which is disabled by default")

        if node_data.get("network-mode") in {"host", "container", "service"}:
            errors.append(f"Node {node_name} uses forbidden network-mode")

        for forbidden_key in FORBIDDEN_NODE_KEYS:
            if forbidden_key in node_data:
                errors.append(f"Node {node_name} defines forbidden host mount key: {forbidden_key}")

        for path_key in ("startup-config", "license", "env-file"):
            value = node_data.get(path_key)
            if isinstance(value, str) and (".." in value or value.startswith("/")):
                errors.append(f"Node {node_name} uses unsafe path in {path_key}")

    def _validate_links(self, links: Any, node_names: set[str], errors: list[str]) -> None:
        if not isinstance(links, list):
            errors.append("topology.links must be a list when provided")
            return

        for index, link in enumerate(links):
            if not isinstance(link, Mapping):
                errors.append(f"Link {index} must be a mapping")
                continue
            endpoints = link.get("endpoints")
            if not isinstance(endpoints, list) or len(endpoints) != 2:
                errors.append(f"Link {index} must define exactly two endpoints")
                continue
            for endpoint in endpoints:
                self._validate_endpoint(endpoint, node_names, errors)

    def _validate_endpoint(self, endpoint: Any, node_names: set[str], errors: list[str]) -> None:
        if not isinstance(endpoint, str) or ":" not in endpoint:
            errors.append(f"Invalid endpoint format: {endpoint}")
            return
        node_name, interface_name = endpoint.split(":", 1)
        if node_name not in node_names:
            errors.append(f"Endpoint references unknown node: {node_name}")
        if not is_safe_interface_name(interface_name):
            errors.append(f"Endpoint uses invalid interface name: {endpoint}")

