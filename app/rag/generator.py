from groq import Groq
from app.config.settings import settings

client = Groq(api_key=settings.GROQ_API_KEY)

def generate_answer(query: str, context: str):
    prompt = f"""
    Answer the question using ONLY the context below.

    Context:
    {context}

    Question:
    {query}
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content