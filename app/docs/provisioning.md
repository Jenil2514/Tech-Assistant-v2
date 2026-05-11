# Provisioning System

## Status

This section describes the intended provisioning system, not a finished implementation.

Current codebase state:

- no provisioning service exists yet
- no provisioning routes exist yet
- `app/agents/onboarding_agent.py` is empty
- `app/agents/knowledge_agent.py` is empty
- the repository only contains the product intent and future constraints for provisioning

Treat this document as the design contract for future implementation.

## Purpose

The provisioning system will handle HR and access workflows for company onboarding and related operational tasks. It should support providers such as:

- GitHub
- Notion
- Google Calendar
- Zoho
- future Google Workspace migration paths

The system must be safe, auditable, tenant-aware, and built on replaceable adapters.

## Core Safety Requirements

All provisioning work must obey these rules:

- dangerous actions require explicit approval
- every action must be audited
- all integrations must support revocation
- connector implementations must be replaceable per client or tenant
- no hardcoded secrets or credentials
- no unrestricted access to external systems
- tenant isolation must be preserved end-to-end

## Intended Workflow

The expected lifecycle for a provisioning request is:

```text
request intake
  -> validation
  -> policy check
  -> approval gate
  -> connector execution
  -> confirmation
  -> audit logging
  -> revocation / rollback support if needed
```

### 1. Request intake

Requests should enter through Slack or another controlled interface. Raw user input should not be executed directly.

### 2. Validation

The system should validate:

- user identity
- workspace or tenant identity
- requested action
- allowed scope
- required metadata

### 3. Policy evaluation

The system should determine whether the action is safe, requires approval, or must be rejected.

### 4. Approval gate

Any action that can create, remove, or modify access must pass through approval before execution.

### 5. Connector execution

Approved actions are executed through provider-specific adapter interfaces.

### 6. Confirmation and audit

Every execution should produce a visible confirmation and a durable audit event.

### 7. Rollback or revocation

If an integration supports rollback or revocation, the system must retain the state needed to reverse the action safely.

## Proposed Domain Model

The future provisioning system will likely need concepts like these:

- `ProvisioningRequest`
- `ProvisioningPlan`
- `ApprovalDecision`
- `ProvisioningTask`
- `ConnectorAdapter`
- `AuditEvent`
- `RevocationRecord`

These are conceptual names, not current database tables.

## Adapter Design

Connector logic should be implemented behind a stable adapter boundary.

Adapter requirements:

- provider-specific auth handling
- idempotent execution where possible
- explicit error reporting
- support for revocation or compensation actions
- no direct Slack coupling

This avoids embedding provider-specific business logic inside agents or route handlers.

## Slack Interaction Model

Provisioning should be Slack-native, but not Slack-dependent.

Expected UX behavior:

- acknowledge the request quickly
- show the current approval or execution state
- update the user instead of posting repeated messages
- surface clear rejection reasons when the action is blocked
- keep human approval flows understandable and auditable

## Audit and Observability

Provisioning actions must be observable.

Audit logs should capture:

- tenant or workspace
- requester identity
- target system
- requested action
- approval decision
- execution result
- timestamps
- correlation or trace identifiers

Never log secrets, credentials, or sensitive payloads in plain text.

## Failure and Recovery Rules

Provisioning is a workflow system, not a best-effort helper.

Required behavior:

- failed actions must be visible
- partial successes must be tracked
- retries must be controlled and idempotent
- compensation logic should be explicit
- dangerous actions must not auto-retry indefinitely

## Current Gaps In The Codebase

The repository currently lacks the implementation surface needed for provisioning:

- no dedicated provisioning agent
- no service layer for provisioning orchestration
- no adapter package for external systems
- no provisioning database tables or migrations
- no approval workflow implementation

That means future work should start by adding a focused service boundary rather than overloading the existing RAG or Slack modules.

## Recommended Implementation Path

When this system is built, the most maintainable path is likely:

1. add a provisioning agent module
2. add a provisioning service layer
3. define a request and approval data model
4. implement one provider adapter end-to-end
5. add audit logging before adding more providers
6. wire Slack progress and approval messages
7. add revocation and compensation support

## Suggested Future File Structure

The current repository already hints at a future modular layout. A provisioning implementation would fit well under paths like:

- `app/agents/provisioning_agent.py`
- `app/services/provisioning_service.py`
- `app/integrations/<provider>/...`
- `app/workflows/provisioning/...`
- `app/db/migrations/...`

## Guardrails For Future Contributors

- Do not treat the provisioning system as a simple Slack command handler.
- Do not bypass approval for convenience.
- Do not embed provider logic directly in the agent router.
- Do not mix provisioning state with RAG retrieval state.
- Do not implement destructive actions without audit and rollback planning.
