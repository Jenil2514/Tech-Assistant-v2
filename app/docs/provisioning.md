# Provisioning System

## Status

Provisioning now has a first Slack-native implementation for HR onboarding.

Implemented today:

- `/onboard "Full Name" email@example.com role-key`
- approval-gated Slack workflow
- local CSV employee register
- JSONL audit log
- saved request state under `runtime/`
- pluggable task-management adapter boundary
- Linear adapter for invites and onboarding issue creation

Still not implemented:

- GitHub access provisioning
- Notion page/doc assignment
- Google Calendar event scheduling
- Zoho employee lookup
- Google Workspace email/account creation
- durable database-backed provisioning tables
- rollback/revocation automation

## Current Workflow

```text
Slack /onboard
  -> parse and validate input
  -> role mapping lookup
  -> save pending provisioning request
  -> show Slack approval preview
  -> approver clicks Approve or Reject
  -> append employee CSV row
  -> send Linear invite
  -> create Linear parent onboarding issue
  -> create Linear onboarding sub-issues
  -> update Slack with final status
  -> write audit events
```

Example:

```text
/onboard "John Doe" john@gmail.com backend-engineer
```

The bot previews employee details, role mapping, planned local CSV write, planned Linear invite, planned Linear issue tree, and approval status.

## Runtime Storage

Provisioning currently uses local runtime files instead of database tables:

- `runtime/onboarding_employees.csv`
- `runtime/provisioning_audit.jsonl`
- `runtime/provisioning_requests/*.json`

`runtime/` is gitignored because it contains employee and audit data.

The CSV is temporary HR-visible storage. It can be locked by Excel or other spreadsheet tools on Windows; if the file is locked, the workflow records a clean failure instead of crashing the Slack listener.

## Role Mapping

Role mappings live in `app/provisioning/role_mappings.py`.

Current role:

- `backend-engineer`

Each mapping defines a display name, access summary, and Linear sub-issue templates.

## Approval

Dangerous/provisioning actions require Slack approval.

Approvers are configured by:

```env
PROVISIONING_APPROVER_SLACK_IDS=U123,U456
```

Only configured approvers can approve or reject the Slack preview.

## Linear Adapter

Task-management systems use a pluggable adapter boundary:

- `TaskManagementAdapter`
- `LinearTaskAdapter`

Current config:

```env
TASK_ADAPTER=linear
LINEAR_API_KEY=...
LINEAR_TEAM_ID=...
LINEAR_INVITE_ROLE=admin
LINEAR_ONBOARDING_LABEL_ID=
LINEAR_INVITE_TEAM_IDS=
```

Current Linear behavior:

- send workspace invite with `organizationInviteCreate`
- treat "already a user in this workspace" as an idempotent successful invite
- create one unassigned parent issue named `Onboard Name (email)`
- create unassigned onboarding sub-issues under that parent
- include name, email, role, and access summary in issue content

The workflow intentionally does not assign Linear issues to the invitee. Assignment before or after invite acceptance had inconsistent API behavior during testing, so v1 keeps ownership simple and visible through the issue title/description.

## Audit And Logs

Audit events are written to `runtime/provisioning_audit.jsonl`.

Terminal logs are emitted for request creation, approval/rejection, CSV append, adapter loading, Linear invite, Linear parent issue creation, Linear sub-issue creation, and failures.

Never log API keys, Slack tokens, or full sensitive payloads.

## Future Direction

Next provisioning steps should preserve the adapter boundary and approval model.

Likely next additions:

- database-backed provisioning requests and audit events
- Google Sheets or real HRIS-backed employee register
- GitHub adapter
- Notion adapter
- Google Calendar adapter
- Zoho lookup adapter
- Jira adapter behind `TaskManagementAdapter`
- Google Workspace account creation when subscription/setup is available
- explicit rollback/revocation records

## Guardrails

- Do not put provider API calls inside Slack handlers.
- Do not bypass Slack approval for provisioning actions.
- Do not commit runtime employee/audit files.
- Do not log credentials or full sensitive payloads.
- Do not couple Linear directly to provisioning orchestration; keep it behind `TaskManagementAdapter`.
