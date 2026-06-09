# utils/fortest_handler.py
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


class ForTestHandler:
    def __init__(self, port=None, baudrate=19200):
        if not port:
            raise ValueError("ForTest-portti puuttuu")

        self.modbus = ModbusHandler(port=port, baudrate=baudrate)

    def write_program(self, program_number):
        """Vaihda ForTestin aktiivinen ohjelma."""
        return self.modbus.write_register(FORTEST_PROGRAM_REGISTER, program_number)

    def start_test(self):
        """Käynnistä ForTest-testi."""
        return self.modbus.write_coil(FORTEST_START_TEST_COIL, True)

    def abort_test(self):
        """Keskeytä / pysäytä ForTest-testi."""
        return self.modbus.write_coil(FORTEST_ABORT_TEST_COIL, True)

    def read_status(self):
        """Lue ForTest-laitteen statusalue."""
        return self.modbus.read_holding_registers(
            FORTEST_STATUS_REGISTER,
            FORTEST_STATUS_REGISTER_COUNT,
        )

    def read_results(self):
        """Lue ForTest-testitulosten alue."""
        return self.modbus.read_holding_registers(
            FORTEST_RESULTS_REGISTER,
            FORTEST_RESULTS_REGISTER_COUNT,
        )


class DummyForTestHandler:
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
