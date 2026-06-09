# utils/dfr0558_handler.py
from collections import deque
import time

import smbus
from PyQt5.QtCore import QObject, QThread, pyqtSignal


class DFR0558Handler(QObject):
    """DFRobot DFR0558 / MAX31855 K-tyypin termoparianturin käsittelijä."""

    sensor_data_ready = pyqtSignal(dict)
    sensor_error = pyqtSignal(str)

    def __init__(self, bus_number=1, address=0x10):
        super().__init__()
        self.bus_number = bus_number
        self.address = address
        self.bus = None
        self.connected = False

        self.retry_interval_s = 10
        self.next_retry_time = 0
        self.error_reported = False
        self.consecutive_error_count = 0
        self.error_report_threshold = 5

        self.last_valid_temperature = None
        self.pending_temperature = None
        self.pending_count = 0

        self.max_jump_c = 10.0
        self.confirm_jump_count = 3
        self.absolute_min_c = -20.0
        self.absolute_max_c = 250.0

        self.average_samples = deque(maxlen=5)

        self.init_sensor()

    def init_sensor(self):
        try:
            self.bus = smbus.SMBus(self.bus_number)
            data = self.bus.read_i2c_block_data(self.address, 0x00, 4)

            if not isinstance(data, list) or len(data) != 4:
                raise RuntimeError("DFR0558 vastasi väärällä datamäärällä")

            self.connected = True
            self.error_reported = False
            self.consecutive_error_count = 0
            print("DFR0558 kappalelämpötila-anturi yhdistetty onnistuneesti")

        except Exception as e:
            self.connected = False
            self.next_retry_time = time.monotonic() + self.retry_interval_s
            self._handle_read_error(f"DFR0558 yhteyden muodostus epäonnistui: {e}")

    def _handle_read_error(self, message):
        self.consecutive_error_count += 1

        if self.consecutive_error_count < self.error_report_threshold:
            return

        if not self.error_reported:
            print(message)
            self.sensor_error.emit(message)
            self.error_reported = True

    def emit_averaged_temperature(self, temperature):
        self.average_samples.append(temperature)
        averaged = sum(self.average_samples) / len(self.average_samples)

        self.sensor_data_ready.emit({
            "part_temperature": round(averaged, 1)
        })

    def read_temperature(self):
        if not self.connected:
            now = time.monotonic()

            if now >= self.next_retry_time:
                self.init_sensor()

            if not self.connected:
                return

        try:
            data = self.bus.read_i2c_block_data(self.address, 0x00, 4)

            if len(data) != 4:
                self._handle_read_error("DFR0558 datan luku epäonnistui")
                return

            if data[3] & 0x07:
                self._handle_read_error("DFR0558 termoparivirhe")
                return

            raw = ((data[0] << 8) | data[1]) >> 2

            if raw & 0x2000:
                raw -= 0x4000

            temperature = raw * 0.25

            if temperature < self.absolute_min_c or temperature > self.absolute_max_c:
                self._handle_read_error(f"DFR0558 epäuskottava lukema hylätty: {temperature:.1f} °C")
                return

            self.consecutive_error_count = 0
            self.error_reported = False

            if self.last_valid_temperature is None:
                self.last_valid_temperature = temperature
                self.emit_averaged_temperature(temperature)
                return

            diff = abs(temperature - self.last_valid_temperature)

            if diff <= self.max_jump_c:
                self.last_valid_temperature = temperature
                self.pending_temperature = None
                self.pending_count = 0
                self.emit_averaged_temperature(temperature)
                return

            if self.pending_temperature is None:
                self.pending_temperature = temperature
                self.pending_count = 1
            else:
                if abs(temperature - self.pending_temperature) <= self.max_jump_c:
                    self.pending_count += 1
                    self.pending_temperature = temperature
                else:
                    self.pending_temperature = temperature
                    self.pending_count = 1

            if self.pending_count >= self.confirm_jump_count:
                self.last_valid_temperature = temperature
                self.pending_temperature = None
                self.pending_count = 0
                self.average_samples.clear()
                self.emit_averaged_temperature(temperature)

        except Exception as e:
            self.connected = False
            self.next_retry_time = time.monotonic() + self.retry_interval_s
            self._handle_read_error(f"DFR0558 lukuvirhe: {str(e)}")


class DFR0558Worker(QObject):
    data_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.sensor = DFR0558Handler()
        self.sensor.sensor_data_ready.connect(self.data_ready.emit)
        self.sensor.sensor_error.connect(self.error_occurred.emit)
        self.running = False

    def stop_reading(self):
        self.running = False

    def read_sensor_data(self):
        self.sensor.read_temperature()


class DFR0558Manager(QObject):
    data_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    read_request = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.thread = QThread()
        self.worker = DFR0558Worker()

        self.worker.moveToThread(self.thread)

        self.worker.data_ready.connect(self.data_updated.emit)
        self.worker.error_occurred.connect(self.error_occurred.emit)
        self.read_request.connect(self.worker.read_sensor_data)

        self.thread.start()

    def read_once(self):
        self.read_request.emit()

    def cleanup(self):
        self.worker.stop_reading()
        self.thread.quit()
        self.thread.wait()
