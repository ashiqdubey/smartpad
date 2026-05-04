"""Priority worker pool — SPEC.md section 9 (Async Engine).

Two queues: HIGH (chat LLM, user-facing search) and LOW (saves, AI metadata,
FTS index updates, grammar/enhance, book classification).

Architecture:
- WorkerPool owns a QThread running an asyncio event loop
- UI enqueues Job objects via submit_high() / submit_low()
- Jobs are coroutines; results/errors come back via Qt signals
- The UI thread NEVER awaits — it emits signals, the pool calls back

Usage:
    pool = WorkerPool()
    pool.start()
    job = pool.submit_high(my_coro(), job_id="j1")
    pool.result_ready.connect(on_result)
    pool.error_occurred.connect(on_error)
"""

from __future__ import annotations

import asyncio
import queue
import threading
import uuid
from collections.abc import Coroutine
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any

from loguru import logger

# Qt is only imported when running inside a Qt application.
# For non-Qt console tests the pool falls back to a plain thread.
try:
    from PyQt6.QtCore import QObject, QThread, pyqtSignal

    _QT_AVAILABLE = True
except ImportError:  # pragma: no cover
    _QT_AVAILABLE = False


class Priority(IntEnum):
    HIGH = 0  # chat LLM, user-facing search
    LOW = 1  # saves, AI metadata, FTS updates


@dataclass(order=True)
class Job:
    priority: Priority
    seq: int = field(compare=True)  # FIFO within same priority
    job_id: str = field(compare=False)
    coro: Coroutine[Any, Any, Any] = field(compare=False)

    def __post_init__(self) -> None:
        if not self.job_id:
            self.job_id = str(uuid.uuid4())


class _JobQueue:
    """Thread-safe priority queue for Job objects."""

    def __init__(self) -> None:
        self._q: queue.PriorityQueue[Job] = queue.PriorityQueue()
        self._seq = 0

    def put(self, priority: Priority, coro: Coroutine[Any, Any, Any], job_id: str = "") -> Job:
        self._seq += 1
        job = Job(priority=priority, seq=self._seq, job_id=job_id or str(uuid.uuid4()), coro=coro)
        self._q.put(job)
        return job

    def get(self) -> Job:
        return self._q.get()

    def task_done(self) -> None:
        self._q.task_done()

    def empty(self) -> bool:
        return self._q.empty()


# ── Callbacks (console / non-Qt) ──────────────────────────────────────────────

ResultCallback = Any  # (job_id: str, result: Any) -> None
ErrorCallback = Any   # (job_id: str, exc: Exception) -> None


class _AsyncWorker(threading.Thread):
    """Daemon thread running an asyncio loop that drains the job queue."""

    def __init__(
        self,
        job_queue: _JobQueue,
        on_result: ResultCallback | None = None,
        on_error: ErrorCallback | None = None,
    ) -> None:
        super().__init__(daemon=True, name="SmartPadWorker")
        self._queue = job_queue
        self._on_result = on_result
        self._on_error = on_error
        self._loop: asyncio.AbstractEventLoop | None = None
        self._stop_event = threading.Event()

    def stop(self) -> None:
        self._stop_event.set()

    def run(self) -> None:
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._drain())
        finally:
            self._loop.close()

    async def _drain(self) -> None:
        while not self._stop_event.is_set():
            try:
                job = self._queue.get()
            except Exception:
                break
            try:
                result = await job.coro
                if self._on_result:
                    self._on_result(job.job_id, result)
            except Exception as exc:
                logger.exception("Worker job {} failed: {}", job.job_id, exc)
                if self._on_error:
                    self._on_error(job.job_id, exc)
            finally:
                self._queue.task_done()


# ── Qt-aware pool (used by the real app) ──────────────────────────────────────

if _QT_AVAILABLE:

    class _WorkerThread(QThread):
        result_ready = pyqtSignal(str, object)   # job_id, result
        error_occurred = pyqtSignal(str, object)  # job_id, exception

        def __init__(self, job_queue: _JobQueue, parent: QObject | None = None) -> None:
            super().__init__(parent)
            self._queue = job_queue
            self._loop: asyncio.AbstractEventLoop | None = None

        def run(self) -> None:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            try:
                self._loop.run_until_complete(self._drain())
            finally:
                self._loop.close()

        async def _drain(self) -> None:
            while True:
                try:
                    job = await asyncio.get_event_loop().run_in_executor(
                        None, self._queue.get
                    )
                except Exception:
                    break
                try:
                    result = await job.coro
                    self.result_ready.emit(job.job_id, result)
                except Exception as exc:
                    logger.exception("Worker job {} failed: {}", job.job_id, exc)
                    self.error_occurred.emit(job.job_id, exc)
                finally:
                    self._queue.task_done()

    class WorkerPool(QObject):
        """Qt-native priority worker pool. Signals are thread-safe."""

        result_ready = pyqtSignal(str, object)   # job_id, result
        error_occurred = pyqtSignal(str, object)  # job_id, exception

        def __init__(self, parent: QObject | None = None) -> None:
            super().__init__(parent)
            self._queue = _JobQueue()
            self._thread = _WorkerThread(self._queue, parent=self)
            self._thread.result_ready.connect(self.result_ready)
            self._thread.error_occurred.connect(self.error_occurred)

        def start(self) -> None:
            self._thread.start()

        def stop(self) -> None:
            self._thread.quit()
            self._thread.wait(3000)

        def submit_high(
            self,
            coro: Coroutine[Any, Any, Any],
            job_id: str = "",
        ) -> str:
            job = self._queue.put(Priority.HIGH, coro, job_id)
            logger.debug("Enqueued HIGH job {}", job.job_id)
            return job.job_id

        def submit_low(
            self,
            coro: Coroutine[Any, Any, Any],
            job_id: str = "",
        ) -> str:
            job = self._queue.put(Priority.LOW, coro, job_id)
            logger.debug("Enqueued LOW job {}", job.job_id)
            return job.job_id

else:  # pragma: no cover — only reached if PyQt6 is not installed

    class WorkerPool:  # type: ignore[no-redef]
        """Fallback pool without Qt signals — for headless testing."""

        def __init__(self) -> None:
            self._queue = _JobQueue()
            self._worker: _AsyncWorker | None = None
            self._results: dict[str, Any] = {}
            self._errors: dict[str, Exception] = {}

        def start(self) -> None:
            self._worker = _AsyncWorker(
                self._queue,
                on_result=lambda jid, r: self._results.__setitem__(jid, r),
                on_error=lambda jid, e: self._errors.__setitem__(jid, e),
            )
            self._worker.start()

        def stop(self) -> None:
            if self._worker:
                self._worker.stop()

        def submit_high(self, coro: Coroutine[Any, Any, Any], job_id: str = "") -> str:
            return self._queue.put(Priority.HIGH, coro, job_id).job_id

        def submit_low(self, coro: Coroutine[Any, Any, Any], job_id: str = "") -> str:
            return self._queue.put(Priority.LOW, coro, job_id).job_id
