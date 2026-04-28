from app.db.connection import get_db
from app.db.queries import insert_chunk
from app.ingestion.loader import load_pdf_pages
from app.ingestion.processor import process_pages


def ingest_document(file_path, tenant_id, document_id):
    print("Starting contextual ingestion...")

    conn = get_db()

    pages = load_pdf_pages(file_path)
    text_length = sum(len(page["text"]) for page in pages)
    print(f"Extracted {len(pages)} pages and {text_length} characters")

    processed_chunks = process_pages(pages, source=file_path)
    print(f"Total contextual chunks: {len(processed_chunks)}")

    for i, chunk in enumerate(processed_chunks):
        print(f"Saving chunk {i + 1}/{len(processed_chunks)}")

        insert_chunk(
            conn=conn,
            tenant_id=tenant_id,
            document_id=document_id,
            content=chunk["content"],
            embedding=chunk["embedding"],
            source=chunk["source"],
            page_number=chunk["page_number"],
            chunk_index=chunk["chunk_index"],
            contextual_text=chunk["contextual_text"],
            document_summary=chunk["document_summary"],
        )

    conn.close()

    print("Contextual ingestion complete")
