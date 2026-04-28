import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from app.ingestion.service import ingest_document

# dummy values (use your real ones)
tenant_id = "11111111-1111-1111-1111-111111111111"
document_id = "22222222-2222-2222-2222-222222222222"

file_path = "file2.pdf"

result = ingest_document(file_path, tenant_id, document_id)

print(result)