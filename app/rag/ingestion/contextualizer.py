from groq import Groq

from app.config.settings import settings


client = Groq(api_key=settings.GROQ_API_KEY)


def _truncate(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0]


def _compact_text(text: str, max_words: int) -> str:
    text = text.replace("*", "")
    text = " ".join(text.split())
    words = text.split()

    if len(words) <= max_words:
        return text

    return " ".join(words[:max_words]).rstrip(" ,;:")


def summarize_document(document_text: str) -> str:
    prompt = f"""
Create a concise factual summary of this company document for retrieval.
Return plain text only. No markdown, no heading, no bullet list.
Keep it to 2 short sentences.

Document:
{_truncate(document_text, 12000)}
"""

    response = client.chat.completions.create(
        model=settings.GROQ_FAST_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    return _compact_text(response.choices[0].message.content.strip(), max_words=60)


def contextualize_chunk(document_summary: str, chunk: str, nearby_text: str = "") -> str:
    prompt = f"""
Write retrieval context for ONLY the chunk below.

Document summary:
{document_summary}

Nearby text:
{_truncate(nearby_text, 2000)}

Chunk:
{_truncate(chunk, 2500)}

Return plain text only. No markdown, no heading, no bullet list.
Return max 2 short sentences and max 45 words.
Do not summarize the whole document.
Do not list all product features or pricing unless this exact chunk is about that.
Explain what this chunk specifically says and any implied subject needed for retrieval.
"""

    response = client.chat.completions.create(
        model=settings.GROQ_FAST_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    return _compact_text(response.choices[0].message.content.strip(), max_words=45)
