def chunk_text(text, size=500, overlap=100):
    words = text.split()
    chunks = []

    start = 0
    while start < len(words):
        chunk = " ".join(words[start:start+size])
        chunks.append(chunk)
        start += size - overlap

    return chunks