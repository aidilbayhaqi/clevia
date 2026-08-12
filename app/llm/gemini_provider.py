"""Gemini provider untuk Clevia.

Patch: clevia-p0-gemini-provider-v0.6.0

Tujuan modul ini adalah menyediakan provider Gemini yang terisolasi dari business logic.
Modul tidak mengubah provider default Clevia. Runtime harus memilih provider secara eksplisit
pada tahap wiring berikutnya.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any


DEFAULT_GEMINI_MODEL = "gemini-3.6-flash"
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_OUTPUT_TOKENS = 2048


class GeminiProviderError(RuntimeError):
    """Error terkontrol dari layer provider Gemini."""


@dataclass(frozen=True, slots=True)
class GeminiProviderConfig:
    api_key: str
    model: str = DEFAULT_GEMINI_MODEL
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    max_output_tokens: int = DEFAULT_MAX_OUTPUT_TOKENS

    @classmethod
    def from_env(cls) -> "GeminiProviderConfig":
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise GeminiProviderError(
                "GEMINI_API_KEY belum di-set. Tambahkan key ke environment lokal; "
                "jangan commit secret ke repository."
            )

        model = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL
        timeout_raw = os.getenv("GEMINI_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)).strip()
        max_tokens_raw = os.getenv(
            "GEMINI_MAX_OUTPUT_TOKENS", str(DEFAULT_MAX_OUTPUT_TOKENS)
        ).strip()

        try:
            timeout_seconds = float(timeout_raw)
        except ValueError as exc:
            raise GeminiProviderError("GEMINI_TIMEOUT_SECONDS harus berupa angka.") from exc

        try:
            max_output_tokens = int(max_tokens_raw)
        except ValueError as exc:
            raise GeminiProviderError("GEMINI_MAX_OUTPUT_TOKENS harus berupa integer.") from exc

        if timeout_seconds <= 0:
            raise GeminiProviderError("GEMINI_TIMEOUT_SECONDS harus lebih besar dari 0.")
        if max_output_tokens <= 0:
            raise GeminiProviderError("GEMINI_MAX_OUTPUT_TOKENS harus lebih besar dari 0.")

        return cls(
            api_key=api_key,
            model=model,
            timeout_seconds=timeout_seconds,
            max_output_tokens=max_output_tokens,
        )


@dataclass(frozen=True, slots=True)
class GeminiTextResult:
    text: str
    provider: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    finish_reason: str | None = None


class GeminiProvider:
    """Async Gemini provider menggunakan official Google Gen AI SDK.

    Catatan desain:
    - API key hanya berasal dari environment/config, tidak pernah ditulis ke trace.
    - Provider tidak menyimpan business rule Clevia.
    - Menggunakan API v1 dan model stable secara default.
    - Tidak mengirim temperature/top_p/top_k karena parameter sampling tersebut
      sudah deprecated untuk generasi Gemini 3.6+.
    """

    provider_name = "gemini"

    def __init__(self, config: GeminiProviderConfig) -> None:
        self.config = config
        self._client: Any | None = None

    @classmethod
    def from_env(cls) -> "GeminiProvider":
        return cls(GeminiProviderConfig.from_env())

    def _get_client(self) -> Any:
        if self._client is not None:
            return self._client

        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise GeminiProviderError(
                "Dependency google-genai belum terpasang. Jalankan dependency install "
                "project setelah menerapkan patch."
            ) from exc

        timeout_ms = int(self.config.timeout_seconds * 1000)
        self._client = genai.Client(
            api_key=self.config.api_key,
            http_options=types.HttpOptions(api_version="v1", timeout=timeout_ms),
        )
        return self._client

    @staticmethod
    def _usage_value(usage: Any, *names: str) -> int | None:
        if usage is None:
            return None
        for name in names:
            value = getattr(usage, name, None)
            if isinstance(value, int):
                return value
        return None

    @staticmethod
    def _finish_reason(response: Any) -> str | None:
        candidates = getattr(response, "candidates", None)
        if not candidates:
            return None
        reason = getattr(candidates[0], "finish_reason", None)
        if reason is None:
            return None
        return getattr(reason, "name", None) or str(reason)

    async def generate_text(
        self,
        prompt: str,
        *,
        system_instruction: str | None = None,
        max_output_tokens: int | None = None,
    ) -> GeminiTextResult:
        if not prompt or not prompt.strip():
            raise GeminiProviderError("Prompt tidak boleh kosong.")

        client = self._get_client()
        try:
            from google.genai import types

            config = types.GenerateContentConfig(
                system_instruction=system_instruction or None,
                max_output_tokens=max_output_tokens or self.config.max_output_tokens,
            )
            response = await client.aio.models.generate_content(
                model=self.config.model,
                contents=prompt,
                config=config,
            )
        except GeminiProviderError:
            raise
        except Exception as exc:  # SDK/network errors are normalized here.
            raise GeminiProviderError(
                f"Gemini request gagal untuk model {self.config.model}: {type(exc).__name__}"
            ) from exc

        text = (getattr(response, "text", None) or "").strip()
        if not text:
            raise GeminiProviderError("Gemini mengembalikan response tanpa text.")

        usage = getattr(response, "usage_metadata", None)
        return GeminiTextResult(
            text=text,
            provider=self.provider_name,
            model=self.config.model,
            input_tokens=self._usage_value(usage, "prompt_token_count", "input_token_count"),
            output_tokens=self._usage_value(
                usage, "candidates_token_count", "output_token_count"
            ),
            total_tokens=self._usage_value(usage, "total_token_count"),
            finish_reason=self._finish_reason(response),
        )

    async def generate_json(
        self,
        prompt: str,
        *,
        system_instruction: str | None = None,
        max_output_tokens: int | None = None,
    ) -> tuple[dict[str, Any] | list[Any], GeminiTextResult]:
        if not prompt or not prompt.strip():
            raise GeminiProviderError("Prompt tidak boleh kosong.")

        client = self._get_client()
        try:
            from google.genai import types

            config = types.GenerateContentConfig(
                system_instruction=system_instruction or None,
                max_output_tokens=max_output_tokens or self.config.max_output_tokens,
                response_mime_type="application/json",
            )
            response = await client.aio.models.generate_content(
                model=self.config.model,
                contents=prompt,
                config=config,
            )
        except GeminiProviderError:
            raise
        except Exception as exc:
            raise GeminiProviderError(
                f"Gemini JSON request gagal untuk model {self.config.model}: {type(exc).__name__}"
            ) from exc

        text = (getattr(response, "text", None) or "").strip()
        if not text:
            raise GeminiProviderError("Gemini mengembalikan JSON response kosong.")

        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise GeminiProviderError("Gemini mengembalikan JSON yang tidak valid.") from exc

        if not isinstance(payload, (dict, list)):
            raise GeminiProviderError("Structured output harus berupa object atau array JSON.")

        usage = getattr(response, "usage_metadata", None)
        result = GeminiTextResult(
            text=text,
            provider=self.provider_name,
            model=self.config.model,
            input_tokens=self._usage_value(usage, "prompt_token_count", "input_token_count"),
            output_tokens=self._usage_value(
                usage, "candidates_token_count", "output_token_count"
            ),
            total_tokens=self._usage_value(usage, "total_token_count"),
            finish_reason=self._finish_reason(response),
        )
        return payload, result

    async def aclose(self) -> None:
        """Tutup koneksi SDK secara eksplisit saat lifecycle aplikasi berakhir."""
        if self._client is None:
            return
        try:
            await self._client.aio.aclose()
        finally:
            self._client.close()
            self._client = None
