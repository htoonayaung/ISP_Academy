import shutil
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi import HTTPException, status

from app.lab_runtime.directory_manager import LabDirectoryManager
from app.models.lab_instance import LabEvent, LabInstance, LabInstanceStatus
from app.models.user import User
from app.repositories.labs import LabRepository
from app.schemas.admin_runtime import (
    RuntimeCleanupRead,
    RuntimeContainerSummary,
    RuntimeLabSummary,
    RuntimeOrphanCandidate,
    RuntimeRecoverRead,
    RuntimeStatusRead,
)


STUCK_THRESHOLD_MINUTES = 10
ALL_LAB_STATUSES = [status.value for status in LabInstanceStatus]
TRANSIENT_STATUSES = {
    LabInstanceStatus.STARTING.value,
    LabInstanceStatus.STOPPING.value,
    LabInstanceStatus.DESTROYING.value,
}


class AdminRuntimeService:
    def __init__(
        self,
        repository: LabRepository,
        directory_manager: LabDirectoryManager | None = None,
        stuck_threshold_minutes: int = STUCK_THRESHOLD_MINUTES,
    ) -> None:
        self.repository = repository
        self.directory_manager = directory_manager or LabDirectoryManager()
        self.stuck_threshold = timedelta(minutes=stuck_threshold_minutes)

    async def get_status(self) -> RuntimeStatusRead:
        labs = await self.repository.list_all()
        nodes_by_lab = await self.repository.list_nodes_by_lab_ids([lab.id for lab in labs])
        summaries = [self._summary(lab, bool(nodes_by_lab.get(lab.id))) for lab in labs]
        labs_by_status = {status_name: [] for status_name in ALL_LAB_STATUSES}
        for summary in summaries:
            labs_by_status.setdefault(summary.status, []).append(summary)
        status_counts = {status_name: len(labs_by_status.get(status_name, [])) for status_name in ALL_LAB_STATUSES}
        stuck_candidates = [summary for summary in summaries if self._is_stuck_summary(summary)]
        demo_labs = [summary for summary in summaries if summary.is_demo]
        orphan_candidates = self._orphan_instance_dirs(labs)
        known_container_count = sum(len(nodes) for nodes in nodes_by_lab.values())
        warnings = [
            "API container does not inspect Docker directly; refresh queues worker-side Containerlab inspection.",
            "Only demo-prefixed runtime cleanup is supported in this MVP phase.",
        ]
        if orphan_candidates:
            warnings.append("Orphan runtime directories are reported read-only; uncertain entries are skipped by cleanup.")
        return RuntimeStatusRead(
            containers=RuntimeContainerSummary(
                source="database-and-worker-refreshed-node-cache",
                known_container_count=known_container_count,
                running_lab_count=status_counts.get(LabInstanceStatus.RUNNING.value, 0),
                message="Docker access remains worker-only; this summary uses DB lab state and cached LabNode data.",
            ),
            status_counts=status_counts,
            labs_by_status=labs_by_status,
            stuck_candidates=stuck_candidates,
            orphan_candidates=orphan_candidates,
            demo_labs=demo_labs,
            warnings=warnings,
        )

    async def refresh(self) -> tuple[int, list[str], list[str]]:
        labs = await self.repository.list_all()
        refreshable_statuses = {
            LabInstanceStatus.STARTING.value,
            LabInstanceStatus.RUNNING.value,
            LabInstanceStatus.STOPPING.value,
            LabInstanceStatus.STOPPED.value,
            LabInstanceStatus.FAILED.value,
        }
        queued = 0
        from app.workers.lab_tasks import refresh_lab_status_task

        for lab in labs:
            if lab.status in refreshable_statuses:
                refresh_lab_status_task.delay(str(lab.id))
                queued += 1
        return (
            queued,
            sorted(refreshable_statuses),
            ["Refresh queued worker-side inspection only; it does not delete or destroy runtime resources."],
        )

    async def recover(self, actor: User, lab_id: uuid.UUID, action: str, confirm: str) -> RuntimeRecoverRead:
        if confirm != "RECOVER_LAB":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Typed confirmation RECOVER_LAB is required")
        lab = await self.repository.get_by_id(lab_id)
        if lab is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab not found")
        if action == "mark_failed":
            return await self._mark_failed(actor, lab)
        if action == "retry_destroy":
            return await self._retry_destroy(actor, lab)
        if action == "force_destroy_demo_only":
            return await self._force_destroy_demo_only(actor, lab)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported recovery action")

    async def cleanup_demo_runtime(self) -> RuntimeCleanupRead:
        labs = await self.repository.list_all()
        eligible = [
            self._summary(lab, False)
            for lab in labs
            if self._is_demo(lab) and lab.status in {LabInstanceStatus.DESTROYED.value, LabInstanceStatus.FAILED.value}
        ]
        skipped = [
            f"{lab.lab_name}: active or non-demo lab skipped"
            for lab in labs
            if self._is_demo(lab) and lab.status not in {LabInstanceStatus.DESTROYED.value, LabInstanceStatus.FAILED.value}
        ]
        from app.workers.lab_tasks import cleanup_demo_runtime_task

        cleanup_demo_runtime_task.delay()
        return RuntimeCleanupRead(
            queued_task=True,
            eligible_demo_labs=eligible,
            skipped=skipped,
            message="Demo runtime cleanup queued. Non-demo and active labs are not removed.",
        )

    async def list_events(self, lab_id: uuid.UUID) -> list[LabEvent]:
        lab = await self.repository.get_by_id(lab_id)
        if lab is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lab not found")
        return await self.repository.list_events(lab.id)

    async def _mark_failed(self, actor: User, lab: LabInstance) -> RuntimeRecoverRead:
        summary = self._summary(lab, False)
        if not self._is_stuck_summary(summary):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only stuck transient labs can be marked failed")
        lab.status = LabInstanceStatus.FAILED.value
        lab.last_error = "Marked failed by admin runtime recovery"
        await self.repository.add_event(
            LabEvent(
                lab_instance_id=lab.id,
                event_type="LAB_RECOVERY_MARK_FAILED",
                message="Admin marked stuck lab as failed",
                created_by=actor.id,
            )
        )
        await self.repository.commit()
        await self.repository.refresh(lab)
        return RuntimeRecoverRead(
            lab_id=lab.id,
            action="mark_failed",
            status=lab.status,
            queued_task=False,
            message="Lab marked failed without touching containers.",
        )

    async def _retry_destroy(self, actor: User, lab: LabInstance) -> RuntimeRecoverRead:
        if lab.status == LabInstanceStatus.DESTROYED.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Destroyed lab cannot retry destroy")
        lab.status = LabInstanceStatus.DESTROYING.value
        await self.repository.add_event(
            LabEvent(
                lab_instance_id=lab.id,
                event_type="LAB_RECOVERY_RETRY_DESTROY",
                message="Admin queued destroy retry",
                created_by=actor.id,
            )
        )
        await self.repository.commit()
        from app.workers.lab_tasks import destroy_lab_task

        destroy_lab_task.delay(str(lab.id), str(actor.id))
        return RuntimeRecoverRead(
            lab_id=lab.id,
            action="retry_destroy",
            status=LabInstanceStatus.DESTROYING.value,
            queued_task=True,
            message="Destroy retry queued.",
        )

    async def _force_destroy_demo_only(self, actor: User, lab: LabInstance) -> RuntimeRecoverRead:
        if not self._is_demo(lab):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Force destroy is restricted to demo-prefixed labs")
        if lab.status == LabInstanceStatus.DESTROYED.value:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Demo lab is already destroyed")
        lab.status = LabInstanceStatus.DESTROYING.value
        await self.repository.add_event(
            LabEvent(
                lab_instance_id=lab.id,
                event_type="LAB_RECOVERY_FORCE_DESTROY_DEMO",
                message="Admin queued demo-only force destroy",
                created_by=actor.id,
            )
        )
        await self.repository.commit()
        from app.workers.lab_tasks import force_destroy_demo_lab_task

        force_destroy_demo_lab_task.delay(str(lab.id), str(actor.id))
        return RuntimeRecoverRead(
            lab_id=lab.id,
            action="force_destroy_demo_only",
            status=LabInstanceStatus.DESTROYING.value,
            queued_task=True,
            message="Demo-only force destroy queued.",
        )

    def cleanup_demo_lab_directory(self, lab: LabInstance) -> bool:
        if not self._is_demo(lab):
            return False
        if lab.status not in {LabInstanceStatus.DESTROYED.value, LabInstanceStatus.FAILED.value}:
            return False
        directory = Path(lab.lab_directory).resolve()
        self.directory_manager.validate_inside_lab_root(directory)
        if directory.exists():
            shutil.rmtree(directory)
            return True
        return False

    def _summary(self, lab: LabInstance, has_containers: bool) -> RuntimeLabSummary:
        warning = None
        if lab.status in TRANSIENT_STATUSES and self._age(lab.updated_at) >= self.stuck_threshold:
            warning = f"{lab.status} for more than {int(self.stuck_threshold.total_seconds() // 60)} minutes"
        return RuntimeLabSummary(
            id=lab.id,
            lab_name=lab.lab_name,
            owner_id=lab.owner_id,
            status=lab.status,
            created_at=lab.created_at,
            updated_at=lab.updated_at,
            is_demo=self._is_demo(lab),
            has_containers=has_containers,
            warning=warning,
        )

    def _orphan_instance_dirs(self, labs: list[LabInstance]) -> list[RuntimeOrphanCandidate]:
        instances_root = (self.directory_manager.lab_root / "instances").resolve()
        self.directory_manager.validate_inside_lab_root(instances_root)
        if not instances_root.exists():
            return []
        known_dirs = {Path(lab.lab_directory).resolve() for lab in labs}
        candidates: list[RuntimeOrphanCandidate] = []
        for child in instances_root.iterdir():
            resolved = child.resolve()
            self.directory_manager.validate_inside_lab_root(resolved)
            if child.is_dir() and resolved not in known_dirs:
                candidates.append(
                    RuntimeOrphanCandidate(
                        path=str(resolved),
                        warning="Directory is not mapped to a DB LabInstance; cleanup skips uncertain orphans.",
                    )
                )
        return candidates

    def _is_stuck_summary(self, summary: RuntimeLabSummary) -> bool:
        return summary.status in TRANSIENT_STATUSES and self._age(summary.updated_at) >= self.stuck_threshold

    @staticmethod
    def _is_demo(lab: LabInstance) -> bool:
        return lab.lab_name.startswith("isp-demo-")

    @staticmethod
    def _age(value: datetime) -> timedelta:
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return datetime.now(UTC) - value
