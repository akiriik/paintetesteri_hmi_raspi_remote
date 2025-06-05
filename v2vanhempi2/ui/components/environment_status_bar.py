# ui/components/environment_status_bar.py
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont


class EnvironmentStatusBar(QWidget):
    """Ympäristötilojen statusrivi (lämpötila, kosteus ja paine)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(45)

        # Musta tausta ja rajaus kuten log_panelissa
        self.setStyleSheet("""
            background-color: black;
            border-top: 1px solid #333333;
        """)

        self.init_ui()

        # Tietojen päivitysajastin
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.request_sensor_update)
        self.update_timer.start(500)

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(250, 0, 10, 0)  # Pieni marginaali
        layout.setSpacing(0)  # Ei väliä elementtien väliin

        label_font = QFont("Consolas", 18, QFont.Bold)

        # Lämpötila
        self.temp_label = QLabel("Lämpötila: --.-°C", self)
        self.temp_label.setFont(label_font)
        self.temp_label.setStyleSheet("color: #33FF33; background-color: black;")
        layout.addWidget(self.temp_label)

        # Kosteus
        self.humidity_label = QLabel("  Kosteus: --.-%", self)
        self.humidity_label.setFont(label_font)
        self.humidity_label.setStyleSheet("color: #33FF33; background-color: black;")
        layout.addWidget(self.humidity_label)

        # Paine
        self.pressure_label = QLabel("  Paine: ---- BAR", self)
        self.pressure_label.setFont(label_font)
        self.pressure_label.setStyleSheet("color: #33FF33; background-color: black;")
        layout.addWidget(self.pressure_label)

        layout.addStretch()

    def update_sensor_data(self, data):
        temperature = data.get('temperature')
        humidity = data.get('humidity')

        if temperature is not None:
            self.temp_label.setText(f"Lämpötila: {temperature:.1f}°C")
        else:
            self.temp_label.setText("Lämpötila: ERR")

        if humidity is not None:
            self.humidity_label.setText(f"  Kosteus: {humidity:.1f}%")
        else:
            self.humidity_label.setText("  Kosteus: ERR")

    def update_pressure_data(self, pressure_value):
        if pressure_value is not None:
            pressure_bar = self.convert_adc_to_bar(pressure_value)
            self.pressure_label.setText(f"  Paine: {pressure_bar:.2f} BAR")
        else:
            self.pressure_label.setText("  Paine: ERR")

    def convert_adc_to_bar(self, adc_value):
        calibration_table = [
            (3277, 0.0), (4544, 0.5), (5811, 1.0), (7079, 1.5), (8346, 2.0),
            (9613, 2.5), (10881, 3.0), (12148, 3.5), (13415, 4.0), (14682, 4.5),
            (15950, 5.0), (17217, 5.5), (18484, 6.0), (19752, 6.5), (21019, 7.0),
            (22286, 7.5), (23553, 8.0), (24821, 8.5), (26088, 9.0), (27355, 9.5),
            (28623, 10.0)
        ]

        if adc_value <= calibration_table[0][0]:
            return 0.0
        if adc_value >= calibration_table[-1][0]:
            return calibration_table[-1][1]

        for i in range(len(calibration_table) - 1):
            adc1, bar1 = calibration_table[i]
            adc2, bar2 = calibration_table[i + 1]
            if adc1 <= adc_value <= adc2:
                ratio = (adc_value - adc1) / (adc2 - adc1)
                return bar1 + ratio * (bar2 - bar1)
        return 0.0

    def show_sensor_error(self, error_message):
        self.temp_label.setText("Lämpötila: ERR")
        self.humidity_label.setText("  Kosteus: ERR")

    def show_pressure_error(self):
        self.pressure_label.setText("  Paine: ERR")

    def request_sensor_update(self):
        if hasattr(self.parent(), 'update_environment_sensors'):
            self.parent().update_environment_sensors()

    def cleanup(self):
        if hasattr(self, 'update_timer') and self.update_timer:
            self.update_timer.stop()
