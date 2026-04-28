from app.rag.chunker import chunk_text
from app.rag.embedder import get_embedding
import re

def clean_text(text):
    text = text.replace("\n", " ")        # remove newlines
    text = re.sub(r"\s+", " ", text)      # remove extra spaces
    return text.strip()

def process_text(text):
    chunks = chunk_text(text)

    processed = []
    for chunk in chunks:
        chunk = clean_text(chunk)
        embedding = get_embedding(chunk)
        processed.append((chunk, embedding))

    return processed