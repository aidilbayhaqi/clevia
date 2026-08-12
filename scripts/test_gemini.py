import asyncio

from app.core.config import settings
from app.llm.provider import get_llm_adapter


async def main() -> None:
    if settings.normalized_llm_provider != "gemini":
        raise SystemExit(
            f"LLM_PROVIDER is {settings.LLM_PROVIDER!r}; expected 'gemini'."
        )

    if not settings.GEMINI_API_KEY:
        raise SystemExit(
            "GEMINI_API_KEY is empty. Create a key in Google AI Studio, "
            "put it in .env, then restart/rebuild the API."
        )

    adapter = get_llm_adapter()
    result = await adapter.respond(
        instructions=(
            "You are a short smoke test. Reply naturally in Indonesian "
            "with one short sentence. Do not call tools."
        ),
        input_items=[{"role": "user", "content": "Halo, tes koneksi Clevia."}],
        tools=[],
    )

    print("provider:", result.provider)
    print("model:", result.model)
    print("reply:", result.text)
    print("input_tokens:", result.input_tokens)
    print("output_tokens:", result.output_tokens)


if __name__ == "__main__":
    asyncio.run(main())