# ui/components/environment_bar.py
from PyQt5.QtWidgets import QFrame, QLabel, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class EnvironmentBar(QFrame):
    """
    Päänäkymän yläpalkki.

    Tämä on UI-komponentti:
    - ei lue Modbusia
    - ei lue GPIO:ta
    - ei lue antureita
    - näyttää vain sille annetut arvot
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.room_temperature = None
        self.room_humidity = None
        self.tank_temperature = None
        self.tank_humidity = None
        self.tank_pressure = None
        self.part_temperature = None
        self.hardware_status_text = "IO: --    ANTURIT: --"
        self.fortest_status_text = "FORTEST 1: --    FORTEST 2: --"

        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #101010;
                border: 2px solid #333333;
                border-radius: 10px;
            }
        """)

        # Koordinaatit
 #       title_x = 10
 #       title_y = 10
 #       title_w = 420
 #       title_h = 60

        env_x = 10
        env_y = 6
        env_w = 850
        env_h = 32

        hw_x = 10
        hw_y = 40
        hw_w = 760
        hw_h = 30

        ft_x = 720
        ft_y = 40
        ft_w = 390
        ft_h = 30

        manual_x = 1450
        manual_y = 10
        manual_w = 190
        manual_h = 60

        shutdown_x = 1660
        shutdown_y = 10
        shutdown_w = 210
        shutdown_h = 60

#        self.title_label = QLabel("TEST", self)
#        self.title_label.setGeometry(title_x, title_y, title_w, title_h)
#        self.title_label.setFont(QFont("Consolas", 22, QFont.Bold))
#        self.title_label.setStyleSheet("color: white; background: transparent; border: none;")
#        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.environment_label = QLabel("", self)
        self.environment_label.setGeometry(env_x, env_y, env_w, env_h)
        self.environment_label.setFont(QFont("Consolas", 14))
        self.environment_label.setStyleSheet("color: #33FF33; background: transparent; border: none;")
        self.environment_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.hardware_label = QLabel("", self)
        self.hardware_label.setGeometry(hw_x, hw_y, hw_w, hw_h)
        self.hardware_label.setFont(QFont("Consolas", 13))
        self.hardware_label.setStyleSheet("color: orange; background: transparent; border: none;")
        self.hardware_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.fortest_label = QLabel("", self)
        self.fortest_label.setGeometry(ft_x, ft_y, ft_w, ft_h)
        self.fortest_label.setFont(QFont("Consolas", 13))
        self.fortest_label.setStyleSheet("color: orange; background: transparent; border: none;")
        self.fortest_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

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
        self.hardware_status_text = text if text else "IO: --    ANTURIT: --"
        self.refresh_display()

    def update_fortest_status(self, text):
        self.fortest_status_text = text if text else "FORTEST 1: --    FORTEST 2: --"
        self.refresh_display()

    def refresh_display(self):
        room_temp = f"{self.room_temperature:.1f}°C" if self.room_temperature is not None else "--.-°C"
        room_hum = f"{self.room_humidity:.1f} %" if self.room_humidity is not None else "--.- %"

        tank_temp = f"{self.tank_temperature:.1f}°C" if self.tank_temperature is not None else "--.-°C"
        tank_hum = f"{self.tank_humidity:.1f} %" if self.tank_humidity is not None else "--.- %"
        tank_pressure = f"{self.tank_pressure:.2f} BAR" if self.tank_pressure is not None else "-.-- BAR"

        part_temp = f"{self.part_temperature:.1f}°C" if self.part_temperature is not None else "--.-°C"

        self.environment_label.setText(
            f"HUONE: {room_temp} / {room_hum}    "
            f"SÄILIÖ: {tank_temp} / {tank_hum} / {tank_pressure}    "
            f"KAPPALE: {part_temp}"
        )

        self.hardware_label.setText(self.hardware_status_text)
        self.fortest_label.setText(self.fortest_status_text)