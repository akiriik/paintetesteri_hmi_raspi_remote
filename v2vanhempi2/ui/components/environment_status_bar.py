# ui/components/environment_status_bar.py
from PyQt5.QtWidgets import QLabel, QWidget, QHBoxLayout
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont


class EnvironmentStatusBar(QWidget):
    """Ympäristötilojen statusrivit"""

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Säiliö-label
        self.container_label = QLabel("SÄILIÖ: --.-°C / --.- % / -.-- BAR", self)
        self.container_label.setFont(QFont("Consolas", 14))
        self.container_label.setStyleSheet("""
            color: #33FF33;
            background-color: black;
            border-radius: 5px;
            border: 1px solid #333333;
            padding: 5px 10px;
        """)
        
        # Tila-label
        self.status_label = QLabel("TILA: 99.0°C / 99.0 %", self)
        self.status_label.setFont(QFont("Consolas", 14))
        self.status_label.setStyleSheet("""
            color: #33FF33;
            background-color: black;
            border-radius: 5px;
            border: 1px solid #333333;
            padding: 5px 10px;
        """)
        
        layout.addWidget(self.container_label)
        layout.addStretch()
        layout.addWidget(self.status_label)
        
        
        # Tallennetut arvot
        self.temperature = None
        self.humidity = None
        self.pressure = None
        
        # Tietojen päivitysajastin
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.request_sensor_update)
        self.update_timer.start(500)

    def update_sensor_data(self, data):
        self.temperature = data.get('temperature')
        self.humidity = data.get('humidity')
        self.update_display()

    def update_pressure_data(self, pressure_value):
        if pressure_value is not None:
            self.pressure = self.convert_adc_to_bar(pressure_value)
        else:
            self.pressure = None
        self.update_display()

    def update_display(self):
        """Päivitä säiliön näyttöteksti"""
        temp_str = f"{self.temperature:.1f}°C" if self.temperature is not None else "--.-°C"
        humidity_str = f"{self.humidity:.1f} %" if self.humidity is not None else "--.- %"
        pressure_str = f"{self.pressure:.2f} BAR" if self.pressure is not None else "-.-- BAR"
        
        self.container_label.setText(f"SÄILIÖ: {temp_str} / {humidity_str} / {pressure_str}")

    def convert_adc_to_bar(self, adc_value):
        calibration_table = [
            (3277, 0.0),   # 0 bar
            (5482, 1.0),   # 1 bar
            (7966, 2.0),   # 2 bar
            (10500, 3.0),  # 3 bar
            (12655, 4.0),  # 4 bar
            (15443, 5.0),  # 5 bar
            (20385, 7.0),  # 7 bar
            (23553, 8.0)   # 8 bar
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
        self.temperature = None
        self.humidity = None
        self.update_display()

    def show_pressure_error(self):
        self.pressure = None
        self.update_display()

    def request_sensor_update(self):
        if hasattr(self.parent(), 'update_environment_sensors'):
            self.parent().update_environment_sensors()

    def cleanup(self):
        if hasattr(self, 'update_timer') and self.update_timer:
            self.update_timer.stop()