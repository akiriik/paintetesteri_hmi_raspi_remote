# utils/sen0332_handler.py
import time

import smbus
from PyQt5.QtCore import QObject, QThread, pyqtSignal


class SEN0332Handler(QObject):
    """DFRobot SEN0332 / SHT31 I2C -huoneen lämpötila- ja kosteusanturi."""

    sensor_data_ready = pyqtSignal(dict)
    sensor_error = pyqtSignal(str)

    def __init__(self, bus_number=1, address=0x45):
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

        self.last_temperature = None
        self.last_humidity = None
        self.max_temperature_jump_c = 5.0
        self.max_humidity_jump_percent = 15.0

        self.init_sensor()

    def init_sensor(self):
        try:
            self.bus = smbus.SMBus(self.bus_number)
            self.bus.write_i2c_block_data(self.address, 0x30, [0xA2])
            time.sleep(0.02)

            self.connected = True
            self.error_reported = False
            self.consecutive_error_count = 0
            print("SEN0332 huoneanturi yhdistetty onnistuneesti")

        except Exception as e:
            self.connected = False
            self.next_retry_time = time.monotonic() + self.retry_interval_s
            self._handle_read_error(f"SEN0332 yhteyden muodostus epäonnistui: {e}")

    def _crc8(self, data):
        crc = 0xFF

        for byte in data:
            crc ^= byte

            for _ in range(8):
                if crc & 0x80:
                    crc = ((crc << 1) ^ 0x31) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF

        return crc

    def _handle_read_error(self, message):
        self.consecutive_error_count += 1

        if self.consecutive_error_count < self.error_report_threshold:
            return

        if not self.error_reported:
            print(message)
            self.sensor_error.emit(message)
            self.error_reported = True

    def _accept_values(self, temperature, humidity):
        if temperature < -40.0 or temperature > 125.0:
            self._handle_read_error(f"SEN0332 epäuskottava lämpötila: {temperature:.1f} °C")
            return False

        if humidity < 0.0 or humidity > 100.0:
            self._handle_read_error(f"SEN0332 epäuskottava kosteus: {humidity:.1f} %")
            return False

        if self.last_temperature is not None:
            if abs(temperature - self.last_temperature) > self.max_temperature_jump_c:
                self._handle_read_error(
                    f"SEN0332 lämpötilahyppy hylätty: {temperature:.1f} °C"
                )
                return False

        if self.last_humidity is not None:
            if abs(humidity - self.last_humidity) > self.max_humidity_jump_percent:
                self._handle_read_error(
                    f"SEN0332 kosteushyppy hylätty: {humidity:.1f} %"
                )
                return False

        return True

    def read_temperature_humidity(self):
        if not self.connected:
            now = time.monotonic()

            if now >= self.next_retry_time:
                self.init_sensor()

            if not self.connected:
                return

        try:
            self.bus.write_i2c_block_data(self.address, 0x2C, [0x06])
            time.sleep(0.02)

            data = self.bus.read_i2c_block_data(self.address, 0x00, 6)

            if len(data) != 6:
                self._handle_read_error("SEN0332 datan luku epäonnistui")
                return

            temperature_raw_bytes = data[0:2]
            humidity_raw_bytes = data[3:5]

            if self._crc8(temperature_raw_bytes) != data[2]:
                self._handle_read_error("SEN0332 lämpötilan CRC-virhe")
                return

            if self._crc8(humidity_raw_bytes) != data[5]:
                self._handle_read_error("SEN0332 kosteuden CRC-virhe")
                return

            raw_temperature = (data[0] << 8) | data[1]
            raw_humidity = (data[3] << 8) | data[4]

            temperature = -45.0 + (175.0 * raw_temperature / 65535.0)
            humidity = 100.0 * raw_humidity / 65535.0

            if not self._accept_values(temperature, humidity):
                return

            self.last_temperature = temperature
            self.last_humidity = humidity
            self.consecutive_error_count = 0
            self.error_reported = False

            self.sensor_data_ready.emit({
                "temperature": round(temperature, 1),
                "humidity": round(humidity, 1),
            })

        except Exception as e:
            self.connected = False
            self.next_retry_time = time.monotonic() + self.retry_interval_s
            self._handle_read_error(f"SEN0332 lukuvirhe: {str(e)}")


class SEN0332Worker(QObject):
    data_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.sensor = SEN0332Handler()
        self.sensor.sensor_data_ready.connect(self.data_ready.emit)
        self.sensor.sensor_error.connect(self.error_occurred.emit)
        self.running = False

    def stop_reading(self):
        self.running = False

    def read_sensor_data(self):
        self.sensor.read_temperature_humidity()


class SEN0332Manager(QObject):
    data_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    read_request = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.thread = QThread()
        self.worker = SEN0332Worker()

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
