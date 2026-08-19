from __future__ import annotations

import asyncio

from google import genai
from google.genai import types

from app.core.config import settings


async def main() -> None:
    print("provider =", settings.LLM_PROVIDER)
    print("model =", settings.GEMINI_MODEL)
    print("key_configured =", bool(settings.GEMINI_API_KEY.strip()))
    print("timeout_seconds =", settings.GEMINI_TIMEOUT_SECONDS)

    if not settings.GEMINI_API_KEY.strip():
        raise RuntimeError("GEMINI_API_KEY is empty.")

    client = genai.Client(
        api_key=settings.GEMINI_API_KEY.strip(),
        http_options=types.HttpOptions(
            api_version="v1",
            timeout=int(settings.GEMINI_TIMEOUT_SECONDS * 1000),
        ),
    )

    try:
        response = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents="Reply with exactly: CLEVIA_OK",
        )
        text = (response.text or "").strip()
        print("response =", text)
        if "CLEVIA_OK" not in text:
            raise RuntimeError(f"Unexpected Gemini smoke response: {text!r}")
    finally:
        try:
            await client.aio.aclose()
        except Exception:
            pass
        try:
            client.close()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
