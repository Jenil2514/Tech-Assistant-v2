from app.rag.generator import generate_answer
from app.rag.retriver import retrieve_context


DEFAULT_TENANT_ID = "11111111-1111-1111-1111-111111111111"


def answer_rag_question(query: str, tenant_id: str = DEFAULT_TENANT_ID) -> str:
    context = retrieve_context(query, tenant_id)
    return generate_answer(query, context)
