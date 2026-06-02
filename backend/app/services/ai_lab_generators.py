import yaml

from app.lab_runtime.name_sanitizer import slugify
from app.schemas.ai import LabPlan


class ContainerlabYamlGenerator:
    def generate(self, plan: LabPlan) -> str:
        nodes = {}
        for node in plan.nodes:
            node_data = {"kind": node.kind, "image": node.image}
            if node.kind == "linux":
                node_data["cmd"] = "sleep infinity"
            nodes[node.name] = node_data

        links = [{"endpoints": link.endpoints} for link in plan.links]
        document = {
            "name": slugify(plan.lab_name),
            "topology": {
                "nodes": nodes,
                "links": links,
            },
        }
        if not links:
            document["topology"].pop("links")
        return yaml.safe_dump(document, sort_keys=False)


class FRRConfigGenerator:
    def generate(self, plan: LabPlan) -> list[dict]:
        configs: list[dict] = []
        frr_nodes = {node.name for node in plan.nodes if node.kind == "frr"}
        for node_name in sorted(frr_nodes):
            lines = [f"! Generated preview for {node_name}", "frr defaults traditional"]
            for address in plan.addressing:
                if address.node == node_name:
                    lines.extend([f"interface {address.interface}", f" ip address {address.ipv4}", "exit"])
            if plan.protocols.ospf.enabled and node_name in plan.protocols.ospf.nodes:
                lines.extend(["router ospf", f" ospf router-id 1.1.1.{len(configs) + 1}"])
                for address in plan.addressing:
                    if address.node == node_name:
                        lines.append(f" network {address.ipv4} area {plan.protocols.ospf.area}")
                lines.append("exit")
            bgp_sessions = [s for s in plan.protocols.bgp.sessions if s.local_node == node_name]
            if plan.protocols.bgp.enabled and bgp_sessions:
                local_as = bgp_sessions[0].local_as
                lines.append(f"router bgp {local_as}")
                for session in bgp_sessions:
                    peer_ip = self._peer_ip(plan, session.peer_node)
                    if peer_ip:
                        lines.append(f" neighbor {peer_ip} remote-as {session.peer_as}")
                lines.append("exit")
            static_routes = [route for route in plan.protocols.static_routes if route.node == node_name]
            for route in static_routes:
                lines.append(f"ip route {route.prefix} {route.next_hop}")
            configs.append({"node": node_name, "config_type": "frr", "content": "\n".join(lines) + "\n"})
        configs.extend(config.model_dump() for config in plan.startup_configs if config.node not in frr_nodes)
        return configs

    @staticmethod
    def _peer_ip(plan: LabPlan, peer_node: str) -> str | None:
        for address in plan.addressing:
            if address.node == peer_node:
                return address.ipv4.split("/", 1)[0]
        return None


class VerificationRulePreviewGenerator:
    def generate(self, plan: LabPlan) -> list[dict]:
        return [rule.model_dump() for rule in plan.verification_rules]


class LabPreviewExplanationGenerator:
    def generate(self, plan: LabPlan) -> str:
        return (
            f"{plan.title}: {len(plan.nodes)} node(s), {len(plan.links)} link(s), "
            f"{len(plan.verification_rules)} verification rule(s). "
            "AI-generated lab plans must be reviewed before approval."
        )
