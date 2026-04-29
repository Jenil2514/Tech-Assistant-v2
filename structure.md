# OnboardMind Project Reference

This file is the quick context document for future conversations. Read this first before changing architecture, routes, Slack handling, RAG behavior, or agent logic.

## Product Goal

OnboardMind is a Slack-native AI onboarding and company knowledge assistant for SaaS teams.

The assistant should answer employee questions from company documents using RAG, support Slack slash commands, and grow into a multi-agent system with command routing and future AI-based routing.

## Current Working System

### RAG Pipeline

Current flow:

```text
PDF -> text extraction -> chunking -> embeddings -> PostgreSQL/pgvector
Query -> embed query -> retrieve chunks -> Groq LLaMA 3.3 -> answer
```

Current embedding model:

```text
Google gemini-embedding-002
768 dimensions using output_dimensionality
```

Current vector store:

```text
PostgreSQL on Neon
pgvector extension
Similarity search using ORDER BY embedding <-> query_embedding
```

Important fixes already implemented:

- Embedding dimension is correctly set to 768.
- pgvector type issue was fixed, avoiding `vector <-> numeric[]`.
- RAG flow avoids duplicate retrieval.
- Chunk cleaning and chunking quality were improved.
- Slack event handling uses `ack()` to avoid Slack retries.

### Backend

Backend framework:

```text
FastAPI
```

Primary modules:

- `rag/` handles embeddings, retrieval, generation, and RAG pipeline orchestration.
- `ingestion/` handles PDF loading and document processing.
- `db/` handles Neon/Postgres connection, models, and queries.
- `agents/` is intended for agent logic and routing.
- `routes/` handles HTTP/API routes.
- `services/` holds service-layer wrappers.

### Slack Integration

Current Slack integration:

```text
Slack Events API + Slack Bolt
```

Current interaction:

```text
@Assistant question...
```

Current UX behavior:

- Shows `Searching documents...`
- Shows `Generating answer...`
- Updates Slack messages instead of posting spammy separate messages.
- Uses `ack()` quickly to prevent duplicate retries.

## Target Architecture

```text
Slack
  |-- /query  -> RAG Agent
  |-- /report -> Report Agent
  |-- @bot    -> fallback / smart routing
```

## Command + Router System — Achieved

Planned commands and routing: implemented. The deterministic router and slash-command handlers are in place and used for `/query` and `/report` flows, plus mention fallback routing.

## Next Goal: HR provisioning & integrations

Objective: enable the agent to automate new-joiner provisioning and HR tasks by integrating with GitHub, Notion, and Google Calendar, and by creating accounts according to company records in Zoho (currently), migrating to Google Workspace in the future.

High-level scope:

- Connectors: GitHub, Notion, Google Calendar (read/write where appropriate), and user-directory provisioning via Zoho (future: Google Workspace).
- Connectors: GitHub, Notion, Google Calendar (read/write where appropriate), Linear (task management, optional plugin similar to Jira), and user-directory provisioning via Zoho (future: Google Workspace).
- Plugin model: task-management connectors (Linear/Jira/etc.) should be implemented as pluggable adapters so each client can enable or replace the task system (e.g., Linear, Jira, GitHub Issues).
- Provisioning actions: create user accounts, add to teams/repos/pages/calendars, assign HR-provided permissions, and schedule onboarding events.
- Authorization: ensure HR-issued scopes and an approval workflow for dangerous actions.
- Audit & logging: record changes, who triggered them, and allow rollbacks.
- UX decision (in progress): decide whether HR uses a web UI or Slack-driven workflow for provisioning; prototype both options before committing.

Implementation priorities for this goal:

1. Design connector interfaces and auth flows (OAuth/service accounts) for each target system.
1.a Design a plugin adapter interface for task-management systems (Linear/Jira) so connectors can be plugged/unplugged per-client.
2. Map company -> provisioning rules from Zoho (fields, groups, role mappings).
3. Implement safe provisioning step with approval/preview and audit logs.
4. Prototype HR UX: Slack slash-commands vs. lightweight web UI; gather feedback.
5. End-to-end tests and dry-run mode before production provisioning.

## RAG Improvements To Add

Retrieval:

- Contextual RAG is implemented for new ingestions: each chunk gets LLM-written context before embedding.
- Query retrieval returns structured chunks with source/page/chunk metadata and vector distance.
- Retrieval uses configurable `top_n`, defaults to 20 candidates.
- LLM reranking selects final chunks before answer generation.
- Redis caching is wired for embeddings, retrieval results, and final answers when `REDIS_URL` is set.
- Semantic retrieval caching is implemented for similar questions using strict embedding similarity.

Prompting:

- Generator uses a grounded system prompt for onboarding and company knowledge.
- Answers are constrained to retrieved/reranked context.
- Missing or insufficient context should produce a clear no-answer response.
- Source references are included when metadata is available.

Reranking:

- LLM reranking is implemented in `app/rag/reranker.py`.
- Reranking is behind a module boundary so it can be replaced with a dedicated rerank model later.

## Multi-Agent Direction

Expected agents:

- RAG Agent: answers document-grounded knowledge questions.
- Report Agent: generates or fetches user/team reports.
- Router Agent: decides which agent handles a Slack event or command.
- Future agents: onboarding tasks, policy assistant, HR assistant, engineering docs assistant.

Router requirements:

- Command routes should be deterministic.
- Mention fallback can use simple heuristics first.
- Future AI routing should fit behind the same router interface.
- Router output should include target agent, normalized input, metadata, and trace/debug info.

## Current File Structure

```text
app/
  .env
  .env.sample
  main.py
  requirements.txt
  sample.pdf
  file2.pdf

  agents/
    knowledge_agent.py
    onboarding_agent.py
    router.py

  config/
    constants.py
    settings.py

  db/
    connection.py
    models.py
    queries.py
    migrations/
      001_contextual_rag.sql

  rag/
    __init__.py
    service.py
    embedding/
      embedder.py
    ingestion/
      __init__.py
      chunker.py
      contextualizer.py
      loader.py
      processor.py
      service.py
    retriver/
      retriver.py
      generator.py
      reranker.py

  routes/
    chat.py

  test_scripts/
    ingestion.py
    retrival.py

  services/
    agent_service.py
    cache_service.py
    rag_service.py
```

Note: current filenames include `retriver.py` and `retrival.py`. Keep imports consistent if renaming later.

## Important Existing Paths

- FastAPI app entry: `app/main.py`
- RAG service: `app/rag/service.py`
- Query embedding: `app/rag/embedding/embedder.py`
- Retrieval: `app/rag/retriver/retriver.py`
- Reranker: `app/rag/retriver/reranker.py`
- LLM generation: `app/rag/retriver/generator.py`
- Database connection: `app/db/connection.py`
- Database queries: `app/db/queries.py`
- Ingestion service: `app/rag/ingestion/service.py`
- Agent router: `app/agents/router.py`
- Agent service: `app/services/agent_service.py`
- RAG service: `app/services/rag_service.py`
- Existing route: `app/routes/chat.py`

## Suggested Slash Command Design

Slack endpoint examples:

```text
POST /slack/commands/query
POST /slack/commands/report
POST /slack/events
```

Expected behavior:

- Slash command handler must `ack()` immediately.
- Long work should run async in the background.
- User receives a fast visible status message.
- Final answer updates or posts to the original Slack response target.
- Errors should be friendly and logged with enough detail for debugging.

Command routing concept:

```text
/query <question>
  -> router receives command=query
  -> router selects RAG Agent
  -> RAG Agent calls RAG service
  -> Slack response is updated

/report <user>
  -> router receives command=report
  -> router selects Report Agent
  -> Report Agent returns report output
  -> Slack response is updated

@bot <message>
  -> router receives event=mention
  -> simple fallback or smart routing
  -> selected agent handles request
```

Current implementation notes:

- `app/main.py` forwards both `/slack/events` and `/slack/commands` to the Slack Bolt request handler.
- `app/services/agent_service.py` registers `/query`, `/report`, and `app_mention` listeners.
- `app/agents/router.py` contains deterministic routing for slash commands and the mention fallback.
- `app/services/rag_service.py` contains the shared default tenant id and a reusable RAG answer helper.
- `app/rag/contextualizer.py` creates document summaries and chunk context during ingestion.
- `app/services/cache_service.py` uses Redis when configured and falls back to no-cache behavior when unavailable.
- `app/db/migrations/001_contextual_rag.sql` adds contextual RAG metadata columns and retrieval indexes.
- Similar questions can reuse cached retrieval results, but final answers remain exact-query cached only.

## Production Readiness Checklist

- Verify Slack signing secret on all Slack endpoints.
- Keep Slack `ack()` under 3 seconds.
- Move long-running work to background tasks or a queue.
- Add structured logging for command, team, channel, user, route, latency, and errors.
- Avoid logging secrets or full private document content.
- Add per-workspace/team metadata in DB before multi-tenant SaaS usage.
- Add command-level permission checks for `/report`.
- Add graceful handling when no relevant chunks are found.
- Add tests for router decisions and RAG service behavior.

## Tech Stack

- FastAPI
- Slack Bolt API
- Slack Events API
- PostgreSQL on Neon
- pgvector
- Google `gemini-embedding-001`
- Groq LLaMA 3.3 70B / instant models
- Python

## Current North Star

Build a production-ready Slack assistant that feels native inside Slack, answers from trusted company documents, supports explicit commands, and can evolve into multiple specialized agents without rewriting the Slack integration.
