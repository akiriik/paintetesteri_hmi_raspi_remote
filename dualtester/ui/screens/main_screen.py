from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt

from ui.components.environment_bar import EnvironmentBar
from ui.components.fortest_station import ForTestStation


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

        self.environment_bar = EnvironmentBar(self)
        self.environment_bar.setGeometry(margin, margin, screen_w - margin * 2, top_h - margin)

        self.fortest1 = ForTestStation(
            station_id=1,
            title="FORTEST 1",
            parent=self
        )
        self.fortest1.setGeometry(margin, station_y, station_w, station_h)

        self.fortest2 = ForTestStation(
            station_id=2,
            title="FORTEST 2",
            parent=self
        )
        self.fortest2.setGeometry(margin + station_w + gap, station_y, station_w, station_h)