import json
import re

from groq import Groq

from app.config.settings import settings


client = Groq(api_key=settings.GROQ_API_KEY)


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0]


def _fallback_rank(chunks, final_k):
    return chunks[:final_k]


def rerank_chunks(query: str, chunks, final_k: int | None = None):
    final_k = final_k or settings.RAG_FINAL_TOP_K
    if len(chunks) <= final_k:
        return chunks

    candidates = []
    for index, chunk in enumerate(chunks, start=1):
        candidates.append({
            "id": index,
            "source": chunk.get("source"),
            "page_number": chunk.get("page_number"),
            "contextual_text": _truncate(chunk.get("contextual_text") or "", 500),
            "content": _truncate(chunk.get("content") or "", 900),
        })

    prompt = f"""
Rerank these retrieved chunks for answering the user question.

Question:
{query}

Candidates:
{json.dumps(candidates, ensure_ascii=False)}

Return only JSON in this format:
{{"ranked_ids":[1,2,3], "reasons":{{"1":"short reason"}}}}

Choose the {final_k} most relevant candidate ids. Prefer chunks that directly answer the question.
"""

    try:
        response = client.chat.completions.create(
            model=settings.GROQ_FAST_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        content = response.choices[0].message.content.strip()
        match = re.search(r"\{.*\}", content, flags=re.DOTALL)
        payload = json.loads(match.group(0) if match else content)
        ranked_ids = payload.get("ranked_ids", [])
    except Exception:
        return _fallback_rank(chunks, final_k)

    by_id = {index: chunk for index, chunk in enumerate(chunks, start=1)}
    reranked = []
    for candidate_id in ranked_ids:
        try:
            candidate_id = int(candidate_id)
        except (TypeError, ValueError):
            continue

        chunk = by_id.get(candidate_id)
        if chunk and chunk not in reranked:
            reranked.append(chunk)

    if not reranked:
        return _fallback_rank(chunks, final_k)

    return reranked[:final_k]
