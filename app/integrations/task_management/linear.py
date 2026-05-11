import json
from urllib import error, request

from app.config.settings import settings
from app.infrastructure.logging import get_logger
from app.integrations.task_management.base import TaskAdapterConfigurationError, TaskManagementAdapter
from app.provisioning.models import ConnectorResult, Employee, RoleMapping


LINEAR_GRAPHQL_URL = "https://api.linear.app/graphql"
logger = get_logger(__name__)


class LinearApiError(RuntimeError):
    pass


class LinearTaskAdapter(TaskManagementAdapter):
    def __init__(
        self,
        api_key: str | None = None,
        team_id: str | None = None,
        onboarding_label_id: str | None = None,
    ):
        self.api_key = (api_key or settings.LINEAR_API_KEY or "").strip()
        self.team_id = (team_id or settings.LINEAR_TEAM_ID or "").strip()
        self.invite_team_ids = [
            team_id.strip()
            for team_id in settings.LINEAR_INVITE_TEAM_IDS.split(",")
            if team_id.strip()
        ]
        self.onboarding_label_id = (onboarding_label_id or settings.LINEAR_ONBOARDING_LABEL_ID or "").strip()
        self.invite_role = settings.LINEAR_INVITE_ROLE.strip().lower()

        if not self.api_key:
            raise TaskAdapterConfigurationError("LINEAR_API_KEY is required for the Linear task adapter.")
        if not self.team_id:
            raise TaskAdapterConfigurationError("LINEAR_TEAM_ID is required for Linear onboarding tasks.")
        if self.invite_role not in {"admin", "user"}:
            raise TaskAdapterConfigurationError("LINEAR_INVITE_ROLE must be `admin` or `user`.")

    def invite_user(self, employee: Employee, role_mapping: RoleMapping) -> ConnectorResult:
        mutation = """
        mutation OrganizationInviteCreate($input: OrganizationInviteCreateInput!) {
          organizationInviteCreate(input: $input) {
            success
            organizationInvite {
              id
              email
            }
          }
        }
        """
        invite_input = {
            "email": employee.email,
            "role": self.invite_role,
        }

        if self.invite_team_ids:
            invite_input["teamIds"] = self.invite_team_ids

        logger.info(
            "Sending Linear invite email=%s invite_role=%s invite_team_count=%s",
            employee.email,
            self.invite_role,
            len(self.invite_team_ids),
        )

        try:
            response = self._graphql(mutation, {"input": invite_input})
        except LinearApiError as exc:
            if _is_existing_user_error(exc):
                logger.info("Linear invite skipped because user already exists email=%s", employee.email)
                return ConnectorResult(
                    success=True,
                    provider="linear",
                    action="invite_user",
                    message=f"Linear user already exists for {employee.email}.",
                    metadata={
                        "email": employee.email,
                        "role": role_mapping.role,
                        "linear_invite_role": self.invite_role,
                        "linear_invite_team_ids": self.invite_team_ids,
                        "invite_skipped": True,
                    },
                )
            raise

        payload = response["data"]["organizationInviteCreate"]
        invite = payload.get("organizationInvite") or {}

        if not payload.get("success"):
            raise LinearApiError(f"Linear invite failed for {employee.email}.")

        logger.info("Linear invite sent email=%s invite_id=%s", employee.email, invite.get("id"))
        return ConnectorResult(
            success=True,
            provider="linear",
            action="invite_user",
            message=f"Linear invite sent to {employee.email}.",
            external_id=invite.get("id"),
            metadata={
                "email": invite.get("email", employee.email),
                "role": role_mapping.role,
                "linear_invite_role": self.invite_role,
                "linear_invite_team_ids": self.invite_team_ids,
                "invite_skipped": False,
            },
        )

    def create_onboarding_tasks(
        self,
        employee: Employee,
        role_mapping: RoleMapping,
    ) -> list[ConnectorResult]:
        logger.info(
            "Creating unassigned Linear onboarding issue tree email=%s team_id=%s",
            employee.email,
            self.team_id,
        )

        parent_issue = self._create_issue(
            {
                "teamId": self.team_id,
                "title": f"Onboard {employee.name} ({employee.email})",
                "description": (
                    f"Coordinate onboarding for {employee.name} ({employee.email}).\n\n"
                    f"Role: {role_mapping.display_name}\n\n"
                    "Access and setup summary:\n"
                    + "\n".join(f"- {item}" for item in role_mapping.access_summary)
                ),
                "priority": 2,
            }
        )
        parent_id = parent_issue.get("id")
        logger.info(
            "Created Linear parent issue email=%s issue_id=%s identifier=%s",
            employee.email,
            parent_id,
            parent_issue.get("identifier"),
        )

        results = [
            ConnectorResult(
                success=True,
                provider="linear",
                action="create_onboarding_parent_issue",
                message=f"Created Linear parent issue {parent_issue.get('identifier', parent_id)}.",
                external_id=parent_id,
                metadata={
                    "identifier": parent_issue.get("identifier"),
                    "title": parent_issue.get("title"),
                    "url": parent_issue.get("url"),
                    "issue_type": "parent",
                },
            )
        ]

        for template in role_mapping.linear_issue_templates:
            title = template.title.format(name=employee.name, email=employee.email, role=employee.role)
            description = template.description.format(name=employee.name, email=employee.email, role=employee.role)
            issue = self._create_issue(
                {
                    "teamId": self.team_id,
                    "title": title,
                    "description": description,
                    "priority": 2,
                    "parentId": parent_id,
                }
            )
            logger.info(
                "Created Linear sub-issue email=%s parent_id=%s issue_id=%s identifier=%s",
                employee.email,
                parent_id,
                issue.get("id"),
                issue.get("identifier"),
            )
            results.append(
                ConnectorResult(
                    success=True,
                    provider="linear",
                    action="create_onboarding_sub_issue",
                    message=f"Created Linear issue {issue.get('identifier', issue.get('id'))}.",
                    external_id=issue.get("id"),
                    metadata={
                        "identifier": issue.get("identifier"),
                        "title": issue.get("title", title),
                        "url": issue.get("url"),
                        "parent_id": parent_id,
                        "issue_type": "sub_issue",
                    },
                )
            )

        return results

    def _create_issue(self, issue_input: dict) -> dict:
        if self.onboarding_label_id and self.onboarding_label_id != "optional_label_id":
            issue_input["labelIds"] = [self.onboarding_label_id]

        response = self._graphql(
            """
            mutation IssueCreate($input: IssueCreateInput!) {
              issueCreate(input: $input) {
                success
                issue {
                  id
                  identifier
                  title
                  url
                }
              }
            }
            """,
            {"input": issue_input},
        )
        payload = response["data"]["issueCreate"]
        issue = payload.get("issue") or {}

        if not payload.get("success"):
            raise LinearApiError(f"Linear issue creation failed for {issue_input.get('title')}.")

        return issue

    def _graphql(self, query: str, variables: dict) -> dict:
        logger.info("Calling Linear GraphQL operation=%s", _operation_name(query))
        payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
        req = request.Request(
            LINEAR_GRAPHQL_URL,
            data=payload,
            headers={
                "Authorization": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        try:
            with request.urlopen(req, timeout=20) as response:
                body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise LinearApiError(f"Linear API returned HTTP {exc.code}: {body}") from exc
        except error.URLError as exc:
            raise LinearApiError(f"Linear API request failed: {exc.reason}") from exc

        data = json.loads(body)
        if data.get("errors"):
            logger.error(
                "Linear GraphQL returned errors operation=%s errors=%s",
                _operation_name(query),
                data["errors"],
            )
            raise LinearApiError(f"Linear API returned errors: {data['errors']}")

        return data


def _operation_name(query: str) -> str:
    words = query.strip().split()
    if len(words) >= 2 and words[0] in {"query", "mutation"}:
        return words[1].split("(")[0]
    return "unknown"


def _is_existing_user_error(exc: LinearApiError) -> bool:
    message = str(exc).lower()
    return "existing user" in message or "already a user in this workspace" in message
