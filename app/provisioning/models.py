from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Employee:
    name: str
    email: str
    role: str


@dataclass(frozen=True)
class LinearIssueTemplate:
    title: str
    description: str


@dataclass(frozen=True)
class RoleMapping:
    role: str
    display_name: str
    access_summary: list[str]
    linear_issue_templates: list[LinearIssueTemplate]


@dataclass
class ProvisioningRequest:
    request_id: str
    employee: Employee
    role_mapping: RoleMapping
    requester_id: str
    workspace_id: str
    channel_id: str | None
    created_at: str
    status: str = "pending"
    approved_by: str | None = None
    approved_at: str | None = None
    rejected_by: str | None = None
    rejected_at: str | None = None
    rejection_reason: str | None = None
    linear_invite_status: str = "not_started"
    linear_tasks_status: str = "not_started"
    linear_invite_id: str | None = None
    linear_issue_ids: list[str] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ConnectorResult:
    success: bool
    provider: str
    action: str
    message: str
    external_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OnboardingActionResult:
    request: ProvisioningRequest | None
    success: bool
    status: str
    message: str
    csv_appended: bool = False
    linear_invite_result: ConnectorResult | None = None
    linear_task_results: list[ConnectorResult] = field(default_factory=list)
