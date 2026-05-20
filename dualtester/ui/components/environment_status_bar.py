# ui/components/environment_status_bar.py
from PyQt5.QtWidgets import QLabel, QWidget, QHBoxLayout
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QFont


class EnvironmentStatusBar(QWidget):
    """
    Ympäristö- ja sensoridatan välikerros.

    Tämä komponentti saa sensorisignaaleja vanhoilta toimivilta handlereilta,
    säilyttää viimeisimmät arvot ja välittää ne uudelle EnvironmentBarille.

    Tämä widget pidetään edelleen piilossa MainWindowissa.
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

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.request_sensor_update)
        self.update_timer.start(100)

    def update_sensor_data(self, data):
        """
        Vanhan SHT20/SHT-tyyppisen datan vastaanotto.

        Jos data ei erikseen kerro onko kyse huoneesta vai säiliöstä,
        käsitellään se säiliödatana vanhan ohjelmalogiikan mukaisesti.
        """
        if not isinstance(data, dict):
            return

        self.tank_temperature = data.get("temperature")
        self.tank_humidity = data.get("humidity")
        self.update_display()

    def update_room_sensor_data(self, data):
        """
        Varattu erilliselle huoneanturille.
        """
        if not isinstance(data, dict):
            return

        self.room_temperature = data.get("temperature")
        self.room_humidity = data.get("humidity")
        self.update_display()

    def update_part_temperature_data(self, data):
        if not isinstance(data, dict):
            return

        self.part_temperature = data.get("part_temperature")
        self.update_display()

    def show_part_temperature_error(self, error_message):
        self.part_temperature = None
        self.update_display()

    def update_pressure_data(self, pressure_value):
        if pressure_value is not None:
            self.tank_pressure = self.convert_adc_to_bar(pressure_value)
        else:
            self.tank_pressure = None

        self.update_display()

    def update_display(self):
        tank_temp_str = f"{self.tank_temperature:.1f}°C" if self.tank_temperature is not None else "--.-°C"
        tank_humidity_str = f"{self.tank_humidity:.1f} %" if self.tank_humidity is not None else "--.- %"
        tank_pressure_str = f"{self.tank_pressure:.2f} BAR" if self.tank_pressure is not None else "-.-- BAR"

        room_temp_str = f"{self.room_temperature:.1f}°C" if self.room_temperature is not None else "--.-°C"
        room_humidity_str = f"{self.room_humidity:.1f} %" if self.room_humidity is not None else "--.- %"

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
            room_temperature=self.room_temperature,
            room_humidity=self.room_humidity,
            tank_temperature=self.tank_temperature,
            tank_humidity=self.tank_humidity,
            tank_pressure=self.tank_pressure,
            part_temperature=self.part_temperature,
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
        self.tank_temperature = None
        self.tank_humidity = None
        self.update_display()

    def show_room_sensor_error(self, error_message):
        self.room_temperature = None
        self.room_humidity = None
        self.update_display()

    def show_pressure_error(self):
        self.tank_pressure = None
        self.update_display()

    def request_sensor_update(self):
        if hasattr(self.parent(), "update_environment_sensors"):
            self.parent().update_environment_sensors()

    def cleanup(self):
        if hasattr(self, "update_timer") and self.update_timer:
            self.update_timer.stop()