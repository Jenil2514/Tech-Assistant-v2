import re


def chunk_text(text, size=500, overlap=100):
    words = text.split()
    chunks = []

    start = 0
    while start < len(words):
        chunk = " ".join(words[start:start + size])
        chunks.append(chunk)
        start += size - overlap

    return chunks


def clean_text(text):
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def chunk_pages(pages, size=500, overlap=100):
    chunks = []
    chunk_index = 0

    for page in pages:
        text = clean_text(page.get("text", ""))
        if not text:
            continue

        for content in chunk_text(text, size=size, overlap=overlap):
            content = clean_text(content)
            if not content:
                continue

            chunks.append({
                "content": content,
                "page_number": page.get("page_number"),
                "chunk_index": chunk_index,
            })
            chunk_index += 1

    return chunks
