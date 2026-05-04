# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for SmartPad — SPEC.MD section 16.5
# Produces a single-file executable on each platform.
# Build with: pyinstaller smartpad.spec

import sys
from pathlib import Path

block_cipher = None

# Platform-specific icon
if sys.platform == "win32":
    icon_file = "resources/icons/smartpad.ico"
elif sys.platform == "darwin":
    icon_file = "resources/icons/smartpad.icns"
else:
    icon_file = "resources/icons/smartpad.png"

a = Analysis(
    ["src/smartpad/__main__.py"],
    pathex=[str(Path.cwd() / "src")],
    binaries=[],
    datas=[
        ("resources/", "resources/"),
        ("alembic/", "alembic/"),
        ("alembic.ini", "."),
    ],
    hiddenimports=[
        "smartpad",
        "smartpad.app",
        "smartpad.config",
        "smartpad.core",
        "smartpad.core.router",
        "smartpad.core.intent_detector",
        "smartpad.core.worker_pool",
        "smartpad.core.ai_levels",
        "smartpad.core.chat_service",
        "smartpad.db",
        "smartpad.db.models",
        "smartpad.db.engine",
        "smartpad.db.migrations",
        "smartpad.db.repositories",
        "smartpad.providers",
        "smartpad.providers.base",
        "smartpad.providers.openai_compatible",
        "smartpad.providers.registry",
        "smartpad.ui",
        "smartpad.ui.floating_panel",
        "smartpad.ui.tray",
        "smartpad.ui.slash_menu",
        "smartpad.ui.styles",
        "smartpad.ui.onboarding",
        "smartpad.ui.settings_dialog",
        "smartpad.ui.browse_window",
        "smartpad.ui.bubbles",
        "smartpad.utils",
        "smartpad.utils.paths",
        "smartpad.utils.portable",
        # Third-party hidden imports
        "PyQt6",
        "PyQt6.QtCore",
        "PyQt6.QtWidgets",
        "PyQt6.QtGui",
        "sqlalchemy.dialects.sqlite",
        "alembic",
        "pynput",
        "pynput.keyboard",
        "zeroconf",
        "loguru",
        "keyring",
        "dateparser",
        "markdown_it",
        "aiosqlite",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="smartpad",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,    # GUI app — no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file if Path(icon_file).exists() else None,
)

# macOS: wrap in .app bundle
if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="SmartPad.app",
        icon=icon_file if Path(icon_file).exists() else None,
        bundle_identifier="com.smartpad.app",
        info_plist={
            "LSUIElement": True,       # hide from Dock — tray-only app
            "NSHighResolutionCapable": True,
            "CFBundleShortVersionString": "0.1.0",
            "CFBundleVersion": "0.1.0",
        },
    )
