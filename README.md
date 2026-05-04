# SmartPad

**Your AI second brain — fast, private, local-first, bring your own model.**

A floating AI scratchpad that lives in your system tray. Press a hotkey from any application to capture notes, tasks, reminders, and code snippets — all stored locally in SQLite and optionally processed by an AI model of your choice.

> Status: Early development, not yet released.

---

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [First Run & Onboarding](#first-run--onboarding)
- [Configuring an AI Provider](#configuring-an-ai-provider)
  - [Anthropic (Claude)](#anthropic-claude)
  - [Google (Gemini)](#google-gemini)
  - [OpenAI or OpenAI-compatible](#openai-or-openai-compatible)
  - [Local model — Ollama](#local-model--ollama)
  - [Local model — LM Studio](#local-model--lm-studio)
  - [Built-in model manager](#built-in-model-manager)
- [Using the App](#using-the-app)
- [Slash Commands](#slash-commands)
- [AI Processing Levels](#ai-processing-levels)
- [Settings & Configuration](#settings--configuration)
- [Local REST API](#local-rest-api)
- [WiFi Sync](#wifi-sync)
- [Data & Backups](#data--backups)
- [Export](#export)
- [Development](#development)
- [Platform Notes](#platform-notes)
- [Stack](#stack)

---

## Features

- **Floating panel** — summons over any app with a global hotkey
- **Local-first storage** — all data in SQLite; nothing leaves your machine by default
- **Bring your own model** — Anthropic, Google, OpenAI, Ollama, LM Studio, or the built-in GGUF runner
- **Five AI levels** — from plain save (level 0) to full enhance + link (level 4)
- **Full-text search** — FTS5 across notes, tasks, reminders, and snippets
- **Smart routing** — intent detection routes input to the right entity type automatically
- **Slash commands** — `/note`, `/task`, `/remind`, `/snippet`, `/search`, `/done`, and more
- **Reminder scheduler** — native desktop notifications with quiet hours support
- **Browse window** — filterable list of all your data
- **Local REST API** — `http://127.0.0.1:7823` with OpenAPI docs
- **WiFi sync** — peer-to-peer sync between devices on the same network
- **Daily backups** — automatic DB snapshots with configurable retention
- **Crash recovery** — last 5 messages persisted across unexpected exits
- **Portable mode** — run without installing by placing `portable.txt` next to the executable

---

## Prerequisites

| Requirement | Minimum version |
|---|---|
| Python | 3.11 or 3.12 |
| pip | 23+ |
| Git | any |
| OS | Windows 10+, macOS 12+, Ubuntu 20.04+ |

> **Linux note:** `libEGL` and Qt system libraries are required. Install them with:
> ```bash
> sudo apt-get install libegl1 libgl1 libxcb-cursor0 libxcb-icccm4 libxcb-keysyms1
> ```

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/smartpad.git
cd smartpad

# 2. Create and activate a virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# 3. Install SmartPad and all dependencies
pip install -e ".[dev]"
```

This installs:
- All runtime dependencies (PyQt6, SQLAlchemy, FastAPI, httpx, pynput, …)
- Dev/test extras (pytest, ruff, mypy, pytest-asyncio, pytest-qt)

---

## First Run & Onboarding

```bash
python -m smartpad
# or use the installed entry-point
smartpad
```

On the **very first launch** the onboarding wizard walks you through:

1. **Provider selection** — pick Anthropic, Google, OpenAI-compatible, or a local model
2. **API key entry** — paste your key; it is stored in the OS keychain (via `keyring`), never in plain text
3. **Hotkey selection** — choose the key combination to summon the panel (default: `Ctrl+Alt+Space`)

After onboarding, SmartPad sits silently in your system tray. The onboarding wizard only appears once; rerun it any time from **Tray → Settings → Reset onboarding**.

---

## Configuring an AI Provider

You can set a provider in three ways (highest priority first):

1. **Environment variable** (before launching the app)
2. **Settings dialog** inside the app (Tray → Settings → Providers)
3. **Onboarding wizard** on first launch

API keys entered through the UI are stored in the OS keychain (Windows Credential Manager, macOS Keychain, Linux Secret Service). Keys set via environment variables are read at startup and not stored.

---

### Anthropic (Claude)

Get an API key at <https://console.anthropic.com/> → API Keys.

```bash
# Set before launching (optional — or enter in-app)
export ANTHROPIC_API_KEY="sk-ant-api03-..."   # macOS / Linux
set ANTHROPIC_API_KEY=sk-ant-api03-...         # Windows CMD
$env:ANTHROPIC_API_KEY="sk-ant-api03-..."      # Windows PowerShell
```

Recommended models: `claude-3-5-haiku-latest` (fast, cheap), `claude-3-7-sonnet-latest` (balanced), `claude-opus-4-5` (most capable).

---

### Google (Gemini)

Get an API key at <https://aistudio.google.com/> → Get API key.

```bash
export GOOGLE_API_KEY="AIza..."
```

Recommended models: `gemini-2.0-flash` (fast), `gemini-2.5-pro-preview` (most capable).

---

### OpenAI or OpenAI-compatible

```bash
export OPENAI_API_KEY="sk-..."

# For a custom base URL (e.g. Azure, Together, Groq, Mistral):
export SMARTPAD_OPENAI_BASE_URL="https://api.groq.com/openai/v1"
```

Any server that speaks the OpenAI REST protocol (`/v1/chat/completions` with SSE) works — Groq, Together AI, Mistral, Azure OpenAI, and self-hosted vLLM instances included.

---

### Local model — Ollama

1. Install Ollama from <https://ollama.com> and run it:

   ```bash
   ollama serve
   # In another terminal, pull a model:
   ollama pull llama3.2:3b
   ```

2. Open **Tray → Settings → Providers → Add local server**.  
   SmartPad auto-detects Ollama on port `11434` — click **Scan** or enter the URL manually:  
   `http://localhost:11434`

3. Select the model from the dropdown and click **Save**.

No API key is needed for Ollama.

---

### Local model — LM Studio

1. Download and start LM Studio from <https://lmstudio.ai>.
2. Load any GGUF model and start the **Local Server** (port `1234` by default).
3. In SmartPad: **Tray → Settings → Providers → Add local server**  
   URL: `http://localhost:1234`  
   Model: match the exact name shown in LM Studio.

---

### Built-in model manager

SmartPad can download and run a small GGUF model entirely on its own — no external tool required.

1. Open **Tray → Settings → Models**.
2. Pick one of the bundled options:

   | Model | Size | Notes |
   |---|---|---|
   | Qwen3-1.7B-Q4_K_M | ~1 GB | Fast, good for organisation/tagging |
   | Llama-3.2-3B-Q4_K_M | ~2 GB | Better reasoning |
   | Phi-3.5-mini-Q4_K_M | ~2.4 GB | Microsoft model, strong on code |
   | Mistral-7B-Q4_K_M | ~4.4 GB | Strongest, needs 8 GB RAM |

3. Click **Download** and wait for the progress bar to complete.
4. SmartPad launches `llama-server` in the background and connects to it automatically.

The model auto-unloads after 30 minutes of inactivity (configurable).

---

## Using the App

| Action | How |
|---|---|
| Open / close panel | Global hotkey (default `Ctrl+Alt+Space`) |
| Open panel from tray | Click the SmartPad tray icon |
| Send a message | Type and press `Enter` |
| New line in message | `Shift+Enter` |
| Slash commands | Type `/` — a popup menu appears |
| Search all items | `Ctrl+F` or type `/search <query>` |
| Browse notes/tasks | **Tray → Browse** |
| Open settings | **Tray → Settings** or type `/settings` |
| Export data | **Tray → Export** |
| Quit | **Tray → Quit** |

### Natural-language queries (no slash needed)

SmartPad understands plain-English queries routed to your database:

| What you type | What happens |
|---|---|
| `what tasks do I have today` | Lists tasks due today |
| `any reminders due?` | Lists pending reminders |
| `show my tasks` | Lists all open tasks |
| Anything else | FTS5 full-text search |

---

## Slash Commands

Type `/` in the input box to see the full popup menu. Arrow keys to navigate, `Enter` to execute, `Esc` to dismiss.

| Command | Aliases | What it does |
|---|---|---|
| `/note` | — | Save a note |
| `/task` | `/todo` | Save a task (optionally with a deadline) |
| `/remind` | `/reminder` | Set a reminder (e.g. `/remind call John at 3pm`) |
| `/snippet` | `/snip` | Save a code snippet |
| `/find` | `/search` | FTS5 search across all items |
| `/tasks` | — | List your open tasks |
| `/today` | — | Show today's tasks and reminders |
| `/notes` | — | Browse your notes |
| `/snippets` | — | Browse your snippets |
| `/done` | — | Mark a task as done |
| `/remove` | `/delete` | Soft-delete an item |
| `/clear` | — | Clear the current chat stream |
| `/settings` | — | Open the settings dialog |
| `/browse` | — | Open the browse window |
| `/model` | — | Change the active AI model |
| `/ai` | `/level` | Change the AI processing level |
| `/help` | — | Show help |

---

## AI Processing Levels

Set the level in **Settings → AI Level** or type `/ai <0-4>`.

| Level | Name | What it does |
|---|---|---|
| 0 | Off | Plain save — zero AI calls, instant |
| 1 | Organise | Auto-tag, classify type, assign notebook (metadata only) |
| 2 | Grammar | Level 1 + silent grammar and typo correction |
| 3 | Tidy | Level 2 + expand shorthand into full sentences |
| 4 | Enhance | Level 3 + add detail, structure, and link to related notes |

Your original text is **always** preserved in `original_content` regardless of the level chosen.

---

## Settings & Configuration

Settings are stored in `<DATA_DIR>/config.json` and can be overridden with environment variables prefixed `SMARTPAD_`. Nested keys use `__` as separator.

### Data directory locations

| OS | Default path |
|---|---|
| Windows | `%APPDATA%\smartpad\` |
| macOS | `~/Library/Application Support/smartpad/` |
| Linux | `~/.local/share/smartpad/` (or `$XDG_DATA_HOME/smartpad/`) |

Override with:
```bash
export SMARTPAD_DATA_DIR="/path/to/my/data"
```

### Key settings

| Setting | Default | Environment variable |
|---|---|---|
| Global hotkey | `ctrl+alt+space` | `SMARTPAD_HOTKEY` |
| Theme | `system` | `SMARTPAD_THEME` |
| AI level | `1` | `SMARTPAD_AI_LEVEL` |
| Local API port | `7823` | `SMARTPAD_API_PORT` |
| Log level | `INFO` | `SMARTPAD_LOG_LEVEL` |
| Quiet hours start | `22` (10 pm) | `SMARTPAD_QUIET_HOURS_START` |
| Quiet hours end | `8` (8 am) | `SMARTPAD_QUIET_HOURS_END` |
| Reminder check interval | `30s` | `SMARTPAD_REMINDER_CHECK_INTERVAL_SECONDS` |
| Backup retention | `7 days` | `SMARTPAD_BACKUP__RETENTION_DAYS` |

### Hotkey format

Hotkeys use the pynput combo format. Examples:

```
ctrl+alt+space          # default
ctrl+shift+space
<ctrl>+<shift>+s
<cmd>+<space>           # macOS
```

---

## Local REST API

SmartPad runs a FastAPI server on `http://127.0.0.1:7823` while the app is open. Use it to integrate SmartPad with scripts, Alfred/Raycast workflows, or other tools.

**Interactive docs:** open `http://127.0.0.1:7823/api/docs` in your browser while the app is running.

### Key endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/notes` | List notes (`?book_id=`, `?pinned=`, `?limit=`, `?offset=`) |
| `POST` | `/api/notes` | Create a note |
| `GET` | `/api/notes/{id}` | Get a note |
| `PUT` | `/api/notes/{id}` | Update a note |
| `DELETE` | `/api/notes/{id}` | Soft-delete a note |
| `GET` | `/api/search?q=<query>` | FTS5 search across all types |
| `POST` | `/api/chat` | SSE chat stream to the active provider |
| `POST` | `/api/sync/handshake` | Initiate WiFi sync pairing |
| `POST` | `/api/sync/delta` | Exchange sync deltas |

### Quick example

```bash
# Create a note via curl
curl -X POST http://127.0.0.1:7823/api/notes \
  -H "Content-Type: application/json" \
  -d '{"content": "Remember to water the plants"}'

# Full-text search
curl "http://127.0.0.1:7823/api/search?q=plants"
```

Change the port with `SMARTPAD_API_PORT=<port>` or in Settings.

---

## WiFi Sync

SmartPad can sync between two desktop instances on the same network using mDNS discovery and a simple delta protocol.

1. On the **host** machine: **Tray → Settings → Sync → Enable sync server**. A pairing code is displayed.
2. On the **client** machine: **Tray → Settings → Sync → Connect to device**, enter the host IP and the pairing code.
3. Sync runs automatically in the background; conflicts are resolved by `sync_version` (last-write-wins per item).

---

## Data & Backups

### Where your data lives

All data is stored in a single SQLite database at `<DATA_DIR>/smartpad.db`. You can back it up or move it by copying that file.

### Automatic daily backups

SmartPad backs up the database once per day to `<DATA_DIR>/backups/smartpad-YYYY-MM-DD.db` and keeps the last **7 copies** by default.

Configure in Settings or via environment variables:

```bash
SMARTPAD_BACKUP__ENABLED=true
SMARTPAD_BACKUP__RETENTION_DAYS=14
SMARTPAD_BACKUP__BACKUP_PATH=/my/backup/dir
```

### Portable mode

Place a file named `portable.txt` (empty) next to the SmartPad executable. The app will store all data alongside the executable instead of in the OS data directory. Useful for running from a USB drive.

---

## Export

**Tray → Export** lets you export your data as Markdown or JSON.

```bash
# Via the API (while app is running):
curl "http://127.0.0.1:7823/api/notes" | jq .

# Markdown export covers notes + tasks, JSON export includes full metadata.
```

---

## Development

### Running tests

```bash
# All tests (headless Qt via offscreen platform)
pytest tests/ -v

# Specific file
pytest tests/test_db.py -v

# With coverage
pytest tests/ --cov=src/smartpad --cov-report=term-missing
```

### Linting & formatting

```bash
# Lint
ruff check src/

# Auto-fix
ruff check src/ --fix

# Format
ruff format src/

# Type-check
mypy src/
```

### Project layout

```
smartpad/
├── src/smartpad/
│   ├── api/             FastAPI local REST server (port 7823)
│   │   └── routes/      notes, chat, sync
│   ├── core/            Business logic
│   │   ├── ai_levels.py       5-level AI pipeline
│   │   ├── chat_service.py    Chat with context management
│   │   ├── context_manager.py Sliding-summary context window
│   │   ├── hotkey.py          Global hotkey listener
│   │   ├── intent_detector.py Slash-command + entity routing
│   │   ├── notification_manager.py Desktop notifications
│   │   ├── reminder_scheduler.py  Background reminder checker
│   │   ├── router.py          Input → intent → tool/AI
│   │   ├── search_service.py  FTS5 search + NL queries
│   │   └── worker_pool.py     HIGH/LOW priority QThread pool
│   ├── db/
│   │   ├── models.py          SQLAlchemy ORM models
│   │   ├── engine.py          Sync + async engine setup
│   │   ├── migrations.py      Alembic wrapper
│   │   └── repositories/      Typed repo per entity
│   ├── model_manager/   GGUF catalog, downloader, llama-server wrapper
│   ├── providers/       AI provider adapters
│   │   ├── anthropic.py
│   │   ├── google.py
│   │   ├── openai_compatible.py
│   │   ├── managed_local.py
│   │   └── server_detector.py
│   ├── ui/              PyQt6 widgets
│   │   ├── floating_panel.py  Main window
│   │   ├── tray.py            System tray icon + menu
│   │   ├── bubbles/           Chat/note/task/reminder/snippet bubbles
│   │   ├── settings_dialog.py
│   │   ├── onboarding.py
│   │   ├── browse_window.py
│   │   └── slash_menu.py
│   ├── utils/           Backup, crash recovery, exporters, paths
│   ├── config.py        pydantic-settings config
│   └── app.py           Application entry point
├── alembic/             DB migration scripts
├── tests/               pytest suite
├── .github/workflows/   CI (ubuntu/macos/windows × py3.11/3.12)
├── smartpad.spec        PyInstaller build spec
└── pyproject.toml
```

### Environment variables (development)

| Variable | Purpose |
|---|---|
| `SMARTPAD_DATA_DIR` | Override the data/DB directory |
| `SMARTPAD_LOG_LEVEL` | `DEBUG` for verbose logs |
| `QT_QPA_PLATFORM=offscreen` | Run headless (CI, tests) |

### Building a distributable

```bash
# Requires PyInstaller
pip install pyinstaller

# One-file executable
pyinstaller smartpad.spec
# Output: dist/smartpad (Linux/macOS) or dist/smartpad.exe (Windows)
```

Release builds are produced automatically by `.github/workflows/release.yml` on every git tag:

| Platform | Artifact |
|---|---|
| Windows | Portable `.zip` |
| macOS Intel | `.dmg` |
| macOS Apple Silicon | `.dmg` |
| Linux | AppImage + `.deb` |

---

## Platform Notes

### macOS — global hotkey permission

pynput requires Accessibility access to register a global hotkey:

> **System Settings → Privacy & Security → Accessibility → enable SmartPad (or Terminal)**

Without this permission the hotkey silently fails; use the tray icon instead.

### Linux — Wayland

Global hotkeys are blocked by the Wayland compositor by design. On Wayland sessions SmartPad logs a warning and falls back to tray-icon-only access.

To force X11 mode:
```bash
QT_QPA_PLATFORM=xcb python -m smartpad
```

### Windows — antivirus false positives

PyInstaller-packaged executables are sometimes flagged. If this happens, add the SmartPad folder to your AV exclusions, or run from source using the instructions above.

---

## Stack

| Layer | Choice |
|---|---|
| Language | Python 3.11+ |
| GUI | PyQt6 |
| DB | SQLite + SQLAlchemy 2.0 + Alembic |
| Async DB driver | aiosqlite |
| HTTP client | httpx (async) |
| Local API | FastAPI + uvicorn |
| Global hotkey | pynput |
| Service discovery | zeroconf (mDNS) |
| Config | pydantic-settings |
| Keychain | keyring |
| Markdown rendering | markdown-it-py |
| Date parsing | dateparser |
| Logging | loguru |
| Packaging | PyInstaller |
| CI | GitHub Actions |

## Specification

See [SPEC.MD](SPEC.MD) for the full product specification.

## License

See [LICENSE](LICENSE).
