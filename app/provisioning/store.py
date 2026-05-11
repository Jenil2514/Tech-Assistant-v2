import json
from pathlib import Path

from app.config.settings import settings
from app.provisioning.models import Employee, LinearIssueTemplate, ProvisioningRequest, RoleMapping


def _state_dir() -> Path:
    return Path(settings.PROVISIONING_STATE_DIR)


def _request_path(request_id: str) -> Path:
    return _state_dir() / f"{request_id}.json"


def save_request(request: ProvisioningRequest) -> None:
    path = _request_path(request.request_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(".tmp")

    with temp_path.open("w", encoding="utf-8") as file:
        json.dump(request.to_dict(), file, indent=2, sort_keys=True)

    temp_path.replace(path)


def load_request(request_id: str) -> ProvisioningRequest | None:
    path = _request_path(request_id)
    if not path.exists():
        return None

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    employee_data = data["employee"]
    role_mapping_data = data["role_mapping"]

    employee = Employee(
        name=employee_data["name"],
        email=employee_data["email"],
        role=employee_data["role"],
    )
    role_mapping = RoleMapping(
        role=role_mapping_data["role"],
        display_name=role_mapping_data["display_name"],
        access_summary=list(role_mapping_data["access_summary"]),
        linear_issue_templates=[
            LinearIssueTemplate(
                title=template["title"],
                description=template["description"],
            )
            for template in role_mapping_data["linear_issue_templates"]
        ],
    )

    return ProvisioningRequest(
        request_id=data["request_id"],
        employee=employee,
        role_mapping=role_mapping,
        requester_id=data["requester_id"],
        workspace_id=data["workspace_id"],
        channel_id=data.get("channel_id"),
        created_at=data["created_at"],
        status=data.get("status", "pending"),
        approved_by=data.get("approved_by"),
        approved_at=data.get("approved_at"),
        rejected_by=data.get("rejected_by"),
        rejected_at=data.get("rejected_at"),
        rejection_reason=data.get("rejection_reason"),
        linear_invite_status=data.get("linear_invite_status", "not_started"),
        linear_tasks_status=data.get("linear_tasks_status", "not_started"),
        linear_invite_id=data.get("linear_invite_id"),
        linear_issue_ids=list(data.get("linear_issue_ids", [])),
        error=data.get("error"),
    )
