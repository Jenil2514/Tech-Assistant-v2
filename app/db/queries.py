def insert_chunk(
    conn,
    tenant_id,
    document_id,
    content,
    embedding,
    source=None,
    page_number=None,
    chunk_index=None,
    contextual_text=None,
    document_summary=None,
):
    if isinstance(embedding, list):
        embedding = str(embedding)

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO chunks (
                id,
                tenant_id,
                document_id,
                content,
                embedding,
                source,
                page_number,
                chunk_index,
                contextual_text,
                document_summary
            )
            VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            tenant_id,
            document_id,
            content,
            embedding,
            source,
            page_number,
            chunk_index,
            contextual_text,
            document_summary,
        ))
        conn.commit()


def search_chunks(conn, tenant_id, query_embedding, top_n=20):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                content,
                document_id,
                source,
                page_number,
                chunk_index,
                contextual_text,
                embedding <-> %s::vector AS distance
            FROM chunks
            WHERE tenant_id = %s
            ORDER BY embedding <-> %s::vector
            LIMIT %s;
        """, (query_embedding, tenant_id, query_embedding, top_n))

        rows = cur.fetchall()

    return [
        {
            "content": row[0],
            "document_id": str(row[1]) if row[1] is not None else None,
            "source": row[2],
            "page_number": row[3],
            "chunk_index": row[4],
            "contextual_text": row[5],
            "distance": float(row[6]) if row[6] is not None else None,
        }
        for row in rows
    ]
