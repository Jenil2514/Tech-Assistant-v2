from app.rag.chunker import chunk_pages, chunk_text, clean_text
from app.rag.contextualizer import contextualize_chunk, summarize_document
from app.rag.embedder import get_embedding


def process_text(text):
    chunks = chunk_text(text)

    processed = []
    for chunk in chunks:
        chunk = clean_text(chunk)
        embedding = get_embedding(chunk)
        processed.append((chunk, embedding))

    return processed


def process_pages(pages, source):
    document_text = clean_text(" ".join(page.get("text", "") for page in pages))
    document_summary = summarize_document(document_text)
    chunks = chunk_pages(pages)

    processed = []
    for index, chunk in enumerate(chunks):
        previous_chunk = chunks[index - 1]["content"] if index > 0 else ""
        next_chunk = chunks[index + 1]["content"] if index + 1 < len(chunks) else ""
        nearby_text = clean_text(f"{previous_chunk} {next_chunk}")

        contextual_text = contextualize_chunk(
            document_summary=document_summary,
            chunk=chunk["content"],
            nearby_text=nearby_text,
        )
        embedding_input = f"{contextual_text}\n\n{chunk['content']}"
        embedding = get_embedding(embedding_input)

        processed.append({
            "content": chunk["content"],
            "embedding": embedding,
            "source": source,
            "page_number": chunk["page_number"],
            "chunk_index": chunk["chunk_index"],
            "contextual_text": contextual_text,
            "document_summary": document_summary,
        })

    return processed
