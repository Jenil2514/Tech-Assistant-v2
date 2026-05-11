import csv
from pathlib import Path

from app.config.settings import settings
from app.provisioning.models import ProvisioningRequest


FIELDNAMES = [
    "request_id",
    "created_at",
    "approved_at",
    "approved_by",
    "name",
    "email",
    "role",
    "access_summary",
    "linear_invite_status",
    "linear_tasks_status",
    "status",
]


def _csv_path() -> Path:
    return Path(settings.EMPLOYEE_REGISTER_CSV_PATH)


def request_exists(request_id: str) -> bool:
    path = _csv_path()
    if not path.exists():
        return False

    with path.open("r", encoding="utf-8", newline="") as file:
        for row in csv.DictReader(file):
            if row.get("request_id") == request_id:
                return True

    return False


def append_employee_row(request: ProvisioningRequest) -> bool:
    if request_exists(request.request_id):
        return False

    path = _csv_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists() or path.stat().st_size == 0

    row = {
        "request_id": request.request_id,
        "created_at": request.created_at,
        "approved_at": request.approved_at or "",
        "approved_by": request.approved_by or "",
        "name": request.employee.name,
        "email": request.employee.email,
        "role": request.employee.role,
        "access_summary": "; ".join(request.role_mapping.access_summary),
        "linear_invite_status": request.linear_invite_status,
        "linear_tasks_status": request.linear_tasks_status,
        "status": request.status,
    }

    with path.open("a", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        if write_header:
            writer.writeheader()
        writer.writerow(row)

    return True


def update_employee_row(request: ProvisioningRequest) -> bool:
    path = _csv_path()
    if not path.exists():
        return False

    with path.open("r", encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))

    updated = False
    for row in rows:
        if row.get("request_id") == request.request_id:
            row["linear_invite_status"] = request.linear_invite_status
            row["linear_tasks_status"] = request.linear_tasks_status
            row["status"] = request.status
            updated = True
            break

    if not updated:
        return False

    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    return True
