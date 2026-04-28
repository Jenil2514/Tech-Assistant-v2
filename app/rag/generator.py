from groq import Groq
from pathlib import Path

from app.config.settings import settings


client = Groq(api_key=settings.GROQ_API_KEY)


def _source_label(chunk):
    source = chunk.get("source") or "source"
    source_name = Path(source).name if source != "source" else source
    page = chunk.get("page_number")

    label = source_name
    if page is not None:
        label += f" p.{page}"

    return label


def _format_context(chunks):
    formatted = []
    for index, chunk in enumerate(chunks, start=1):
        label = _source_label(chunk)
        contextual_text = chunk.get("contextual_text")
        content = chunk.get("content") or ""

        if contextual_text:
            formatted.append(f"Source {index}: [{label}]\nContext: {contextual_text}\nContent: {content}")
        else:
            formatted.append(f"Source {index}: [{label}]\nContent: {content}")

    return "\n\n".join(formatted)


def generate_answer(query: str, chunks):
    if not chunks:
        return "I do not have enough information in the available documents to answer that."

    context = _format_context(chunks)

    messages = [
        {
            "role": "system",
            "content": (
                "You are OnboardMind, a company onboarding and knowledge assistant. "
                "Answer only from the provided context. If the context does not contain "
                "the answer, say you do not have enough information. Do not invent policy, "
                "dates, owners, or process details. Cite factual claims using the provided "
                "filename/page labels, for example [handbook.pdf p.3]. Do not cite [S1], "
                "[S2], or generic source numbers."
            ),
        },
        {
            "role": "user",
            "content": f"""
Context:
{context}

Question:
{query}

Answer in a concise Slack-friendly format.
""",
        },
    ]

    response = client.chat.completions.create(
        model=settings.GROQ_QUALITY_MODEL,
        messages=messages,
        temperature=0,
    )

    return response.choices[0].message.content.strip()
