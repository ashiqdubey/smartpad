# SmartPad — Final Product Specification v1.0

> A floating AI panel that lives beside your work. SmartPad your ideas in fast — it remembers, organises, and reminds you. Privately, locally, no cloud required.

> **Note:** if "SmartPad" (working codename, rename later) is taken when you check trademarks/domains, replace globally before first commit. Working name throughout this spec.

---

## 1. Product Identity

A floating AI panel that lives beside your work. Ask it anything. Save anything — notes, tasks, reminders, snippets. It remembers, organises, and reminds you. Privately, locally, no cloud required.

**One-line pitch:** Your AI second brain — fast, private, local-first, bring your own model.

**Differentiator:** No other app combines floating quick-capture + AI auto-organisation + local LLM support + WiFi sync + open source.

**Name origin:** A "smartpad" is a small mark made to remember something. SmartPad your ideas in fast, find them later. Short, verb-or-noun, no major company owns it in this space.

---

## 2. Design Principles

1. **Out of the way by default.** Invisible until summoned by hotkey or tray click.
2. **Capture is dumb fast.** UI responds in under 100ms always. AI processing is background.
3. **AI organises, user doesn't.** No folders to create, no tags to manage. AI handles it.
4. **User controls AI depth.** From "off" to "full enhancement" — five levels, configurable.
5. **Original content always preserved.** Even after AI edits, original is one click away.
6. **Local-first, sync optional.** No account required. Cloud is opt-in, never required.
7. **Visually polished.** Animations, streaming, status indicators. Never feels CLI-like.
8. **Bring your own model.** Local llama-server, Ollama, OpenAI, Anthropic, Gemini, OpenRouter, Groq, custom.

---

## 3. Tech Stack (Locked)

| Layer | Choice | Rationale |
|---|---|---|
| Language | Python 3.11+ | Fast iteration, mature ecosystem |
| GUI | PyQt6 | Frameless windows, tray, hotkeys, animations |
| DB | SQLite + SQLAlchemy + Alembic | Industry standard, single file, migrations |
| HTTP client | httpx (async) | Better than requests for long-running app |
| Local API | FastAPI + uvicorn | For desktop-to-desktop sync; forward-compatible with future clients |
| Hotkey | pynput | Cross-platform, no admin needed |
| Notifications | PyQt6 QSystemTrayIcon.showMessage | Native, no extra deps |
| mDNS | zeroconf | Device discovery on local WiFi |
| Packaging | PyInstaller | One-file .exe |
| Config | pydantic-settings | Type-safe |
| Logging | loguru | Rotating file logs |
| Secrets | keyring | OS-native key storage |
| Markdown render | markdown-it-py | For note content display |

**Distribution:** Windows .exe (portable + installer) for v1. Mac/Linux for v2.

---

## 4. Architecture

### High-level

```
┌───────────────────────────────────────────────────────┐
│                    SmartPad App                       │
│                                                       │
│  ┌───────────┐  ┌────────────┐  ┌─────────────────┐   │
│  │   Tray    │  │   Hotkey   │  │  Floating Panel │   │
│  │   Icon    │  │  Listener  │  │   (PyQt6 UI)    │   │
│  └─────┬─────┘  └──────┬─────┘  └────────┬────────┘   │
│        └───────────────┴─────────────────┘            │
│                       │                               │
│                       ▼                               │
│          ┌─────────────────────────┐                  │
│          │   Browse Window         │  (secondary)     │
│          │   (notes browser)       │                  │
│          └────────────┬────────────┘                  │
│                       │                               │
│                       ▼                               │
│          ┌─────────────────────────┐                  │
│          │   Router                │                  │
│          │   slash > pattern > AI  │                  │
│          └─────┬───────────┬───────┘                  │
│                │           │                          │
│        ┌───────▼──┐    ┌───▼────────┐                 │
│        │ Worker   │    │ Tool       │                 │
│        │ Pool     │    │ Registry   │                 │
│        └────┬─────┘    └─────┬──────┘                 │
│             │                │                        │
│             ▼                ▼                        │
│        ┌─────────────────────────────┐                │
│        │  Provider Adapter Layer     │                │
│        │  (OpenAI/Anthropic/Google/  │                │
│        │   Local/Custom)             │                │
│        └─────────────┬───────────────┘                │
│                      │                                │
│                      ▼                                │
│        ┌─────────────────────────────┐                │
│        │  Repository Layer           │                │
│        │  (NotesRepo/TasksRepo/...)  │                │
│        └─────────────┬───────────────┘                │
│                      │                                │
│                      ▼                                │
│        ┌─────────────────────────────┐                │
│        │  SQLite + FTS5              │                │
│        └─────────────────────────────┘                │
│                                                       │
│  ┌────────────────────────────────────────────────┐   │
│  │  Local API Server (FastAPI on port 7823)       │   │
│  │  /api/sync  /api/chat  /api/notes              │   │
│  │  + mDNS broadcast for device discovery         │   │
│  └────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────┘
```

### Project structure

```
notch/
├── pyproject.toml
├── alembic.ini
├── alembic/versions/
├── src/notch/
│   ├── __main__.py
│   ├── app.py                     # QApplication setup
│   ├── config.py                  # paths, hotkeys, defaults
│   │
│   ├── ui/
│   │   ├── tray.py                # QSystemTrayIcon
│   │   ├── floating_panel.py      # main capture panel
│   │   ├── browse_window.py       # notes browser (secondary)
│   │   ├── settings_dialog.py     # settings
│   │   ├── onboarding.py          # first-run flow
│   │   ├── slash_menu.py          # / command popup
│   │   ├── bubbles/
│   │   │   ├── chat_bubble.py
│   │   │   ├── note_bubble.py
│   │   │   ├── task_bubble.py
│   │   │   ├── reminder_bubble.py
│   │   │   ├── snippet_bubble.py
│   │   │   └── error_bubble.py
│   │   ├── animations.py
│   │   └── styles.py              # QSS themes (dark/light)
│   │
│   ├── core/
│   │   ├── router.py              # decides intent
│   │   ├── worker_pool.py         # priority task queue
│   │   ├── intent_detector.py     # pattern + LLM routing
│   │   ├── ai_levels.py           # 0-4 enhancement pipeline
│   │   ├── chat_service.py
│   │   ├── reminder_scheduler.py  # background time-trigger thread
│   │   └── hotkey.py              # pynput global hotkey
│   │
│   ├── providers/
│   │   ├── base.py                # Provider abstract
│   │   ├── openai_compatible.py   # OpenAI/OpenRouter/local/Ollama/LM Studio
│   │   ├── anthropic.py
│   │   ├── google.py
│   │   ├── managed_local.py       # owns llama-server child process
│   │   ├── server_detector.py     # auto-detect Ollama/LM Studio
│   │   └── registry.py
│   │
│   ├── tools/
│   │   ├── base.py                # Tool abstract
│   │   ├── registry.py
│   │   ├── builtin/
│   │   │   ├── save_note.py
│   │   │   ├── save_task.py
│   │   │   ├── save_reminder.py
│   │   │   ├── save_snippet.py
│   │   │   ├── search_notes.py
│   │   │   ├── list_tasks.py
│   │   │   ├── mark_done.py
│   │   │   ├── soft_delete.py
│   │   │   └── calculator.py
│   │   └── mcp_client.py          # stub in v1, real in v1.1
│   │
│   ├── db/
│   │   ├── engine.py
│   │   ├── models.py              # SQLAlchemy ORM
│   │   ├── migrations.py          # Alembic runner
│   │   └── repositories/
│   │       ├── notes.py
│   │       ├── tasks.py
│   │       ├── reminders.py
│   │       ├── snippets.py
│   │       ├── books.py
│   │       └── chat.py
│   │
│   ├── api/
│   │   ├── server.py              # FastAPI app
│   │   ├── routes/
│   │   │   ├── notes.py
│   │   │   ├── chat.py
│   │   │   └── sync.py
│   │   └── mdns.py                # zeroconf broadcast
│   │
│   ├── model_manager/
│   │   ├── downloader.py          # HF model download
│   │   ├── llama_server.py        # subprocess management
│   │   └── catalog.py             # curated model list
│   │
│   └── utils/
│       ├── secrets.py             # keyring wrapper
│       ├── exporters.py           # markdown/JSON export
│       ├── time_parser.py         # natural language → datetime
│       └── portable.py            # detect portable mode
│
└── resources/
    ├── icons/
    └── themes/
```

---

## 5. Data Model

```sql
-- All IDs are UUIDs (TEXT). All deletes are soft (deleted_at IS NULL = active).
-- All rows have updated_at for sync.

CREATE TABLE messages (
    id TEXT PRIMARY KEY,            -- UUID
    role TEXT NOT NULL,             -- 'user' | 'assistant' | 'system'
    content TEXT NOT NULL,
    kind TEXT NOT NULL,             -- 'chat' | 'note' | 'task' | 'reminder' | 'snippet' | 'tool_result' | 'error'
    metadata JSON,                  -- provider, model, tokens, etc
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    deleted_at DATETIME,
    device_id TEXT,                 -- which device created this
    sync_version INTEGER DEFAULT 0
);
CREATE INDEX idx_messages_kind ON messages(kind, created_at);
CREATE INDEX idx_messages_active ON messages(deleted_at) WHERE deleted_at IS NULL;

CREATE TABLE notes (
    id TEXT PRIMARY KEY,            -- UUID, matches a messages.id
    content TEXT NOT NULL,          -- AI-processed version
    original_content TEXT NOT NULL, -- always preserve original
    book_id TEXT REFERENCES books(id),
    tags TEXT,                      -- comma-separated, AI-generated
    pinned BOOLEAN DEFAULT 0,
    ai_level_applied INTEGER,       -- 0-4
    grammar_fixed BOOLEAN DEFAULT 0,
    enhanced BOOLEAN DEFAULT 0,
    created_at DATETIME,
    updated_at DATETIME,
    deleted_at DATETIME,
    device_id TEXT,
    sync_version INTEGER DEFAULT 0
);

CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    deadline DATETIME,              -- nullable
    priority TEXT,                  -- 'low' | 'medium' | 'high' | NULL
    status TEXT DEFAULT 'todo',     -- 'todo' | 'done'
    completed_at DATETIME,
    book_id TEXT REFERENCES books(id),
    tags TEXT,
    created_at DATETIME,
    updated_at DATETIME,
    deleted_at DATETIME,
    device_id TEXT,
    sync_version INTEGER DEFAULT 0
);

CREATE TABLE reminders (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    trigger_at DATETIME NOT NULL,
    notified BOOLEAN DEFAULT 0,
    notified_at DATETIME,
    created_at DATETIME,
    updated_at DATETIME,
    deleted_at DATETIME,
    device_id TEXT,
    sync_version INTEGER DEFAULT 0
);

CREATE TABLE snippets (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    description TEXT,               -- AI-generated label for recall
    language TEXT,                  -- 'bash' | 'python' | 'sql' | etc
    tags TEXT,
    use_count INTEGER DEFAULT 0,
    last_used_at DATETIME,
    created_at DATETIME,
    updated_at DATETIME,
    deleted_at DATETIME,
    device_id TEXT,
    sync_version INTEGER DEFAULT 0
);

CREATE TABLE books (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    ai_generated BOOLEAN DEFAULT 1,
    created_at DATETIME,
    updated_at DATETIME,
    deleted_at DATETIME,
    device_id TEXT,
    sync_version INTEGER DEFAULT 0
);

CREATE TABLE providers (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,      -- 'openai' | 'local' | 'my-vllm-server' | etc
    type TEXT NOT NULL,             -- adapter class
    base_url TEXT,
    default_model TEXT,
    extra JSON,
    enabled BOOLEAN DEFAULT 1,
    is_active BOOLEAN DEFAULT 0,    -- exactly one active at a time
    created_at DATETIME,
    updated_at DATETIME
);
-- API keys live in OS keyring under "notch/{provider_name}"

CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value JSON NOT NULL
);
-- Stores: ai_level, hotkey_combo, panel_position, theme, paired_devices, etc.

CREATE TABLE paired_devices (
    id TEXT PRIMARY KEY,            -- UUID for the other device
    name TEXT NOT NULL,             -- "iPhone 15", "Work Laptop"
    type TEXT NOT NULL,             -- 'desktop' | 'mobile'
    public_key TEXT,                -- for future sync auth
    last_sync_at DATETIME,
    last_sync_version INTEGER,
    created_at DATETIME
);

-- Full-text search virtual table (covers notes + tasks + reminders + snippets)
CREATE VIRTUAL TABLE search_index USING fts5(
    item_id UNINDEXED,
    item_type UNINDEXED,            -- 'note' | 'task' | 'reminder' | 'snippet'
    content,
    description
);
```

**Sync-readiness:** every row has `id` (UUID), `updated_at`, `deleted_at`, `device_id`, `sync_version`. Last-write-wins on conflict.

---

## 6. AI Level System

User-configurable AI processing depth. Set globally, override per-note via slash command.

| Level | Name | Behaviour |
|---|---|---|
| 0 | Off | Plain text save, no AI processing at all |
| 1 | Organise only (default) | Auto-tag, auto-classify type, auto-book, no content changes |
| 2 | Fix grammar | Level 1 + silent grammar/typo correction |
| 3 | Tidy + clarify | Level 2 + expand shorthand into full sentences |
| 4 | Full enhancement | Level 3 + add detail, structure, link related notes |

```python
async def process_capture(text: str, ai_level: int):
    # ALWAYS: type detection (note/task/reminder/snippet)
    classification = await ai.classify_type(text)

    if ai_level == 0:
        save_as(classification.type, text, original=text)
        return

    # Level 1+: organisation metadata
    metadata = await ai.extract_metadata(text, classification.type)
    # extracts: tags, book, deadline (if task), trigger_time (if reminder), etc

    content = text
    if ai_level >= 2:
        content = await ai.fix_grammar(content)
    if ai_level >= 3:
        content = await ai.clarify(content)
    if ai_level == 4:
        content = await ai.enhance(content, related_notes=...)

    save_as(classification.type, content, original=text, metadata=metadata)
```

Original content is ALWAYS preserved in `original_content` field. User can restore via right-click → "Show original" → "Restore original".

---

## 7. Routing Logic

When user submits text in the panel:

```
1. SLASH COMMAND? (text starts with /)
   /note, /task, /remind, /snippet → save with that type
   /find, /tasks, /today, /snippets → query
   /done, /remove, /clear → action
   /settings, /browse, /model, /help → app commands
   → execute directly, no LLM call

2. PATTERN MATCH? (regex on common phrasings)
   "remind me to X at Y" → REMINDER
   "todo: X" / "task: X" / "X by Y" → TASK
   pure math expression → calculator tool
   "save: X" / "snippet: X" / starts with $ or > → SNIPPET
   → save with that type, optional Level 1+ AI metadata

3. PERSONAL DATA QUERY?
   "what do I have today" / "any deadlines" / "my tasks" / "find my X command"
   → search local DB, feed results to AI for natural-language answer
   → DO NOT route to general chat

4. AMBIGUOUS — ask AI router (one quick LLM call):
   classification: NOTE | TASK | REMINDER | SNIPPET | CHAT
   → if NOTE/TASK/REMINDER/SNIPPET: save as that type
   → if CHAT: stream a chat reply

5. FALLBACK: treat as CHAT
```

**Two-call pattern for chat:**
- Call 1 (routing): temperature=0.0, max_tokens=8 — instant
- Call 2 (chat reply): temperature=0.6, streaming — quality

**Personal-data query detection:** if user input matches patterns like `my X`, `what do I have`, `any X due`, `find my X`, the router enters **DB-first mode**: query SQLite, summarise findings via AI, never hit general knowledge.

---

## 8. Context Window Management

The conversation grows over time. Without management, you either hit token limits or pay for huge contexts on cloud providers. SmartPad handles this in the background, invisibly.

### Strategy: sliding window with auto-summarisation

```
Conversation grows past threshold
        ↓
Background worker (LOW priority) detects threshold hit
        ↓
Take oldest N messages, summarise via active provider:
"Earlier in conversation: user asked about X,
 we discussed Y, decided Z, user saved W as a note"
        ↓
Replace those N messages in the active context with a single
SYSTEM message containing the summary
        ↓
Original messages stay in DB (visible in browse window)
flagged with summarised_in=<summary_id>
        ↓
Conversation continues with summary + recent messages.
User never sees the swap.
```

### Configurable settings

| Setting | Default | Range / options |
|---|---|---|
| Strategy | sliding_summary | none / truncate / sliding_summary |
| Trigger threshold (messages) | 30 | 5-200 |
| Trigger threshold (tokens) | 6000 | 1000-32000 |
| Messages to summarise per pass | 15 | 5-50 |
| Recent messages always kept | 15 | 5-50 |
| Summary model | active provider | any configured provider/model |
| Show summarised originals in browse | yes | yes/no |

When user has a 256K-context model loaded, can disable entirely. On small local models, can be aggressive.

### Personal data queries are exempt
When the router detects "do I have any tasks", "find my X" etc., the DB is queried directly — context window doesn't matter. The user's conversation history is ONLY needed for chat-mode replies, not for personal-data queries.

---

## 9. Async Engine

UI thread NEVER waits for LLM or DB. All work happens in the worker pool.

```
┌─────────────────────────┐
│      UI Thread          │
│  (renders bubbles,      │
│   handles input)        │
└───────────┬─────────────┘
            │ Qt signals only
            ▼
┌─────────────────────────┐
│   Worker Pool (4-8)     │
│                         │
│   HIGH queue            │
│   ─ chat LLM stream     │
│   ─ user-facing search  │
│                         │
│   LOW queue             │
│   ─ note saves          │
│   ─ AI metadata extract │
│   ─ FTS index update    │
│   ─ grammar/enhance     │
│   ─ book classification │
└───────────┬─────────────┘
            │
            ▼
       SQLite + FTS5
```

**Optimistic UI rule:** save bubble appears in UI in <100ms with `status="saving"`. Worker writes to DB in background. On success, bubble updates to `status="saved"` (tiny checkmark). On failure, bubble shows retry icon + error.

**Bubble morphing:** if AI router decides an ambiguous input is a NOTE not CHAT, the chat bubble morphs into a note bubble with a 200ms animation.

---

## 10. Provider Abstraction

```python
class Provider(ABC):
    name: str

    @abstractmethod
    async def list_models(self) -> list[ModelInfo]: ...

    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        model: str,
        tools: list[ToolSchema] | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        stream: bool = True,
    ) -> AsyncIterator[ChatChunk]: ...

    @abstractmethod
    def validate_credentials(self) -> bool: ...
```

| Concrete class | Covers |
|---|---|
| `OpenAICompatibleProvider` | OpenAI, OpenRouter, Together, Groq, Ollama, LM Studio, llama-server, custom OpenAI-compat servers |
| `AnthropicProvider` | Anthropic native API |
| `GoogleProvider` | Gemini native API |
| `ManagedLocalProvider` | Owns llama-server child process: download model, start, monitor, stop |

**Adding a new provider:** subclass + register in `providers/registry.py`. Done.

**Server detector** probes on startup: `localhost:11434` (Ollama), `localhost:1234` (LM Studio), `localhost:8080` (raw llama-server). Detected services appear in onboarding as one-click options.

---

## 11. Onboarding Flow

First-run experience after install:

```
┌─────────────────────────────────────────────┐
│  Welcome to SmartPad                        │
│                                             │
│  How would you like to set up your AI?      │
│                                             │
│  ┌───────────────────────────────────────┐  │
│  │ ✨ Quick start (recommended)          │  │
│  │ Download a small AI model and run it  │  │
│  │ on your computer. No setup, free.     │  │
│  └───────────────────────────────────────┘  │
│                                             │
│  ┌───────────────────────────────────────┐  │
│  │ 🔌 Use Ollama (detected: 5 models)    │  │
│  │ Use models you already have           │  │
│  └───────────────────────────────────────┘  │
│                                             │
│  ┌───────────────────────────────────────┐  │
│  │ ☁️  Use a cloud API                   │  │
│  │ OpenAI, Claude, Gemini, OpenRouter    │  │
│  └───────────────────────────────────────┘  │
│                                             │
│  ┌───────────────────────────────────────┐  │
│  │ ⚙️  Advanced setup                    │  │
│  │ Custom endpoint, vLLM, remote server  │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

After AI setup → quick walkthrough (3 cards):
1. Press `Ctrl+Alt+Space` to open the panel anywhere
2. Type anything — questions, notes, tasks, reminders
3. Type `/` to see all commands

→ panel opens with welcome bubble.

---

## 12. UI Specifications

### Floating Panel
- Frameless, always-on-top, translucent
- Default size: 420px × 560px, draggable, position remembered
- Header: app dot indicator + title + browse button + drag area
- Stream: QScrollArea, vertical, auto-scroll to bottom on new
- Slash menu: appears above input when `/` typed, filters as user types
- Input: QLineEdit, multi-line on Shift+Enter, Enter sends
- Hide: Esc, click outside, hotkey toggle
- Show: hotkey or tray click — fade+slide in 180ms

### Bubble types (visually distinct)
- **Chat (user)**: right-aligned, accent blue bg, white text, 80% max width
- **Chat (AI)**: left-aligned, neutral bg, streaming cursor while generating
- **Note**: full-width, pale yellow bg, 📝 prefix, italic
- **Task**: full-width, blue tint, ✓ checkbox, deadline pill, click checkbox to mark done
- **Reminder**: full-width, amber tint, ⏰ icon, time pill, "in X minutes" countdown
- **Snippet**: full-width, mono font, dark bg, code block, 📋 copy button
- **Tool result**: full-width card, tool name header, formatted body
- **Error**: full-width, red tint, retry button

### Browse Window (secondary, opened via tray or `/browse`)
- 900×600 default, resizable
- Left sidebar: Books list + filters (Today, This Week, Pinned, All)
- Right pane: card grid of items in selected book/filter
- Top bar: search box (FTS5), sort dropdown, type filter chips
- Click card → expands inline showing full content + edit/delete/pin actions

### Settings Dialog
Three tabs:
1. **General**: hotkey, theme, AI level (0-4 slider), startup behaviour, panel position
2. **AI Providers**: list, add/edit/remove, set active, test connection, manage downloaded local models
3. **Data**: export markdown, export JSON, database location, paired devices, clear chat, clear all

### Theme
- Dark mode default (most users want this)
- Light mode + system mode toggleable
- Colour tokens defined in `ui/styles.py`, applied via QSS
- Smooth theme transitions

---

## 13. Local API Server

Runs on `127.0.0.1:7823` alongside the desktop app. Used by sync between desktop instances. Architecture is forward-compatible with future mobile clients but mobile is not a v1/v1.1 commitment.

```
GET  /api/health              → {status, version, device_id}
GET  /api/notes               → paginated list with filters
GET  /api/notes/{id}          → single note
POST /api/notes               → create note
PUT  /api/notes/{id}          → update
DELETE /api/notes/{id}        → soft delete

GET  /api/tasks               → list with filters (status, deadline)
POST /api/tasks/{id}/done     → mark done
GET  /api/reminders           → list pending
GET  /api/snippets            → list with search
GET  /api/search?q=…          → FTS5 search across all types

POST /api/chat                → SSE streaming chat (proxies to active provider)

POST /api/sync/handshake      → initiate pairing with code
POST /api/sync/delta          → exchange deltas since last sync_version
GET  /api/sync/status         → last sync time, pending changes
```

**mDNS broadcast** registers `_notch._tcp.local.` so other SmartPad instances on the same WiFi can discover this one.

**Auth (v1.1):** simple bearer token issued during pairing. Token stored in `paired_devices` table. Unpaired requests rejected with 401.

---

## 14. Notifications & Reminders

All notifications are configurable. User decides what's worth interrupting them for.

### Categories and per-category settings

| Category | Default | What it triggers |
|---|---|---|
| Reminders | Toast + Sound | Time-triggered reminders firing |
| Tasks due today | Tray badge only | Morning check, badge shows count |
| Tasks overdue | Toast | Once per day on first launch |
| Sync events | Off | Pair success, sync conflict |
| New messages | Off | Background AI completed long task while panel hidden |
| Errors | Toast + Tray badge | LLM down, save failed, etc. |

Each category has independent toggles for: **Toast popup**, **Sound**, **Tray badge**.

### Quiet hours
- Default: 10pm – 8am (configurable, can be disabled)
- During quiet hours: no toasts, no sound. Tray badges still appear.
- Reminders that fire during quiet hours: queued, delivered at end of quiet window.

### Global mute
Right-click tray → "Pause notifications for…" → 1h / 4h / Until tomorrow / Until I unmute. Tray icon shows muted state visually.

### Reminder scheduler (background thread)

Background QThread checks pending reminders every 30 seconds:

```python
def reminder_loop():
    while running:
        if is_quiet_hours():
            sleep(30); continue

        due = reminder_repo.find_due(within=now())
        for r in due:
            if notification_settings.reminders.toast:
                tray.showMessage("Reminder", r.content,
                                 QSystemTrayIcon.Information, 10000)
            if notification_settings.reminders.sound:
                play_sound("reminder.wav")
            if notification_settings.reminders.tray_badge:
                tray.set_badge(badge_count + 1)
            r.notified = True
            r.notified_at = now()
            reminder_repo.save(r)
        sleep(30)
```

Click notification → show panel with that reminder highlighted in stream. Click tray badge → opens browse window filtered to today/pending.

Natural language time parsing: use `dateparser` library. "tomorrow at 9am", "in 30 minutes", "next Friday 3pm" all work.

---

## 15. Distribution

### Build artefacts (v1)
- `Notch-1.0.0-win64-setup.exe` — installer, ~80MB, adds to startup folder, optional
- `Notch-1.0.0-win64-portable.zip` — extract and run, DB next to exe

### Portable detection
```python
exe_dir = Path(sys.executable).parent
if (exe_dir / "portable.txt").exists() or (exe_dir / "notch.db").exists():
    DATA_DIR = exe_dir
else:
    DATA_DIR = Path(os.getenv("APPDATA")) / "SmartPad" (working codename, rename later)
```

### Local model storage
- Installed mode: `%APPDATA%/Notch/models/`
- Portable mode: `<exe_dir>/models/`
- llama-server binary: download from llama.cpp GitHub releases on first run, cache to models dir

### Open source
- License: **MIT**
- Repo: GitHub public
- Releases page hosts pre-built `.exe` and `.zip`
- README has GIF demo, install instructions, contribution guide

---

## 16. Phased Roadmap

**Scope decision: this product is desktop-only.** Windows, macOS, and Linux all ship together in v1. Mobile is reserved for v2 and only if real user demand justifies it.

### v1.0 — Cross-desktop walking real product (target: 5-7 weeks)

Everything in this spec EXCEPT what's listed under v1.1 / v2 below. Specifically includes:
- Floating panel, hotkey, tray, slash menu
- All four save types (note/task/reminder/snippet)
- AI levels 0-4, configurable
- Personal-data query routing
- Multi-provider AI (managed local + Ollama detect + cloud + custom)
- Async engine, optimistic bubbles, streaming
- SQLite + FTS5
- Browse window
- Settings dialog
- Onboarding flow
- Reminder scheduler with notifications
- Markdown + JSON export
- **All three desktop platforms ship together:**
  - Windows: portable `.zip` + installer `.exe`
  - macOS: `.dmg` containing `.app` (universal binary, Intel + Apple Silicon)
  - Linux: `AppImage` (works across distros) + `.deb` for Debian/Ubuntu
- Open source on GitHub with GitHub Actions building all three artifacts on release tag

### v1.1 — Sync milestone (target: +3-4 weeks)
- Local WiFi sync via mDNS + delta API (between desktop instances on same network)
- Pairing code flow
- Auto-update via version check
- AI-assisted search (`/find` with vague queries)
- Edge strip option
- Pin notes
- MCP client (real, not stub) with calendar/mail integration
- Two-model routing toggle (fast routing model + smart chat model)

### v2 — Polish + community (no specific target)
- Self-hosted sync server option (PocketBase or custom) for cross-network sync
- Conflict resolution UI for sync edge cases
- Plugin / theme system
- Localization (i18n)
- **Mobile apps (iOS + Android) — only if user demand justifies it.** Architecture is forward-compatible (local API + sync protocol exist), but mobile is not a committed roadmap item. Will be reassessed after v1.0 ships and gets real users. Likely React Native or Flutter, talking to the existing local API.

### Never building
- PC remote control (separate product)
- Note folders / notebooks (AI does organisation)
- Rich text editor / formatting toolbar
- File attachments
- Web search / browsing
- Multi-conversation sidebar
- Sharing / collaboration
- Telemetry / analytics

---

## 16.5. Cross-platform requirements (applies to ALL phases)

Since v1 ships to Win/Mac/Linux simultaneously, every phase must follow these rules:

**Code-level rules:**
- Never use `os.path` string concatenation — always `pathlib.Path`
- Never use Windows-only APIs (win32com, pywin32) without a fallback per OS
- Never hardcode forward or back slashes in paths
- File paths use `Path.home()`, `os.getenv("APPDATA")` only on Windows, `~/.config` on Linux, `~/Library/Application Support` on macOS — abstract this in `utils/paths.py`
- Notifications: `QSystemTrayIcon.showMessage` works on all three — use it, never platform-specific notification APIs
- Hotkeys via `pynput` (cross-platform); on macOS the user must grant Accessibility permission, the app must detect this and show a guided enable flow
- File system watcher (if used): `watchdog` library which abstracts inotify/FSEvents/ReadDirectoryChangesW

**Build-level rules:**
- One `pyproject.toml`, no platform-specific forks
- PyInstaller spec file uses platform conditionals only for icon files and launcher options
- GitHub Actions matrix build: `[windows-latest, macos-latest, macos-14 (Apple Silicon), ubuntu-latest]`
- Release artifacts:
  - `smartpad-{version}-windows-x64-setup.exe`
  - `smartpad-{version}-windows-x64-portable.zip`
  - `smartpad-{version}-macos-universal.dmg`
  - `smartpad-{version}-linux-x64.AppImage`
  - `smartpad-{version}-linux-x64.deb`

**Platform-specific gotchas (read before building):**
| Issue | Windows | macOS | Linux |
|---|---|---|---|
| Tray icon visibility | Always visible | Hidden by default in some setups; requires `LSUIElement` in Info.plist | Depends on desktop env (KDE, GNOME extension may be needed) |
| Global hotkey | Works out of box | Needs Accessibility permission, user-granted | Wayland blocks global hotkeys; X11 only |
| App on top | `WindowStaysOnTopHint` works | Same | Same on X11; Wayland has limits |
| llama.cpp prebuilt binaries | `.exe` available | `.dylib` for both archs | `.so` per glibc version |
| First-run model download path | `%APPDATA%/smartpad/models/` | `~/Library/Application Support/smartpad/models/` | `~/.local/share/smartpad/models/` |
| Code signing (v1.0) | Optional, SmartScreen warning if unsigned | **Required** or app shows "developer cannot be verified" — Apple Dev ID needed ($99/yr) | Not needed |
| App startup auto-launch | Startup folder shortcut | LaunchAgent plist | `.desktop` file in `~/.config/autostart/` |

**Wayland reality check (Linux):** GNOME Wayland blocks global hotkeys by design. Workaround: detect Wayland on startup, fall back to a tray-only summon (no hotkey) and show a one-time notice explaining why. X11 users get full hotkey support.

**macOS first-launch UX:** Without a paid Apple Developer account ($99/yr), users right-click → Open → Open the first time to bypass Gatekeeper. Document this in the README. v1.0 ships unsigned; v1.1 should add code signing.

---



---

## 17. Defaults Locked

| Setting | Default |
|---|---|
| Hotkey | Ctrl+Alt+Space |
| AI level | 1 (organise only) |
| Theme | System |
| Panel position | Top-right, 80px from top, 60px from right |
| Panel size | 420 × 560 |
| Startup with Windows | Off (user opts in) |
| Local model | Qwen 3 1.7B Q4_K_M |
| Routing temperature | 0.0 |
| Chat temperature | 0.6 |
| **Context strategy** | **sliding_summary** |
| **Context trigger (messages)** | **30** |
| **Context trigger (tokens)** | **6000** |
| **Messages summarised per pass** | **15** |
| **Recent messages always kept** | **15** |
| FTS5 search results limit | 50 |
| Reminder check interval | 30 seconds |
| Local API port | 7823 |
| **Quiet hours** | **10pm – 8am** |
| **Reminder notifications** | **Toast + Sound, on** |
| **Task notifications** | **Tray badge only, on** |
| **Error notifications** | **Toast + Tray badge, on** |
| **Sync notifications** | **Off** |
| **Auto-backup** | **Daily, keep last 7, on** |
| **Crash recovery** | **Always on, no toggle** |
| **Local model idle unload** | **30 min idle, on, configurable** |
| Telemetry | NONE |

---

## 18. Error Handling Conventions

| Failure | UX |
|---|---|
| LLM timeout / unreachable | Inline error bubble, retry button, never popup |
| DB write failure | Bubble shows ⚠️ with "couldn't save — retry?" |
| Model not loaded | Status bar warning + inline bubble offering "load model" |
| Provider auth failed | Settings opens auto-scrolled to that provider with error |
| Sync pairing failed | Toast notification, doesn't break anything |
| Disk full | Persistent warning bubble until resolved |
| Import malformed JSON | Confirmation dialog with details, don't import partial |

All errors logged to `<DATA_DIR>/logs/notch.log` via loguru with rotation.

---

## 19. Keyboard Shortcuts (in panel)

| Key | Action |
|---|---|
| Ctrl+Alt+Space | Toggle panel (global) |
| Esc | Hide panel |
| Enter | Send message |
| Shift+Enter | New line |
| / | Open slash menu |
| Up arrow (empty input) | Edit last user message |
| Ctrl+K | Focus search |
| Ctrl+, | Open settings |
| Ctrl+B | Open browse window |
| Ctrl+L | Clear chat stream |

---

## 20. Reliability Features

These are always-on or default-on. Each protects user data or trust.

### Auto-backup (default on, configurable)
- SQLite DB auto-copies to `<DATA_DIR>/backups/notch-YYYY-MM-DD.db` once per day
- Keeps last 7 backups, deletes older
- Triggered on first app launch each calendar day
- Settings: enable/disable, retention count (1-30), backup path override

### Crash recovery (always on)
- Every chat send writes a `.recovery` file before sending
- On next launch, if `.recovery` exists from previous session: panel reopens with last 5 messages restored, recovery file deleted
- No toggle. Always on. Silent.

### Local model idle unload (default on, configurable)
- llama-server holds VRAM continuously — wasteful when not chatting
- After 30 min of no chat activity, app sends shutdown to llama-server
- On next chat: app restarts llama-server (3-8 sec cold start, shows "warming up" status)
- Settings: enable/disable, idle threshold (5 min – 4 hours)

### Search history (always on)
- Last 10 searches remembered per session
- Shown as suggestions when search box focused
- Cleared on app close (not persisted across sessions for privacy)

### Export with filters (v1)
Export dialog has filters:
- Type: notes / tasks / reminders / snippets / all
- Date range: today / this week / this month / all time / custom
- Book: specific book or all
- Format: markdown / JSON / both

---

## 21. What's Different From Standard Note Apps

The spec deliberately omits things that turn note apps into productivity suites:

- **No folders** — books are AI-classified, user doesn't create them
- **No tags UI** — tags are AI-applied, search by tag works but no tag manager
- **No rich editor** — plain text, simple markdown rendering
- **No collaboration** — single user, multi-device
- **No web clipper** — out of scope
- **No daily notes / journal** — chat stream IS the daily log
- **No graph view** — search replaces visual exploration
- **No templates** — friction the AI eliminates

Stay disciplined on these. Every note app starts simple and bloats. The cuts above are what keeps SmartPad fast and clear.

---

## 22. Build Sequence (suggested for Claude Code)

When handing this to Claude Code, build in this order to maintain a working app at every step:

1. Project scaffold + `pyproject.toml` + Alembic init + first migration (create all tables)
2. `db/models.py` + repositories with basic CRUD
3. `providers/base.py` + `OpenAICompatibleProvider` (skip others first)
4. Worker pool + priority queues (no UI yet, console-driven test)
5. Router + intent detector + pattern matching (no LLM call yet, just slash + patterns)
6. Floating panel UI + tray + hotkey (hardcoded provider, simple chat)
7. Bubble widgets (chat first, then note/task/reminder/snippet)
8. Slash menu UI
9. AI level pipeline (Level 0 + 1 first, others later)
10. **Context window management — sliding window + summarisation**
11. FTS5 search + personal-data query routing
12. Reminder scheduler + tray notifications
13. **Notification settings — categories, quiet hours, mute**
14. Settings dialog (with all configurable options surfaced)
15. Onboarding flow
16. ManagedLocalProvider (model download + llama-server lifecycle + idle unload)
17. Anthropic + Google providers
18. Server detector (Ollama / LM Studio)
19. Browse window
20. Local API server (FastAPI) — even unused, for future
21. Auto-backup + crash recovery + search history
22. Export functions with filters
23. PyInstaller build + portable detection + first release

Each step should result in a runnable app that does something demoable. Don't build all 23 in parallel.

---

## 23. Open Items for Future Decisions

- Verify "SmartPad" (working codename, rename later) trademark/domain availability before public release
- Project icon / logo (suggest: a small notched-edge mark, monochrome)
- GitHub repo name: suggest `smartpad-app` or `getsmartpad`
- Code signing certificate (later, for SmartScreen warnings)
- Documentation site (mkdocs? README only for v1?)

---

End of spec. Hand this to Claude Code with the instruction "Build this product following the build sequence in section 22. Maintain a working app at every step."
