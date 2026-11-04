# utils/fortest_handler.py
import time

from config.fortest_config import (
    FORTEST_START_TEST_COIL,
    FORTEST_ABORT_TEST_COIL,
    FORTEST_STATUS_REGISTER,
    FORTEST_STATUS_REGISTER_COUNT,
    FORTEST_RESULTS_REGISTER,
    FORTEST_RESULTS_REGISTER_COUNT,
    FORTEST_PROGRAM_REGISTER,
)

from utils.modbus_handler import ModbusHandler


RECONNECT_INTERVAL_S = 2.0
DISCONNECT_AFTER_FAILURES = 2


class ForTestHandler:
    """
    Yhden ForTest-laitteen Modbus-yhteys.

    Yhteys avataan uudelleen automaattisesti, jos peräkkäiset
    Modbus-operaatiot epäonnistuvat. Tämä estää tilanteen, jossa
    USB/RS232-katkon jälkeen ohjelma jäisi käyttämään pysyvästi
    vanhaa rikkoutunutta serial-clientia.
    """

    def __init__(self, port=None, baudrate=19200):
        if not port:
            raise ValueError("ForTest-portti puuttuu")

        self.port = port
        self.baudrate = baudrate

        self.modbus = None
        self.consecutive_failures = 0
        self.next_reconnect_time = 0.0
        self.last_success_monotonic = None
        self.last_error = ""
        self.last_operation_ok = False

        self._open_connection(initial=True)

    def _open_connection(self, initial=False):
        if self.modbus:
            try:
                self.modbus.close()
            except Exception:
                pass

        self.modbus = ModbusHandler(
            port=self.port,
            baudrate=self.baudrate,
        )

        if self.modbus.connected:
            self.consecutive_failures = 0
            self.next_reconnect_time = 0.0
            self.last_error = ""
            if not initial:
                print(f"ForTest {self.port}: serial-yhteys avattu uudelleen")
            return True

        self.next_reconnect_time = time.monotonic() + RECONNECT_INTERVAL_S
        self.last_error = f"ForTest {self.port}: yhteyttä ei saatu"
        self.last_operation_ok = False

        if not initial:
            print(
                f"ForTest {self.port}: reconnect epäonnistui, "
                f"uusi yritys {RECONNECT_INTERVAL_S:.0f} s kuluttua"
            )

        return False

    def _ensure_connected(self):
        if self.modbus and self.modbus.connected:
            return True

        now = time.monotonic()

        if now < self.next_reconnect_time:
            self.last_operation_ok = False
            self.last_error = (
                f"ForTest {self.port}: ei yhteyttä, reconnect odottaa"
            )
            return False

        print(f"ForTest {self.port}: yritetään reconnectia")
        return self._open_connection(initial=False)

    @staticmethod
    def _result_is_success(result):
        if result is None or result is False:
            return False

        if hasattr(result, "isError"):
            try:
                return not result.isError()
            except Exception:
                return False

        return bool(result)

    def _mark_success(self):
        self.consecutive_failures = 0
        self.last_success_monotonic = time.monotonic()
        self.last_error = ""
        self.last_operation_ok = True

    def _mark_failure(self, operation_name):
        self.consecutive_failures += 1
        self.last_operation_ok = False
        self.last_error = (
            f"ForTest {self.port}: {operation_name} epäonnistui "
            f"({self.consecutive_failures}/{DISCONNECT_AFTER_FAILURES})"
        )

        if self.consecutive_failures < DISCONNECT_AFTER_FAILURES:
            return

        print(
            f"ForTest {self.port}: {DISCONNECT_AFTER_FAILURES} peräkkäistä "
            "kommunikaatiovirhettä, yhteys suljetaan"
        )

        if self.modbus:
            try:
                self.modbus.close()
            except Exception:
                pass

            self.modbus.connected = False

        self.next_reconnect_time = time.monotonic() + RECONNECT_INTERVAL_S

    def _execute(self, operation_name, callback, failure_value=None):
        self.last_operation_ok = False

        if not self._ensure_connected():
            return failure_value

        try:
            result = callback()
        except Exception as e:
            self.last_error = f"ForTest {self.port}: {operation_name}: {e}"
            self._mark_failure(operation_name)
            return failure_value

        if self._result_is_success(result):
            self._mark_success()
            return result

        self._mark_failure(operation_name)
        return result if result is not None else failure_value

    def is_connected(self):
        return bool(
            self.modbus
            and self.modbus.connected
            and self.consecutive_failures < DISCONNECT_AFTER_FAILURES
        )

    def get_last_error(self):
        return self.last_error

    def write_program(self, program_number):
        """Vaihda ForTestin aktiivinen ohjelma."""
        return self._execute(
            "ohjelman vaihto",
            lambda: self.modbus.write_register(
                FORTEST_PROGRAM_REGISTER,
                program_number,
            ),
            failure_value=False,
        )

    def start_test(self):
        """Käynnistä ForTest-testi."""
        return self._execute(
            "testin käynnistys",
            lambda: self.modbus.write_coil(
                FORTEST_START_TEST_COIL,
                True,
            ),
            failure_value=False,
        )

    def abort_test(self):
        """Keskeytä / pysäytä ForTest-testi."""
        return self._execute(
            "testin keskeytys",
            lambda: self.modbus.write_coil(
                FORTEST_ABORT_TEST_COIL,
                True,
            ),
            failure_value=False,
        )

    def read_status(self):
        """Lue ForTest-laitteen statusalue."""
        return self._execute(
            "statuksen luku",
            lambda: self.modbus.read_holding_registers(
                FORTEST_STATUS_REGISTER,
                FORTEST_STATUS_REGISTER_COUNT,
            ),
            failure_value=None,
        )

    def read_results(self):
        """Lue ForTest-testitulosten alue."""
        return self._execute(
            "tulosten luku",
            lambda: self.modbus.read_holding_registers(
                FORTEST_RESULTS_REGISTER,
                FORTEST_RESULTS_REGISTER_COUNT,
            ),
            failure_value=None,
        )

    def close(self):
        if self.modbus:
            try:
                self.modbus.close()
            except Exception:
                pass

            self.modbus.connected = False

        self.last_operation_ok = False


class DummyForTestHandler:
    last_operation_ok = False

    def write_program(self, program_number):
        print(f"DummyForTest: Ohjelma vaihdettu {program_number} (ei oikeaa laitetta)")
        return True

    def start_test(self):
        print("DummyForTest: Testi käynnistetty (ei oikeaa laitetta)")
        return True

    def abort_test(self):
        print("DummyForTest: Testi pysäytetty (ei oikeaa laitetta)")
        return True

    def read_status(self):
        return None

    def read_results(self):
        return None

    def is_connected(self):
        return False

    def get_last_error(self):
        return "ForTest-yhteys ei ole käytössä"

    def close(self):
        pass
