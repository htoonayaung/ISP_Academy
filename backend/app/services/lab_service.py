import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.adapters.containerlab_adapter import ContainerlabAdapter
from app.lab_runtime.directory_manager import LabDirectoryManager
from app.models.lab_instance import LabEvent, LabInstance, LabInstanceStatus, LabNode
from app.models.user import User, UserRole
from app.repositories.lab_templates import LabTemplateRepository
from app.repositories.labs import LabRepository
from app.schemas.lab_instance import LabCreate, LabStatusRead


class LabService:
    def __init__(
        self,
        repository: LabRepository,
        template_repository: LabTemplateRepository,
        directory_manager: LabDirectoryManager | None = None,
        adapter: ContainerlabAdapter | None = None,
    ) -> None:
        self.repository = repository
        self.template_repository = template_repository
        self.directory_manager = directory_manager or LabDirectoryManager()
        self.adapter = adapter or ContainerlabAdapter()

    async def create_lab(self, actor: User, data: LabCreate) -> LabInstance:
        template = await self.template_repository.get_by_id(data.template_id)
        if template is None or not template.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active lab template not found")

        lab_id = uuid.uuid4()
        directory = self.directory_manager.create_instance_directory(lab_id)
        lab = LabInstance(
            id=lab_id,
            template_id=template.id,
            owner_id=actor.id,
            status=LabInstanceStatus.CREATED.value,
            lab_name=self.directory_manager.lab_name(template.slug, lab_id),
            lab_directory=str(directory),
        )
        rendered_yaml = self._render_lab_yaml(template.containerlab_yaml, lab.lab_name)
        self.adapter.save_lab_file(lab, rendered_yaml)

        try:
            created = await self.repository.create(lab)
            await self.repository.add_event(
                LabEvent(
                    lab_instance_id=lab.id,
                    event_type="LAB_CREATED",
                    message="Lab instance created from active template",
                    created_by=actor.id,
                )
            )
            await self.repository.commit()
            await self.repository.refresh(created)
            return created
        except IntegrityError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Lab name already exists") from exc

    async def list_labs(self, actor: User) -> list[LabInstance]:
        if actor.role in {UserRole.ADMIN, UserRole.INSTRUCTOR}:
            return await self.repository.list_all()
        return await self.repository.list_by_owner(actor.id)

    async def get_lab(self, actor: User, lab_id: uuid.UUID) -> LabInstance:
        lab = await self.repository.get_by_id(lab_id)
        if lab is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab not found")
        self._require_lab_access(actor, lab)
        return lab

    async def start_lab(self, actor: User, lab_id: uuid.UUID) -> LabInstance:
        lab = await self.get_lab(actor, lab_id)
        if lab.status in {
            LabInstanceStatus.STARTING.value,
            LabInstanceStatus.RUNNING.value,
            LabInstanceStatus.STOPPING.value,
            LabInstanceStatus.DESTROYING.value,
            LabInstanceStatus.DESTROYED.value,
        }:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Lab cannot be started from current state")
        lab.status = LabInstanceStatus.STARTING.value
        lab.last_error = None
        await self.repository.add_event(
            LabEvent(
                lab_instance_id=lab.id,
                event_type="LAB_START_QUEUED",
                message="Lab start queued",
                created_by=actor.id,
            )
        )
        await self.repository.commit()
        await self.repository.refresh(lab)
        from app.workers.lab_tasks import start_lab_task

        start_lab_task.delay(str(lab.id), str(actor.id))
        return lab

    async def stop_lab(self, actor: User, lab_id: uuid.UUID) -> LabInstance:
        lab = await self.get_lab(actor, lab_id)
        if lab.status != LabInstanceStatus.RUNNING.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only running labs can be stopped")
        lab.status = LabInstanceStatus.STOPPING.value
        await self.repository.add_event(
            LabEvent(
                lab_instance_id=lab.id,
                event_type="LAB_STOP_QUEUED",
                message="Lab stop queued",
                created_by=actor.id,
            )
        )
        await self.repository.commit()
        await self.repository.refresh(lab)
        from app.workers.lab_tasks import stop_lab_task

        stop_lab_task.delay(str(lab.id), str(actor.id))
        return lab

    async def destroy_lab(self, actor: User, lab_id: uuid.UUID) -> LabInstance:
        lab = await self.get_lab(actor, lab_id)
        if lab.status in {LabInstanceStatus.DESTROYING.value, LabInstanceStatus.DESTROYED.value}:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Lab cannot be destroyed from current state")
        lab.status = LabInstanceStatus.DESTROYING.value
        await self.repository.add_event(
            LabEvent(
                lab_instance_id=lab.id,
                event_type="LAB_DESTROY_QUEUED",
                message="Lab destroy queued",
                created_by=actor.id,
            )
        )
        await self.repository.commit()
        await self.repository.refresh(lab)
        from app.workers.lab_tasks import destroy_lab_task

        destroy_lab_task.delay(str(lab.id), str(actor.id))
        return lab

    async def list_nodes(self, actor: User, lab_id: uuid.UUID) -> list[LabNode]:
        lab = await self.get_lab(actor, lab_id)
        return await self.repository.list_nodes(lab.id)

    async def list_events(self, actor: User, lab_id: uuid.UUID) -> list[LabEvent]:
        lab = await self.get_lab(actor, lab_id)
        events = await self.repository.list_events(lab.id)
        if actor.role == UserRole.STUDENT:
            return [self._student_safe_event(event) for event in events]
        return events

    def shape_lab_status(self, actor: User, lab: LabInstance) -> LabStatusRead:
        last_error = lab.last_error
        if actor.role == UserRole.STUDENT and last_error:
            last_error = "Lab operation failed. Ask an instructor to review lab events."
        return LabStatusRead(id=lab.id, status=lab.status, last_error=last_error)

    async def set_failed(self, lab: LabInstance, message: str, stdout: str | None, stderr: str | None) -> None:
        lab.status = LabInstanceStatus.FAILED.value
        lab.last_error = message
        await self.repository.add_event(
            LabEvent(
                lab_instance_id=lab.id,
                event_type="LAB_FAILED",
                message=message,
                stdout=stdout,
                stderr=stderr,
            )
        )
        await self.repository.commit()

    @staticmethod
    def _require_lab_access(actor: User, lab: LabInstance) -> None:
        if actor.role in {UserRole.ADMIN, UserRole.INSTRUCTOR}:
            return
        if lab.owner_id == actor.id:
            return
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    @staticmethod
    def _student_safe_event(event: LabEvent) -> LabEvent:
        return LabEvent(
            id=event.id,
            lab_instance_id=event.lab_instance_id,
            event_type=event.event_type,
            message=LabService._student_safe_message(event),
            stdout=None,
            stderr=None,
            created_by=event.created_by,
            created_at=event.created_at,
        )

    @staticmethod
    def _student_safe_message(event: LabEvent) -> str:
        if event.event_type == "LAB_FAILED":
            return "Lab operation failed. Ask an instructor to review details."
        return event.message

    @staticmethod
    def _render_lab_yaml(raw_yaml: str, lab_name: str) -> str:
        import yaml

        document = yaml.safe_load(raw_yaml)
        document["name"] = lab_name
        return yaml.safe_dump(document, sort_keys=False)


def utc_now() -> datetime:
    return datetime.now(UTC)
