# ui/components/environment_bar.py
from PyQt5.QtWidgets import QFrame, QLabel, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class EnvironmentBar(QFrame):
    """
    Päänäkymän yläpalkki.

    Etusivulla näytetään vain ympäristöarvot ja navigointinapit.
    Laiteyhteyksien tilat näytetään asetussivulla.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.room_temperature = None
        self.room_humidity = None
        self.tank_temperature = None
        self.tank_humidity = None
        self.tank_pressure = None
        self.part_temperature = None

        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #101010;
                border: 0px solid #bfbfbf;
                border-radius: 0px;
            }
        """)

        env_x = 220
        env_y = 6
        env_w = 940
        env_h = 70

        settings_x = 1240
        settings_y = 10
        settings_w = 190
        settings_h = 60

        manual_x = 1450
        manual_y = 10
        manual_w = 190
        manual_h = 60

        shutdown_x = 1660
        shutdown_y = 10
        shutdown_w = 210
        shutdown_h = 60

        self.environment_label = QLabel("", self)
        self.environment_label.setGeometry(env_x, env_y, env_w, env_h)
        self.environment_label.setFont(QFont("Consolas", 20, QFont.Bold))
        self.environment_label.setStyleSheet("color: white; background: transparent; border: none;")
        self.environment_label.setAlignment(Qt.AlignCenter)

        self.settings_button = QPushButton("ASETUKSET", self)
        self.settings_button.setGeometry(settings_x, settings_y, settings_w, settings_h)
        self.settings_button.setFont(QFont("Arial", 16, QFont.Bold))
        self.settings_button.setStyleSheet("""
            QPushButton {
                background-color: #303030;
                color: white;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)

        self.manual_button = QPushButton("KÄSIKÄYTTÖ", self)
        self.manual_button.setGeometry(manual_x, manual_y, manual_w, manual_h)
        self.manual_button.setFont(QFont("Arial", 16, QFont.Bold))
        self.manual_button.setStyleSheet("""
            QPushButton {
                background-color: #303030;
                color: white;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)

        self.shutdown_button = QPushButton("SAMMUTA", self)
        self.shutdown_button.setGeometry(shutdown_x, shutdown_y, shutdown_w, shutdown_h)
        self.shutdown_button.setFont(QFont("Arial", 16, QFont.Bold))
        self.shutdown_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)

        self.refresh_display()

    def update_environment_values(
        self,
        room_temperature=None,
        room_humidity=None,
        tank_temperature=None,
        tank_humidity=None,
        tank_pressure=None,
        part_temperature=None,
    ):
        self.room_temperature = room_temperature
        self.room_humidity = room_humidity
        self.tank_temperature = tank_temperature
        self.tank_humidity = tank_humidity
        self.tank_pressure = tank_pressure
        self.part_temperature = part_temperature

        self.refresh_display()

    def update_hardware_status(self, text):
        pass

    def update_fortest_status(self, text):
        pass

    def refresh_display(self):
        room_temp = f"{self.room_temperature:.1f}°C" if self.room_temperature is not None else "--.-°C"
        room_hum = f"{self.room_humidity:.1f} %" if self.room_humidity is not None else "--.- %"
        part_temp = f"{self.part_temperature:.1f}°C" if self.part_temperature is not None else "--.-°C"

        self.environment_label.setText(
            f"HUONE: {room_temp} / {room_hum}        KAPPALE: {part_temp}"
        )
