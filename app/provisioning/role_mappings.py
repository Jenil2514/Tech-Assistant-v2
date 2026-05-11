from app.provisioning.models import LinearIssueTemplate, RoleMapping


ROLE_MAPPINGS = {
    "backend-engineer": RoleMapping(
        role="backend-engineer",
        display_name="Backend Engineer",
        access_summary=[
            "Linear workspace member invite",
            "Backend onboarding issues in Linear",
            "Planned backend repository access",
            "Planned engineering onboarding docs",
            "Planned backend Slack channels",
        ],
        linear_issue_templates=[
            LinearIssueTemplate(
                title="Onboard {name}: engineering environment setup",
                description=(
                    "Prepare backend development setup for {name} ({email}).\n\n"
                    "- Share local setup instructions\n"
                    "- Confirm repository access plan\n"
                    "- Confirm environment variable handoff process"
                ),
            ),
            LinearIssueTemplate(
                title="Onboard {name}: backend team walkthrough",
                description=(
                    "Schedule and track backend architecture walkthrough for {name} ({email}).\n\n"
                    "- Service overview\n"
                    "- Deployment flow\n"
                    "- Ownership and escalation paths"
                ),
            ),
            LinearIssueTemplate(
                title="Onboard {name}: first-week checklist",
                description=(
                    "Track first-week backend onboarding tasks for {name} ({email}).\n\n"
                    "- Confirm access requests\n"
                    "- Pairing session\n"
                    "- First starter task"
                ),
            ),
        ],
    ),
}


class UnknownRoleError(ValueError):
    pass


def get_role_mapping(role: str) -> RoleMapping:
    mapping = ROLE_MAPPINGS.get(role)
    if mapping is None:
        known_roles = ", ".join(sorted(ROLE_MAPPINGS))
        raise UnknownRoleError(f"Unknown role `{role}`. Known roles: {known_roles}.")
    return mapping
