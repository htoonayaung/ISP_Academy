import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.verification import VerificationResult, VerificationRule, VerificationRun


class VerificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_rule(self, rule: VerificationRule) -> VerificationRule:
        self.session.add(rule)
        await self.session.flush()
        await self.session.refresh(rule)
        return rule

    async def get_rule_by_id(self, rule_id: str | uuid.UUID) -> VerificationRule | None:
        try:
            parsed_id = uuid.UUID(str(rule_id))
        except ValueError:
            return None
        return await self.session.get(VerificationRule, parsed_id)

    async def list_rules_for_ticket(self, ticket_id: uuid.UUID) -> list[VerificationRule]:
        result = await self.session.execute(
            select(VerificationRule)
            .where(VerificationRule.ticket_id == ticket_id)
            .order_by(VerificationRule.created_at.asc())
        )
        return list(result.scalars().all())

    async def list_active_rules_for_ticket(self, ticket_id: uuid.UUID) -> list[VerificationRule]:
        result = await self.session.execute(
            select(VerificationRule)
            .where(VerificationRule.ticket_id == ticket_id, VerificationRule.is_active.is_(True))
            .order_by(VerificationRule.created_at.asc())
        )
        return list(result.scalars().all())

    async def create_run(self, run: VerificationRun) -> VerificationRun:
        self.session.add(run)
        await self.session.flush()
        await self.session.refresh(run)
        return run

    async def get_run_by_id(self, run_id: str | uuid.UUID) -> VerificationRun | None:
        try:
            parsed_id = uuid.UUID(str(run_id))
        except ValueError:
            return None
        return await self.session.get(VerificationRun, parsed_id)

    async def list_runs_for_attempt(self, attempt_id: uuid.UUID) -> list[VerificationRun]:
        result = await self.session.execute(
            select(VerificationRun)
            .where(VerificationRun.ticket_attempt_id == attempt_id)
            .order_by(VerificationRun.created_at.desc())
        )
        return list(result.scalars().all())

    async def add_result(self, result: VerificationResult) -> VerificationResult:
        self.session.add(result)
        await self.session.flush()
        await self.session.refresh(result)
        return result

    async def list_results_for_run(self, run_id: uuid.UUID) -> list[VerificationResult]:
        result = await self.session.execute(
            select(VerificationResult)
            .where(VerificationResult.verification_run_id == run_id)
            .order_by(VerificationResult.created_at.asc())
        )
        return list(result.scalars().all())

    async def commit(self) -> None:
        await self.session.commit()

    async def refresh(self, item: VerificationRule | VerificationRun | VerificationResult) -> None:
        await self.session.refresh(item)
