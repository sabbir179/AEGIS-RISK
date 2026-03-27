from openai import OpenAI
from app.core.config import settings


def generate_ai_answer(query: str, docs: list[str]) -> str:
    if not settings.openai_api_key:
        return "OPENAI_API_KEY is missing."

    if not docs:
        return "No relevant documents were found."

    client = OpenAI(api_key=settings.openai_api_key)

    context = "\n\n".join(docs[:5])

    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
            {
                "role": "system",
                "content": (
                    "You are a geopolitical and supply-chain risk analyst. "
                    "Use only the provided context. "
                    "Write a structured answer with these exact section headings:\n"
                    "1. Overall Assessment\n"
                    "2. Risk Level\n"
                    "3. Key Risk Drivers\n"
                    "4. Why It Matters\n"
                    "5. Recommended Watchpoints\n\n"
                    "Keep the answer concise, practical, and professional. "
                    "If the context is weak, say so clearly."
                ),
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {query}",
            },
        ],
    )

    return response.output_text