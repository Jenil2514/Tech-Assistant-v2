from app.services.rag_service import answer_rag_question


def answer_query(query, tenant_id):
    return answer_rag_question(query, tenant_id)
