from typing import Any

from app.models.lab_instance import LabNode


def parse_containerlab_nodes(lab_id: Any, payload: Any) -> list[LabNode]:
    rows = _extract_rows(payload)
    nodes: list[LabNode] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or row.get("Name") or row.get("node") or row.get("Node") or "")
        if not name:
            continue
        nodes.append(
            LabNode(
                lab_instance_id=lab_id,
                name=name,
                kind=str(row.get("kind") or row.get("Kind") or "unknown"),
                role=row.get("role") or row.get("Role"),
                container_name=row.get("container_name") or row.get("Container Name") or row.get("container"),
                management_ipv4=row.get("ipv4_address") or row.get("IPv4 Address") or row.get("mgmt_ipv4"),
                status=str(row.get("state") or row.get("State") or row.get("status") or "UNKNOWN"),
            )
        )
    return nodes


def _extract_rows(payload: Any) -> list[Any]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("containers", "nodes", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
        for value in payload.values():
            if isinstance(value, list):
                return value
        return [payload]
    return []
