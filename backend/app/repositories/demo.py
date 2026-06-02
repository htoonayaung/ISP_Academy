from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lab_instance import LabEvent, LabInstance, LabInstanceStatus, LabNode
from app.models.lab_template import LabTemplate
from app.models.ticket import Ticket, TicketAttempt
from app.models.user import User
from app.models.verification import VerificationResult, VerificationRule, VerificationRun


class DemoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user_by_username(self, username: str) -> User | None:
        result = await self.session.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def get_template_by_slug(self, slug: str) -> LabTemplate | None:
        result = await self.session.execute(select(LabTemplate).where(LabTemplate.slug == slug))
        return result.scalar_one_or_none()

    async def get_ticket_by_slug(self, slug: str) -> Ticket | None:
        result = await self.session.execute(select(Ticket).where(Ticket.slug == slug))
        return result.scalar_one_or_none()

    async def get_rule_by_name_for_ticket(self, ticket_id, name: str) -> VerificationRule | None:
        result = await self.session.execute(
            select(VerificationRule).where(
                VerificationRule.ticket_id == ticket_id,
                VerificationRule.name == name,
            )
        )
        return result.scalar_one_or_none()

    async def list_demo_labs(self) -> list[LabInstance]:
        result = await self.session.execute(
            select(LabInstance)
            .join(LabTemplate, LabTemplate.id == LabInstance.template_id)
            .where(LabTemplate.slug.like("demo-%"))
            .order_by(LabInstance.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_running_demo_labs(self) -> list[LabInstance]:
        result = await self.session.execute(
            select(LabInstance)
            .join(LabTemplate, LabTemplate.id == LabInstance.template_id)
            .where(
                LabTemplate.slug.like("demo-%"),
                LabInstance.status.in_(
                    [
                        LabInstanceStatus.STARTING.value,
                        LabInstanceStatus.RUNNING.value,
                        LabInstanceStatus.STOPPING.value,
                        LabInstanceStatus.DESTROYING.value,
                    ]
                ),
            )
        )
        return list(result.scalars().all())

    async def delete_demo_data(self, destroy_demo_labs: bool, demo_usernames: list[str]) -> list[str]:
        deleted: list[str] = []
        demo_tickets = await self.session.execute(select(Ticket).where(Ticket.slug.like("demo-%")))
        ticket_ids = [ticket.id for ticket in demo_tickets.scalars().all()]

        demo_templates = await self.session.execute(select(LabTemplate).where(LabTemplate.slug.like("demo-%")))
        template_ids = [template.id for template in demo_templates.scalars().all()]

        demo_labs = await self.list_demo_labs()
        demo_lab_ids = [lab.id for lab in demo_labs]
        demo_attempts = await self.session.execute(
            select(TicketAttempt).where(TicketAttempt.ticket_id.in_(ticket_ids)) if ticket_ids else select(TicketAttempt).where(False)
        )
        attempt_ids = [attempt.id for attempt in demo_attempts.scalars().all()]

        if attempt_ids:
            runs = await self.session.execute(
                select(VerificationRun).where(VerificationRun.ticket_attempt_id.in_(attempt_ids))
            )
            run_ids = [run.id for run in runs.scalars().all()]
            if run_ids:
                await self.session.execute(delete(VerificationResult).where(VerificationResult.verification_run_id.in_(run_ids)))
                await self.session.execute(delete(VerificationRun).where(VerificationRun.id.in_(run_ids)))
                deleted.append("demo verification runs/results")
            await self.session.execute(delete(TicketAttempt).where(TicketAttempt.id.in_(attempt_ids)))
            deleted.append("demo ticket attempts")

        if demo_lab_ids and destroy_demo_labs:
            await self.session.execute(delete(LabEvent).where(LabEvent.lab_instance_id.in_(demo_lab_ids)))
            await self.session.execute(delete(LabNode).where(LabNode.lab_instance_id.in_(demo_lab_ids)))
            await self.session.execute(delete(LabInstance).where(LabInstance.id.in_(demo_lab_ids)))
            deleted.append("demo lab instances")

        if ticket_ids:
            await self.session.execute(delete(VerificationRule).where(VerificationRule.ticket_id.in_(ticket_ids)))
            await self.session.execute(delete(Ticket).where(Ticket.id.in_(ticket_ids)))
            deleted.append("demo tickets and verification rules")

        if template_ids:
            await self.session.execute(delete(LabTemplate).where(LabTemplate.id.in_(template_ids)))
            deleted.append("demo lab templates")

        await self.session.execute(delete(User).where(User.username.in_(demo_usernames)))
        deleted.append("demo users")
        return deleted

    async def add(self, item) -> None:
        self.session.add(item)
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()
