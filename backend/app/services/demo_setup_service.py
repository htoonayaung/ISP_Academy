import secrets
import string
from datetime import UTC, datetime

from fastapi import HTTPException, status

from app.core.config import Settings
from app.core.security import hash_password
from app.models.lab_template import LabTemplate
from app.models.ticket import Ticket, TicketStatus
from app.models.user import User, UserRole
from app.models.verification import AssertionType, ParserType, VerificationRule
from app.repositories.demo import DemoRepository
from app.schemas.demo import (
    DemoAccountRead,
    DemoResetResponse,
    DemoSetupRequest,
    DemoSetupResponse,
    DemoSetupStatusLabTemplates,
    DemoSetupStatusRead,
    DemoSetupStatusTickets,
    DemoSetupStatusUsers,
    DemoSetupStatusVerificationRules,
)

DEMO_TEMPLATE_SLUG = "demo-basic-linux-lab"
DEMO_TICKET_SLUG = "demo-linux-verification-ticket"
DEMO_RULE_NAME = "Demo uname verification"


class DemoSetupService:
    def __init__(self, repository: DemoRepository, settings: Settings) -> None:
        self.repository = repository
        self.settings = settings

    async def status(self, actor: User) -> DemoSetupStatusRead:
        self._require_admin(actor)
        instructor = await self.repository.get_user_by_username(self.settings.demo_instructor_username)
        student = await self.repository.get_user_by_username(self.settings.demo_student_username)
        template = await self.repository.get_template_by_slug(DEMO_TEMPLATE_SLUG)
        ticket = await self.repository.get_ticket_by_slug(DEMO_TICKET_SLUG)
        rule = None
        if ticket is not None:
            rule = await self.repository.get_rule_by_name_for_ticket(ticket.id, DEMO_RULE_NAME)
        warnings: list[str] = []
        if not self.settings.demo_setup_enabled:
            warnings.append("Demo setup is disabled by DEMO_SETUP_ENABLED=false")
        demo_ready = bool(
            instructor
            and student
            and template
            and template.is_active
            and ticket
            and ticket.status == TicketStatus.PUBLISHED.value
            and rule
        )
        return DemoSetupStatusRead(
            demo_ready=demo_ready,
            users=DemoSetupStatusUsers(
                demo_instructor_exists=instructor is not None,
                demo_student_exists=student is not None,
            ),
            lab_templates=DemoSetupStatusLabTemplates(
                basic_linux_exists=template is not None,
                basic_linux_active=bool(template and template.is_active),
            ),
            tickets=DemoSetupStatusTickets(
                demo_ticket_exists=ticket is not None,
                demo_ticket_published=bool(ticket and ticket.status == TicketStatus.PUBLISHED.value),
            ),
            verification_rules=DemoSetupStatusVerificationRules(demo_rule_exists=rule is not None),
            safe_to_run_setup=self.settings.demo_setup_enabled,
            warnings=warnings,
        )

    async def setup(self, actor: User, request: DemoSetupRequest) -> DemoSetupResponse:
        self._require_admin(actor)
        if not self.settings.demo_setup_enabled:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Demo setup is disabled")
        created: list[str] = []
        existing: list[str] = []
        accounts: list[DemoAccountRead] = []

        instructor, instructor_password = await self._ensure_demo_user(
            username=self.settings.demo_instructor_username,
            role=UserRole.INSTRUCTOR,
            configured_password=self.settings.demo_instructor_password,
            full_name="Demo Instructor",
            email="demo_instructor@example.com",
            created=created,
            existing=existing,
        )
        student, student_password = await self._ensure_demo_user(
            username=self.settings.demo_student_username,
            role=UserRole.STUDENT,
            configured_password=self.settings.demo_student_password,
            full_name="Demo Student",
            email="demo_student@example.com",
            created=created,
            existing=existing,
        )
        accounts.append(DemoAccountRead(role="INSTRUCTOR", username=instructor.username, password=instructor_password))
        accounts.append(DemoAccountRead(role="STUDENT", username=student.username, password=student_password))

        template = None
        if request.include_linux_demo:
            template = await self._ensure_linux_template(instructor, request.activate_templates, created, existing)
            ticket = await self._ensure_demo_ticket(instructor, template, request.publish_tickets, created, existing)
            await self._ensure_demo_rule(ticket, created, existing)

        await self.repository.commit()
        return DemoSetupResponse(
            status="ok",
            created=created,
            existing=existing,
            credentials_note="Demo passwords are returned only by setup response. Store them safely for the demo session.",
            demo_accounts=accounts,
            next_steps=[
                "Login as demo_student.",
                "Open Demo Linux Verification Ticket.",
                "Start attempt.",
                "Start lab and wait for RUNNING.",
                "Run verification.",
                "Destroy lab after the demo.",
            ],
        )

    async def reset(self, actor: User, confirm: str | None, destroy_demo_labs: bool) -> DemoResetResponse:
        self._require_admin(actor)
        if confirm != "RESET_DEMO_DATA":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset requires RESET_DEMO_DATA confirmation")
        demo_labs = await self.repository.list_demo_labs()
        if demo_labs and not destroy_demo_labs:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=[f"{lab.id}:{lab.status}" for lab in demo_labs],
            )
        running_labs = await self.repository.list_running_demo_labs()
        if running_labs and not destroy_demo_labs:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=[f"{lab.id}:{lab.status}" for lab in running_labs],
            )
        deleted = await self.repository.delete_demo_data(
            destroy_demo_labs=destroy_demo_labs,
            demo_usernames=[
                self.settings.demo_instructor_username,
                self.settings.demo_student_username,
            ],
        )
        await self.repository.commit()
        return DemoResetResponse(status="ok", deleted=deleted, skipped=[], warnings=["Only demo-prefixed data was targeted."])

    async def _ensure_demo_user(
        self,
        *,
        username: str,
        role: UserRole,
        configured_password: str | None,
        full_name: str,
        email: str,
        created: list[str],
        existing: list[str],
    ) -> tuple[User, str | None]:
        user = await self.repository.get_user_by_username(username)
        if user is not None:
            existing.append(f"user:{username}")
            return user, configured_password or None
        password = configured_password or self._generate_password()
        user = User(
            email=email,
            username=username,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=role,
            is_active=True,
        )
        await self.repository.add(user)
        created.append(f"user:{username}")
        return user, password

    async def _ensure_linux_template(
        self,
        instructor: User,
        activate: bool,
        created: list[str],
        existing: list[str],
    ) -> LabTemplate:
        template = await self.repository.get_template_by_slug(DEMO_TEMPLATE_SLUG)
        if template is not None:
            if activate and not template.is_active:
                template.is_active = True
            existing.append(f"lab_template:{DEMO_TEMPLATE_SLUG}")
            return template
        template = LabTemplate(
            name="Demo Basic Linux Lab",
            slug=DEMO_TEMPLATE_SLUG,
            description="Demo: one Alpine Linux host for uname verification.",
            category="Linux",
            difficulty="Easy",
            containerlab_yaml=self._linux_containerlab_yaml(),
            default_startup_config=None,
            estimated_cpu=1,
            estimated_memory_mb=256,
            estimated_duration_minutes=20,
            is_active=activate,
            created_by=instructor.id,
        )
        await self.repository.add(template)
        created.append(f"lab_template:{DEMO_TEMPLATE_SLUG}")
        return template

    async def _ensure_demo_ticket(
        self,
        instructor: User,
        template: LabTemplate,
        publish: bool,
        created: list[str],
        existing: list[str],
    ) -> Ticket:
        ticket = await self.repository.get_ticket_by_slug(DEMO_TICKET_SLUG)
        if ticket is not None:
            if publish and ticket.status != TicketStatus.PUBLISHED.value:
                ticket.status = TicketStatus.PUBLISHED.value
                ticket.published_at = datetime.now(UTC)
            existing.append(f"ticket:{DEMO_TICKET_SLUG}")
            return ticket
        ticket = Ticket(
            lab_template_id=template.id,
            title="Demo Linux Verification Ticket",
            slug=DEMO_TICKET_SLUG,
            description="Demo ticket for validating a simple Linux lab.",
            student_instructions="Start the linked lab, wait until it is RUNNING, then run verification.",
            hints="The verification checks the Linux kernel name with uname.",
            hidden_solution="Expected uname output contains Linux.",
            status=TicketStatus.PUBLISHED.value if publish else TicketStatus.DRAFT.value,
            created_by=instructor.id,
            published_at=datetime.now(UTC) if publish else None,
        )
        await self.repository.add(ticket)
        created.append(f"ticket:{DEMO_TICKET_SLUG}")
        return ticket

    async def _ensure_demo_rule(self, ticket: Ticket, created: list[str], existing: list[str]) -> VerificationRule:
        rule = await self.repository.get_rule_by_name_for_ticket(ticket.id, DEMO_RULE_NAME)
        if rule is not None:
            existing.append(f"verification_rule:{DEMO_RULE_NAME}")
            return rule
        rule = VerificationRule(
            ticket_id=ticket.id,
            name=DEMO_RULE_NAME,
            target_node="host1",
            command="uname",
            parser_type=ParserType.SIMPLE_TEXT.value,
            assertion_type=AssertionType.CONTAINS.value,
            expected_value="Linux",
            timeout_seconds=10,
            is_active=True,
        )
        await self.repository.add(rule)
        created.append(f"verification_rule:{DEMO_RULE_NAME}")
        return rule

    @staticmethod
    def _linux_containerlab_yaml() -> str:
        return """name: demo-basic-linux-lab
topology:
  nodes:
    host1:
      kind: linux
      image: alpine:latest
      cmd: sleep infinity
"""

    @staticmethod
    def _generate_password() -> str:
        alphabet = string.ascii_letters + string.digits + "!@#%"
        return "".join(secrets.choice(alphabet) for _ in range(20))

    @staticmethod
    def _require_admin(actor: User) -> None:
        if actor.role != UserRole.ADMIN:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
