from datetime import UTC, datetime
from uuid import uuid4

from app.config.settings import settings
from app.infrastructure.logging import get_logger
from app.integrations.task_management.base import TaskAdapterConfigurationError
from app.integrations.task_management.factory import get_task_management_adapter
from app.provisioning.audit import append_audit_event
from app.provisioning.employee_register import append_employee_row, request_exists, update_employee_row
from app.provisioning.models import OnboardingActionResult, ProvisioningRequest
from app.provisioning.parser import parse_onboard_command
from app.provisioning.role_mappings import get_role_mapping
from app.provisioning.store import load_request, save_request


logger = get_logger(__name__)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _configured_approvers() -> set[str]:
    return {
        approver.strip()
        for approver in settings.PROVISIONING_APPROVER_SLACK_IDS.split(",")
        if approver.strip()
    }


def is_authorized_approver(user_id: str) -> bool:
    return user_id in _configured_approvers()


def create_onboarding_request(
    text: str,
    requester_id: str,
    workspace_id: str,
    channel_id: str | None,
) -> ProvisioningRequest:
    employee = parse_onboard_command(text)
    role_mapping = get_role_mapping(employee.role)
    request = ProvisioningRequest(
        request_id=str(uuid4()),
        employee=employee,
        role_mapping=role_mapping,
        requester_id=requester_id,
        workspace_id=workspace_id,
        channel_id=channel_id,
        created_at=_utc_now(),
    )

    save_request(request)
    logger.info(
        "Created onboarding request request_id=%s workspace_id=%s requester_id=%s role=%s email=%s",
        request.request_id,
        workspace_id,
        requester_id,
        employee.role,
        employee.email,
    )
    append_audit_event(
        "provisioning_request_created",
        request.request_id,
        requester_id,
        {
            "workspace_id": workspace_id,
            "role": employee.role,
            "email": employee.email,
        },
    )

    return request


def approve_onboarding_request(request_id: str, approver_id: str) -> OnboardingActionResult:
    request = load_request(request_id)
    logger.info("Approval received request_id=%s approver_id=%s", request_id, approver_id)
    if request is None:
        logger.warning("Approval failed because request was missing request_id=%s", request_id)
        return OnboardingActionResult(
            request=None,
            success=False,
            status="missing",
            message="I could not find that onboarding request. Please run `/onboard` again.",
        )

    if not is_authorized_approver(approver_id):
        logger.warning(
            "Approval denied request_id=%s approver_id=%s reason=unauthorized_approver",
            request.request_id,
            approver_id,
        )
        append_audit_event(
            "provisioning_approval_denied",
            request.request_id,
            approver_id,
            {"reason": "unauthorized_approver"},
        )
        return OnboardingActionResult(
            request=request,
            success=False,
            status=request.status,
            message="You are not configured as a provisioning approver.",
        )

    if request.status in {"completed", "failed"} or request_exists(request.request_id):
        logger.info(
            "Approval ignored because request already processed request_id=%s status=%s",
            request.request_id,
            request.status,
        )
        return OnboardingActionResult(
            request=request,
            success=request.status == "completed",
            status=request.status,
            message=f"This onboarding request has already been processed with status `{request.status}`.",
        )

    if request.status == "rejected":
        return OnboardingActionResult(
            request=request,
            success=False,
            status="rejected",
            message="This onboarding request was already rejected.",
        )

    request.status = "approved"
    request.approved_by = approver_id
    request.approved_at = _utc_now()
    save_request(request)
    logger.info("Request approved request_id=%s approver_id=%s", request.request_id, approver_id)
    append_audit_event("provisioning_request_approved", request.request_id, approver_id)

    try:
        csv_appended = append_employee_row(request)
        logger.info(
            "Employee register append complete request_id=%s csv_appended=%s path=%s",
            request.request_id,
            csv_appended,
            settings.EMPLOYEE_REGISTER_CSV_PATH,
        )
        append_audit_event(
            "employee_register_appended" if csv_appended else "employee_register_already_exists",
            request.request_id,
            approver_id,
            {"path": settings.EMPLOYEE_REGISTER_CSV_PATH},
        )
    except OSError as exc:
        logger.exception(
            "Employee register append failed request_id=%s path=%s",
            request.request_id,
            settings.EMPLOYEE_REGISTER_CSV_PATH,
        )
        request.status = "failed"
        request.error = f"Employee register write failed: {exc}"
        save_request(request)
        append_audit_event(
            "employee_register_append_failed",
            request.request_id,
            approver_id,
            {
                "path": settings.EMPLOYEE_REGISTER_CSV_PATH,
                "error": str(exc),
            },
        )
        return OnboardingActionResult(
            request=request,
            success=False,
            status="failed",
            message=(
                "I could not write to the employee CSV. Close the file if it is open, "
                "then run a fresh `/onboard` request."
            ),
            csv_appended=False,
        )

    try:
        adapter = get_task_management_adapter()
        logger.info(
            "Task adapter loaded request_id=%s adapter=%s",
            request.request_id,
            settings.TASK_ADAPTER,
        )
        invite_result = adapter.invite_user(request.employee, request.role_mapping)
        logger.info(
            "Linear invite step complete request_id=%s success=%s external_id=%s skipped=%s",
            request.request_id,
            invite_result.success,
            invite_result.external_id,
            invite_result.metadata.get("invite_skipped", False),
        )
        request.linear_invite_status = "sent"
        request.linear_invite_id = invite_result.external_id
        append_audit_event(
            "task_adapter_invite_completed",
            request.request_id,
            approver_id,
            invite_result.metadata | {"external_id": invite_result.external_id},
        )

        task_results = adapter.create_onboarding_tasks(request.employee, request.role_mapping)
        logger.info(
            "Linear task creation complete request_id=%s created_count=%s",
            request.request_id,
            len(task_results),
        )
        request.linear_tasks_status = "created"
        request.linear_issue_ids = [
            result.external_id
            for result in task_results
            if result.external_id
        ]
        append_audit_event(
            "task_adapter_tasks_completed",
            request.request_id,
            approver_id,
            {"issue_ids": request.linear_issue_ids},
        )

        request.status = "completed"
        save_request(request)
        update_employee_row(request)
        logger.info("Onboarding completed request_id=%s", request.request_id)
        append_audit_event("provisioning_request_completed", request.request_id, approver_id)

        return OnboardingActionResult(
            request=request,
            success=True,
            status="completed",
            message="Onboarding approved and completed.",
            csv_appended=csv_appended,
            linear_invite_result=invite_result,
            linear_task_results=task_results,
        )
    except (RuntimeError, TaskAdapterConfigurationError) as exc:
        logger.exception("Provisioning failed request_id=%s", request.request_id)
        request.status = "failed"
        request.error = str(exc)
        if request.linear_invite_status == "not_started":
            request.linear_invite_status = "failed"
        if request.linear_tasks_status == "not_started":
            request.linear_tasks_status = "failed"
        save_request(request)
        update_employee_row(request)
        append_audit_event(
            "provisioning_request_failed",
            request.request_id,
            approver_id,
            {"error": str(exc)},
        )
        return OnboardingActionResult(
            request=request,
            success=False,
            status="failed",
            message="The employee row was recorded, but Linear provisioning failed. Check the audit log for details.",
            csv_appended=csv_appended,
        )


def reject_onboarding_request(request_id: str, approver_id: str, reason: str | None = None) -> OnboardingActionResult:
    request = load_request(request_id)
    logger.info("Rejection received request_id=%s approver_id=%s", request_id, approver_id)
    if request is None:
        logger.warning("Rejection failed because request was missing request_id=%s", request_id)
        return OnboardingActionResult(
            request=None,
            success=False,
            status="missing",
            message="I could not find that onboarding request. Please run `/onboard` again.",
        )

    if not is_authorized_approver(approver_id):
        logger.warning(
            "Rejection denied request_id=%s approver_id=%s reason=unauthorized_approver",
            request.request_id,
            approver_id,
        )
        append_audit_event(
            "provisioning_rejection_denied",
            request.request_id,
            approver_id,
            {"reason": "unauthorized_approver"},
        )
        return OnboardingActionResult(
            request=request,
            success=False,
            status=request.status,
            message="You are not configured as a provisioning approver.",
        )

    if request.status != "pending":
        return OnboardingActionResult(
            request=request,
            success=False,
            status=request.status,
            message=f"This onboarding request is already `{request.status}`.",
        )

    request.status = "rejected"
    request.rejected_by = approver_id
    request.rejected_at = _utc_now()
    request.rejection_reason = reason
    save_request(request)
    logger.info("Onboarding rejected request_id=%s approver_id=%s", request.request_id, approver_id)
    append_audit_event(
        "provisioning_request_rejected",
        request.request_id,
        approver_id,
        {"reason": reason},
    )

    return OnboardingActionResult(
        request=request,
        success=True,
        status="rejected",
        message="Onboarding request rejected. No CSV row or Linear changes were made.",
    )

