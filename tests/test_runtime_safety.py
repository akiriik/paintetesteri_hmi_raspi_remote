"""Ohjaimen regressiotestit ilman fyysisiä ForTest- ja Opta-laitteita."""

import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from collections import deque
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dualtester"))

from PyQt5.QtCore import QObject, QCoreApplication, pyqtSignal

from controllers.fortest_result_controller import ForTestResultController
from controllers.station_controller import StationController
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
