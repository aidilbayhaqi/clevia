from __future__ import annotations

import json
import logging
import time
import uuid
from contextvars import ContextVar, Token
from dataclasses import dataclass, replace

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


logger = logging.getLogger("clevia.request")


@dataclass(frozen=True, slots=True)
class RequestContext:
    request_id: str
    clinic_id: uuid.UUID | None = None
    user_id: uuid.UUID | None = None
    channel: str = "http"


_request_context: ContextVar[RequestContext | None] = ContextVar(
    "clevia_request_context",
    default=None,
)


def get_request_context() -> RequestContext:
    context = _request_context.get()
    if context is None:
        return RequestContext(request_id=f"req_{uuid.uuid4().hex}")
    return context


def set_clinic_context(clinic_id: uuid.UUID) -> None:
    context = get_request_context()
    _request_context.set(replace(context, clinic_id=clinic_id))


def set_user_context(user_id: uuid.UUID, clinic_id: uuid.UUID | None = None) -> None:
    context = get_request_context()
    _request_context.set(
        replace(
            context,
            user_id=user_id,
            clinic_id=clinic_id if clinic_id is not None else context.clinic_id,
        )
    )


def _structured_log(level: int, payload: dict) -> None:
    logger.log(level, json.dumps(payload, ensure_ascii=False, default=str))


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex}"
        token: Token = _request_context.set(
            RequestContext(
                request_id=request_id,
                channel=request.headers.get("X-Clevia-Channel", "http"),
            )
        )
        started = time.perf_counter()
        try:
            response = await call_next(request)
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            context = get_request_context()
            response.headers["X-Request-ID"] = request_id
            _structured_log(
                logging.INFO,
                {
                    "event": "http_request",
                    "request_id": request_id,
                    "clinic_id": context.clinic_id,
                    "user_id": context.user_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status": response.status_code,
                    "latency_ms": elapsed_ms,
                },
            )
            return response
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
            context = get_request_context()
            _structured_log(
                logging.ERROR,
                {
                    "event": "http_request_error",
                    "request_id": request_id,
                    "clinic_id": context.clinic_id,
                    "user_id": context.user_id,
                    "method": request.method,
                    "path": request.url.path,
                    "latency_ms": elapsed_ms,
                    "error_type": type(exc).__name__,
                },
            )
            raise
        finally:
            _request_context.reset(token)
