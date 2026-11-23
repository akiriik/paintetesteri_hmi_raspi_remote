# utils/ui_freeze_watchdog.py
"""Kirjaa Qt-pääsäikeen pitkät jumit diagnostiikkaa varten."""

import faulthandler
from datetime import datetime
from pathlib import Path
from threading import Event, Thread
import time

from PyQt5.QtCore import QObject, QTimer


FREEZE_THRESHOLD_S = 15.0
CHECK_INTERVAL_S = 2.0
DIAGNOSTIC_FILE = (
    Path.home()
    / ".local"
    / "share"
    / "painetesteri_hmi"
    / "ui_freeze_diagnostics.log"
)


class UiFreezeWatchdog(QObject):
    """Ei tee laiteohjauksia eikä käynnistä sovellusta uudelleen."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self._last_heartbeat = time.monotonic()
        self._stop_event = Event()
        self._freeze_reported = False

        self._heartbeat_timer = QTimer(self)
        self._heartbeat_timer.timeout.connect(self._heartbeat)
        self._heartbeat_timer.start(1000)

        self._watchdog_thread = Thread(
            target=self._monitor,
            name="painetesteri-ui-watchdog",
            daemon=True,
        )
        self._watchdog_thread.start()

    def _heartbeat(self):
        self._last_heartbeat = time.monotonic()

    def _monitor(self):
        while not self._stop_event.wait(CHECK_INTERVAL_S):
            stalled_for = time.monotonic() - self._last_heartbeat

            if stalled_for < FREEZE_THRESHOLD_S:
                self._freeze_reported = False
                continue

            if self._freeze_reported:
                continue

            self._freeze_reported = True

            try:
                DIAGNOSTIC_FILE.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                with DIAGNOSTIC_FILE.open(
                    "a",
                    encoding="utf-8",
                ) as diagnostic_log:
                    diagnostic_log.write(
                        "\n=== UI JUMI " +
                        datetime.now().astimezone().isoformat() +
                        f" ({stalled_for:.1f} s) ===\n"
                    )
                    diagnostic_log.flush()
                    faulthandler.dump_traceback(
                        file=diagnostic_log,
                        all_threads=True,
                    )
                    diagnostic_log.flush()
            except Exception as e:
                print(f"UI-watchdogin lokikirjoitus epäonnistui: {e}")

    def cleanup(self):
        self._heartbeat_timer.stop()
        self._stop_event.set()
