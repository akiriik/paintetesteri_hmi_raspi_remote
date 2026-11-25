"""Opta-rajapintojen ja yhteisen jigin regressiotestit."""

import os
from pathlib import Path
from types import SimpleNamespace
import re
import sys
import time
import types
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dualtester"))

# Optan dev-testissä I2C/GPIO:ta ei käytetä, mutta modulien importit
# vaativat Raspberry Pi -kirjastojen nimet.
sys.modules.setdefault("smbus", types.ModuleType("smbus"))
rpi = types.ModuleType("RPi")
rpi.__path__ = []
sys.modules.setdefault("RPi", rpi)
sys.modules.setdefault("RPi.GPIO", types.ModuleType("RPi.GPIO"))

from PyQt5.QtCore import QCoreApplication

from services.hardware_service import HardwareService
from utils import modbus_handler
from config import modbus_config


class FakeModbusResponse:
    registers = [1]

    def isError(self):
        return False


class FakeSerialClient:
    instances = []
    fail_reads = True

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.closed = False
        self.instances.append(self)

    def connect(self):
        return True

    def close(self):
        self.closed = True

    def read_holding_registers(self, **kwargs):
        if self.fail_reads:
            return None
        return FakeModbusResponse()


class HardwareContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def test_opta_python_register_contract(self):
        source = (ROOT / "Aduino_opta_plc" / "opta_config.h").read_text(
            encoding="utf-8"
        )
        constants = (
            "FORTEST1_TEST_VALVE_REGISTER",
            "FORTEST2_TEST_VALVE_REGISTER",
            "JIG_SEQUENCE_COMMAND_REGISTER",
            "JIG_SEQUENCE_START_REGISTER",
            "JIG_SEQUENCE_STOP_REGISTER",
            "JIG_SEQUENCE_STATUS_REGISTER",
            "JIG_SEQUENCE_STEP_REGISTER",
            "JIG_SEQUENCE_ERROR_REGISTER",
            "JIG_SEQUENCE_STATUS_IDLE",
            "JIG_SEQUENCE_STATUS_RUNNING",
            "JIG_SEQUENCE_STATUS_DONE",
            "JIG_SEQUENCE_STATUS_ERROR",
            "JIG_SEQUENCE_COMMAND_PART_CLAMP",
            "JIG_SEQUENCE_COMMAND_PART_RELEASE",
            "JIG_SEQUENCE_COMMAND_PART_REMOVE",
            "JIG_SEQUENCE_ERROR_PART_MISSING",
            "JIG_SEQUENCE_ERROR_EXPANSION_MISSING",
        )
        for name in constants:
            match = re.search(
                rf"\bconst uint16_t {name}\s*=\s*(\d+)\s*;", source
            )
            self.assertIsNotNone(match, name)
            self.assertEqual(int(match.group(1)), getattr(modbus_config, name), name)

    def test_opta_auto_reconnect_after_two_failed_reads(self):
        original = modbus_handler.ModbusSerialClient
        modbus_handler.ModbusSerialClient = FakeSerialClient
        FakeSerialClient.fail_reads = True
        FakeSerialClient.instances = []
        try:
            handler = modbus_handler.ModbusHandler(
                port="mock-opta", auto_reconnect=True
            )
            self.assertTrue(handler.connected)
            self.assertIsNone(handler.read_holding_registers(19100, 1))
            self.assertIsNone(handler.read_holding_registers(19100, 1))
            self.assertFalse(handler.connected)
            FakeSerialClient.fail_reads = False
            handler._next_reconnect_at = 0
            response = handler.read_holding_registers(19100, 1)
            self.assertEqual(response.registers, [1])
            self.assertTrue(handler.connected)
            self.assertGreaterEqual(len(FakeSerialClient.instances), 2)
            handler.close()
        finally:
            modbus_handler.ModbusSerialClient = original

    def test_tester2_abb_jig_can_start_while_tester1_hp_coo_runs(self):
        hw = HardwareService(dev_mode_modbus=True, dev_mode_gpio=True)
        try:
            # Yhteisen Optan jigikirjoituksen jonotus simuloidaan,
            # jotta testi ei tarvitse kytkettyä PLC:tä.
            hw._submit_jig_job = lambda *args: True
            hw.parent_window = SimpleNamespace(station_controllers={
                1: SimpleNamespace(
                    program_number=1,
                    is_running=True,
                    _start_request_pending=False,
                    waiting_result_from_finished_test=False,
                ),
                2: SimpleNamespace(
                    program_number=3,
                    is_running=False,
                    _start_request_pending=False,
                    waiting_result_from_finished_test=False,
                ),
            })
            ok, reason = hw.request_jig_start(
                2, "start_jig_part_clamp_sequence"
            )
            self.assertTrue(ok, reason)
            self.assertEqual(hw._jig_owner_station, 2)

            # Varsinainen jigikomento pysyy yksikäsitteisenä:
            # toisen jigin päällekkäinen komento estetään.
            other_ok, _ = hw.request_jig_start(
                1, "start_jig_part_release_sequence"
            )
            self.assertFalse(other_ok)
        finally:
            hw.cleanup()

    def test_same_station_active_test_still_blocks_its_own_jig(self):
        hw = HardwareService(dev_mode_modbus=True, dev_mode_gpio=True)
        try:
            hw._submit_jig_job = lambda *args: True
            hw.parent_window = SimpleNamespace(station_controllers={
                1: SimpleNamespace(
                    is_running=False,
                    _start_request_pending=False,
                    waiting_result_from_finished_test=False,
                ),
                2: SimpleNamespace(
                    is_running=True,
                    _start_request_pending=False,
                    waiting_result_from_finished_test=False,
                ),
            })
            ok, _ = hw.request_jig_start(
                2, "start_jig_part_release_sequence"
            )
            self.assertFalse(ok)
            self.assertIsNone(hw._jig_owner_station)
        finally:
            hw.cleanup()

    def test_only_one_station_can_own_jig(self):
        hw = HardwareService(
            dev_mode_modbus=True,
            dev_mode_gpio=True,
        )
        started = []
        status_results = []
        hw.jigStartFinished.connect(
            lambda station, success, message: started.append(
                (station, success)
            )
        )
        hw.jigStateReady.connect(
            lambda station, state: status_results.append((station, state))
        )
        try:
            self.assertTrue(
                hw.request_jig_start(1, "start_jig_part_clamp_sequence")[0]
            )
            self.assertFalse(
                hw.request_jig_start(2, "start_jig_part_clamp_sequence")[0]
            )

            deadline = time.monotonic() + 3.0
            while not started and time.monotonic() < deadline:
                self.app.processEvents()
                time.sleep(0.01)

            self.assertEqual(started[0], (1, True))
            self.assertTrue(hw.request_jig_state(1))

            while not status_results and time.monotonic() < deadline:
                self.app.processEvents()
                time.sleep(0.01)

            self.assertTrue(status_results)
            self.assertIsNone(hw._jig_owner_station)
            self.assertTrue(
                hw.request_jig_start(2, "start_jig_part_clamp_sequence")[0]
            )
        finally:
            hw.cleanup()


if __name__ == "__main__":
    unittest.main()
