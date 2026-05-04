"""Browse window — SPEC.MD section 12 (secondary window).

Layout:
  Left sidebar: Books list + filter pills (Today, This Week, Pinned, All)
  Right pane:   Card grid of items in selected book/filter
  Top bar:      Search box (FTS5), sort dropdown, type filter chips
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)


class BrowseWindow(QWidget):
    """Secondary browse window — 900×600 default, resizable."""

    search_requested = pyqtSignal(str)    # FTS5 search query
    item_selected = pyqtSignal(str, str)  # (item_id, item_type)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("SmartPad — Browse")
        self.resize(900, 600)
        self.setMinimumSize(600, 400)
        self._current_filter = "all"
        self._current_book: str | None = None
        self._build_ui()

    # ── Build ─────────────────────────────────────────────────────────────────

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_top_bar())

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_sidebar())
        splitter.addWidget(self._build_card_pane())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([200, 700])
        root.addWidget(splitter, stretch=1)

    def _build_top_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("BrowseTopBar")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        self._search_box = QLineEdit()
        self._search_box.setObjectName("BrowseSearch")
        self._search_box.setPlaceholderText("Search notes, tasks, snippets…")
        self._search_box.returnPressed.connect(self._on_search)
        layout.addWidget(self._search_box, stretch=1)

        # Type filter chips
        for label, tag in [("All", "all"), ("Notes", "note"), ("Tasks", "task"),
                            ("Reminders", "reminder"), ("Snippets", "snippet")]:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setChecked(tag == "all")
            btn.setObjectName("TypeChip")
            btn.clicked.connect(lambda checked, t=tag: self._set_type_filter(t))
            layout.addWidget(btn)

        return bar

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("BrowseSidebar")
        sidebar.setFixedWidth(200)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(8, 8, 4, 8)
        layout.setSpacing(4)

        filter_label = QLabel("Quick filters")
        filter_label.setObjectName("SidebarSection")
        layout.addWidget(filter_label)

        for label, key in [("📅 Today", "today"), ("📆 This week", "week"),
                            ("📌 Pinned", "pinned"), ("🗂 All items", "all")]:
            btn = QPushButton(label)
            btn.setObjectName("SidebarFilter")
            btn.setCheckable(True)
            btn.setChecked(key == "all")
            btn.clicked.connect(lambda checked, k=key: self._set_filter(k))
            layout.addWidget(btn)

        books_label = QLabel("Books")
        books_label.setObjectName("SidebarSection")
        layout.addWidget(books_label)

        self._books_list = QListWidget()
        self._books_list.setObjectName("BooksList")
        self._books_list.currentItemChanged.connect(self._on_book_selected)
        layout.addWidget(self._books_list, stretch=1)

        return sidebar

    def _build_card_pane(self) -> QWidget:
        pane = QWidget()
        layout = QVBoxLayout(pane)
        layout.setContentsMargins(0, 0, 0, 0)

        self._cards_scroll = QScrollArea()
        self._cards_scroll.setObjectName("CardsArea")
        self._cards_scroll.setWidgetResizable(True)

        self._cards_container = QWidget()
        self._cards_container.setObjectName("CardsContainer")
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.setContentsMargins(12, 12, 12, 12)
        self._cards_layout.setSpacing(8)
        self._cards_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._empty_label = QLabel("Nothing here yet. Start capturing!")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setObjectName("EmptyState")
        self._cards_layout.addWidget(self._empty_label)

        self._cards_scroll.setWidget(self._cards_container)
        layout.addWidget(self._cards_scroll)
        return pane

    # ── Public API ────────────────────────────────────────────────────────────

    def populate_books(self, books: list[dict[str, str]]) -> None:
        """Set the books list. books is a list of {id, name} dicts."""
        self._books_list.clear()
        for b in books:
            item = QListWidgetItem(b["name"])
            item.setData(Qt.ItemDataRole.UserRole, b["id"])
            self._books_list.addItem(item)

    def populate_cards(self, items: list[dict]) -> None:
        """Populate the card grid. Each item: {id, type, content, created_at, ...}"""
        # Clear existing cards except empty label
        for i in reversed(range(self._cards_layout.count())):
            w = self._cards_layout.itemAt(i).widget()
            if w is not self._empty_label:
                self._cards_layout.removeWidget(w)
                w.deleteLater()

        self._empty_label.setVisible(len(items) == 0)

        for item in items:
            card = self._make_card(item)
            self._cards_layout.insertWidget(self._cards_layout.count() - 1, card)

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _on_search(self) -> None:
        query = self._search_box.text().strip()
        if query:
            self.search_requested.emit(query)

    def _set_filter(self, key: str) -> None:
        self._current_filter = key

    def _set_type_filter(self, tag: str) -> None:
        pass  # Wired to DB queries in Phase 19 full implementation

    def _on_book_selected(self, current: QListWidgetItem, _prev: object) -> None:
        if current:
            self._current_book = current.data(Qt.ItemDataRole.UserRole)

    # ── Card widget ───────────────────────────────────────────────────────────

    def _make_card(self, item: dict) -> QWidget:
        card = QWidget()
        card.setObjectName("BrowseCard")
        card.setStyleSheet("""
            QWidget#BrowseCard {
                background: #2b2d31;
                border: 1px solid #3d3f45;
                border-radius: 8px;
            }
            QWidget#BrowseCard:hover { border-color: #5865f2; }
        """)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)

        type_icons = {"note": "📝", "task": "✓", "reminder": "⏰", "snippet": "📋"}
        icon = QLabel(type_icons.get(item.get("type", "note"), "📝"))
        icon.setFixedWidth(24)
        layout.addWidget(icon)

        content = QLabel(str(item.get("content", ""))[:120])
        content.setWordWrap(True)
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        layout.addWidget(content, stretch=1)

        # Click handler
        item_id = item.get("id", "")
        item_type = item.get("type", "note")
        card.mousePressEvent = lambda e, iid=item_id, it=item_type: self.item_selected.emit(iid, it)  # type: ignore[method-assign]

        return card
