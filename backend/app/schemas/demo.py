from pydantic import BaseModel


class DemoSetupStatusUsers(BaseModel):
    demo_instructor_exists: bool
    demo_student_exists: bool


class DemoSetupStatusLabTemplates(BaseModel):
    basic_linux_exists: bool
    basic_linux_active: bool


class DemoSetupStatusTickets(BaseModel):
    demo_ticket_exists: bool
    demo_ticket_published: bool


class DemoSetupStatusVerificationRules(BaseModel):
    demo_rule_exists: bool


class DemoSetupStatusRead(BaseModel):
    demo_ready: bool
    users: DemoSetupStatusUsers
    lab_templates: DemoSetupStatusLabTemplates
    tickets: DemoSetupStatusTickets
    verification_rules: DemoSetupStatusVerificationRules
    safe_to_run_setup: bool
    warnings: list[str]


class DemoSetupRequest(BaseModel):
    include_linux_demo: bool = True
    include_frr_demo: bool = False
    activate_templates: bool = True
    publish_tickets: bool = True


class DemoAccountRead(BaseModel):
    role: str
    username: str
    password: str | None = None


class DemoSetupResponse(BaseModel):
    status: str
    created: list[str]
    existing: list[str]
    credentials_note: str
    demo_accounts: list[DemoAccountRead]
    next_steps: list[str]


class DemoResetRequest(BaseModel):
    confirm: str | None = None
    destroy_demo_labs: bool = False


class DemoResetResponse(BaseModel):
    status: str
    deleted: list[str]
    skipped: list[str]
    warnings: list[str]
