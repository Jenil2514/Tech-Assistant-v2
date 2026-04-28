import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from app.rag.retriver import retrieve_context

tenant_id = "11111111-1111-1111-1111-111111111111"

query = "what is Automated Account Provisioning & Access Setup and what pain it solves?"

context = retrieve_context(query, tenant_id)

print("\n📄 Retrieved Context:\n")
print(context)