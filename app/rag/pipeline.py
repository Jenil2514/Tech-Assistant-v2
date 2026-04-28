from groq import Groq
from app.config.settings import settings
from app.rag.retriver import retrieve_context

client = Groq(api_key=settings.GROQ_API_KEY)

def answer_query(query, tenant_id):
    context = retrieve_context(query, tenant_id)

    prompt = f"""
    Answer ONLY using this context:

    {context}

    Question: {query}
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content