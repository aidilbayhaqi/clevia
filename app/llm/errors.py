from __future__ import annotations


class LLMRuntimeError(RuntimeError):
    """Base class for controlled LLM/runtime failures."""


class LLMNotConfiguredError(LLMRuntimeError):
    """Provider configuration is missing or invalid."""


class LLMTimeoutError(LLMRuntimeError):
    """Provider request exceeded the configured deadline."""


class LLMRateLimitedError(LLMRuntimeError):
    """Provider rejected the request because of rate limiting."""


class LLMProviderError(LLMRuntimeError):
    """Provider/network failure safe to normalize for the public API."""


class LLMInvalidResponseError(LLMRuntimeError):
    """Provider/agent response could not complete the expected protocol."""
