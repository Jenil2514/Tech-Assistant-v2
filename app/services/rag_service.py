from app.config.settings import settings
from app.rag.generator import generate_answer
from app.rag.reranker import rerank_chunks
from app.rag.retriver import retrieve_context
from app.services.cache_service import cache


DEFAULT_TENANT_ID = "11111111-1111-1111-1111-111111111111"


def _normalize_query(query: str) -> str:
    return " ".join(query.lower().strip().split())


def answer_rag_question(
    query: str,
    tenant_id: str = DEFAULT_TENANT_ID,
    top_n: int | None = None,
    final_k: int | None = None,
) -> str:
    normalized_query = _normalize_query(query)
    top_n = top_n or settings.RAG_RETRIEVAL_TOP_N
    final_k = final_k or settings.RAG_FINAL_TOP_K

    cache_key = cache.make_key(
        "answer",
        tenant_id,
        normalized_query,
        top_n,
        final_k,
        settings.RAG_DOCUMENT_VERSION,
    )
    cached_answer = cache.get_json(cache_key)
    if cached_answer:
        return cached_answer

    candidates = retrieve_context(query, tenant_id, top_n=top_n)
    ranked_chunks = rerank_chunks(query, candidates, final_k=final_k)
    answer = generate_answer(query, ranked_chunks)

    cache.set_json(cache_key, answer, settings.ANSWER_CACHE_TTL_SECONDS)
    return answer
