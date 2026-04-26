"""Time-window scheduler.

Ticks every 30 s. If the user enabled a window, the queue is allowed to
run only when the local clock falls inside (start, end) on an enabled
weekday. Crossing midnight (e.g. 22:00 -> 06:00) is supported.
"""
from __future__ import annotations

from datetime import datetime, time as dtime

from PySide6.QtCore import QObject, QTimer, Signal

from .config import ScheduleWindow


class Scheduler(QObject):
    allowed_changed = Signal(bool)

    def __init__(self, window: ScheduleWindow, parent: QObject | None = None):
        super().__init__(parent)
        self.window = window
        self._allowed = True
        self._timer = QTimer(self)
        self._timer.setInterval(30_000)
        self._timer.timeout.connect(self._tick)
        self._timer.start()
        self._tick()

    def update_window(self, window: ScheduleWindow) -> None:
        self.window = window
        self._tick()

    @property
    def allowed(self) -> bool:
        return self._allowed

    def _tick(self) -> None:
        allowed = self._compute_allowed(datetime.now())
        if allowed != self._allowed:
            self._allowed = allowed
            self.allowed_changed.emit(allowed)

    def _compute_allowed(self, now: datetime) -> bool:
        w = self.window
        if not w.enabled:
            return True
        weekday = now.weekday()
        start = dtime(w.start_hour, w.start_minute)
        end = dtime(w.end_hour, w.end_minute)
        cur = now.time()
        if start == end:
            return False
        if start < end:
            return weekday in w.days and start <= cur < end
        # Window wraps past midnight.
        if cur >= start:
            return weekday in w.days
        prev = (weekday - 1) % 7
        return prev in w.days and cur < end
