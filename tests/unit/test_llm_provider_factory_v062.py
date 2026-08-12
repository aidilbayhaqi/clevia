from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from unittest.mock import patch

from app.llm.gemini_adapter import GeminiLLMAdapter
from app.llm.provider_contract import LLMProvider
from app.llm.provider_factory import (
    LLMProviderFactoryError,
    available_llm_providers,
    create_llm_provider,
    normalize_provider_name,
)


class LLMProviderFactoryTest(unittest.TestCase):
    def test_gemini_registered(self) -> None:
        self.assertIn("gemini", available_llm_providers())

    def test_alias_google_normalized(self) -> None:
        self.assertEqual(normalize_provider_name("google"), "gemini")
        self.assertEqual(normalize_provider_name("google-gemini"), "gemini")

    def test_factory_builds_gemini_without_network_call(self) -> None:
        with patch.dict(os.environ, {"GEMINI_API_KEY": "unit-test-key", "LLM_PROVIDER": "gemini"}, clear=False):
            provider = create_llm_provider()
        self.assertIsInstance(provider, GeminiLLMAdapter)
        self.assertIsInstance(provider, LLMProvider)

    def test_unknown_provider_fails_closed(self) -> None:
        with self.assertRaises(LLMProviderFactoryError):
            create_llm_provider("provider-tidak-ada")


if __name__ == "__main__":
    unittest.main(verbosity=2)
