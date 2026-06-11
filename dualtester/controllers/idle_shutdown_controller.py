# controllers/idle_shutdown_controller.py
import time

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QLabel, QPushButton, QFrame

from ui.components.shutdown_dialogs import ShutdownController


IDLE_SHUTDOWN_TIMEOUT_S = 3 * 60 * 60
IDLE_SHUTDOWN_WARNING_S = 30 * 60
IDLE_CHECK_INTERVAL_MS = 1000


class IdleShutdownWarningOverlay(QFrame):
    """Koko ruudun varoitus automaattisesta sammutuksesta."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setGeometry(0, 0, 1920, 1080)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(0, 0, 0, 235);
                border: none;
            }
        """)

        self.title_label = QLabel("JÄRJESTELMÄ SAMMUU AUTOMAATTISESTI", self)
        self.title_label.setGeometry(210, 255, 1500, 80)
        self.title_label.setFont(QFont("Arial", 36, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("color: white; background: transparent; border: none;")

        self.info_label = QLabel("Järjestelmää ei ole käytetty kolmeen tuntiin.", self)
        self.info_label.setGeometry(210, 355, 1500, 60)
        self.info_label.setFont(QFont("Arial", 24))
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #DDDDDD; background: transparent; border: none;")

        self.countdown_label = QLabel("Aikaa jäljellä: 30:00", self)
        self.countdown_label.setGeometry(210, 455, 1500, 90)
        self.countdown_label.setFont(QFont("Consolas", 44, QFont.Bold))
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setStyleSheet("color: #FFCC00; background: transparent; border: none;")

        self.cancel_button = QPushButton("PERUUTA SAMMUTUS", self)
        self.cancel_button.setGeometry(660, 640, 600, 115)
        self.cancel_button.setFont(QFont("Arial", 28, QFont.Bold))
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #0B7A28;
                color: white;
                border-radius: 16px;
                border: none;
            }
            QPushButton:hover {
                background-color: #10A838;
            }
            QPushButton:pressed {
                background-color: #07551C;
            }
        """)

        self.hide()

    def set_remaining_seconds(self, remaining_seconds):
        remaining_seconds = max(0, int(remaining_seconds))
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        self.countdown_label.setText(f"Aikaa jäljellä: {minutes:02d}:{seconds:02d}")


class IdleShutdownController:
    """
    Automaattinen sammutus, jos yhtään testiä ei ole tehty kolmeen tuntiin.

    30 min ennen sammutusta näytetään koko ruudun varoitus ja peruutusnappi.
    Sammutusta ei tehdä, jos ForTest-testi tai Opta/jig-sekvenssi on kesken.
    """

    def __init__(self, main_window):
        self.main_window = main_window
        self.last_test_activity_at = time.monotonic()
        self.shutdown_started = False

        self.overlay = IdleShutdownWarningOverlay(main_window)
        self.overlay.cancel_button.clicked.connect(self.cancel_shutdown_warning)

        self.timer = QTimer(main_window)
        self.timer.timeout.connect(self.check_idle_shutdown)
        self.timer.start(IDLE_CHECK_INTERVAL_MS)

    def register_test_activity(self):
        self.last_test_activity_at = time.monotonic()
        self.shutdown_started = False
        self.hide_warning()

    def cancel_shutdown_warning(self):
        self.register_test_activity()

    def hide_warning(self):
        if self.overlay.isVisible():
            self.overlay.hide()

    def show_warning(self, remaining_seconds):
        self.overlay.set_remaining_seconds(remaining_seconds)

        if not self.overlay.isVisible():
            self.overlay.setGeometry(0, 0, self.main_window.width(), self.main_window.height())
            self.overlay.show()
            self.overlay.raise_()

    def check_idle_shutdown(self):
        if self.shutdown_started:
            return

        elapsed = time.monotonic() - self.last_test_activity_at
        remaining = IDLE_SHUTDOWN_TIMEOUT_S - elapsed

        if remaining <= 0:
            if self.is_system_busy():
                self.register_test_activity()
                return

            self.shutdown_started = True
            self.show_warning(0)
            ShutdownController.shutdown_system(self.main_window)
            return

        if remaining <= IDLE_SHUTDOWN_WARNING_S:
            self.show_warning(remaining)
            return

        self.hide_warning()

    def is_system_busy(self):
        station_controllers = getattr(self.main_window, "station_controllers", {}) or {}

        for controller in station_controllers.values():
            if getattr(controller, "is_running", False):
                return True

            if getattr(controller, "waiting_result_from_finished_test", False):
                return True

            if getattr(controller, "auto_part_change_in_progress", False):
                return True

        return False

    def cleanup(self):
        if self.timer:
            self.timer.stop()

        self.hide_warning()
