"""Smoke test manual Gemini provider Clevia.

Jalankan dari root repository:
    python scripts/smoke_gemini_provider.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.llm.gemini_provider import GeminiProvider, GeminiProviderError


async def main() -> int:
    if not os.getenv("GEMINI_API_KEY", "").strip():
        print("ERROR: GEMINI_API_KEY belum tersedia di environment.")
        return 2

    provider = GeminiProvider.from_env()
    try:
        result = await provider.generate_text(
            "Jawab persis: CLEVIA_GEMINI_OK",
            system_instruction=(
                "Anda sedang menjalankan smoke test provider. "
                "Ikuti instruksi output secara ketat dan jangan menambahkan penjelasan."
            ),
            max_output_tokens=64,
        )
        print(f"provider={result.provider}")
        print(f"model={result.model}")
        print(f"text={result.text}")
        print(f"input_tokens={result.input_tokens}")
        print(f"output_tokens={result.output_tokens}")
        print(f"total_tokens={result.total_tokens}")
        return 0 if "CLEVIA_GEMINI_OK" in result.text else 3
    except GeminiProviderError as exc:
        print(f"ERROR: {exc}")
        return 1
    finally:
        await provider.aclose()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
