# Claude Code Kickoff — SmartPad

This is the prompt to paste into Claude Code as your **very first message** in a fresh empty folder. It bootstraps everything: project scaffold, git, GitHub repo, branch strategy, and the first build step from the spec.

The codename is **SmartPad**. You'll rename later when you pick a final name. For now this lets us ship code without blocking on naming.

---

## Before you paste — one-time setup

You need these installed and authenticated on your machine:

1. **Git** — `git --version`
2. **GitHub CLI** — install from cli.github.com, then run `gh auth login` once
3. **Python 3.11+** — `python --version`
4. **Claude Code** — installed and ready in an empty folder

Then drop **`SPEC.md`** AND **`AGENTS.md`** into that empty folder. Those are the only two files that should exist before you start. SPEC.md defines what the product does. AGENTS.md defines how to work on the codebase. Both are required.

---

## The kickoff prompt — paste this into Claude Code

```
You are setting up a brand new desktop app project from scratch.
The complete spec is in @SPEC.md and the working conventions are in @AGENTS.md.
Read BOTH files fully before doing anything else.

Project codename: smartpad (lowercase for repo/package, "SmartPad" for display).
This is a placeholder name; the user will rename later via global find-replace.

=== PHASE 0: REPO INITIALIZATION ===

Do these in order, in the current empty folder:

1. Initialize git: `git init -b main`

2. Create .gitignore for Python + PyQt + PyInstaller projects. Include:
   - __pycache__/, *.pyc, *.pyo
   - .venv/, venv/, env/
   - dist/, build/, *.spec (except smartpad.spec we'll commit later)
   - *.db, *.db-journal (SQLite)
   - .env, .env.local
   - logs/, *.log
   - .DS_Store, Thumbs.db
   - .idea/, .vscode/ (let user decide later)
   - models/ (downloaded GGUFs are huge, never commit)
   - backups/

3. Create a minimal README.md with:
   - One-line pitch from spec section 1
   - "Status: Early development, not yet released"
   - Stack summary
   - "Cross-platform: Windows, macOS, Linux. Mobile not planned."
   - "See SPEC.md for full product specification"

4. Create LICENSE file with standard MIT license, year 2026,
   author placeholder "[Your Name]" — user will fill in.

5. Create CHANGELOG.md with one entry:
   "## [Unreleased] - Initial development"

6. **Drop in AGENTS.md** — the user provides this file alongside SPEC.md.
   This file defines code style, architecture rules, git workflow, and
   conventions for AI agents working on the codebase. READ IT BEFORE
   EVERY PHASE.

7. Create .github/workflows/ci.yml — a basic CI workflow that runs
   on push and pull_request to develop, with matrix:
   strategy:
     matrix:
       os: [windows-latest, macos-latest, ubuntu-latest]
       python-version: ["3.11", "3.12"]
   Steps: checkout, setup-python, install deps, run pytest, run ruff check.
   This catches platform-specific bugs from day one.

8. Create .github/workflows/release.yml — placeholder for now, fully
   implemented in Phase 23. Must trigger on tag v*.*.* and produce
   release artifacts for all three platforms. Leave a TODO comment for now
   but set up the file structure so it exists.

9. Initial commit:
   git add .
   git commit -m "chore: initial repo setup with spec, AGENTS.md, license, and CI matrix"

10. Create GitHub repo and push:
    gh repo create smartpad --public --source=. --remote=origin --push \
      --description "Floating AI scratchpad — ask, save, search. Cross-platform desktop. Local-first, BYO-model."

    If the user is not authenticated with gh, output the exact command they
    need to run (`gh auth login`) and STOP, asking them to authenticate
    then re-run this prompt.

11. Create the branch strategy:
    - main → protected, only release-tagged merges later
    - develop → working branch for active development
    - feature/* → individual features

    Run:
    git checkout -b develop
    git push -u origin develop

    Then on GitHub via gh CLI:
    gh repo edit --default-branch develop

    (We'll keep main for stable releases later. Active work happens on develop.)

12. Create initial feature branch for phase 1:
    git checkout -b feature/01-project-scaffold

=== PHASE 1: PROJECT SCAFFOLD ===

Now build section 22 step 1 from SPEC.md:
"Project scaffold + pyproject.toml + Alembic init + first migration"

Specifically:

1. Create pyproject.toml using setuptools with:
   - name = "smartpad"
   - version = "0.0.1"
   - python_requires = ">=3.11"
   - All dependencies from SPEC.md section 3 (PyQt6, SQLAlchemy, alembic,
     httpx, fastapi, uvicorn, pynput, zeroconf, pydantic-settings, loguru,
     keyring, markdown-it-py, dateparser)
   - Dev dependencies: pytest, pytest-qt, pytest-asyncio, ruff, mypy
   - Entry point: smartpad = "smartpad.__main__:main"
   - Console script for CLI testing during development

2. Create the full directory tree from SPEC.md section 4 with empty
   __init__.py files in each Python package. Include all subfolders for
   ui/, ui/bubbles/, core/, providers/, tools/, tools/builtin/, db/,
   db/repositories/, api/, api/routes/, model_manager/, utils/, resources/,
   resources/icons/, resources/themes/, alembic/versions/.

3. Create src/smartpad/__main__.py with a stub:
   def main():
       print("SmartPad starting...")
   if __name__ == "__main__":
       main()

4. Create src/smartpad/config.py with pydantic-settings BaseSettings class
   covering ALL settings from SPEC.md section 17 (Defaults Locked).
   Each with proper type hints and documented defaults. Settings should
   load from a JSON file at <DATA_DIR>/config.json with environment
   override support. Include the portable-mode detection logic from
   SPEC.md section 15.

5. Initialize Alembic:
   - Run alembic init alembic (or create files manually)
   - Configure alembic.ini and alembic/env.py to point at the SQLAlchemy
     metadata in src/smartpad/db/models.py (which we'll create next)
   - Use the DATA_DIR-aware SQLite URL from config

6. Create src/smartpad/db/models.py with ALL SQLAlchemy ORM models
   matching the schema in SPEC.md section 5 EXACTLY:
   - Message, Note, Task, Reminder, Snippet, Book, Provider, Setting,
     PairedDevice
   - Plus the FTS5 virtual table created via raw SQL in the migration
   - All UUID primary keys, soft-delete fields, sync fields, indexes
   - Use SQLAlchemy 2.0 typed style (Mapped[...], mapped_column)

7. Generate the first Alembic migration:
   alembic revision --autogenerate -m "initial schema"
   Then add the FTS5 virtual table creation manually to the migration
   (autogenerate doesn't handle virtual tables).

8. Create a quick smoke test in tests/test_smoke.py:
   - Imports smartpad
   - Creates a temp DB
   - Runs migrations
   - Inserts one message
   - Reads it back
   - Asserts FTS5 table exists

9. Verify everything runs:
   - `pip install -e ".[dev]"` succeeds
   - `python -m smartpad` prints "SmartPad starting..."
   - `pytest tests/` passes
   - `alembic upgrade head` creates a fresh DB cleanly

10. Commit phase 1:
    git add .
    git commit -m "feat(scaffold): project structure, config, ORM models, initial migration

    - pyproject.toml with all spec dependencies
    - Full directory tree per SPEC.md section 4
    - Pydantic-settings config covering all defaults from SPEC.md section 17
    - SQLAlchemy 2.0 models for all entities in SPEC.md section 5
    - Alembic initial migration with FTS5 virtual table
    - Portable-mode detection
    - Smoke test passing"

    git push -u origin feature/01-project-scaffold

11. Open a PR for review:
    gh pr create \
      --base develop \
      --title "Phase 1: Project scaffold" \
      --body "Implements section 22 step 1 from SPEC.md. See commit message for details. Ready for review before merging to develop."

=== STOP HERE ===

After phase 1 is done and the PR is open, STOP. Show me:
- The repo URL on GitHub
- The PR URL
- Output of `python -m smartpad` and `pytest tests/`
- Confirmation that `alembic upgrade head` runs cleanly

Wait for me to either approve the PR or request changes before moving to phase 2.

=== RULES FOR ALL PHASES ===

- ALWAYS re-read @AGENTS.md at the start of every phase — it has the conventions
- ALWAYS reference @SPEC.md for product behaviour decisions
- One feature branch per phase (feature/02-..., feature/03-..., etc.)
- Each phase ends with a working app, a commit, a push, and a PR
- Never skip the smoke/integration tests at each phase
- Use SQLAlchemy 2.0 typed syntax throughout, never legacy Query API
- Every async function uses asyncio properly; never block the UI thread
- All file paths use pathlib.Path, never string concatenation
- All datetimes are timezone-aware UTC
- All UUIDs are uuid7 (time-ordered) where possible, uuid4 acceptable
- Logging via loguru, configured once in app.py, never print() in production code
- Type hints on every function, mypy must pass
- Ruff format + ruff check must pass before each commit

CROSS-PLATFORM RULES (this is desktop-only but ALL THREE OSes from v1):
- Never use os.path string concatenation, always pathlib.Path
- Never use Windows-only APIs (win32com, pywin32) without per-OS fallback
- Never hardcode forward or back slashes in any path
- Use utils/paths.py to abstract OS-specific data dirs:
  - Windows: %APPDATA%/smartpad/
  - macOS: ~/Library/Application Support/smartpad/
  - Linux: ~/.local/share/smartpad/ (XDG_DATA_HOME respected)
- Notifications: QSystemTrayIcon.showMessage only, never platform-specific APIs
- Hotkeys: pynput. On macOS detect missing Accessibility permission and guide user.
- File watching: watchdog library only, never raw inotify/FSEvents
- CI matrix runs on Windows + macOS + Linux for every PR — if any platform breaks, fix before merging
- llama-server binaries are platform-specific; ManagedLocalProvider must download
  the correct binary from llama.cpp GitHub releases per OS
- Test on Linux (Ubuntu via CI is fine), Windows, and macOS before tagging any release.
  If you don't have all three machines, use GitHub Actions runners as your test bed.

When in doubt, ask before assuming. Don't invent product behaviour
that isn't in SPEC.md.
```

---

## After Phase 1 — what comes next

Once Phase 1 is approved and merged to `develop`, paste this for Phase 2:

```
Phase 1 is merged. Now do Phase 2: SPEC.md section 22 step 2 —
db/models.py was already done; now add db/repositories/ with all
the repository pattern classes (NotesRepo, TasksRepo, RemindersRepo,
SnippetsRepo, BooksRepo, ChatRepo, ProvidersRepo, SettingsRepo).

Each repository:
- Constructor takes a Session
- Methods: save(entity), get(id), list(filters), search(query), soft_delete(id)
- Returns ORM objects, not dicts
- All async methods use AsyncSession (for compatibility with FastAPI later)
- Includes integration tests covering CRUD + soft-delete + sync field updates

Branch: feature/02-repositories
Commit, push, PR to develop. Then STOP and show me the PR.
```

The pattern continues: Phase 3 = providers, Phase 4 = worker pool, etc. — all 23 phases from SPEC.md section 22. **Each phase = one PR.** This keeps the work reviewable, the history clean, and lets you stop at any point with a working app.

---

## Phase prompts — quick reference for all 23

You'll just copy each of these as you finish the previous phase. Paste them one at a time.

```
Phase 03 → providers: feature/03-providers
"Implement SPEC.md section 22 step 3: Provider abstraction (base.py) plus
OpenAICompatibleProvider only. Skip Anthropic, Google, ManagedLocal for now.
Include unit tests with mocked HTTP."

Phase 04 → worker pool: feature/04-worker-pool
"Implement SPEC.md section 22 step 4: priority worker pool from spec section
9 (Async Engine). Two queues (HIGH/LOW), QThread-based, signal-based UI updates.
Console-driven test harness only — no UI yet."

Phase 05 → router: feature/05-router
"Implement SPEC.md section 22 step 5: router + intent_detector + pattern
matching from spec section 7. Slash commands and pattern matching only —
LLM routing call comes in phase 9."

Phase 06 → floating panel: feature/06-floating-panel
"Implement SPEC.md section 22 step 6: floating panel UI + tray + global hotkey.
Hardcoded OpenAI-compatible provider, basic chat working end to end. This
is the first visually demoable phase."

Phase 07 → bubbles: feature/07-bubble-widgets
"Implement SPEC.md section 22 step 7: all bubble widgets per spec section 12.
ChatBubble, NoteBubble, TaskBubble, ReminderBubble, SnippetBubble, ToolResult,
ErrorBubble. Include status dots, streaming cursor, copy buttons."

Phase 08 → slash menu: feature/08-slash-menu
"Implement SPEC.md section 22 step 8: slash command menu. Filters as user
types. Arrow keys navigate, Enter executes, Esc closes. All commands from
section 7."

Phase 09 → AI levels: feature/09-ai-levels
"Implement SPEC.md section 22 step 9: AI level pipeline from spec section 6.
Level 0 + Level 1 only for now. Background metadata extraction. Always
preserve original_content."

Phase 10 → context window: feature/10-context-window
"Implement SPEC.md section 22 step 10: context window management from spec
section 8. Sliding window with auto-summarisation. All thresholds from
spec section 17 defaults."

Phase 11 → search: feature/11-search
"Implement SPEC.md section 22 step 11: FTS5 search + personal-data query
routing from spec section 7. Include search across notes/tasks/reminders/
snippets via the search_index virtual table."

Phase 12 → reminders: feature/12-reminders
"Implement SPEC.md section 22 step 12: reminder scheduler from spec section 14.
Background QThread, dateparser-based time extraction, tray notifications.
Notification settings come in phase 13."

Phase 13 → notification settings: feature/13-notifications
"Implement SPEC.md section 22 step 13: notification configuration from spec
section 14. Per-category toggles, quiet hours, global mute via tray menu."

Phase 14 → settings dialog: feature/14-settings
"Implement SPEC.md section 22 step 14: full settings dialog from spec section 12.
Three tabs: General, AI Providers, Data. Every setting from spec section 17
must be reachable via UI."

Phase 15 → onboarding: feature/15-onboarding
"Implement SPEC.md section 22 step 15: first-run onboarding from spec section 11.
Four-tier AI setup wizard. Walkthrough cards. Smooth transition to first chat."

Phase 16 → managed local: feature/16-managed-local
"Implement SPEC.md section 22 step 16: ManagedLocalProvider from spec section 10.
Owns llama-server child process — download model from HuggingFace, start, monitor,
stop, idle unload. Curated model catalog (Fast/Balanced/Smart)."

Phase 17 → other providers: feature/17-other-providers
"Implement SPEC.md section 22 step 17: AnthropicProvider + GoogleProvider.
Both adapt their native APIs to the common Provider interface."

Phase 18 → server detector: feature/18-server-detector
"Implement SPEC.md section 22 step 18: server detector from spec section 10.
Probes localhost:11434 (Ollama), :1234 (LM Studio), :8080 (raw llama-server).
Surfaces detected services in onboarding."

Phase 19 → browse window: feature/19-browse-window
"Implement SPEC.md section 22 step 19: secondary browse window from spec
section 12. Books sidebar, card grid, FTS-backed search, type filters."

Phase 20 → local API: feature/20-local-api
"Implement SPEC.md section 22 step 20: FastAPI local API server on port 7823
from spec section 13. All endpoints. mDNS broadcast. No real sync logic yet —
just the API surface for future mobile."

Phase 21 → reliability: feature/21-reliability
"Implement SPEC.md section 22 step 21: reliability features from spec section 20.
Auto-backup, crash recovery, search history. All defaults from section 17."

Phase 22 → exports: feature/22-exports
"Implement SPEC.md section 22 step 22: export functions with filters from
spec section 20. Markdown + JSON. Type/date/book filters in dialog."

Phase 23 → packaging: feature/23-packaging
"Implement SPEC.md section 22 step 23: cross-platform PyInstaller builds.
Per spec section 16 and 16.5, produce ALL platform artifacts:
- Windows: .exe installer + portable .zip
- macOS: .dmg with universal .app (Intel + Apple Silicon)
- Linux: AppImage + .deb

Set up GitHub Actions matrix build workflow (.github/workflows/release.yml)
that triggers on git tag v*.*.* and produces all five artifacts as a
GitHub Release. Include platform-specific PyInstaller spec files where
needed for icon/launcher differences.

First GitHub release tagged v0.1.0 from main branch with all artifacts
attached."
```

---

## When you finish all 23 phases

You have a working desktop app. At that point:

1. Pick the final name (verify on Cloudflare for `.app`)
2. Global find-replace `smartpad` → `<finalname>` across the codebase
3. Rename the GitHub repo via `gh repo rename`
4. Buy the domain
5. Tag v0.1.0 release with the new name
6. Post on r/LocalLLaMA, r/selfhosted, Hacker News with a demo GIF

That's launch.

---

## A few things that will save you pain

- **Don't skip PRs even though it's just you.** Reviewing your own diff catches bugs and forces you to write good commit messages. Future-you will thank present-you.
- **Stop at each phase** even if you're hyped. Each phase ending = a working app you can demo. Phases stacked = bugs that hide each other.
- **If Claude Code goes off-script**, point it back at SPEC.md by paragraph. "Section 9 says async engine never blocks UI; this code awaits in the click handler." The spec is your weapon.
- **Don't try to add features mid-phase.** New ideas go in a `IDEAS.md` file in the repo root, addressed in v1.1.

Good luck. The spec is solid, the build sequence is solid. Now it's just hours of typing — and you've got Claude Code doing most of the typing.