# Audit Wiring LLM Clevia v0.6.2

- Canonical orchestrator tersedia: `True`
- File dipindai: `27`
- File dengan indikasi wiring LLM: `7`

## Kandidat wiring

### `app/agent/orchestrator.py`

Import relevan:
- `app.llm.prompt_registry`
- `app.llm.provider`

- L232: `outcome = "answered" if sources else "completed"`

### `app/llm/gemini_adapter.py`

Import relevan:
- `app.llm.gemini_provider`
- `app.llm.provider_contract`

- L1: `"""Adapter Gemini ke kontrak LLM canonical Clevia."""`
- L4: `from app.llm.gemini_provider import GeminiProvider`
- L8: `class GeminiLLMAdapter:`
- L9: `provider_name = "gemini"`
- L11: `def __init__(self, provider: GeminiProvider) -> None:`
- L15: `def from_env(cls) -> "GeminiLLMAdapter":`
- L16: `return cls(GeminiProvider.from_env())`
- L22: `async def complete(`
- L29: `result = await self._provider.generate_text(`

### `app/llm/gemini_provider.py`

- L1: `"""Gemini provider untuk Clevia.`
- L3: `Patch: clevia-p0-gemini-provider-v0.6.0`
- L5: `Tujuan modul ini adalah menyediakan provider Gemini yang terisolasi dari business logic.`
- L18: `DEFAULT_GEMINI_MODEL = "gemini-3.6-flash"`
- L23: `class GeminiProviderError(RuntimeError):`
- L24: `"""Error terkontrol dari layer provider Gemini."""`
- L28: `class GeminiProviderConfig:`
- L30: `model: str = DEFAULT_GEMINI_MODEL`
- L35: `def from_env(cls) -> "GeminiProviderConfig":`
- L36: `api_key = os.getenv("GEMINI_API_KEY", "").strip()`
- L38: `raise GeminiProviderError(`
- L39: `"GEMINI_API_KEY belum di-set. Tambahkan key ke environment lokal; "`
- L43: `model = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL`
- L44: `timeout_raw = os.getenv("GEMINI_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)).strip()`
- L46: `"GEMINI_MAX_OUTPUT_TOKENS", str(DEFAULT_MAX_OUTPUT_TOKENS)`
- L52: `raise GeminiProviderError("GEMINI_TIMEOUT_SECONDS harus berupa angka.") from exc`
- L57: `raise GeminiProviderError("GEMINI_MAX_OUTPUT_TOKENS harus berupa integer.") from exc`
- L60: `raise GeminiProviderError("GEMINI_TIMEOUT_SECONDS harus lebih besar dari 0.")`
- L62: `raise GeminiProviderError("GEMINI_MAX_OUTPUT_TOKENS harus lebih besar dari 0.")`
- L73: `class GeminiTextResult:`
- L83: `class GeminiProvider:`
- L84: `"""Async Gemini provider menggunakan official Google Gen AI SDK.`
- L91: `sudah deprecated untuk generasi Gemini 3.6+.`
- L94: `provider_name = "gemini"`
- L96: `def __init__(self, config: GeminiProviderConfig) -> None:`
- L101: `def from_env(cls) -> "GeminiProvider":`
- L102: `return cls(GeminiProviderConfig.from_env())`
- L112: `raise GeminiProviderError(`
- L144: `async def generate_text(`
- L150: `) -> GeminiTextResult:`
- L152: `raise GeminiProviderError("Prompt tidak boleh kosong.")`
- L167: `except GeminiProviderError:`
- L170: `raise GeminiProviderError(`
- L171: `f"Gemini request gagal untuk model {self.config.model}: {type(exc).__name__}"`
- L176: `raise GeminiProviderError("Gemini mengembalikan response tanpa text.")`
- L179: `return GeminiTextResult(`
- L197: `) -> tuple[dict[str, Any] | list[Any], GeminiTextResult]:`
- L199: `raise GeminiProviderError("Prompt tidak boleh kosong.")`
- L215: `except GeminiProviderError:`
- L218: `raise GeminiProviderError(`

### `app/llm/openai_adapter.py`

Import relevan:
- `app.llm.base`
- `openai`

- L5: `from openai import AsyncOpenAI`
- L11: `class OpenAIResponsesAdapter:`
- L12: `provider = "openai"`
- L14: `def _get_client(self) -> AsyncOpenAI:`
- L15: `if not settings.OPENAI_API_KEY:`
- L17: `"OPENAI_API_KEY is not configured. Set it in .env and restart the API container."`
- L19: `return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)`
- L30: `"model": settings.OPENAI_MODEL,`
- L31: `"reasoning": {"effort": settings.OPENAI_REASONING_EFFORT},`
- L39: `response = await client.responses.create(**kwargs)`
- L57: `model=settings.OPENAI_MODEL,`

### `app/llm/provider.py`

Import relevan:
- `app.llm.base`
- `app.llm.gemini_adapter`
- `app.llm.openai_adapter`

- L5: `from app.llm.gemini_adapter import GeminiGenerateContentAdapter`
- L6: `from app.llm.openai_adapter import OpenAIResponsesAdapter`
- L12: `if provider == "gemini":`
- L13: `return GeminiGenerateContentAdapter()`
- L15: `if provider == "openai":`
- L16: `return OpenAIResponsesAdapter()`
- L20: `"Supported providers: gemini, openai."`

### `app/llm/provider_contract.py`

- L30: `async def complete(`

### `app/llm/provider_factory.py`

Import relevan:
- `app.llm.gemini_adapter`
- `app.llm.provider_contract`

- L11: `from app.llm.gemini_adapter import GeminiLLMAdapter`
- L15: `DEFAULT_LLM_PROVIDER = "gemini"`
- L24: `_ALIASES = {"google": "gemini", "google-gemini": "gemini"}`
- L61: `def _build_gemini() -> LLMProvider:`
- L62: `return GeminiLLMAdapter.from_env()`
- L65: `register_llm_provider("gemini", _build_gemini)`

## Keputusan

Audit ini bersifat read-only. v0.6.2 memasang kontrak + factory, tetapi tidak menimpa orchestrator secara heuristik. Titik wiring dari report ini menjadi input patch berikutnya agar perubahan runtime bersifat eksplisit dan dapat diuji.
