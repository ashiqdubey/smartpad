# SmartPad

**Your AI second brain — fast, private, local-first, bring your own model.**

Status: Early development, not yet released.

---

## Stack

| Layer | Choice |
|---|---|
| Language | Python 3.11+ |
| GUI | PyQt6 |
| DB | SQLite + SQLAlchemy + Alembic |
| HTTP client | httpx (async) |
| Local API | FastAPI + uvicorn |
| Hotkey | pynput |
| Packaging | PyInstaller |
| Config | pydantic-settings |
| Logging | loguru |

## Platform support

Cross-platform: Windows, macOS, Linux. Mobile not planned.

## Specification

See [SPEC.MD](SPEC.MD) for full product specification.

## Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run
python -m smartpad

# Tests
pytest tests/

# Lint
ruff check src/
```
