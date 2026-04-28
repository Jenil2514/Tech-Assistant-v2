from app.db.connection import get_db
from app.db.queries import insert_chunk
from app.ingestion.loader import load_pdf
from app.ingestion.processor import process_text

def ingest_document(file_path, tenant_id, document_id):
    print("🚀 Starting ingestion...")

    conn = get_db()

    text = load_pdf(file_path)
    print(f"📄 Extracted text length: {len(text)}")

    processed_chunks = process_text(text)
    print(f"🧩 Total chunks: {len(processed_chunks)}")

    for i, (chunk, embedding) in enumerate(processed_chunks):
        print(f"⚡ Processing chunk {i+1}/{len(processed_chunks)}")

        insert_chunk(conn, tenant_id, document_id, chunk, embedding)

    conn.close()

    print("✅ Ingestion complete!")