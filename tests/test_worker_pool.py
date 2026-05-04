"""Tests for the priority worker pool — no Qt UI, pure asyncio + threading."""

from __future__ import annotations

import asyncio
import threading
import time

import pytest

from smartpad.core.worker_pool import Priority, _AsyncWorker, _JobQueue


# ── _JobQueue ─────────────────────────────────────────────────────────────────

def _closed_coro(coro: object) -> object:
    """Close a coroutine immediately (test queue ordering, not execution)."""
    c = coro  # type: ignore[assignment]
    c.close()  # type: ignore[attr-defined]
    return coro


def test_job_queue_priority_ordering() -> None:
    """HIGH jobs must come out before LOW jobs regardless of insertion order."""
    q = _JobQueue()

    async def noop() -> str:
        return "done"

    # Insert LOW first, then HIGH (coroutines closed immediately — we test ordering only)
    low_job = q.put(Priority.LOW, _closed_coro(noop()), "low")  # type: ignore[arg-type]
    high_job = q.put(Priority.HIGH, _closed_coro(noop()), "high")  # type: ignore[arg-type]

    first = q.get()
    second = q.get()
    assert first.priority == Priority.HIGH
    assert second.priority == Priority.LOW
    assert first.job_id == "high"
    assert second.job_id == "low"


def test_job_queue_fifo_within_same_priority() -> None:
    """Jobs at the same priority must come out in insertion order."""
    q = _JobQueue()

    async def noop() -> None:
        pass

    q.put(Priority.HIGH, _closed_coro(noop()), "first")  # type: ignore[arg-type]
    q.put(Priority.HIGH, _closed_coro(noop()), "second")  # type: ignore[arg-type]
    q.put(Priority.HIGH, _closed_coro(noop()), "third")  # type: ignore[arg-type]

    assert q.get().job_id == "first"
    assert q.get().job_id == "second"
    assert q.get().job_id == "third"


def test_job_queue_auto_job_id() -> None:
    q = _JobQueue()

    async def noop() -> None:
        pass

    job = q.put(Priority.LOW, _closed_coro(noop()))  # type: ignore[arg-type]
    assert job.job_id  # must be non-empty


# ── _AsyncWorker ──────────────────────────────────────────────────────────────

def _run_jobs_and_collect(
    coros: list[tuple[Priority, object]],
    timeout: float = 2.0,
) -> tuple[dict[str, object], dict[str, Exception]]:
    """Helper: submit jobs, drain worker, collect results/errors."""
    q = _JobQueue()
    results: dict[str, object] = {}
    errors: dict[str, Exception] = {}
    done = threading.Event()
    total = len(coros)
    seen: list[int] = [0]

    def on_result(jid: str, r: object) -> None:
        results[jid] = r
        seen[0] += 1
        if seen[0] >= total:
            done.set()

    def on_error(jid: str, exc: Exception) -> None:
        errors[jid] = exc
        seen[0] += 1
        if seen[0] >= total:
            done.set()

    worker = _AsyncWorker(q, on_result=on_result, on_error=on_error)
    worker.start()

    job_ids = []
    for priority, coro in coros:
        job = q.put(priority, coro)
        job_ids.append(job.job_id)

    done.wait(timeout=timeout)
    worker.stop()
    return results, errors


def test_worker_executes_coroutine() -> None:
    async def compute() -> int:
        return 42

    results, errors = _run_jobs_and_collect([(Priority.HIGH, compute())])
    assert len(errors) == 0
    assert 42 in results.values()


def test_worker_captures_exception() -> None:
    async def boom() -> None:
        raise ValueError("intentional")

    results, errors = _run_jobs_and_collect([(Priority.HIGH, boom())])
    assert len(results) == 0
    assert len(errors) == 1
    exc = next(iter(errors.values()))
    assert isinstance(exc, ValueError)
    assert "intentional" in str(exc)


def test_worker_runs_multiple_jobs() -> None:
    results_list: list[int] = []
    lock = threading.Lock()

    async def append(n: int) -> int:
        with lock:
            results_list.append(n)
        return n

    coros = [(Priority.HIGH, append(i)) for i in range(5)]
    results, errors = _run_jobs_and_collect(coros)
    assert len(errors) == 0
    assert sorted(results.values()) == list(range(5))


def test_worker_high_before_low() -> None:
    """HIGH-priority job result must arrive before LOW when submitted close together."""
    order: list[str] = []
    lock = threading.Lock()

    async def tag(label: str) -> str:
        await asyncio.sleep(0.01)  # small delay so ordering matters
        with lock:
            order.append(label)
        return label

    # Enqueue BOTH jobs BEFORE starting the worker so the priority queue
    # decides the order rather than the wall-clock race between enqueue and dequeue.
    q = _JobQueue()
    q.put(Priority.LOW, tag("low"))
    q.put(Priority.HIGH, tag("high"))

    done = threading.Event()
    seen: list[int] = [0]

    def on_result(jid: str, r: object) -> None:
        seen[0] += 1
        if seen[0] >= 2:
            done.set()

    worker = _AsyncWorker(q, on_result=on_result, on_error=on_result)
    worker.start()

    done.wait(timeout=3.0)
    worker.stop()

    # The first item processed should be "high"
    assert order[0] == "high"


def test_worker_async_io_inside_job() -> None:
    """Jobs can contain real async I/O (sleep) without blocking the thread."""

    async def slow() -> str:
        await asyncio.sleep(0.05)
        return "async-ok"

    results, errors = _run_jobs_and_collect([(Priority.HIGH, slow())])
    assert "async-ok" in results.values()
    assert not errors
