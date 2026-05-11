# Product Vision and Roadmap

## Vision

OnboardMind is a Slack-native AI assistant for onboarding and internal company knowledge. The product should help employees ask questions, find grounded answers quickly, and eventually automate safe workflow actions such as provisioning and onboarding tasks.

The product is not meant to be a generic chatbot. It should behave like a trusted company assistant with deterministic routing, grounded answers, and strong workflow boundaries.

## Core Jobs To Be Done

Primary user needs:

- Ask company knowledge questions without leaving Slack.
- Get concise, cited, and reliable answers.
- Receive progress updates while the system is working.
- Upload documents that become part of the knowledge base.
- Route onboarding and provisioning requests into safe workflows.

Secondary system needs:

- Support multi-tenant company data.
- Keep knowledge retrieval fast and deterministic.
- Allow future integrations to plug in without rewriting the core assistant.

## Current Product Surface

The current codebase exposes these experiences:

- `/query` for company knowledge questions.
- `@mention` for fallback knowledge questions in-channel.
- `/report` as a routed placeholder for future reporting workflows.
- `/upload` as an unmounted ingestion helper in `app/routes/chat.py`.

The most mature experience today is knowledge Q&A. Reporting and provisioning are roadmap items.

## Product Principles

### Grounded answers first

The assistant should only answer from retrieved company content. When the content is insufficient, it should say so clearly.

### Slack-native UX

The product should feel native to Slack:

- ack quickly
- show progress
- update messages instead of spamming new ones
- keep responses short and readable

### Deterministic routing

Slash commands should be routed deterministically. If the system does not know how to handle a command, it should say that explicitly instead of guessing.

### Safe automation

Any future provisioning or HR action must be approval-gated, auditable, and revocable.

### Multi-tenant by design

Product features must not assume a single workspace forever. Tenant separation should be preserved in every workflow.

## User Personas

### New hires

New hires want clear onboarding answers, policy clarification, and quick access to the right internal information.

### Employees

Employees want fast answers about company processes, tools, and internal documentation.

### HR and operations teams

HR and ops users will eventually drive provisioning, onboarding workflows, and integration actions.

### Workspace admins

Admins need visibility, auditing, and control over dangerous actions and external integrations.

## Roadmap

### Now

Current focus:

- stabilize the Slack knowledge assistant path
- keep retrieval grounded and fast
- preserve deterministic routing
- keep ingestion and retrieval compatible with the current 768-dimensional embeddings

### Next

Near-term product work should focus on:

- implementing a real report agent
- wiring or replacing the current upload helper with a production-safe ingestion path
- adding onboarding-specific agent logic
- adding structured logging and better runtime diagnostics
- improving Slack error handling and retry behavior
- adding tests for routing, retrieval, and cache fallback
- pluggable connector architecture

### Later

Medium-term product goals:

- approval-driven provisioning flows
- audit logs for every dangerous action
- background job execution for long-running work
- per-tenant configuration and permissions
- document access controls and tenant-aware knowledge scopes

### Long term

Future platform goals:

- LangGraph-based orchestration
- connector plugin architecture
- enterprise integrations
- observability and tracing across agents and workflows
- admin tooling for approvals, revocation, and auditing

## What Success Looks Like

The product is working well when:

- users ask one question in Slack and get a useful answer fast
- answers are grounded in internal documents
- the assistant never invents policy or process details
- long-running actions are visible and safe
- provisioning actions cannot happen without approval and auditing
- new integrations can be added without coupling them to Slack handlers or retrieval internals

## Non-Goals

The current product should not be treated as:

- a free-form chat app with no grounding
- a single-purpose script with hardcoded workflows
- a provisioning system that can take destructive actions without approval
- a replacement for explicit policy or process ownership

## Product Notes For Future Contributors

- Keep knowledge answering concise and cited.
- Keep routing deterministic unless the router contract is intentionally extended.
- Preserve tenant isolation everywhere.
- Never let an integration or workflow bypass approval and audit requirements.
- Treat placeholder modules as intentional scaffolding, not finished product surface.
