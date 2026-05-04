# AGENTS.md

> Read this file before making any code changes. It defines how to work on this codebase.

## What this project is

A cross-platform desktop AI scratchpad — floating panel for quick chat + notes + tasks + reminders + snippets. Local-first, BYO-model, open source.

**Codename in code:** `smartpad` (lowercase package), `SmartPad` (display). This is a placeholder; rename happens before public release.

**Source of truth for product behaviour:** `SPEC.md`. If anything in this AGENTS.md conflicts with SPEC.md, SPEC.md wins.

## Cross-platform discipline (NON-NEGOTIABLE)

This app ships to Windows + macOS + Linux from v1. Every line of code must work on all three.

**Always:**
- `pathlib.Path` for paths, never string concat
- `utils/paths.py` to get platform-specific data dirs
- `QSystemTrayIcon.showMessage` for notifications
- `pynput` for hotkeys (with macOS Accessibility flow)
- `watchdog` for file watching
- Test on all three OSes via CI before merging

**Never:**
- `os.path.join` — use `Path` operators
- `win32com`, `pywin32`, or any Windows-only API without per-OS fallback
- Hardcoded `/` or `\` in paths
- Platform-specific notification APIs (toast4windows, pync, etc.)
- Raw inotify / FSEvents / ReadDirectoryChangesW

If a feature requires per-OS code, isolate it in a function under `utils/` with platform branching, never sprinkle `if sys.platform` in business logic.

## Architecture rules

### Layer separation
```
ui/      → PyQt6 widgets only. Imports from core/, db/, providers/. Never the reverse.
core/    → business logic. Pure Python. No PyQt imports allowed.
db/      → SQLAlchemy models + repositories. No business logic.
providers/ → AI provider adapters. Stateless. No UI imports.
tools/   → Tool registry + implementations. No UI imports.
api/     → FastAPI server. Calls into core/ and db/. No UI imports.
utils/   → Pure helpers. No internal imports from ui/, core/, db/.
```

**Test**: if you `import core` or `import db` from a UI file, it should work. If you need PyQt anywhere outside `ui/`, you've made a mistake — refactor.

### UI never blocks
The UI thread NEVER waits for:
- LLM calls (use worker pool)
- DB writes (use worker pool LOW priority)
- Network requests (httpx async via worker pool)
- File I/O on large files

UI handlers emit signals into the worker pool, return immediately. Worker pool emits signals back when done. No `await` in click handlers, no `time.sleep`, no synchronous DB calls in UI code.

### Optimistic UI rule
When user takes an action (save note, send message), the UI bubble appears in <100ms with a "saving" indicator. The actual DB write happens in the background. On success, indicator updates silently. On failure, show retry option in the bubble.

## Code style

### Python
- Python 3.11+ syntax (use `match`, `|` unions, `Self` type)
- SQLAlchemy 2.0 typed style (`Mapped[...]`, `mapped_column`, `select()`)
- Pydantic v2 for all data validation
- Type hints on every function signature
- `loguru` for logging, never `print()` in non-test code
- Docstrings on public functions (Google style)

### Datetimes
- Always timezone-aware UTC: `datetime.now(timezone.utc)`
- Never `datetime.now()` without tz
- Convert to local time only at display layer

### IDs
- All entity IDs are UUIDs as strings (TEXT in SQLite)
- Prefer uuid7 (time-ordered) where library allows; uuid4 acceptable
- Never autoincrement integer IDs (breaks sync)

### Errors
- Never bare `except:` — always specific exception types
- Errors in worker pool are caught and surfaced as ErrorBubble in UI
- Errors in API layer become structured JSON responses with proper HTTP codes
- All exceptions logged with loguru including stack trace

### Imports
- Standard library → third-party → local, separated by blank lines
- Absolute imports only (`from smartpad.core import router`), never relative
- No `import *` ever

## Git workflow

### Branch model
- `main` — release-only, tagged versions
- `develop` — active integration, default branch
- `feature/NN-name` — one feature branch per phase or feature
- `fix/issue-N` — bug fixes from issues
- `refactor/scope` — refactors that don't change behaviour

### Commits
Conventional Commits format:
```
<type>(<scope>): <subject>

<body>
```
Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `build`, `ci`, `perf`.

Example:
```
feat(notes): auto-extract deadlines from natural language

Uses dateparser to find time references in note content.
When found, save as Task with deadline instead of plain Note.
Falls back to plain Note if dateparser returns nothing.
```

### PRs
- One PR per phase from SPEC.md section 22
- PR description references the spec section being implemented
- All CI checks must pass (Windows + macOS + Linux + ruff + mypy + pytest)
- Self-review before requesting merge — read your own diff first
- Squash-merge to develop, never merge commits

### What requires a new branch
- Anything that adds, removes, or modifies a feature → feature branch
- Bug fix that takes >5 minutes → fix branch
- Trivial typo fix in docs → can go straight to develop

## Testing

### Required tests per phase
- Unit tests for any new function in `core/`, `db/`, `providers/`, `tools/`
- Integration test for any new repository method
- Smoke test that the app launches without crashing
- For UI changes: at least one pytest-qt test that creates the widget and verifies it renders

### Coverage target
80% on `core/`, `db/`, `providers/`, `tools/`. UI coverage is best-effort.

### Test data
- Tests use fresh SQLite in `tmp_path`, never the real DB
- Mock all HTTP calls, never hit real LLM providers in tests
- Mock file system writes for tests of save flows

## Spec adherence

The spec is canonical. If you think a feature should differ from SPEC.md, **stop and ask before changing code.** Don't quietly implement a different design and hope it's fine.

When the user requests something not in the spec:
1. Ask if it should be added to SPEC.md
2. Add it to `IDEAS.md` if it's for a future version
3. Implement only after the spec is updated

## What NOT to do

- Don't add a feature because "it would be cool" — stick to spec
- Don't pick libraries not listed in SPEC.md section 3 without asking
- Don't add telemetry, analytics, or crash reporting — spec section 17 forbids it
- Don't make assumptions about user environment (model availability, GPU, network) — defensive defaults always
- Don't write platform-specific code in business logic
- Don't use deprecated PyQt5 APIs — this is PyQt6
- Don't pre-optimize — write correct, readable code first
- Don't write CLI tools or scripts that aren't in the spec
- Don't commit binaries, models, GGUFs, or generated artifacts
- Don't push directly to main or develop — always via feature branch + PR

## Common patterns

### Adding a new tool
1. Create `tools/builtin/your_tool.py` with class extending `Tool`
2. Define schema (OpenAI function-calling format) in `schema()` method
3. Implement `execute(args) -> ToolResult` async
4. Register in `tools/registry.py`
5. Add unit test
6. Tool is now available to router automatically

### Adding a new provider
1. Create `providers/your_provider.py` extending `Provider`
2. Implement `list_models`, `chat`, `validate_credentials`
3. Register in `providers/registry.py`
4. Add tests with mocked HTTP
5. Add to settings dialog dropdown

### Adding a new bubble type
1. Create `ui/bubbles/your_bubble.py` extending `BubbleBase`
2. Define visual style in `styles.py`
3. Register render mapping in `ui/panel.py` for the corresponding `kind`
4. Add pytest-qt rendering test

### Adding a new save type (note/task/reminder/snippet)
This is a bigger lift. Requires:
1. New table in `db/models.py` with sync fields
2. Alembic migration (don't autogenerate, write manually for clarity)
3. Repository in `db/repositories/`
4. Tool in `tools/builtin/save_*.py`
5. Bubble in `ui/bubbles/`
6. Pattern in `core/intent_detector.py`
7. Slash command in `core/router.py`

If the spec doesn't already define the new type, ask before starting.

## Performance targets

These are the user-visible numbers from SPEC.md. Tests should verify them.

- UI response to user input: <100ms always
- First token from local LLM (idle warm): <300ms
- First token from cloud LLM: <500ms
- FTS5 search across 10k notes: <50ms
- App cold start to ready: <2s
- App memory baseline (no model loaded): <150MB

If a change makes any of these worse, justify it in the PR.

## When in doubt

Ask. Better to pause for 30 seconds and confirm than spend 2 hours building the wrong thing.

The product is better if it ships small and right than large and confused.
