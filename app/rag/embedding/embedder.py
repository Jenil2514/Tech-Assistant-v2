from google import genai
from app.config.settings import settings

client = genai.Client(api_key=settings.GOOGLE_API_KEY)
def get_embedding(text: str):
    print("🔍 Generating embedding...")

    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=genai.types.EmbedContentConfig(
            output_dimensionality=768
        )
    )

    print("✅ Embedding done")

    return response.embeddings[0].values