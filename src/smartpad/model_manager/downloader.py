"""HuggingFace GGUF model downloader — SPEC.MD section 16.

Downloads model files from HuggingFace Hub to the local models directory.
Progress is reported via a callback so the UI can display a progress bar.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from pathlib import Path

import httpx
from loguru import logger

from smartpad.model_manager.catalog import CatalogModel

ProgressCallback = Callable[[int, int], None]  # (bytes_downloaded, total_bytes)

_HF_BASE = "https://huggingface.co"
_TIMEOUT = httpx.Timeout(connect=30.0, read=300.0, write=30.0, pool=5.0)


async def download_model(
    model: CatalogModel,
    models_dir: Path,
    on_progress: ProgressCallback | None = None,
    *,
    _client_factory: Callable[[], httpx.AsyncClient] | None = None,
) -> Path:
    """Download a GGUF model file to models_dir.

    Returns the local path of the downloaded file.
    Skips download if the file already exists and matches expected size.
    """
    models_dir.mkdir(parents=True, exist_ok=True)
    dest = models_dir / model.filename

    url = f"{_HF_BASE}/{model.repo_id}/resolve/main/{model.filename}"

    if dest.exists():
        size_mb = dest.stat().st_size / 1_048_576
        expected_mb = model.size_gb * 1024
        if size_mb >= expected_mb * 0.95:
            logger.info("Model {} already downloaded at {}", model.filename, dest)
            return dest
        logger.info("Incomplete model file found, re-downloading {}", model.filename)
        dest.unlink()

    logger.info("Downloading {} from {}", model.filename, url)

    make_client = _client_factory or (lambda: httpx.AsyncClient(timeout=_TIMEOUT, follow_redirects=True))

    async with make_client() as client, client.stream("GET", url) as response:
        response.raise_for_status()
        total = int(response.headers.get("content-length", 0))
        downloaded = 0

        with dest.open("wb") as f:
            async for chunk in response.aiter_bytes(chunk_size=65536):
                f.write(chunk)
                downloaded += len(chunk)
                if on_progress:
                    on_progress(downloaded, total)

    logger.success("Downloaded {} ({:.1f} MB)", model.filename, dest.stat().st_size / 1_048_576)
    return dest


def is_downloaded(model: CatalogModel, models_dir: Path) -> bool:
    dest = models_dir / model.filename
    if not dest.exists():
        return False
    size_mb = dest.stat().st_size / 1_048_576
    return size_mb >= model.size_gb * 1024 * 0.95


async def cancel_download() -> None:
    """Placeholder — real cancellation via asyncio.Task.cancel() from caller."""
    await asyncio.sleep(0)
