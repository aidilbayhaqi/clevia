"""Smoke test provider factory Clevia.

Default hanya offline: memastikan factory, config, dan adapter dapat dibentuk tanpa
request jaringan. Gunakan --live untuk satu request Gemini nyata.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.llm.provider_factory import available_llm_providers, create_llm_provider


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Kirim request nyata ke provider")
    args = parser.parse_args()

    provider = create_llm_provider()
    print(f"provider={provider.provider_name}")
    print(f"available={','.join(available_llm_providers())}")
    model = getattr(provider, "model", None)
    if model:
        print(f"model={model}")

    if not args.live:
        print("status=CLEVIA_LLM_FACTORY_OK_OFFLINE")
        await provider.close()
        return 0

    result = await provider.complete(
        "Balas persis: CLEVIA_LLM_FACTORY_OK",
        system_instruction="Ikuti instruksi user secara literal untuk smoke test.",
        max_output_tokens=32,
    )
    print(f"text={result.text}")
    print(f"provider_result={result.provider}")
    print(f"model_result={result.model}")
    print(f"total_tokens={result.total_tokens}")
    await provider.close()
    return 0


if __name__ == "__main__":
    if not os.getenv("GEMINI_API_KEY"):
        # Dummy aman untuk offline; --live tetap memerlukan key nyata dari environment.
        os.environ["GEMINI_API_KEY"] = "offline-smoke-key"
    raise SystemExit(asyncio.run(main()))
