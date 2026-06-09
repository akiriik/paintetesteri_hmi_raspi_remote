# ui/components/environment_status_bar.py
import time

from PyQt5.QtWidgets import QLabel, QWidget, QHBoxLayout
from PyQt5.QtGui import QFont


SENSOR_STALE_TIMEOUT_S = 30


class EnvironmentStatusBar(QWidget):
    """
    Ympäristö- ja sensoridatan välikerros.

    Lyhyt yksittäinen anturivirhe ei tyhjennä viimeisintä hyvää arvoa.
    Jos uutta onnistunutta lukemaa ei tule määräajassa, arvo tulkitaan vanhaksi
    eikä sitä käytetä tuloksiin tai SQL-tallennukseen.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.container_label = QLabel("SÄILIÖ: --.-°C / --.- % / -.-- BAR", self)
        self.container_label.setFont(QFont("Consolas", 14))
        self.container_label.setStyleSheet("""
            color: #33FF33;
            background-color: black;
            border-radius: 5px;
            border: 1px solid #333333;
            padding: 5px 10px;
        """)

        self.status_label = QLabel("HUONE: --.-°C / --.- %", self)
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

        self.tank_temperature = None
        self.tank_humidity = None
        self.tank_pressure = None

        self.room_temperature = None
        self.room_humidity = None
        self.part_temperature = None

        self.tank_sensor_updated_at = None
        self.room_sensor_updated_at = None
        self.part_temperature_updated_at = None

    def _now(self):
        return time.monotonic()

    def _is_fresh(self, updated_at):
        if updated_at is None:
            return False

        return (self._now() - updated_at) <= SENSOR_STALE_TIMEOUT_S

    def _fresh_or_none(self, value, updated_at):
        if value is None:
            return None

        if not self._is_fresh(updated_at):
            return None

        return value

    def get_room_temperature_for_result(self):
        return self._fresh_or_none(self.room_temperature, self.room_sensor_updated_at)

    def get_room_humidity_for_result(self):
        return self._fresh_or_none(self.room_humidity, self.room_sensor_updated_at)

    def get_part_temperature_for_result(self):
        return self._fresh_or_none(self.part_temperature, self.part_temperature_updated_at)

    def update_sensor_data(self, data):
        if not isinstance(data, dict):
            return

        self.tank_temperature = data.get("temperature")
        self.tank_humidity = data.get("humidity")
        self.tank_sensor_updated_at = self._now()
        self.update_display()

    def update_room_sensor_data(self, data):
        if not isinstance(data, dict):
            return

        self.room_temperature = data.get("temperature")
        self.room_humidity = data.get("humidity")
        self.room_sensor_updated_at = self._now()
        self.update_display()

    def update_part_temperature_data(self, data):
        if not isinstance(data, dict):
            return

        self.part_temperature = data.get("part_temperature")
        self.part_temperature_updated_at = self._now()
        self.update_display()

    def show_part_temperature_error(self, error_message):
        self.update_display()

    def update_pressure_data(self, pressure_value):
        if pressure_value is not None:
            self.tank_pressure = self.convert_adc_to_bar(pressure_value)
        else:
            self.tank_pressure = None

        self.update_display()

    def _format_temperature(self, value, updated_at):
        if value is None:
            return "--.-°C"

        if not self._is_fresh(updated_at):
            return "--.-°C"

        return f"{value:.1f}°C"

    def _format_humidity(self, value, updated_at):
        if value is None:
            return "--.- %"

        if not self._is_fresh(updated_at):
            return "--.- %"

        return f"{value:.1f} %"

    def update_display(self):
        tank_temp_str = self._format_temperature(self.tank_temperature, self.tank_sensor_updated_at)
        tank_humidity_str = self._format_humidity(self.tank_humidity, self.tank_sensor_updated_at)
        tank_pressure_str = f"{self.tank_pressure:.2f} BAR" if self.tank_pressure is not None else "-.-- BAR"

        room_temp_str = self._format_temperature(self.room_temperature, self.room_sensor_updated_at)
        room_humidity_str = self._format_humidity(self.room_humidity, self.room_sensor_updated_at)

        self.container_label.setText(
            f"SÄILIÖ: {tank_temp_str} / {tank_humidity_str} / {tank_pressure_str}"
        )
        self.status_label.setText(
            f"HUONE: {room_temp_str} / {room_humidity_str}"
        )

        self.update_main_environment_bar()

    def update_main_environment_bar(self):
        parent = self.parent()

        if not parent:
            return

        if not hasattr(parent, "main_screen"):
            return

        main_screen = parent.main_screen

        if not hasattr(main_screen, "environment_bar"):
            return

        main_screen.environment_bar.update_environment_values(
            room_temperature=self.get_room_temperature_for_result(),
            room_humidity=self.get_room_humidity_for_result(),
            tank_temperature=self._fresh_or_none(self.tank_temperature, self.tank_sensor_updated_at),
            tank_humidity=self._fresh_or_none(self.tank_humidity, self.tank_sensor_updated_at),
            tank_pressure=self.tank_pressure,
            part_temperature=self.get_part_temperature_for_result(),
        )

    def convert_adc_to_bar(self, adc_value):
        calibration_table = [
            (3277, 0.0),
            (5482, 1.0),
            (7966, 2.0),
            (10500, 3.0),
            (12655, 4.0),
            (15443, 5.0),
            (20385, 7.0),
            (23553, 8.0),
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
        self.update_display()

    def show_room_sensor_error(self, error_message):
        self.update_display()

    def show_pressure_error(self):
        self.tank_pressure = None
        self.update_display()

    def request_sensor_update(self):
        pass

    def cleanup(self):
        if hasattr(self, "update_timer") and self.update_timer:
            self.update_timer.stop()
