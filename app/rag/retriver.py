import math
import time

from app.config.settings import settings
from app.db.connection import get_db
from app.db.queries import search_chunks
from app.rag.embedder import get_embedding
from app.services.cache_service import cache


def _normalize_query(query: str) -> str:
    return " ".join(query.lower().strip().split())


def _get_cached_embedding(query: str):
    normalized_query = _normalize_query(query)
    cache_key = cache.make_key("embedding", normalized_query)
    cached_embedding = cache.get_json(cache_key)

    if cached_embedding:
        print("Embedding cache hit")
        return cached_embedding

    embedding = get_embedding(query)
    cache.set_json(cache_key, embedding, settings.EMBEDDING_CACHE_TTL_SECONDS)
    return embedding


def _cosine_similarity(left, right) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0

    dot_product = 0.0
    left_norm = 0.0
    right_norm = 0.0

    for left_value, right_value in zip(left, right):
        left_float = float(left_value)
        right_float = float(right_value)
        dot_product += left_float * right_float
        left_norm += left_float * left_float
        right_norm += right_float * right_float

    if left_norm == 0 or right_norm == 0:
        return 0.0

    return dot_product / (math.sqrt(left_norm) * math.sqrt(right_norm))


def _semantic_index_key(tenant_id: str, top_n: int) -> str:
    return cache.make_key("semantic_retrieval_index", tenant_id, top_n, settings.RAG_DOCUMENT_VERSION)


def _semantic_entry_key(tenant_id: str, normalized_query: str, top_n: int) -> str:
    return cache.make_key("semantic_retrieval_entry", tenant_id, normalized_query, top_n, settings.RAG_DOCUMENT_VERSION)


def _get_semantic_retrieval_cache(tenant_id: str, query_embedding, top_n: int):
    if not settings.SEMANTIC_RETRIEVAL_CACHE_ENABLED:
        print("Semantic retrieval cache disabled by settings")
        return None

    index_key = _semantic_index_key(tenant_id, top_n)
    entry_keys = cache.list_range(
        index_key,
        0,
        settings.SEMANTIC_RETRIEVAL_CACHE_MAX_CANDIDATES - 1,
    )

    if not entry_keys:
        print("Semantic retrieval cache miss: no cached retrieval entries")
        return None

    best_match = None
    best_similarity = 0.0

    for entry_key in entry_keys:
        entry = cache.get_json(entry_key)
        if not entry:
            continue

        similarity = _cosine_similarity(query_embedding, entry.get("embedding"))
        if similarity > best_similarity:
            best_similarity = similarity
            best_match = entry

    if best_match and best_similarity >= settings.SEMANTIC_RETRIEVAL_CACHE_THRESHOLD:
        print(
            "Semantic retrieval cache hit "
            f"({best_similarity:.3f}) from query: {best_match.get('query')}"
        )
        return best_match.get("chunks")

    if best_match:
        print(
            "Semantic retrieval cache miss "
            f"({best_similarity:.3f} < {settings.SEMANTIC_RETRIEVAL_CACHE_THRESHOLD}) "
            f"nearest query: {best_match.get('query')}"
        )
    else:
        print("Semantic retrieval cache miss: no valid cached entries")

    return None


def _set_semantic_retrieval_cache(tenant_id: str, normalized_query: str, query_embedding, chunks, top_n: int):
    if not settings.SEMANTIC_RETRIEVAL_CACHE_ENABLED:
        return

    entry_key = _semantic_entry_key(tenant_id, normalized_query, top_n)
    index_key = _semantic_index_key(tenant_id, top_n)
    entry = {
        "query": normalized_query,
        "embedding": query_embedding,
        "chunks": chunks,
        "created_at": int(time.time()),
    }

    cache.set_json(entry_key, entry, settings.RETRIEVAL_CACHE_TTL_SECONDS)
    cache.list_prepend(
        key=index_key,
        value=entry_key,
        ttl_seconds=settings.RETRIEVAL_CACHE_TTL_SECONDS,
        max_items=settings.SEMANTIC_RETRIEVAL_CACHE_MAX_CANDIDATES,
    )


def retrieve_context(query: str, tenant_id: str, top_n: int | None = None):
    top_n = top_n or settings.RAG_RETRIEVAL_TOP_N
    normalized_query = _normalize_query(query)
    cache_key = cache.make_key("retrieval", tenant_id, normalized_query, top_n, settings.RAG_DOCUMENT_VERSION)

    print("Generating query embedding...")
    query_embedding = _get_cached_embedding(query)
    query_embedding_vector = query_embedding

    cached_results = cache.get_json(cache_key)
    if cached_results is not None:
        print("Exact retrieval cache hit")
        return cached_results

    semantic_results = _get_semantic_retrieval_cache(tenant_id, query_embedding, top_n)
    if semantic_results is not None:
        cache.set_json(cache_key, semantic_results, settings.RETRIEVAL_CACHE_TTL_SECONDS)
        return semantic_results

    query_embedding = str(query_embedding)

    print("Searching vector database...")
    conn = get_db()
    try:
        chunks = search_chunks(conn, tenant_id, query_embedding, top_n=top_n)
    finally:
        conn.close()

    print(f"Retrieved {len(chunks)} candidate chunks")
    cache.set_json(cache_key, chunks, settings.RETRIEVAL_CACHE_TTL_SECONDS)
    _set_semantic_retrieval_cache(tenant_id, normalized_query, query_embedding_vector, chunks, top_n)
    return chunks
