"""Ohjaimen regressiotestit ilman fyysisiä ForTest- ja Opta-laitteita."""

import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from collections import deque
from types import MethodType, SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dualtester"))

from PyQt5.QtCore import QObject, QCoreApplication, pyqtSignal

from controllers.fortest_result_controller import ForTestResultController
from controllers.modbus_result_controller import ModbusResultController
from controllers.station_controller import (
    StationController,
    AUTO_PHASE_WAIT_BEFORE_RELEASE,
    AUTO_PHASE_WAIT_BEFORE_REMOVE,
    AUTO_POST_TEST_PRESSURE_RELEASE_DELAY_MS,
)
from controllers.test_valve_controller import (
    PRESSURE_RELEASE_HOLD_MS,
    JAKOTUKKI_PRESSURE_RELEASE_HOLD_MS,
)
from controllers.station_result_handler import StationResultHandler
from controllers.test_valve_controller import TestValveController
from services.result_storage_service import ResultStorageService
from utils.program_manager import ProgramManager
from utils.fortest_manager import ForTestManager


class FakeForTestManager:
    _queue_control = ForTestManager._queue_control
    _dispatch_pending_control = ForTestManager._dispatch_pending_control

    def __init__(self):
        self._busy = True
        self._pending_controls = deque()
        self.calls = []
        self.port = "dummy"

    def _invoke_worker(self, method, argument=None):
        self.calls.append((method, argument))
        self._busy = True
        return True


class FakeOpta(QObject):
    writeAcknowledged = pyqtSignal(int, int, bool, str)

    def __init__(self):
        super().__init__()
        self.writes = []
        self.can_queue = True

    def write_register(self, register, value):
        self.writes.append((register, value))
        return self.can_queue


class SafetyRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def test_fortest_control_queue_preserves_program_then_start(self):
        manager = FakeForTestManager()
        self.assertTrue(manager._queue_control("write_program", 32))
        self.assertTrue(manager._queue_control("start_test"))
        self.assertEqual(
            list(manager._pending_controls),
            [("write_program", 32), ("start_test", None)],
        )
        manager._busy = False
        manager._dispatch_pending_control()
        self.assertEqual(manager.calls[0], ("write_program", 32))

    def test_stop_overrides_pending_fortest_commands(self):
        manager = FakeForTestManager()
        manager._queue_control("write_program", 32)
        manager._queue_control("start_test")
        manager._queue_control("abort_test")
        self.assertEqual(
            list(manager._pending_controls),
            [("abort_test", None)],
        )
        self.assertFalse(manager._queue_control("start_test"))

    def test_stop_dispatch_precedes_status_callback(self):
        events = []
        manager = FakeForTestManager()
        manager._pending_controls.append(("abort_test", None))

        class Recorder:
            def emit(self, *args):
                events.append("status")

        manager.resultReady = Recorder()
        def dispatch(method, arg=None):
            events.append(method)
            manager._busy = True
            return True
        manager._invoke_worker = dispatch
        ForTestManager.handle_result(manager, None, 3, "")
        self.assertEqual(events[:2], ["abort_test", "status"])

    def test_valve_is_only_confirmed_after_modbus_ack(self):
        hw = FakeOpta()
        valve = TestValveController(hw)
        success, _ = valve.close_valve(1)
        self.assertTrue(success)
        self.assertFalse(valve.is_closed_confirmed(1))
        self.assertEqual(hw.writes[-1], (18092, 0))
        hw.writeAcknowledged.emit(18092, 0, True, "")
        self.assertTrue(valve.is_closed_confirmed(1))

    def test_purge_timer_begins_only_after_open_ack(self):
        hw = FakeOpta()
        valve = TestValveController(hw)
        valve.release_pressure_after_stop(1)
        self.assertFalse(valve.pressure_release_timers[1].isActive())
        self.assertEqual(hw.writes[-1], (18092, 1))
        hw.writeAcknowledged.emit(18092, 1, True, "")
        self.assertTrue(valve.pressure_release_timers[1].isActive())
        self.assertFalse(valve.is_pressure_release_complete(1))
        valve.pressure_release_timers[1].stop()

    def test_abb_jakotukki_5s_is_restricted_to_its_two_programs(self):
        self.assertEqual(AUTO_POST_TEST_PRESSURE_RELEASE_DELAY_MS, 5000)
        self.assertEqual(JAKOTUKKI_PRESSURE_RELEASE_HOLD_MS, 5000)
        self.assertEqual(PRESSURE_RELEASE_HOLD_MS, 10000)

        for station_id, jakotukki_id in ((1, 32), (2, 3)):
            hw = FakeOpta()
            valve = TestValveController(hw)
            stub = SimpleNamespace(
                station_id=station_id,
                program_number=jakotukki_id,
                program_written_to_fortest=True,
                test_valve_controller=valve,
            )
            stub.get_jakotukki_program_number = MethodType(
                StationController.get_jakotukki_program_number, stub
            )
            stub.is_jakotukki_station_and_program = MethodType(
                StationController.is_jakotukki_station_and_program, stub
            )

            StationController._configure_automatic_purge_hold(stub)
            self.assertEqual(
                valve.automatic_release_hold_ms_by_station[station_id], 5000
            )

            stub.program_number = 99
            StationController._configure_automatic_purge_hold(stub)
            self.assertEqual(
                valve.automatic_release_hold_ms_by_station[station_id], 10000
            )
            stub.program_number = jakotukki_id
            stub.program_written_to_fortest = False
            StationController._configure_automatic_purge_hold(stub)
            self.assertEqual(
                valve.automatic_release_hold_ms_by_station[station_id], 10000
            )

    def test_abb_jakotukki_auto_purge_timers_run_5_seconds(self):
        for station_id, register in ((1, 18092), (2, 18093)):
            hw = FakeOpta()
            valve = TestValveController(hw)
            valve.configure_automatic_release_hold(
                station_id, JAKOTUKKI_PRESSURE_RELEASE_HOLD_MS
            )
            valve.update_from_fortest_status(station_id, 1)
            hw.writeAcknowledged.emit(register, 0, True, "")
            valve.update_from_fortest_status(station_id, 3)
            hw.writeAcknowledged.emit(register, 1, True, "")
            valve.update_from_fortest_status(station_id, 0)
            timer = valve.pressure_release_timers[station_id]
            self.assertTrue(timer.isActive())
            self.assertEqual(
                valve.active_release_hold_ms_by_station[station_id], 5000
            )
            self.assertLessEqual(timer.remainingTime(), 5500)
            self.assertGreater(timer.remainingTime(), 0)
            timer.stop()

    def test_stop_purge_remains_10_seconds_on_jakotukki(self):
        for station_id, register in ((1, 18092), (2, 18093)):
            hw = FakeOpta()
            valve = TestValveController(hw)
            valve.configure_automatic_release_hold(
                station_id, JAKOTUKKI_PRESSURE_RELEASE_HOLD_MS
            )
            valve.release_pressure_after_stop(station_id)
            hw.writeAcknowledged.emit(register, 1, True, "")
            timer = valve.pressure_release_timers[station_id]
            self.assertTrue(timer.isActive())
            self.assertEqual(
                valve.active_release_hold_ms_by_station[station_id], 10000
            )
            self.assertGreater(timer.remainingTime(), 8500)
            timer.stop()

    def test_valve_failure_does_not_cache_closed(self):
        hw = FakeOpta()
        valve = TestValveController(hw)
        valve.close_valve(2)
        hw.writeAcknowledged.emit(18093, 0, False, "Modbus-virhe")
        self.assertFalse(valve.is_closed_confirmed(2))
        valve.close_valve(2)
        self.assertEqual(hw.writes[-1], (18093, 0))
        self.assertEqual(len(hw.writes), 2)

    def test_stop_cancels_200ms_start(self):
        events = []
        stub = SimpleNamespace(
            is_running=False,
            _start_request_pending=True,
            _start_generation=5,
            auto_part_change_in_progress=False,
            auto_part_change_enabled=False,
            _manual_jig_in_progress=False,
            hardware_service=None,
            results_started=False,
            test_has_reached_active_status=False,
            waiting_result_from_finished_test=False,
            dev_mode_fortest=True,
            release_test_pressure_after_stop=lambda: events.append("purku"),
            update_status=lambda *args: events.append("viesti"),
            refresh_station_state=lambda: events.append("ui"),
        )
        StationController.stop_test(stub)
        self.assertFalse(stub._start_request_pending)
        self.assertEqual(stub._start_generation, 6)
        StationController._continue_start_test(stub, 5)
        self.assertIn("purku", events)

    def test_old_auto_restart_timer_cannot_start_after_stop(self):
        calls = []
        stub = SimpleNamespace(
            _auto_restart_generation=6,
            auto_part_change_enabled=False,
            auto_part_change_in_progress=False,
            auto_cycle_phase="IDLE",
            has_selected_program=lambda: True,
            is_jakotukki_station_and_program=lambda: True,
            start_test=lambda: calls.append("START"),
        )
        StationController._automatic_restart_if_allowed(stub, 5)
        self.assertEqual(calls, [])
        StationController._automatic_restart_if_allowed(stub, 6)
        self.assertEqual(calls, [])
        stub.auto_part_change_enabled = True
        StationController._automatic_restart_if_allowed(stub, 6)
        self.assertEqual(calls, ["START"])

    def test_old_jig_delay_cannot_run_after_stop(self):
        stub = SimpleNamespace(_auto_cycle_generation=12)
        StationController._start_auto_remove_after_delay(stub, 11)
        StationController._start_auto_release_after_delay(stub, 11)

    def test_opta_valve_error_is_handled_by_valve_controller_only(self):
        displayed = []
        station = SimpleNamespace(
            update_status=lambda *args: displayed.append(args)
        )
        controller = ModbusResultController({1: station})
        failed_write = SimpleNamespace(address=18092)
        controller.handle_result(
            failed_write, 2, "Opta rekisteri 18092: kirjoitusta ei kuitattu"
        )
        self.assertEqual(displayed, [])

    def test_generic_opta_error_is_not_repainted_repeatedly(self):
        displayed = []
        station = SimpleNamespace(
            update_status=lambda *args: displayed.append(args)
        )
        controller = ModbusResultController({1: station})
        for _ in range(3):
            controller.handle_result(False, 2, "Opta yhteysvirhe")
        self.assertEqual(displayed, [("Opta yhteysvirhe", "ERROR")])

    def test_idle_valve_error_does_not_replace_last_test_result(self):
        displayed = []
        station = SimpleNamespace(
            station_id=1,
            _start_request_pending=False,
            is_running=False,
            auto_part_change_in_progress=False,
            _manual_jig_in_progress=False,
            test_valve_controller=SimpleNamespace(
                pressure_release_active_by_station={1: False}
            ),
            update_status=lambda *args: displayed.append(args),
        )
        StationController._handle_valve_command_failed(
            station, 1, "Opta ei yhteydessä"
        )
        self.assertEqual(displayed, [])

        station.is_running = True
        StationController._handle_valve_command_failed(
            station, 1, "Opta ei yhteydessä"
        )
        self.assertEqual(displayed, [("Opta ei yhteydessä", "ERROR")])

    def _auto_release_test_station(self, phase):
        class Valve:
            ready = False
            def is_pressure_release_complete(self, station_id):
                return self.ready

        events = []
        valve = Valve()
        hw = SimpleNamespace(
            start_jig_part_release_sequence=lambda: True,
            request_jig_start=lambda station_id, method: (
                events.append(("JIG", station_id, method)) or (True, "JIG-OK")
            ),
        )
        stub = SimpleNamespace(
            _auto_cycle_generation=7,
            _auto_pressure_release_deadline=time.monotonic() + 20,
            auto_part_change_enabled=True,
            auto_part_change_in_progress=True,
            auto_cycle_phase=phase,
            station_id=2,
            is_jakotukki_station_and_program=lambda: True,
            test_valve_controller=valve,
            hardware_service=hw,
            update_status=lambda *args: events.append(("STATUS", *args)),
            refresh_station_state=lambda: None,
            disable_auto_part_change=lambda *args: events.append(("DISABLE", *args)),
        )
        stub._auto_pressure_release_ready_or_wait = MethodType(
            StationController._auto_pressure_release_ready_or_wait, stub
        )
        stub._start_auto_release_after_delay = MethodType(
            StationController._start_auto_release_after_delay, stub
        )
        stub._start_auto_remove_after_delay = MethodType(
            StationController._start_auto_remove_after_delay, stub
        )
        return stub, valve, events

    def test_nok_jig_waits_for_purge_close_ack_instead_of_disabling(self):
        station, valve, events = self._auto_release_test_station(
            AUTO_PHASE_WAIT_BEFORE_RELEASE
        )
        scheduled = []
        with patch(
            "controllers.station_controller.QTimer.singleShot",
            side_effect=lambda ms, fn: scheduled.append((ms, fn))
        ):
            station._start_auto_release_after_delay(7)
            self.assertEqual(len(scheduled), 1)
            self.assertEqual(scheduled[0][0], 250)
            self.assertFalse(any(x[0] in ("JIG", "DISABLE") for x in events))

            valve.ready = True  # ajastettu purku JA sulkukuittaus valmistuneet
            scheduled[0][1]()
            self.assertIn(
                ("JIG", 2, "start_jig_part_release_sequence"),
                events
            )
            self.assertFalse(any(x[0] == "DISABLE" for x in events))

    def test_ok_jig_waits_for_purge_close_ack_instead_of_disabling(self):
        station, valve, events = self._auto_release_test_station(
            AUTO_PHASE_WAIT_BEFORE_REMOVE
        )
        scheduled = []
        with patch(
            "controllers.station_controller.QTimer.singleShot",
            side_effect=lambda ms, fn: scheduled.append((ms, fn))
        ):
            station._start_auto_remove_after_delay(7)
            self.assertEqual(len(scheduled), 1)
            self.assertFalse(any(x[0] in ("JIG", "DISABLE") for x in events))

            valve.ready = True
            scheduled[0][1]()
            self.assertIn(
                ("JIG", 2, "start_jig_part_remove_sequence"),
                events
            )

    def test_nok_purge_confirmation_timeout_disables_jig(self):
        station, _, events = self._auto_release_test_station(
            AUTO_PHASE_WAIT_BEFORE_RELEASE
        )
        station._auto_pressure_release_deadline = time.monotonic() - 1
        station._start_auto_release_after_delay(7)
        self.assertTrue(any(x[0] == "DISABLE" for x in events))
        self.assertFalse(any(x[0] == "JIG" for x in events))

    def test_stale_nok_retry_after_stop_cannot_start_jig(self):
        station, valve, events = self._auto_release_test_station(
            AUTO_PHASE_WAIT_BEFORE_RELEASE
        )
        station._auto_cycle_generation = 8
        valve.ready = True
        station._start_auto_release_after_delay(7)
        self.assertFalse(any(x[0] == "JIG" for x in events))

    def test_fortest_program_ack_error_is_not_discarded(self):
        calls = []
        station = SimpleNamespace(
            handle_program_write_ack=lambda ok, err: calls.append((ok, err)),
            refresh_station_state=lambda: None,
        )
        receiver = ForTestResultController({1: station})
        receiver.handle_result(1, False, 5, "Ohjelmanvaihto epäonnistui")
        self.assertEqual(calls, [(False, "Ohjelmanvaihto epäonnistui")])

    def test_missing_program_json_does_not_create_fake_programs(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "missing_programs.json"
            manager = ProgramManager(str(path))
            self.assertEqual(manager.get_program_list(), [])
            self.assertFalse(path.exists())

    def test_invalid_program_json_is_rejected_without_defaults(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "programs.json"
            path.write_text('{"programs":[{"id":1,"name":"A"},{"id":1,"name":"B"}]}')
            manager = ProgramManager(str(path))
            self.assertEqual(manager.get_program_list(), [])
            self.assertEqual(manager.get_program_by_index(0), None)

    def test_invalid_fortest_timestamp_is_not_guessed(self):
        result = StationResultHandler._get_result_datetime_parts(
            object(), 2026, 13, 5, 11, 20, 0
        )
        self.assertEqual(result, (None, None, None))

    def _sample_db_row(self):
        return {
            "timestamp": "2026-11-24T10:00:00",
            "date": "2026-11-24",
            "time": "10:00:00",
            "station_id": 1,
            "tester_name": "ForTest 1",
            "program_number": 32,
            "result_code": 2,
            "raw_result": {"registers": [1, 2, 3]},
        }

    def test_sqlite_duplicate_retry_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            service = ResultStorageService(
                database_path=str(Path(td) / "test_results.db")
            )
            row = self._sample_db_row()
            self.assertTrue(service.save_test_result(row))
            self.assertTrue(service.save_test_result(row))
            with sqlite3.connect(service.database_path) as db:
                total = db.execute(
                    "SELECT COUNT(*) FROM test_results"
                ).fetchone()[0]
            self.assertEqual(total, 1)
            service.cleanup()

    def test_sqlite_failure_uses_durable_queue_and_recovers(self):
        with tempfile.TemporaryDirectory() as td:
            service = ResultStorageService(
                database_path=str(Path(td) / "test_results.db")
            )
            original_connect = service._connect
            def fail():
                raise sqlite3.OperationalError("database locked")
            service._connect = fail
            self.assertFalse(service.save_test_result(self._sample_db_row()))
            self.assertTrue(Path(service.pending_path).exists())
            with open(service.pending_path, encoding="utf-8") as pending:
                self.assertEqual(len(json.load(pending)), 1)

            service._connect = original_connect
            service._retry_pending_results()
            with sqlite3.connect(service.database_path) as db:
                total = db.execute(
                    "SELECT COUNT(*) FROM test_results"
                ).fetchone()[0]
            self.assertEqual(total, 1)
            self.assertEqual(service._pending_results, [])
            service.cleanup()


if __name__ == "__main__":
    unittest.main()
