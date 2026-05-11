# RAG System Rules and Behavior

## Goal

The RAG system exists to answer company knowledge questions from internal documents with grounded, Slack-friendly responses. It should be reliable, tenant-scoped, and resilient to cache or retrieval misses.

## Current End-To-End Pipeline

### Ingestion path

```text
PDF upload
  -> page extraction
  -> text cleaning
  -> page chunking
  -> document summarization
  -> chunk contextualization
  -> embedding generation
  -> Postgres insert
```

### Query path

```text
User query
  -> query normalization
  -> answer cache lookup
  -> embedding cache lookup
  -> semantic retrieval cache lookup
  -> pgvector search
  -> reranking
  -> grounded generation
  -> answer cache write-back
```

## Ingestion Details

The ingestion pipeline lives under `app/rag/ingestion/`.

### Page loading

`load_pdf_pages()` uses `PyPDF2` to read a PDF page-by-page and return a list of page text blobs.

### Chunking

Chunking is word-based, not token-based.

- `chunk_text()` defaults to 500 words per chunk with 100-word overlap.
- `chunk_pages()` cleans each page and creates chunk records with `page_number` and `chunk_index` metadata.
- Chunk indices are sequential across the full document, not reset per page.

### Document summary

`summarize_document()` uses a Groq fast model to produce a short factual summary of the full document. The summary is compacted to a small word budget so it can be reused during chunk contextualization.

### Chunk contextualization

`contextualize_chunk()` uses the document summary, the chunk text, and nearby text to produce retrieval context for that specific chunk.

Important rule:

- contextualization happens at ingestion time only
- retrieval must not rewrite or regenerate chunk context

### Embeddings

`get_embedding()` uses Google GenAI with `gemini-embedding-001` and requests `output_dimensionality=768`.

That 768-dimensional output is a hard compatibility boundary for the current database schema and cache behavior.

### Persistence

`ingest_document()` stores each processed chunk via `insert_chunk()` with the following fields:

- `tenant_id`
- `document_id`
- `content`
- `embedding`
- `source`
- `page_number`
- `chunk_index`
- `contextual_text`
- `document_summary`

## Storage Model

The migration at `app/db/migrations/001_contextual_rag.sql` extends the `chunks` table with:

- `source TEXT`
- `page_number INTEGER`
- `chunk_index INTEGER`
- `contextual_text TEXT`
- `document_summary TEXT`
- `created_at TIMESTAMPTZ DEFAULT NOW()`

Indexes currently include:

- `(tenant_id, document_id)`
- `(tenant_id, source)`
- `(tenant_id, chunk_index)`
- an HNSW index on `embedding` using `vector_l2_ops`

## Retrieval Details

`retrieve_context()` in `app/rag/retriver/retriver.py` is the retrieval orchestrator.

### Query normalization

The query is normalized by:

- lowercasing
- trimming whitespace
- collapsing repeated whitespace

This normalization is used for cache keys, not for semantic meaning changes.

### Cache hierarchy

The retrieval path checks caches in this order:

1. exact answer cache in `app/rag/service.py`
2. exact retrieval cache in `retrieve_context()`
3. embedding cache for query embeddings
4. semantic retrieval cache based on embedding similarity

If a cache layer is unavailable, the system should continue to the next layer or the database path.

### Vector search

If cache lookup misses, retrieval queries Postgres with a vector distance search:

```sql
ORDER BY embedding <-> %s::vector
```

Current retrieval characteristics:

- tenant-scoped filtering is mandatory
- `top_n` defaults to the configured retrieval limit
- the database query expects a pgvector-compatible embedding string

### Semantic retrieval cache

The semantic retrieval cache stores previous retrieval results and compares query embeddings with cosine similarity.

Important settings:

- threshold default: `0.92`
- max cached candidates default: `50`
- cache entries are keyed by tenant, normalized query, `top_n`, and document version

If the best cached query does not meet the threshold, the system falls back to live vector search.

## Reranking

`rerank_chunks()` uses a Groq fast model to reorder the candidate chunks.

Behavior:

- if the candidate list is already smaller than or equal to `final_k`, reranking is skipped
- candidate content is truncated before prompting the model
- the model is expected to return JSON with ranked IDs
- if parsing fails or the model call errors, the code falls back to the original order

Reranking must never be treated as a source of truth. It is a ranking hint over already retrieved company content.

## Answer Generation

`generate_answer()` uses a Groq quality model to draft the final response.

System constraints embedded in the prompt:

- answer only from the provided context
- do not invent policy, dates, owners, or process details
- cite factual claims using filename/page labels
- keep the final answer concise and Slack-friendly

If no chunks are provided, the generator returns a clear uncertainty response instead of hallucinating.

## Cache Keys and Versioning

Cache keys are derived from a namespace plus a hashed payload.

Important versioning rule:

- `RAG_DOCUMENT_VERSION` must be included in retrieval and answer cache keys
- changing the knowledge base structure or ingestion strategy should usually bump that version

This is the main mechanism for invalidating stale retrieval data without flushing the entire cache.

## Embedded Models and Config

Relevant settings from `app/config/settings.py`:

- `GROQ_FAST_MODEL` for summarization and reranking
- `GROQ_QUALITY_MODEL` for final answer generation
- `RAG_RETRIEVAL_TOP_N`
- `RAG_FINAL_TOP_K`
- `EMBEDDING_CACHE_TTL_SECONDS`
- `RETRIEVAL_CACHE_TTL_SECONDS`
- `ANSWER_CACHE_TTL_SECONDS`
- `SEMANTIC_RETRIEVAL_CACHE_ENABLED`
- `SEMANTIC_RETRIEVAL_CACHE_THRESHOLD`
- `SEMANTIC_RETRIEVAL_CACHE_MAX_CANDIDATES`

## Grounding Rules

The following rules should always be preserved:

- Never answer from memory when context is available.
- Never invent company facts.
- When context is insufficient, say so explicitly.
- Preserve source metadata through ingestion, retrieval, and generation.
- Keep retrieval and reranking modular so they can be swapped independently later.

## Current Implementation Notes

- The path spelling `retriver` is intentional in the codebase and should not be casually renamed.
- `DEFAULT_TENANT_ID` is currently a development placeholder.
- The current cache layer is optional and should not be a hard dependency for correctness.
- The upload route in `app/routes/chat.py` is not mounted from the main FastAPI app yet.

## Failure Modes

Expected failure behavior:

- cache unavailable -> continue without cache
- reranker unavailable -> return original retrieved order
- no context found -> uncertainty response

Potential risk areas:

- embedding dimension drift
- tenant scoping mistakes
- prompt changes that weaken grounding
- document versioning not being updated after ingestion changes
