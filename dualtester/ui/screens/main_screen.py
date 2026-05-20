from PyQt5.QtWidgets import QWidget

from ui.components.environment_bar import EnvironmentBar
from ui.components.fortest_station import ForTestStation
from ui.components.shutdown_dialogs import ShutdownController


class MainScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background-color: black;")

        screen_w = self.parent().screen_width if self.parent() else 1920
        screen_h = self.parent().screen_height if self.parent() else 1080

        top_h = 90
        margin = 10
        gap = 10

        station_y = top_h + margin
        station_h = screen_h - station_y - margin
        station_w = (screen_w - (margin * 2) - gap) // 2

        # Yhteinen yläpalkki
        self.environment_bar = EnvironmentBar(self)
        self.environment_bar.setGeometry(
            margin,
            margin,
            screen_w - margin * 2,
            top_h - margin
        )

        # Vasen ForTest
        self.fortest1 = ForTestStation(
            station_id=1,
            title="FORTEST 1",
            parent=self
        )
        self.fortest1.setGeometry(
            margin,
            station_y,
            station_w,
            station_h
        )

        # Oikea ForTest
        self.fortest2 = ForTestStation(
            station_id=2,
            title="FORTEST 2",
            parent=self
        )
        self.fortest2.setGeometry(
            margin + station_w + gap,
            station_y,
            station_w,
            station_h
        )

        # Yläpalkin napit
        self.environment_bar.manual_button.clicked.connect(self.open_manual_screen)
        self.environment_bar.shutdown_button.clicked.connect(self.show_confirm_shutdown_dialog)

    def open_manual_screen(self):
        """Avaa käsikäyttösivu MainWindowin kautta"""
        if hasattr(self.parent(), "show_manual"):
            self.parent().show_manual()

    def show_confirm_shutdown_dialog(self):
        """Avaa sammutusdialogi erillisestä komponentista"""
        ShutdownController.show_confirm_dialog(self)

    def cleanup(self):
        """MainScreen cleanup"""
        pass