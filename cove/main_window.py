"""Cove Download Manager main window.

Layout matches the cove-screen-recorder shell:
    * frameless QMainWindow + custom Titlebar
    * Hero (h1 + subtitle + status pill)
    * StatsStrip
    * Two columns: downloads list (stage) | controls (panel)
    * Bottom action bar (Add, Add From Clipboard, Pause/Start Queue, ...)
    * Footer with hotkey hints + platform tag
"""
from __future__ import annotations

import platform as _platform

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QGuiApplication, QIcon, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from . import APP_NAME, __version__
from .clipboard import extract_urls
from .config import Settings
from .dialogs import (
    AddDownloadDialog,
    ClipboardBatchDialog,
    SchedulerDialog,
    SettingsDialog,
)
from .queue import DownloadTask, QueueManager
from .scheduler import Scheduler
from .widgets import (
    Footer,
    FramelessResizer,
    Section,
    StatsStrip,
    StatusPill,
    Titlebar,
    find_icon,
)

# Tree column indices.
COL_NAME = 0
COL_STATUS = 1
COL_PROGRESS = 2
COL_SIZE = 3
COL_SPEED = 4


def _human_bytes(n: int) -> str:
    if n <= 0:
        return "—"
    units = ["B", "KB", "MB", "GB", "TB"]
    f = float(n)
    for u in units:
        if f < 1024:
            return f"{int(f)} {u}" if u == "B" else f"{f:.1f} {u}"
        f /= 1024
    return f"{f:.1f} PB"


def _human_speed(bps: int) -> str:
    if bps <= 0:
        return "—"
    return f"{_human_bytes(bps)}/s"


def _platform_label() -> str:
    sys = _platform.system()
    if sys != "Linux":
        return sys
    import os

    session = os.environ.get("XDG_SESSION_TYPE", "").lower()
    if session == "wayland":
        return "Linux · Wayland"
    if session == "x11":
        return "Linux · X11"
    return "Linux"


class MainWindow(QMainWindow):
    def __init__(
        self,
        settings: Settings,
        queue: QueueManager,
        scheduler: Scheduler,
    ):
        super().__init__()
        self.settings = settings
        self.queue = queue
        self.scheduler = scheduler

        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setWindowTitle(f"{APP_NAME} Download Manager")
        icon_path = find_icon()
        if icon_path:
            self.setWindowIcon(QIcon(str(icon_path)))
        self.resize(1180, 720)
        self.setMinimumSize(880, 540)
        self._resizer = FramelessResizer(self)

        self._build_ui()
        self._wire_signals()

        # The scheduler may have already settled into "outside window"
        # before we connected its signal — push the current state into
        # the queue so launches respect the schedule from boot, not just
        # from the next transition.
        self.queue.set_scheduler_allowed(self.scheduler.allowed)

        for tid in self.queue.tasks:
            self._on_task_added(tid)

        # 1 Hz: stats strip + status pill (low-frequency overview).
        self._tick = QTimer(self)
        self._tick.setInterval(1000)
        self._tick.timeout.connect(self._slow_tick)
        self._tick.start()
        # ~30 Hz: re-render only the active rows so progress bars
        # interpolate smoothly between aria2 status samples.
        self._smooth = QTimer(self)
        self._smooth.setInterval(33)
        self._smooth.timeout.connect(self._smooth_tick)
        self._smooth.start()
        self._refresh_stats()
        self._refresh_status_pill()
        self._refresh_schedule_section()

    # ---- UI construction ------------------------------------------------

    def _build_ui(self) -> None:
        chrome = QWidget()
        chrome.setObjectName("chrome")
        outer = QVBoxLayout(chrome)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Titlebar
        self.titlebar = Titlebar(self, f"{APP_NAME} Download Manager", __version__)
        outer.addWidget(self.titlebar)

        # Body
        body = QWidget()
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(28, 24, 28, 16)
        body_lay.setSpacing(18)

        # Hero
        hero = QHBoxLayout()
        hero.setSpacing(16)
        hero_text = QVBoxLayout()
        hero_text.setSpacing(4)
        h1 = QLabel(f"{APP_NAME} Download Manager")
        h1.setProperty("role", "hero-h1")
        sub = QLabel(
            "Multi-connection downloads with a queue, schedule, and a global speed cap."
        )
        sub.setProperty("role", "hero-sub")
        hero_text.addWidget(h1)
        hero_text.addWidget(sub)
        hero.addLayout(hero_text, 1)
        self.status_pill = StatusPill("Idle")
        hero.addWidget(self.status_pill, 0, Qt.AlignTop)
        body_lay.addLayout(hero)

        # Stats strip
        self.stats = StatsStrip()
        self.stats.add_cell("Active", "0")
        self.stats.add_cell("Queued", "0")
        self.stats.add_cell("Total", "—")
        self.stats.add_cell("Cap", "Unlimited", last=True)
        body_lay.addWidget(self.stats)

        # Two-column area
        cols = QHBoxLayout()
        cols.setSpacing(16)
        cols.addLayout(self._build_stage(), 7)
        cols.addLayout(self._build_panel(), 4)
        body_lay.addLayout(cols, 1)

        # Bottom action bar
        body_lay.addLayout(self._build_actionbar())

        outer.addWidget(body, 1)

        # Footer
        self.footer = Footer()
        self.footer.add_hotkey("Add", "Ctrl + N")
        self.footer.add_hotkey("From Clipboard", "Ctrl + Shift + V")
        self.footer.add_hotkey("Toggle Queue", "Ctrl + P")
        self.footer.set_platform(_platform_label())
        outer.addWidget(self.footer)

        self.setCentralWidget(chrome)

        # Shortcuts
        self._add_shortcut("Ctrl+N", self._add_download)
        self._add_shortcut("Ctrl+Shift+V", self._add_from_clipboard)
        self._add_shortcut("Ctrl+P", self._toggle_queue)

    def _build_stage(self) -> QVBoxLayout:
        stage = QVBoxLayout()
        stage.setSpacing(12)

        label = QLabel("Downloads")
        label.setProperty("role", "section-label")
        stage.addWidget(label)

        self.tree = QTreeWidget()
        self.tree.setColumnCount(5)
        self.tree.setHeaderLabels(["Name", "Status", "Progress", "Size", "Speed"])
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.setUniformRowHeights(True)
        self.tree.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._open_context_menu)

        header = self.tree.header()
        header.setSectionResizeMode(COL_NAME, QHeaderView.Stretch)
        header.setSectionResizeMode(COL_STATUS, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_PROGRESS, QHeaderView.Fixed)
        header.resizeSection(COL_PROGRESS, 220)
        header.setSectionResizeMode(COL_SIZE, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(COL_SPEED, QHeaderView.ResizeToContents)
        stage.addWidget(self.tree, 1)

        self._items: dict[int, QTreeWidgetItem] = {}
        self._bars: dict[int, QProgressBar] = {}

        # Delete key removes the selected rows. WidgetShortcut so it only
        # fires when the tree has focus.
        del_sc = QShortcut(QKeySequence(Qt.Key_Delete), self.tree)
        del_sc.setContext(Qt.WidgetShortcut)
        del_sc.activated.connect(lambda: self._remove_selected(delete_file=False))
        return stage

    def _build_panel(self) -> QVBoxLayout:
        panel = QVBoxLayout()
        panel.setSpacing(10)

        # Concurrent
        sec_conc = Section("Concurrent downloads")
        self.concurrent_spin = QSpinBox()
        self.concurrent_spin.setRange(1, 16)
        self.concurrent_spin.setValue(self.settings.max_concurrent)
        self.concurrent_spin.valueChanged.connect(self.queue.set_max_concurrent)
        hint_conc = QLabel("How many files run at once.")
        hint_conc.setProperty("role", "muted")
        sec_conc.body().addWidget(self.concurrent_spin)
        sec_conc.body().addWidget(hint_conc)
        panel.addWidget(sec_conc)

        # Speed cap
        sec_speed = Section("Global speed limit")
        # Header row: spinbox + small (i) info badge.
        head = QHBoxLayout()
        head.setSpacing(8)
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(0, 1_000_000)
        self.speed_spin.setSuffix(" KB/s")
        self.speed_spin.setSpecialValueText("Unlimited")
        self.speed_spin.setValue(self.settings.overall_speed_limit_kbps)
        self.speed_spin.valueChanged.connect(self._on_speed_value_changed)
        head.addWidget(self.speed_spin, 1)

        info = QLabel("i")
        info.setObjectName("infoBadge")
        info.setAlignment(Qt.AlignCenter)
        info.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        info.setFixedSize(20, 20)
        info.setToolTip(
            "Internet servers may break the connection when speed is too "
            "limited. It's not recommended to use the Speed Limiter to "
            "download from servers that don't support resume."
        )
        head.addWidget(info, 0)
        sec_speed.body().addLayout(head)

        # Always-on-startup checkbox.
        self.speed_always_on = QCheckBox("Always turn on Speed Limiter on startup")
        self.speed_always_on.setChecked(self.settings.speed_limiter_enabled)
        self.speed_always_on.toggled.connect(self._on_speed_always_on_toggled)
        sec_speed.body().addWidget(self.speed_always_on)

        speed_hint = QLabel("Total downstream cap across all files.")
        speed_hint.setProperty("role", "muted")
        sec_speed.body().addWidget(speed_hint)
        panel.addWidget(sec_speed)

        # Schedule
        sec_sched = Section("Schedule")
        self.schedule_state_label = QLabel("Off")
        self.schedule_state_label.setProperty("role", "mono")
        self.schedule_window_label = QLabel("Downloads run any time.")
        self.schedule_window_label.setProperty("role", "muted")
        self.schedule_window_label.setWordWrap(True)
        edit = QPushButton("Edit schedule")
        edit.clicked.connect(self._open_scheduler)
        sec_sched.body().addWidget(self.schedule_state_label)
        sec_sched.body().addWidget(self.schedule_window_label)
        sec_sched.body().addWidget(edit)
        panel.addWidget(sec_sched)

        panel.addStretch(1)
        return panel

    def _build_actionbar(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(10)

        self.add_btn = QPushButton("Add download")
        self.add_btn.setProperty("kind", "accent")
        self.add_btn.clicked.connect(self._add_download)
        row.addWidget(self.add_btn)

        self.clip_btn = QPushButton("Add from clipboard")
        self.clip_btn.clicked.connect(self._add_from_clipboard)
        row.addWidget(self.clip_btn)

        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self._open_settings)
        row.addWidget(self.settings_btn)

        self.clear_btn = QPushButton("Clear completed")
        self.clear_btn.clicked.connect(lambda: self._clear_completed(False))
        row.addWidget(self.clear_btn)

        row.addStretch(1)

        self.queue_btn = QPushButton("Pause queue")
        self.queue_btn.clicked.connect(self._toggle_queue)
        row.addWidget(self.queue_btn)
        return row

    def _add_shortcut(self, key: str, slot) -> None:
        act = QAction(self)
        act.setShortcut(QKeySequence(key))
        act.triggered.connect(slot)
        self.addAction(act)

    def _wire_signals(self) -> None:
        self.queue.task_added.connect(self._on_task_added)
        self.queue.task_changed.connect(self._on_task_changed)
        self.queue.task_removed.connect(self._on_task_removed)
        self.queue.queue_running_changed.connect(self._on_queue_running_changed)
        self.queue.error.connect(self._on_error)
        self.scheduler.allowed_changed.connect(self._on_scheduler_changed)

    # ---- actions --------------------------------------------------------

    def _add_download(self) -> None:
        dlg = AddDownloadDialog(self.settings, self)
        if dlg.exec() != AddDownloadDialog.Accepted:
            return
        urls = dlg.get_urls()
        if not urls:
            QMessageBox.information(self, "Nothing to add", "No URLs detected.")
            return
        self.settings.download_dir = dlg.get_dir()
        self.settings.save()
        self.queue.add_urls(urls)

    def _add_from_clipboard(self) -> None:
        text = QGuiApplication.clipboard().text() or ""
        urls = extract_urls(text)
        if not urls:
            QMessageBox.information(
                self, "Clipboard empty", "No URLs found on the clipboard."
            )
            return
        dlg = ClipboardBatchDialog(urls, self)
        if dlg.exec() == ClipboardBatchDialog.Accepted:
            chosen = dlg.selected()
            if chosen:
                self.queue.add_urls(chosen)

    def _toggle_queue(self) -> None:
        if self.queue.is_running:
            self.queue.stop_queue()
        else:
            self.queue.start_queue()

    def _open_scheduler(self) -> None:
        dlg = SchedulerDialog(self.settings.schedule, self.settings, self)
        if dlg.exec() == SchedulerDialog.Accepted:
            self.settings.schedule = dlg.result_window()
            self.settings.time_format_24h = dlg.use_24h_format()
            self.settings.save()
            self.scheduler.update_window(self.settings.schedule)
            self._refresh_status_pill()
            self._refresh_schedule_section()

    def _open_settings(self) -> None:
        dlg = SettingsDialog(self.settings, self)
        if dlg.exec() == SettingsDialog.Accepted:
            self.concurrent_spin.blockSignals(True)
            self.concurrent_spin.setValue(self.settings.max_concurrent)
            self.concurrent_spin.blockSignals(False)
            self.speed_spin.blockSignals(True)
            self.speed_spin.setValue(self.settings.overall_speed_limit_kbps)
            self.speed_spin.blockSignals(False)
            self.queue.set_max_concurrent(self.settings.max_concurrent)
            self._apply_speed_limit()
            self._refresh_schedule_section()

    def _clear_completed(self, delete_files: bool) -> None:
        completed = [t for t in self.queue.tasks.values() if t.status == "completed"]
        if not completed:
            return
        if delete_files:
            ans = QMessageBox.question(
                self,
                "Delete completed files?",
                f"This permanently deletes {len(completed)} file(s) from disk.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if ans != QMessageBox.Yes:
                return
        self.queue.clear_completed(delete_files=delete_files)

    def _on_speed_value_changed(self, value: int) -> None:
        self.settings.overall_speed_limit_kbps = value
        self.settings.save()
        self._apply_speed_limit()

    def _on_speed_always_on_toggled(self, checked: bool) -> None:
        self.settings.speed_limiter_enabled = checked
        self.settings.save()
        self._apply_speed_limit()

    def _apply_speed_limit(self) -> None:
        """Push the effective limit (kbps if enabled, else 0) to aria2."""
        kbps = self.settings.overall_speed_limit_kbps
        effective = kbps if self.settings.speed_limiter_enabled else 0
        self.queue.set_overall_speed_limit(effective)
        cap = "Unlimited" if effective == 0 else f"{effective} KB/s"
        self.stats.set_value("Cap", cap)

    # ---- context menu --------------------------------------------------

    def _selected_tids(self) -> list[int]:
        return [int(it.data(0, Qt.UserRole)) for it in self.tree.selectedItems()]

    def _remove_selected(self, *, delete_file: bool) -> None:
        tids = self._selected_tids()
        if not tids:
            return
        if delete_file:
            ans = QMessageBox.question(
                self,
                "Delete files?",
                f"This permanently deletes {len(tids)} file(s) from disk.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if ans != QMessageBox.Yes:
                return
        for tid in tids:
            self.queue.remove(tid, delete_file=delete_file)

    def _clear_all(self) -> None:
        tids = list(self.queue.tasks.keys())
        if not tids:
            return
        ans = QMessageBox.question(
            self,
            "Clear all downloads?",
            f"Remove all {len(tids)} downloads from the list? Files on disk are kept.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if ans != QMessageBox.Yes:
            return
        for tid in tids:
            self.queue.remove(tid, delete_file=False)

    def _open_context_menu(self, pos) -> None:
        menu = QMenu(self)
        item = self.tree.itemAt(pos)

        if item is not None:
            tid = item.data(0, Qt.UserRole)
            task = self.queue.tasks.get(tid)
            selected = self._selected_tids()
            if task is not None:
                # If the right-clicked row isn't part of the existing
                # selection, treat the click as selecting just that row.
                if tid not in selected:
                    self.tree.setCurrentItem(item)
                    selected = [tid]
                if task.status in {"queued", "active"}:
                    menu.addAction("Pause").triggered.connect(
                        lambda: [self.queue.pause(t) for t in selected]
                    )
                if task.status in {"paused", "error"}:
                    menu.addAction("Resume").triggered.connect(
                        lambda: [self.queue.resume(t) for t in selected]
                    )
                menu.addSeparator()
                menu.addAction("Remove\tDel").triggered.connect(
                    lambda: self._remove_selected(delete_file=False)
                )
                menu.addAction("Remove and delete file").triggered.connect(
                    lambda: self._remove_selected(delete_file=True)
                )
                menu.addSeparator()

        # Always-available bulk actions (shown on rows and on empty space).
        completed_count = sum(
            1 for t in self.queue.tasks.values() if t.status == "completed"
        )
        a = menu.addAction(f"Clear completed ({completed_count})")
        a.setEnabled(completed_count > 0)
        a.triggered.connect(lambda: self._clear_completed(False))
        b = menu.addAction("Clear all")
        b.setEnabled(bool(self.queue.tasks))
        b.triggered.connect(self._clear_all)

        menu.exec(self.tree.viewport().mapToGlobal(pos))

    # ---- queue handlers ------------------------------------------------

    def _on_task_added(self, tid: int) -> None:
        task = self.queue.tasks.get(tid)
        if not task:
            return
        item = QTreeWidgetItem(["", "", "", "", ""])
        item.setData(0, Qt.UserRole, tid)
        self.tree.addTopLevelItem(item)
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setTextVisible(True)
        self.tree.setItemWidget(item, COL_PROGRESS, bar)
        self._items[tid] = item
        self._bars[tid] = bar
        self._render(task)
        self._refresh_status_pill()

    def _on_task_changed(self, tid: int) -> None:
        task = self.queue.tasks.get(tid)
        if task:
            self._render(task)
            self._refresh_stats()
            self._refresh_status_pill()

    def _on_task_removed(self, tid: int) -> None:
        item = self._items.pop(tid, None)
        self._bars.pop(tid, None)
        if item:
            idx = self.tree.indexOfTopLevelItem(item)
            if idx >= 0:
                self.tree.takeTopLevelItem(idx)
        self._refresh_stats()
        self._refresh_status_pill()

    def _on_queue_running_changed(self, running: bool) -> None:
        self.queue_btn.setText("Pause queue" if running else "Start queue")
        self.queue_btn.setProperty("kind", "" if running else "accent")
        self.queue_btn.style().unpolish(self.queue_btn)
        self.queue_btn.style().polish(self.queue_btn)
        self._refresh_status_pill()

    def _on_scheduler_changed(self, allowed: bool) -> None:
        self.queue.set_scheduler_allowed(allowed)
        self._refresh_status_pill()
        self._refresh_schedule_section()

    def _on_error(self, msg: str) -> None:
        # Don't be intrusive — flash it in the status pill briefly.
        self.status_pill.set_state("error", "Error")
        QTimer.singleShot(4000, self._refresh_status_pill)

    # ---- rendering -----------------------------------------------------

    def _render(self, task: DownloadTask) -> None:
        item = self._items.get(task.id)
        bar = self._bars.get(task.id)
        if not item or not bar:
            return
        name = task.filename or task.url
        item.setText(COL_NAME, name)
        item.setToolTip(COL_NAME, task.error or task.url)
        item.setText(COL_STATUS, _status_label(task.status))
        completed = task.interpolated_completed_bytes()
        if task.total_bytes > 0:
            pct = int(completed * 100 / task.total_bytes)
            bar.setValue(pct)
            bar.setFormat(f"{pct}%")
        else:
            bar.setValue(100 if task.status == "completed" else 0)
            bar.setFormat("100%" if task.status == "completed" else "—")
        size_text = (
            f"{_human_bytes(completed)} / {_human_bytes(task.total_bytes)}"
            if task.total_bytes
            else _human_bytes(completed)
        )
        item.setText(COL_SIZE, size_text)
        item.setText(
            COL_SPEED,
            _human_speed(task.download_speed) if task.status == "active" else "—",
        )

    def _slow_tick(self) -> None:
        self._refresh_stats()
        self._refresh_status_pill()

    def _smooth_tick(self) -> None:
        # Re-render only active rows; everything else is static between
        # aria2 polls so re-rendering it would just be wasted work.
        for tid, task in list(self.queue.tasks.items()):
            if task.status == "active":
                self._render(task)

    def _refresh_stats(self) -> None:
        active = sum(1 for t in self.queue.tasks.values() if t.status == "active")
        queued = sum(1 for t in self.queue.tasks.values() if t.status == "queued")
        speed = sum(t.download_speed for t in self.queue.tasks.values() if t.status == "active")
        kbps = self.settings.overall_speed_limit_kbps
        if kbps == 0 or not self.settings.speed_limiter_enabled:
            cap_text = "Unlimited"
        else:
            cap_text = f"{kbps} KB/s"
        self.stats.set_value("Active", str(active))
        self.stats.set_value("Queued", str(queued))
        self.stats.set_value("Total", _human_speed(speed) if speed > 0 else "—")
        self.stats.set_value("Cap", cap_text)

    def _refresh_status_pill(self) -> None:
        if not self.queue.is_running:
            self.status_pill.set_state("paused", "Queue paused")
            return
        if self.settings.schedule.enabled and not self.scheduler.allowed:
            self.status_pill.set_state("off", "Outside schedule")
            return
        active = any(t.status == "active" for t in self.queue.tasks.values())
        queued = any(t.status == "queued" for t in self.queue.tasks.values())
        if active:
            self.status_pill.set_state("ok", "Running")
        elif queued:
            self.status_pill.set_state("ok", "Queued")
        else:
            self.status_pill.set_state("ok", "Idle")

    def _refresh_schedule_section(self) -> None:
        s = self.settings.schedule
        if not s.enabled:
            self.schedule_state_label.setText("Off")
            self.schedule_window_label.setText("Downloads run any time.")
            return
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        on_days = ", ".join(days[d] for d in sorted(s.days)) or "no days"
        start = _fmt_time(s.start_hour, s.start_minute, self.settings.time_format_24h)
        end = _fmt_time(s.end_hour, s.end_minute, self.settings.time_format_24h)
        self.schedule_state_label.setText(f"{start} – {end}")
        tag = "within window" if self.scheduler.allowed else "outside window"
        self.schedule_window_label.setText(f"{on_days} · {tag}")


def _fmt_time(hour: int, minute: int, use_24h: bool) -> str:
    if use_24h:
        return f"{hour:02d}:{minute:02d}"
    period = "AM" if hour < 12 else "PM"
    h12 = hour % 12 or 12
    return f"{h12}:{minute:02d} {period}"


def _status_label(s: str) -> str:
    return {
        "queued": "Queued",
        "active": "Downloading",
        "paused": "Paused",
        "completed": "Done",
        "error": "Error",
    }.get(s, s)
