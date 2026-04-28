def insert_chunk(conn, tenant_id, document_id, content, embedding):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO chunks (id, tenant_id, document_id, content, embedding)
            VALUES (gen_random_uuid(), %s, %s, %s, %s)
        """, (tenant_id, document_id, content, embedding))
        conn.commit()


def search_chunks(conn, tenant_id, query_embedding):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT content
            FROM chunks
            WHERE tenant_id = %s
            ORDER BY embedding <-> %s::vector
            LIMIT 5;
        """, (tenant_id, query_embedding))

        return [row[0] for row in cur.fetchall()]