# Slack Integration Behavior

## Overview

Slack is the primary user interface for OnboardMind. The current integration is implemented with Slack Bolt in `app/services/agent_service.py` and exposed through FastAPI transport endpoints in `app/main.py`.

```text
Slack -> FastAPI -> SlackRequestHandler -> Slack Bolt handlers -> router/RAG services
```

## Transport Layer

`app/main.py` forwards both Slack event traffic and Slack command traffic to the same request handler:

- `POST /slack/events`
- `POST /slack/commands`

The root path `/` is just a lightweight health indicator.

## Slack App Configuration

The Slack app is created with:

- bot token from `SLACK_BOT_TOKEN`
- signing secret from `SLACK_SIGNING_SECRET`
- `token_verification_enabled=False`

The codebase currently relies on Slack Bolt for request handling. Do not introduce a second, conflicting verification scheme in a separate layer.

## Slash Command Behavior

### `/query`

This is the main user-facing knowledge command.

Current behavior:

1. The command payload is routed through `route_slash_command()`.
2. The handler acknowledges immediately with a progress payload.
3. The progress payload tells the user the assistant is searching docs, ranking matches, and drafting an answer.
4. If the route is not `rag`, the user gets a short ephemeral error.
5. If the text is empty, the user is asked to add a question after `/query`.
6. The RAG system generates the answer.
7. The final response is sent as an ephemeral message that replaces the original progress state.

The command is intentionally Slack-friendly: users should not wait in silence.

### `/report`

This command is routed deterministically, but it is not implemented yet.

Current behavior:

- the handler acknowledges with a short "Preparing report..." response
- if the router does not map the command to the report agent, an unknown-command response is returned
- otherwise the command ends with a placeholder message that the report agent is not implemented yet

### `/onboard`

This command starts the HR onboarding workflow.

Expected format:

```text
/onboard "Full Name" email@example.com backend-engineer
```

Current behavior:

1. The command payload is routed through `route_slash_command()`.
2. The handler parses the quoted name, email, and role key.
3. Invalid format, invalid email, or unknown role returns an ephemeral error.
4. A pending provisioning request is saved under `runtime/provisioning_requests/`.
5. The bot returns an ephemeral approval preview with employee summary, role mapping, planned CSV write, planned Linear invite, and planned Linear issue tree.
6. Configured approvers can click Approve or Reject.
7. On approval, the bot immediately updates the Slack message to a working state.
8. The workflow appends the employee CSV row, sends a Linear invite, creates one unassigned Linear parent issue plus sub-issues, writes audit events, and returns final status.
9. On rejection, no CSV row or Linear action is performed, and a rejection audit event is written.

Required Slack app setup:

- slash command `/onboard` points to `POST /slack/commands`
- Interactivity is enabled and points to `POST /slack/commands`

Approvers are configured by `PROVISIONING_APPROVER_SLACK_IDS`.

## App Mention Behavior

App mentions are treated as a knowledge query fallback.

Current flow:

1. The mention text is stripped down to the user query.
2. `route_app_mention()` maps it to the RAG agent.
3. A channel message saying "Searching documents..." is posted.
4. The message is updated to "Generating answer...".
5. The final answer replaces the message text.

This path is more visible than slash commands because it updates the channel message directly.

## Event Handling Rules

### Message events

Generic `message` events are intentionally ignored.

This avoids accidental duplicate processing of normal Slack traffic.

### Retry and duplication behavior

The code should avoid duplicate retries and duplicate replies. Slack can resend events, so handlers should stay idempotent where possible.

## UX Rules

The Slack experience should follow these rules:

- ack immediately for slash commands
- show visible progress for longer work
- update messages instead of posting repeated progress messages
- keep ephemeral error messages short and human-readable
- do not expose stack traces to end users

## Error Handling

Current behavior in `/query`:

- the user gets a generic failure message if answer generation raises an exception
- the exception is re-raised after the user-facing response

Current behavior in app mentions:

- there is no local try/except block yet around the final answer generation and message update path

This means the mention flow is more fragile than the slash-command flow and should be treated carefully in future work.

## Routing Contract

Slack handlers should not hardcode routing logic in multiple places.

The routing contract is:

- `/query` -> `rag`
- `/report` -> `report`
- `/onboard` -> `provisioning`
- unknown command -> `unknown`
- app mention -> `rag`

Keep this contract centralized in `app/agents/router.py`.

## Current Gaps

Known Slack-facing limitations in the current codebase:

- there is no real report workflow yet
- the upload route exists outside the active FastAPI app surface
- mention flow error handling is thinner than the slash-command flow
- provisioning execution currently happens inside the Slack action handler and may take several seconds while Linear responds

## Recommended Slack Standards

When extending Slack behavior, keep the following standards:

- never block handlers with long synchronous work if it can be avoided
- prefer background execution for expensive tasks
- preserve tenant and workspace context in logs and downstream calls
- keep responses short, specific, and readable in Slack
- if an action is dangerous, route it through approval before execution
