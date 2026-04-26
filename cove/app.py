"""Cove Download Manager bootstrap.

Order:
  1. QApplication + cove theme + window icon
  2. Settings, Scheduler, MainWindow (window is shown immediately so any
     subsequent error dialogs have a real top-level parent — Wayland +
     QMessageBox(None, ...) crashes on some systems)
  3. Aria2 daemon start (deferred via QTimer). On failure, show an error
     parented to the main window and disable user actions.
"""
from __future__ import annotations

import sys

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication, QIcon, QPalette, QColor
from PySide6.QtWidgets import QApplication, QMessageBox

from . import APP_NAME, __version__
from .aria2 import Aria2Daemon, Aria2Error, Aria2RPC
from .config import Settings
from .main_window import MainWindow
from .queue import QueueManager
from .scheduler import Scheduler
from .theme import BG, QSS, SURFACE_2, TEXT
from .updater import UpdateController
from .widgets import find_icon

UPDATE_REPO = "Sin213/cove-download-manager"


def _apply_palette(app: QApplication) -> None:
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor(BG))
    pal.setColor(QPalette.WindowText, QColor(TEXT))
    pal.setColor(QPalette.Base, QColor(BG))
    pal.setColor(QPalette.AlternateBase, QColor(SURFACE_2))
    pal.setColor(QPalette.Text, QColor(TEXT))
    pal.setColor(QPalette.ToolTipBase, QColor(SURFACE_2))
    pal.setColor(QPalette.ToolTipText, QColor(TEXT))
    pal.setColor(QPalette.Highlight, QColor("#50e6cf"))
    pal.setColor(QPalette.HighlightedText, QColor("#07120f"))
    app.setPalette(pal)


def run() -> int:
    QApplication.setAttribute(Qt.AA_DontUseNativeDialogs, False)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("cove")

    icon_path = find_icon()
    if icon_path:
        app.setWindowIcon(QIcon(str(icon_path)))

    _apply_palette(app)
    app.setStyleSheet(QSS)

    settings = Settings.load()
    daemon = Aria2Daemon(settings)
    rpc = Aria2RPC(settings)
    queue = QueueManager(settings, rpc)
    scheduler = Scheduler(settings.schedule)

    window = MainWindow(settings, queue, scheduler)
    window.show()
    app.processEvents()

    def _boot_daemon() -> None:
        try:
            daemon.start()
        except Aria2Error as e:
            QMessageBox.critical(window, f"{APP_NAME} — aria2 missing", str(e))
            window.setEnabled(False)
            return
        # Apply the effective speed limit (kbps if the limiter is on, else 0).
        effective = settings.overall_speed_limit_kbps if settings.speed_limiter_enabled else 0
        try:
            rpc.set_overall_speed_limit_kbps(effective)
        except Aria2Error:
            pass
        # Now that aria2 is reachable, drive any persisted-queued tasks.
        queue.resume_persisted()

    QTimer.singleShot(0, _boot_daemon)

    # Update check — opt-in by default, always prompts before installing.
    if settings.auto_update_check:
        updater = UpdateController(
            parent=window,
            current_version=__version__,
            repo=UPDATE_REPO,
            app_display_name=f"{APP_NAME} Download Manager",
            cache_subdir="cove-download-manager",
        )
        # Defer a few seconds so the window has fully painted before any
        # network or dialog work happens.
        QTimer.singleShot(4000, updater.check)
        window._updater = updater  # keep a reference

    def _cleanup() -> None:
        try:
            rpc.shutdown()
        except Exception:
            pass
        daemon.stop()

    app.aboutToQuit.connect(_cleanup)
    return app.exec()
