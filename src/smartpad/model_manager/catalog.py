"""Curated local model catalog — SPEC.MD section 16.

Three tiers: Fast (small, low VRAM), Balanced (recommended default),
Smart (larger, better quality). All GGUF format for llama-server.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CatalogModel:
    id: str
    display_name: str
    tier: str          # "fast" | "balanced" | "smart"
    repo_id: str       # HuggingFace repo, e.g. "Qwen/Qwen3-1.7B-GGUF"
    filename: str      # GGUF filename to download
    size_gb: float     # approximate download size
    vram_gb: float     # approximate VRAM required
    context_length: int
    description: str


CATALOG: list[CatalogModel] = [
    CatalogModel(
        id="qwen3-1.7b-q4",
        display_name="Qwen3 1.7B (Fast, ~1GB)",
        tier="fast",
        repo_id="Qwen/Qwen3-1.7B-GGUF",
        filename="Qwen3-1.7B-Q4_K_M.gguf",
        size_gb=1.1,
        vram_gb=1.5,
        context_length=32768,
        description="Very fast, runs on any machine. Good for quick captures.",
    ),
    CatalogModel(
        id="qwen3-4b-q4",
        display_name="Qwen3 4B (Balanced, ~2.5GB) ★",
        tier="balanced",
        repo_id="Qwen/Qwen3-4B-GGUF",
        filename="Qwen3-4B-Q4_K_M.gguf",
        size_gb=2.5,
        vram_gb=3.5,
        context_length=32768,
        description="Recommended default. Great quality + speed balance.",
    ),
    CatalogModel(
        id="qwen3-8b-q4",
        display_name="Qwen3 8B (Smart, ~5GB)",
        tier="smart",
        repo_id="Qwen/Qwen3-8B-GGUF",
        filename="Qwen3-8B-Q4_K_M.gguf",
        size_gb=5.0,
        vram_gb=6.0,
        context_length=32768,
        description="Best quality. Requires 6GB+ VRAM or runs on CPU (slower).",
    ),
    CatalogModel(
        id="llama3.2-3b-q4",
        display_name="Llama 3.2 3B (Fast, ~2GB)",
        tier="fast",
        repo_id="bartowski/Llama-3.2-3B-Instruct-GGUF",
        filename="Llama-3.2-3B-Instruct-Q4_K_M.gguf",
        size_gb=2.0,
        vram_gb=3.0,
        context_length=131072,
        description="Fast Llama with very large context window.",
    ),
]


def get_by_id(model_id: str) -> CatalogModel | None:
    return next((m for m in CATALOG if m.id == model_id), None)


def get_by_tier(tier: str) -> list[CatalogModel]:
    return [m for m in CATALOG if m.tier == tier]


DEFAULT_MODEL_ID = "qwen3-1.7b-q4"
