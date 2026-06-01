import ipaddress
from dataclasses import dataclass, field

from pydantic import ValidationError

from app.lab_runtime.name_sanitizer import is_safe_interface_name, is_safe_node_name, slugify
from app.lab_runtime.yaml_validator import ALLOWED_IMAGE_PREFIXES, ALLOWED_KINDS, ContainerlabYamlValidator
from app.schemas.ai import LabPlan

ALLOWED_CATEGORIES = {"Linux", "BGP", "OSPF"}
ALLOWED_DIFFICULTIES = {"Easy", "Medium", "Hard"}
ALLOWED_ASSERTIONS = {
    "CONTAINS",
    "NOT_CONTAINS",
    "EQUALS",
    "EXIT_CODE_ZERO",
    "BGP_NEIGHBOR_ESTABLISHED",
    "ROUTE_EXISTS",
}
ALLOWED_COMMANDS = {
    "uname",
    "show bgp summary",
    "show ip bgp summary",
    "show ip ospf neighbor",
    "show ip route",
    "ip route",
}


@dataclass(frozen=True)
class LabPlanValidationOutcome:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    lab_plan: LabPlan | None = None


class LabPlanValidator:
    def __init__(self, yaml_validator: ContainerlabYamlValidator | None = None) -> None:
        self.yaml_validator = yaml_validator or ContainerlabYamlValidator()

    def validate_raw(self, raw_plan: dict) -> LabPlanValidationOutcome:
        errors: list[str] = []
        try:
            lab_plan = LabPlan.model_validate(raw_plan)
        except ValidationError as exc:
            return LabPlanValidationOutcome(False, [error["msg"] for error in exc.errors()])

        errors.extend(self.validate_plan(lab_plan))
        return LabPlanValidationOutcome(not errors, errors, lab_plan)

    def validate_plan(self, plan: LabPlan) -> list[str]:
        errors: list[str] = []
        if slugify(plan.lab_name) == "lab-template":
            errors.append("lab_name must contain safe slug characters")
        if plan.category not in ALLOWED_CATEGORIES:
            errors.append(f"Unsupported category: {plan.category}")
        if plan.difficulty not in ALLOWED_DIFFICULTIES:
            errors.append(f"Unsupported difficulty: {plan.difficulty}")
        if len(plan.nodes) > 6:
            errors.append("Node count exceeds Phase 8 limit of 6")
        if len(plan.links) > 10:
            errors.append("Link count exceeds Phase 8 limit of 10")
        if len(plan.verification_rules) > 10:
            errors.append("Verification rule count exceeds Phase 8 limit of 10")

        node_names: set[str] = set()
        for node in plan.nodes:
            if not is_safe_node_name(node.name):
                errors.append(f"Invalid node name: {node.name}")
            if node.name in node_names:
                errors.append(f"Duplicate node name: {node.name}")
            node_names.add(node.name)
            if node.kind not in ALLOWED_KINDS:
                errors.append(f"Unsupported node kind: {node.kind}")
            if not node.image.startswith(ALLOWED_IMAGE_PREFIXES):
                errors.append(f"Unsupported image for {node.name}: {node.image}")
            if "vrnetlab" in node.image.lower():
                errors.append(f"vrnetlab image is not allowed for {node.name}")

        endpoint_set: set[str] = set()
        for index, link in enumerate(plan.links):
            if len(link.endpoints) != 2:
                errors.append(f"Link {index} must have exactly two endpoints")
                continue
            for endpoint in link.endpoints:
                node_name, interface_name = self._split_endpoint(endpoint, errors)
                if not node_name:
                    continue
                if node_name not in node_names:
                    errors.append(f"Endpoint references unknown node: {endpoint}")
                if not is_safe_interface_name(interface_name):
                    errors.append(f"Endpoint uses invalid interface: {endpoint}")
                if endpoint in endpoint_set:
                    errors.append(f"Duplicate endpoint/interface conflict: {endpoint}")
                endpoint_set.add(endpoint)
            if link.subnet:
                self._validate_network(link.subnet, f"Link {index} subnet", errors)

        for address in plan.addressing:
            if address.node not in node_names:
                errors.append(f"Addressing references unknown node: {address.node}")
            if not is_safe_interface_name(address.interface):
                errors.append(f"Addressing uses invalid interface: {address.node}:{address.interface}")
            self._validate_interface(address.ipv4, f"Addressing {address.node}:{address.interface}", errors)

        for route in plan.protocols.static_routes:
            if route.node not in node_names:
                errors.append(f"Static route references unknown node: {route.node}")
            self._validate_network(route.prefix, f"Static route prefix on {route.node}", errors)
            self._validate_ip(route.next_hop, f"Static route next hop on {route.node}", errors)

        for node in plan.protocols.ospf.nodes:
            if node not in node_names:
                errors.append(f"OSPF references unknown node: {node}")

        for session in plan.protocols.bgp.sessions:
            if session.local_node not in node_names:
                errors.append(f"BGP local node unknown: {session.local_node}")
            if session.peer_node not in node_names:
                errors.append(f"BGP peer node unknown: {session.peer_node}")

        for config in plan.startup_configs:
            if config.node not in node_names:
                errors.append(f"Startup config references unknown node: {config.node}")
            if ".." in config.content:
                errors.append(f"Startup config for {config.node} contains unsafe path traversal text")

        for rule in plan.verification_rules:
            if rule.target_node not in node_names:
                errors.append(f"Verification rule target node unknown: {rule.target_node}")
            if rule.parser_type != "SIMPLE_TEXT":
                errors.append(f"Unsupported parser type: {rule.parser_type}")
            if rule.assertion_type not in ALLOWED_ASSERTIONS:
                errors.append(f"Unsupported assertion type: {rule.assertion_type}")
            if rule.command not in ALLOWED_COMMANDS:
                errors.append(f"Unsupported AI-generated verification command: {rule.command}")

        return errors

    def validate_generated_yaml(self, raw_yaml: str) -> list[str]:
        result = self.yaml_validator.validate(raw_yaml)
        return result.errors

    @staticmethod
    def _split_endpoint(endpoint: str, errors: list[str]) -> tuple[str, str]:
        if ":" not in endpoint:
            errors.append(f"Invalid endpoint format: {endpoint}")
            return "", ""
        return tuple(endpoint.split(":", 1))  # type: ignore[return-value]

    @staticmethod
    def _validate_network(value: str, label: str, errors: list[str]) -> None:
        try:
            network = ipaddress.ip_network(value, strict=False)
        except ValueError:
            errors.append(f"{label} is not a valid subnet: {value}")
            return
        if not network.is_private:
            errors.append(f"{label} must use private addressing: {value}")

    @staticmethod
    def _validate_interface(value: str, label: str, errors: list[str]) -> None:
        try:
            interface = ipaddress.ip_interface(value)
        except ValueError:
            errors.append(f"{label} is not a valid interface address: {value}")
            return
        if not interface.ip.is_private:
            errors.append(f"{label} must use private addressing: {value}")

    @staticmethod
    def _validate_ip(value: str, label: str, errors: list[str]) -> None:
        try:
            address = ipaddress.ip_address(value)
        except ValueError:
            errors.append(f"{label} is not a valid IP address: {value}")
            return
        if not address.is_private:
            errors.append(f"{label} must use private addressing: {value}")
