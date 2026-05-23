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

        # Kiinteä 1920x1080 koordinaattiasettelu
        # Kaikki koordinaatit ovat suhteessa MainScreenin vasempaan yläkulmaan

        # Yhteinen yläpalkki
        self.environment_bar = EnvironmentBar(self)
        self.environment_bar.setGeometry(0, 0, 1920, 85)

        # Vasen ForTest
        self.fortest1 = ForTestStation(
            station_id=1,
            parent=self
        )
        self.fortest1.setGeometry(0, 85, 960, 995)

        # Oikea ForTest
        self.fortest2 = ForTestStation(
            station_id=2,
            parent=self
        )
        self.fortest2.setGeometry(960, 85, 960, 995)

        # Yläpalkin napit
        self.environment_bar.settings_button.clicked.connect(self.open_settings_screen)
        self.environment_bar.manual_button.clicked.connect(self.open_manual_screen)
        self.environment_bar.shutdown_button.clicked.connect(self.show_confirm_shutdown_dialog)

    def open_settings_screen(self):
        """Avaa asetussivu MainWindowin kautta"""
        if hasattr(self.parent(), "show_settings"):
            self.parent().show_settings()

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