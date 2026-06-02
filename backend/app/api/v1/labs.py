import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.permissions import get_current_user
from app.models.lab_instance import LabEvent, LabInstance, LabNode
from app.models.user import User
from app.repositories.lab_templates import LabTemplateRepository
from app.repositories.labs import LabRepository
from app.schemas.console import ConsoleBatchRequest, ConsoleExecuteRead, ConsoleExecuteRequest, ConsoleNodesRead
from app.schemas.lab_instance import LabCreate, LabEventRead, LabNodeRead, LabRead, LabStatusRead
from app.schemas.topology import TopologyRead
from app.services.console_service import ConsoleService
from app.services.lab_service import LabService
from app.services.topology_parser import TopologyParser

router = APIRouter(tags=["labs"])


def get_lab_service(session: AsyncSession = Depends(get_db_session)) -> LabService:
    return LabService(LabRepository(session), LabTemplateRepository(session))


def get_console_service(session: AsyncSession = Depends(get_db_session)) -> ConsoleService:
    lab_repository = LabRepository(session)
    return ConsoleService(LabService(lab_repository, LabTemplateRepository(session)), lab_repository)


@router.post("", response_model=LabRead, status_code=status.HTTP_201_CREATED)
async def create_lab(
    payload: LabCreate,
    current_user: User = Depends(get_current_user),
    service: LabService = Depends(get_lab_service),
) -> LabInstance:
    return await service.create_lab(current_user, payload)


@router.get("", response_model=list[LabRead])
async def list_labs(
    current_user: User = Depends(get_current_user),
    service: LabService = Depends(get_lab_service),
) -> list[LabInstance]:
    return await service.list_labs(current_user)


@router.get("/{lab_id}", response_model=LabRead)
async def get_lab(
    lab_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: LabService = Depends(get_lab_service),
) -> LabInstance:
    return await service.get_lab(current_user, lab_id)


@router.get("/{lab_id}/topology", response_model=TopologyRead)
async def get_lab_topology(
    lab_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: LabService = Depends(get_lab_service),
) -> TopologyRead:
    lab = await service.get_lab(current_user, lab_id)
    template = await service.template_repository.get_by_id(lab.template_id)
    if template is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab template not found")
    nodes = await service.list_nodes(current_user, lab.id)
    return TopologyParser().parse_containerlab_yaml(template.containerlab_yaml, runtime_nodes=nodes, actor=current_user)


@router.post("/{lab_id}/start", response_model=LabRead)
async def start_lab(
    lab_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: LabService = Depends(get_lab_service),
) -> LabInstance:
    return await service.start_lab(current_user, lab_id)


@router.post("/{lab_id}/stop", response_model=LabRead)
async def stop_lab(
    lab_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: LabService = Depends(get_lab_service),
) -> LabInstance:
    return await service.stop_lab(current_user, lab_id)


@router.post("/{lab_id}/destroy", response_model=LabRead)
async def destroy_lab(
    lab_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: LabService = Depends(get_lab_service),
) -> LabInstance:
    return await service.destroy_lab(current_user, lab_id)


@router.delete("/{lab_id}/hard-delete", status_code=status.HTTP_204_NO_CONTENT)
async def hard_delete_lab(
    lab_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: LabService = Depends(get_lab_service),
) -> None:
    await service.hard_delete_lab(current_user, lab_id)


@router.get("/{lab_id}/status", response_model=LabStatusRead)
async def get_lab_status(
    lab_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: LabService = Depends(get_lab_service),
) -> LabStatusRead:
    lab = await service.get_lab(current_user, lab_id)
    return service.shape_lab_status(current_user, lab)


@router.get("/{lab_id}/nodes", response_model=list[LabNodeRead])
async def list_lab_nodes(
    lab_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: LabService = Depends(get_lab_service),
) -> list[LabNode]:
    return await service.list_nodes(current_user, lab_id)


@router.get("/{lab_id}/console/nodes", response_model=ConsoleNodesRead)
async def list_console_nodes(
    lab_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ConsoleService = Depends(get_console_service),
) -> ConsoleNodesRead:
    return ConsoleNodesRead(nodes=await service.list_console_nodes(current_user, lab_id))


@router.post("/{lab_id}/nodes/{node_id}/console/execute", response_model=ConsoleExecuteRead)
async def execute_console_command(
    lab_id: uuid.UUID,
    node_id: uuid.UUID,
    payload: ConsoleExecuteRequest,
    current_user: User = Depends(get_current_user),
    service: ConsoleService = Depends(get_console_service),
) -> ConsoleExecuteRead:
    return await service.execute(current_user, lab_id, node_id, payload.command)


@router.post("/{lab_id}/nodes/{node_id}/console/batch", response_model=ConsoleExecuteRead)
async def execute_console_batch(
    lab_id: uuid.UUID,
    node_id: uuid.UUID,
    payload: ConsoleBatchRequest,
    current_user: User = Depends(get_current_user),
    service: ConsoleService = Depends(get_console_service),
) -> ConsoleExecuteRead:
    return await service.execute_batch(current_user, lab_id, node_id, payload.commands)


@router.get("/{lab_id}/events", response_model=list[LabEventRead])
async def list_lab_events(
    lab_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: LabService = Depends(get_lab_service),
) -> list[LabEvent]:
    return await service.list_events(current_user, lab_id)
