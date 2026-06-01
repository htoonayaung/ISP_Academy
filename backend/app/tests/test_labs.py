import pytest
from httpx import AsyncClient

from app.models.lab_template import LabTemplate


@pytest.mark.asyncio
async def test_student_can_create_lab_from_active_template(
    client: AsyncClient,
    auth_header,
    student_token: str,
    active_template: LabTemplate,
) -> None:
    response = await client.post(
        "/api/v1/labs",
        headers=auth_header(student_token),
        json={"template_id": str(active_template.id)},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["template_id"] == str(active_template.id)
    assert data["status"] == "CREATED"
    assert data["lab_name"].startswith("isp-active-lab-")


@pytest.mark.asyncio
async def test_student_cannot_create_lab_from_inactive_template(
    client: AsyncClient,
    auth_header,
    student_token: str,
    inactive_template: LabTemplate,
) -> None:
    response = await client.post(
        "/api/v1/labs",
        headers=auth_header(student_token),
        json={"template_id": str(inactive_template.id)},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_lab_create_does_not_call_containerlab(
    client: AsyncClient,
    auth_header,
    student_token: str,
    active_template: LabTemplate,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_run(*args, **kwargs):
        raise AssertionError("Lab create must not execute Containerlab")

    monkeypatch.setattr("subprocess.run", fail_run)
    response = await client.post(
        "/api/v1/labs",
        headers=auth_header(student_token),
        json={"template_id": str(active_template.id)},
    )

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_lab_status_nodes_and_events_endpoints(
    client: AsyncClient,
    auth_header,
    student_token: str,
    active_template: LabTemplate,
) -> None:
    create_response = await client.post(
        "/api/v1/labs",
        headers=auth_header(student_token),
        json={"template_id": str(active_template.id)},
    )
    lab_id = create_response.json()["id"]

    status_response = await client.get(f"/api/v1/labs/{lab_id}/status", headers=auth_header(student_token))
    nodes_response = await client.get(f"/api/v1/labs/{lab_id}/nodes", headers=auth_header(student_token))
    events_response = await client.get(f"/api/v1/labs/{lab_id}/events", headers=auth_header(student_token))

    assert status_response.status_code == 200
    assert status_response.json()["status"] == "CREATED"
    assert nodes_response.status_code == 200
    assert nodes_response.json() == []
    assert events_response.status_code == 200
    assert events_response.json()[0]["event_type"] == "LAB_CREATED"
