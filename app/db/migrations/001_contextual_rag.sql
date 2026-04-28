ALTER TABLE chunks
ADD COLUMN IF NOT EXISTS source TEXT,
ADD COLUMN IF NOT EXISTS page_number INTEGER,
ADD COLUMN IF NOT EXISTS chunk_index INTEGER,
ADD COLUMN IF NOT EXISTS contextual_text TEXT,
ADD COLUMN IF NOT EXISTS document_summary TEXT,
ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_chunks_tenant_document
ON chunks (tenant_id, document_id);

CREATE INDEX IF NOT EXISTS idx_chunks_tenant_source
ON chunks (tenant_id, source);

CREATE INDEX IF NOT EXISTS idx_chunks_tenant_chunk_index
ON chunks (tenant_id, chunk_index);

CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw
ON chunks USING hnsw (embedding vector_l2_ops);
