from typing import Any

import yaml
from fastapi import HTTPException, status

from app.models.lab_instance import LabNode
from app.models.user import User, UserRole
from app.schemas.topology import TopologyLink, TopologyNode, TopologyRead


class TopologyParser:
    def parse_containerlab_yaml(
        self,
        raw_yaml: str,
        runtime_nodes: list[LabNode] | None = None,
        actor: User | None = None,
    ) -> TopologyRead:
        try:
            document = yaml.safe_load(raw_yaml)
        except yaml.YAMLError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Could not parse topology.",
            ) from exc
        if not isinstance(document, dict):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Could not parse topology.")
        topology = document.get("topology")
        if not isinstance(topology, dict):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Could not parse topology.")
        raw_nodes = topology.get("nodes", {})
        if not isinstance(raw_nodes, dict):
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Could not parse topology.")

        runtime_by_name = {node.name: node for node in runtime_nodes or []}
        nodes: list[TopologyNode] = []
        warnings: list[str] = []
        for name, payload in raw_nodes.items():
            if not isinstance(name, str):
                warnings.append("A node with non-string name was skipped.")
                continue
            node_payload = payload if isinstance(payload, dict) else {}
            runtime_node = runtime_by_name.get(name)
            nodes.append(
                TopologyNode(
                    id=name,
                    label=name,
                    kind=str(node_payload.get("kind") or runtime_node.kind if runtime_node else node_payload.get("kind") or "unknown"),
                    role=str(node_payload.get("role")) if node_payload.get("role") else None,
                    image=str(node_payload.get("image")) if node_payload.get("image") else None,
                    status=runtime_node.status if runtime_node else None,
                    management_ipv4=runtime_node.management_ipv4 if runtime_node else None,
                    container_name=self._container_name(runtime_node, actor),
                    metadata={},
                )
            )

        known_node_ids = {node.id for node in nodes}
        links = self._parse_containerlab_links(topology.get("links", []), known_node_ids, warnings)
        if not links:
            warnings.append("No topology links were found.")
        return TopologyRead(nodes=nodes, links=links, warnings=warnings)

    def parse_lab_plan(self, raw_plan: dict[str, Any], actor: User | None = None) -> TopologyRead:
        raw_nodes = raw_plan.get("nodes", [])
        raw_links = raw_plan.get("links", [])
        nodes: list[TopologyNode] = []
        warnings: list[str] = []
        if isinstance(raw_nodes, list):
            for node in raw_nodes:
                if not isinstance(node, dict):
                    warnings.append("A malformed LabPlan node was skipped.")
                    continue
                name = str(node.get("name") or "")
                if not name:
                    warnings.append("A LabPlan node without a name was skipped.")
                    continue
                nodes.append(
                    TopologyNode(
                        id=name,
                        label=name,
                        kind=str(node.get("kind") or "unknown"),
                        role=str(node.get("role")) if node.get("role") else None,
                        image=str(node.get("image")) if node.get("image") else None,
                        metadata={},
                    )
                )
        known_node_ids = {node.id for node in nodes}
        links = self._parse_lab_plan_links(raw_links, known_node_ids, warnings)
        if not links:
            warnings.append("No topology links were found.")
        return TopologyRead(nodes=nodes, links=links, warnings=warnings)

    def _parse_containerlab_links(
        self,
        raw_links: Any,
        known_node_ids: set[str],
        warnings: list[str],
    ) -> list[TopologyLink]:
        links: list[TopologyLink] = []
        if raw_links is None:
            return links
        if not isinstance(raw_links, list):
            warnings.append("Topology links field is not a list.")
            return links
        for index, raw_link in enumerate(raw_links):
            endpoints = raw_link.get("endpoints") if isinstance(raw_link, dict) else None
            subnet = raw_link.get("subnet") if isinstance(raw_link, dict) else None
            parsed = self._parse_endpoints(endpoints, known_node_ids, warnings)
            if parsed is None:
                warnings.append(f"Link {index + 1} was skipped.")
                continue
            source, source_interface, target, target_interface = parsed
            links.append(
                TopologyLink(
                    id=f"{source}-{source_interface or 'link'}-{target}-{target_interface or 'link'}",
                    source=source,
                    target=target,
                    source_interface=source_interface,
                    target_interface=target_interface,
                    label=self._link_label(source, source_interface, target, target_interface),
                    subnet=str(subnet) if subnet else None,
                )
            )
        return links

    def _parse_lab_plan_links(
        self,
        raw_links: Any,
        known_node_ids: set[str],
        warnings: list[str],
    ) -> list[TopologyLink]:
        links: list[TopologyLink] = []
        if raw_links is None:
            return links
        if not isinstance(raw_links, list):
            warnings.append("LabPlan links field is not a list.")
            return links
        for index, raw_link in enumerate(raw_links):
            if not isinstance(raw_link, dict):
                warnings.append(f"LabPlan link {index + 1} was skipped.")
                continue
            endpoints = raw_link.get("endpoints")
            parsed = self._parse_endpoints(endpoints, known_node_ids, warnings)
            if parsed is None:
                warnings.append(f"LabPlan link {index + 1} was skipped.")
                continue
            source, source_interface, target, target_interface = parsed
            subnet = raw_link.get("subnet")
            links.append(
                TopologyLink(
                    id=f"{source}-{source_interface or 'link'}-{target}-{target_interface or 'link'}",
                    source=source,
                    target=target,
                    source_interface=source_interface,
                    target_interface=target_interface,
                    label=self._link_label(source, source_interface, target, target_interface),
                    subnet=str(subnet) if subnet else None,
                )
            )
        return links

    def _parse_endpoints(
        self,
        endpoints: Any,
        known_node_ids: set[str],
        warnings: list[str],
    ) -> tuple[str, str | None, str, str | None] | None:
        if not isinstance(endpoints, list) or len(endpoints) != 2:
            warnings.append("A link has invalid endpoints.")
            return None
        first = self._split_endpoint(endpoints[0])
        second = self._split_endpoint(endpoints[1])
        if first is None or second is None:
            warnings.append("A link endpoint could not be parsed.")
            return None
        source, source_interface = first
        target, target_interface = second
        for node_name in (source, target):
            if node_name not in known_node_ids:
                warnings.append(f"Endpoint references unknown node {node_name}.")
        return source, source_interface, target, target_interface

    @staticmethod
    def _split_endpoint(value: Any) -> tuple[str, str | None] | None:
        if not isinstance(value, str) or not value.strip():
            return None
        if ":" not in value:
            return value.strip(), None
        node, interface = value.split(":", 1)
        node = node.strip()
        interface = interface.strip()
        if not node:
            return None
        return node, interface or None

    @staticmethod
    def _link_label(source: str, source_interface: str | None, target: str, target_interface: str | None) -> str:
        left = f"{source}:{source_interface}" if source_interface else source
        right = f"{target}:{target_interface}" if target_interface else target
        return f"{left} <-> {right}"

    @staticmethod
    def _container_name(runtime_node: LabNode | None, actor: User | None) -> str | None:
        if runtime_node is None or actor is None:
            return None
        if actor.role in {UserRole.ADMIN, UserRole.INSTRUCTOR}:
            return runtime_node.container_name
        return None
