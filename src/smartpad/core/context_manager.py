"""Context window management — SPEC.md section 8.

Sliding-window summarisation to keep conversation context
within token/message limits. Works on in-memory message lists only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from smartpad.providers.base import ChatMessage

if TYPE_CHECKING:
    from smartpad.providers.base import Provider


def _estimate_tokens(messages: list[ChatMessage]) -> int:
    """Rough heuristic: chars / 4 ≈ tokens."""
    return sum(len(m.content) // 4 for m in messages)


class ContextManager:
    """Manages conversation context to avoid hitting token limits.

    Supports three strategies:
    - ``none``: pass through unchanged
    - ``truncate``: drop oldest messages
    - ``sliding_summary``: summarise oldest chunk, keep recent
    """

    def __init__(
        self,
        *,
        strategy: str = "sliding_summary",
        trigger_messages: int = 30,
        trigger_tokens: int = 6000,
        messages_per_summary: int = 15,
        recent_kept: int = 15,
    ) -> None:
        self.strategy = strategy
        self.trigger_messages = trigger_messages
        self.trigger_tokens = trigger_tokens
        self.messages_per_summary = messages_per_summary
        self.recent_kept = recent_kept

    # ── public API ─────────────────────────────────────────────────────────────

    def needs_summarisation(self, messages: list[ChatMessage]) -> bool:
        """Return True if context should be compressed."""
        if self.strategy == "none":
            return False
        if len(messages) > self.trigger_messages:
            logger.debug(
                "Context trigger: {} messages > threshold {}",
                len(messages),
                self.trigger_messages,
            )
            return True
        tokens = _estimate_tokens(messages)
        if tokens > self.trigger_tokens:
            logger.debug(
                "Context trigger: ~{} tokens > threshold {}",
                tokens,
                self.trigger_tokens,
            )
            return True
        return False

    async def summarise(
        self,
        messages: list[ChatMessage],
        provider: Provider,
        model: str,
    ) -> list[ChatMessage]:
        """Compress *messages* according to the configured strategy.

        Args:
            messages: Current in-memory message list.
            provider: Active AI provider used to generate the summary.
            model: Model identifier to use for summarisation.

        Returns:
            Updated message list (shorter than input).
        """
        if self.strategy == "none" or not messages:
            return messages

        if self.strategy == "truncate":
            return self._truncate(messages)

        if self.strategy == "sliding_summary":
            return await self._sliding_summary(messages, provider, model)

        logger.warning("Unknown context strategy '{}'; passing through.", self.strategy)
        return messages

    # ── strategies ─────────────────────────────────────────────────────────────

    def _truncate(self, messages: list[ChatMessage]) -> list[ChatMessage]:
        """Drop oldest messages, keeping only `recent_kept` most recent."""
        kept = messages[-self.recent_kept :]
        dropped = len(messages) - len(kept)
        logger.info("Context truncate: dropped {} oldest messages.", dropped)
        return kept

    async def _sliding_summary(
        self,
        messages: list[ChatMessage],
        provider: Provider,
        model: str,
    ) -> list[ChatMessage]:
        """Summarise the oldest `messages_per_summary` messages and keep the rest."""
        # Need enough messages to make summarisation worthwhile
        if len(messages) <= self.recent_kept:
            return messages

        to_summarise = messages[: self.messages_per_summary]
        to_keep = messages[self.messages_per_summary :]

        summary_text = await self._call_summary(to_summarise, provider, model)
        summary_msg = ChatMessage(
            role="system",
            content=f"[Earlier conversation summary]\n{summary_text}",
        )
        result = [summary_msg, *to_keep]
        logger.info(
            "Context sliding_summary: summarised {} messages into 1 system message; "
            "keeping {} recent.",
            len(to_summarise),
            len(to_keep),
        )
        return result

    async def _call_summary(
        self,
        messages: list[ChatMessage],
        provider: Provider,
        model: str,
    ) -> str:
        """Ask the provider to summarise the given messages."""
        transcript_lines: list[str] = []
        for msg in messages:
            role_label = msg.role.capitalize()
            transcript_lines.append(f"{role_label}: {msg.content}")
        transcript = "\n".join(transcript_lines)

        prompt_messages = [
            ChatMessage(
                role="system",
                content=(
                    "You are a conversation summariser. "
                    "Write a concise summary of the following conversation fragment. "
                    "Capture key topics, decisions, and saved items. "
                    "Be factual and brief."
                ),
            ),
            ChatMessage(
                role="user",
                content=f"Summarise this conversation:\n\n{transcript}",
            ),
        ]

        chunks: list[str] = []
        async for chunk in await provider.chat(  # type: ignore[call-overload]
            prompt_messages,
            model=model,
            temperature=0.0,
            max_tokens=512,
            stream=False,
        ):
            chunks.append(chunk.delta)
        return "".join(chunks).strip()
