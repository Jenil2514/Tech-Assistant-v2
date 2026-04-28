from app.db.connection import get_db
from app.db.queries import search_chunks
from app.rag.embedder import get_embedding

def retrieve_context(query: str, tenant_id: str):
    print("🔍 Generating query embedding...")

    query_embedding = get_embedding(query)
    query_embedding = str(query_embedding)  # Convert to string for DB query

    print("📡 Searching DB...")

    conn = get_db()
    chunks = search_chunks(conn, tenant_id, query_embedding)
    conn.close()

    print(f"✅ Retrieved {len(chunks)} chunks")

    return "\n\n".join(chunks)