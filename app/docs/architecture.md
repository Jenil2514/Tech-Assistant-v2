# OnboardMind Architecture

## Purpose

OnboardMind is a Slack-native AI onboarding and company knowledge assistant. The current codebase is organized around a small number of deterministic control points that fan out into specialized services:

```text
Slack
  -> FastAPI entrypoints
  -> Slack Bolt handler
  -> Router
  -> RAG / Provisioning services
  -> Cache / Postgres / LLM providers / integrations
```

The system is intentionally modular so routing, retrieval, ingestion, and future provisioning workflows can evolve independently.

## Live Runtime Entry Points

The actual runtime surface today is concentrated in a few files:

- `app/main.py` exposes the HTTP server.
- `app/services/agent_service.py` owns the Slack Bolt app and all Slack event/command handlers.
- `app/agents/router.py` resolves command intent deterministically.
- `app/rag/service.py` orchestrates retrieval, reranking, generation, and answer caching.
- `app/rag/ingestion/*` handles PDF ingestion, contextualization, chunking, and embedding.
- `app/db/*` stores and searches chunks in Postgres with pgvector.
- `app/services/cache_service.py` provides optional Redis-backed caching with graceful fallback.
- `app/provisioning/*` handles onboarding request state, approval orchestration, CSV writes, and audit events.
- `app/integrations/task_management/*` provides the task-management adapter boundary and Linear implementation.

## Request Flow

### HTTP and Slack transport

`app/main.py` creates the FastAPI application and forwards Slack traffic to the Slack Bolt handler:

```text
POST /slack/events   -> SlackRequestHandler.handle()
POST /slack/commands -> SlackRequestHandler.handle()
GET  /               -> simple health response
```

The FastAPI app is intentionally thin. It should not contain business logic.

### Slash commands

Slash commands are handled inside `app/services/agent_service.py`.

Current behavior:

1. Slack sends the command payload to `/slack/commands`.
2. The Slack Bolt command handler calls `route_slash_command()`.
3. The handler acknowledges immediately with a progress payload.
4. `/query` routes to the RAG system.
5. `/report` is recognized but not implemented.
6. `/onboard` routes to the provisioning workflow.
7. Unknown commands are rejected with a short ephemeral message.

### Provisioning

The current provisioning workflow is Slack-native:

```text
/onboard
  -> router
  -> Slack preview and approval buttons
  -> provisioning service
  -> local CSV register
  -> JSONL audit log
  -> task-management adapter
  -> Linear API
```

The Slack handler owns Slack interaction and message rendering. Provisioning business logic lives under `app/provisioning/`, while Linear-specific API calls live under `app/integrations/task_management/linear.py`.

Provisioning currently stores prototype runtime state in:

- `runtime/onboarding_employees.csv`
- `runtime/provisioning_audit.jsonl`
- `runtime/provisioning_requests/*.json`

### App mentions

App mentions are treated as a fallback knowledge query:

1. The mention text is stripped down to the user query.
2. `route_app_mention()` maps it to the RAG agent.
3. The bot posts a visible progress message in the channel.
4. The bot updates that message while retrieval/generation runs.
5. The final answer replaces the temporary message text.

### Document upload and ingestion

There is a separate upload route in `app/routes/chat.py`:

```text
POST /upload -> save PDF -> ingest_document()
```

Important caveat: this router is not currently included in `app/main.py`, so it is not part of the active HTTP surface yet. Treat it as a utility/prototype path until it is explicitly wired into the FastAPI app and hardened.

## Core Components

### Router layer

`app/agents/router.py` performs deterministic routing. Today it supports these outcomes:

- `rag` for `/query`
- `report` for `/report`
- `provisioning` for `/onboard`
- `unknown` for everything else

This router returns a `RoutedRequest` object with the selected agent, normalized text, source, and command metadata. That shape is the contract future AI routing should preserve.

### Slack service layer

`app/services/agent_service.py` is the orchestration layer between Slack and the rest of the system.

Responsibilities:

- build the Slack Bolt app
- configure bot token and signing secret
- register slash command and event handlers
- convert routed requests into user-visible Slack responses
- call the RAG service for knowledge questions
- call provisioning services for onboarding previews, approvals, and rejections

What it should not do:

- access the database directly
- embed retrieval logic
- duplicate routing rules
- implement provider-specific provisioning business logic

### RAG layer

`app/rag/service.py` is the orchestrator for question answering.

It performs:

1. query normalization
2. answer cache lookup
3. retrieval
4. reranking
5. grounded generation
6. answer cache write-back

The service uses a default tenant ID placeholder today. That is a development convenience, not a multi-tenant solution.

### Retrieval and generation sublayer

The retrieval package lives under `app/rag/retriver/`.

Note the spelling of `retriver` is intentionally preserved in the current codebase.

Sub-responsibilities:

- `retriver.py` manages exact retrieval caching, semantic retrieval caching, vector search, and tenant scoping.
- `reranker.py` uses a Groq model to reorder candidate chunks.
- `generator.py` produces the final grounded answer from ranked context.

### Ingestion pipeline

The ingestion pipeline is under `app/rag/ingestion/` and is designed for contextual RAG.

Pipeline stages:

```text
PDF -> page extraction -> chunking -> document summary -> chunk contextualization -> embeddings -> Postgres
```

The contextualization step is ingestion-time only. Retrieval should not re-write or re-contextualize document content.

### Storage and cache layers

Storage and caching are separated on purpose:

- Postgres stores durable chunk records and vector embeddings.
- Redis stores answer caches, retrieval caches, embedding caches, and semantic retrieval indices.
- If Redis is unavailable, the app should continue operating without cache acceleration.

## Data Boundaries

### Tenant isolation

Tenant ID is a first-class input in the retrieval and ingestion layers. Queries against Postgres always filter by `tenant_id`.

This is a critical boundary for future multi-tenant SaaS support. Avoid introducing any path that bypasses tenant scoping.

### Vector compatibility

The embedding pipeline currently uses a 768-dimensional vector. That dimension must remain consistent across:

- embedding generation
- Postgres vector column type
- retrieval queries
- cached embeddings

If the embedding model changes, the data migration strategy must be explicit.

## External Systems

Current integrations:

- Slack via Slack Bolt
- Linear via the task-management adapter
- Groq for summarization, reranking, and answer generation
- Google GenAI for embeddings
- PostgreSQL with pgvector
- Redis for optional caching

## Operational Constraints

The current implementation implies the following constraints:

- Slack handlers must ack quickly.
- Long-running work should not block the Slack event loop.
- Provisioning approval actions should show a visible working state before calling external APIs.
- Retrieval must remain grounded in stored company context.
- Missing context should produce an uncertainty response instead of hallucination.
- Document versioning should be used for cache invalidation.
- Cache failures must not break core knowledge answering.

## Current Gaps and Scaffolding

The following areas are incomplete, prototype-level, or intentionally scaffolded:

- `app/agents/knowledge_agent.py` is empty.
- `app/agents/onboarding_agent.py` is empty.
- `app/routes/chat.py` exists but is not mounted from `app/main.py`.
- `/report` is routed but returns a placeholder response.
- Provisioning uses local runtime files rather than durable database tables.
- Provisioning currently supports Linear only; GitHub, Notion, Google Calendar, Zoho, and Google Workspace are future adapters.

These gaps matter because future work should extend the current architecture instead of inventing parallel systems.
