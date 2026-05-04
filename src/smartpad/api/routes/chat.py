"""Chat API route — SPEC.md section 13.

SSE streaming proxy to the active AI provider.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from smartpad.providers.base import ChatMessage
from smartpad.providers.registry import get_active

router = APIRouter()


class ChatRequest(BaseModel):
    messages: list[dict[str, str]]
    model: str = ""
    temperature: float = 0.7
    max_tokens: int | None = None
    stream: bool = True


@router.post("/chat")
async def chat_endpoint(body: ChatRequest, request: Request) -> StreamingResponse:
    """Proxy a chat request to the active provider via SSE."""
    provider = get_active()
    if provider is None:
        raise HTTPException(status_code=503, detail="No active AI provider configured.")

    messages = [
        ChatMessage(role=m["role"], content=m["content"])
        for m in body.messages
    ]
    model = body.model

    async def _event_stream() -> AsyncGenerator[str, None]:
        try:
            async for chunk in await provider.chat(  # type: ignore[call-overload]
                messages,
                model=model,
                temperature=body.temperature,
                max_tokens=body.max_tokens,
                stream=body.stream,
            ):
                if chunk.delta:
                    yield f"data: {chunk.delta}\n\n"
                if chunk.finish_reason:
                    yield "data: [DONE]\n\n"
                    return
        except Exception as exc:  # noqa: BLE001
            yield f"data: [ERROR] {exc}\n\n"

    return StreamingResponse(_event_stream(), media_type="text/event-stream")
