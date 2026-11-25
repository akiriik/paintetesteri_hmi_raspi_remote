"""Jigin käsikäytön, palautumisen ja lokin regressiotestit."""

import base64
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import types
import unittest
import urllib.error
from types import MethodType, SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "dualtester"))

sys.modules.setdefault("smbus", types.ModuleType("smbus"))
rpi = types.ModuleType("RPi")
rpi.__path__ = []
sys.modules.setdefault("RPi", rpi)
sys.modules.setdefault("RPi.GPIO", types.ModuleType("RPi.GPIO"))

from PyQt5.QtCore import QCoreApplication

from config.modbus_config import (
    JIG_SEQUENCE_STATUS_DONE,
    JIG_SEQUENCE_STATUS_ERROR,
)
from controllers.station_controller import StationController
from controllers.physical_button_controller import PhysicalButtonController
from services.hardware_service import HardwareService
from utils.runtime_diagnostics import RuntimeDiagnostics


class FakeStationWidget:
    def __init__(self):
        self.jig_enabled = None
        self.jig_visible = None

    def set_jig_controls_enabled(self, enabled):
        self.jig_enabled = enabled

    def set_jig_controls_visible(self, visible):
        self.jig_visible = visible

    def set_auto_part_change_visible(self, visible):
        pass

    def set_auto_part_change_enabled_state(self, enabled):
        pass


def make_station(phase="IDLE"):
    widget = FakeStationWidget()
    hardware = SimpleNamespace(
        is_jig_busy=lambda: False,
        is_jig_owned_by=lambda sid: False,
        _jig_owner_station=None,
        request_jig_stop=lambda sid: (True, "STOP"),
        request_jig_state=lambda sid: True,
    )
    station = SimpleNamespace(
        station_id=2,
        program_number=3,
        program_written_to_fortest=True,
        main_window=SimpleNamespace(station_controllers={}),
        hardware_service=hardware,
        station_widget=widget,
        status_handler=SimpleNamespace(last_status=0),
        test_valve_controller=SimpleNamespace(
            pressure_release_active_by_station={2: False}
        ),
        auto_cycle_phase=phase,
        auto_part_change_enabled=False,
        auto_part_change_in_progress=False,
        auto_cycle_started_by_user=False,
        auto_restart_after_manual_clamp=False,
        is_running=False,
        _start_request_pending=False,
        _manual_jig_in_progress=False,
        _manual_jig_started_at=None,
        _manual_jig_stop_requested=False,
        _last_manual_block_reason=None,
        waiting_result_from_finished_test=False,
        _trace=lambda *args, **kwargs: None,
        update_status=lambda *args: None,
        refresh_station_state=lambda: None,
    )
    station.get_jakotukki_program_number = MethodType(
        StationController.get_jakotukki_program_number, station
    )
    station.is_jakotukki_station_and_program = MethodType(
        StationController.is_jakotukki_station_and_program, station
    )
    station._manual_jig_block_reason = MethodType(
        StationController._manual_jig_block_reason, station
    )
    return station, widget, hardware


class JigRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def test_manual_buttons_match_actual_guard_not_just_auto_flag(self):
        station, widget, hw = make_station()
        StationController.update_jig_controls_visibility(station)
        self.assertTrue(widget.jig_enabled)

        station._manual_jig_in_progress = True
        StationController.update_jig_controls_visibility(station)
        self.assertFalse(widget.jig_enabled)
        self.assertEqual(station._manual_jig_block_reason(), "manual_jig_active")

        station._manual_jig_in_progress = False
        hw.is_jig_busy = lambda: True
        StationController.update_jig_controls_visibility(station)
        self.assertFalse(widget.jig_enabled)
        self.assertEqual(station._manual_jig_block_reason(), "jig_owner_active")

    def test_pending_result_blocks_start_but_physical_button_calls_stop(self):
        station, widget, hardware = make_station()
        station.dev_mode_fortest = True
        station.waiting_result_from_finished_test = True
        station.has_selected_program = lambda: True
        station.check_ready_to_start = MethodType(
            StationController.check_ready_to_start, station
        )
        self.assertFalse(station.check_ready_to_start())

        pressed = []
        station.handle_physical_button_press = lambda: False
        station.stop_test = lambda: pressed.append("STOP")
        station.start_test = lambda: pressed.append("START")
        fake_controller = SimpleNamespace(station_controllers={2: station})
        PhysicalButtonController.toggle_station(fake_controller, 2)
        self.assertEqual(pressed, ["STOP"])

        station.waiting_result_from_finished_test = False
        PhysicalButtonController.toggle_station(fake_controller, 2)
        self.assertEqual(pressed, ["STOP", "START"])

    def test_manual_buttons_work_in_fail_wait_state_if_safe(self):
        station, widget, _ = make_station("WAIT_FAIL_REMOVE")
        StationController.update_jig_controls_visibility(station)
        self.assertTrue(widget.jig_enabled)
        self.assertIsNone(station._manual_jig_block_reason())

    def test_manual_buttons_blocked_until_fortest_really_ready(self):
        station, widget, _ = make_station()
        station.status_handler.last_status = 3
        StationController.update_jig_controls_visibility(station)
        self.assertFalse(widget.jig_enabled)
        self.assertEqual(station._manual_jig_block_reason(), "fortest_not_ready")

    def test_manual_jig_missing_done_times_out_and_requests_stop(self):
        station, widget, hw = make_station()
        stop_calls = []
        hw.request_jig_stop = lambda sid: (
            stop_calls.append(sid) or (True, "STOP")
        )
        station._manual_jig_in_progress = True
        station._manual_jig_started_at = time.monotonic() - 30
        StationController.poll_auto_part_change_state(station)
        StationController.poll_auto_part_change_state(station)
        self.assertEqual(stop_calls, [2])
        self.assertTrue(station._manual_jig_stop_requested)
        self.assertTrue(station._manual_jig_in_progress)

    def test_manual_done_releases_flag_and_refreshes_buttons(self):
        station, widget, hw = make_station()
        station._manual_jig_in_progress = True
        station._manual_jig_started_at = time.monotonic()
        refreshes = []
        station.refresh_station_state = lambda: refreshes.append(True)
        StationController._handle_jig_state_ready(
            station, 2, {"status": JIG_SEQUENCE_STATUS_DONE, "error": 0}
        )
        self.assertFalse(station._manual_jig_in_progress)
        self.assertIsNone(station._manual_jig_started_at)
        self.assertEqual(len(refreshes), 1)

    def test_manual_error_preserves_guard_until_stop_confirmed(self):
        station, widget, hw = make_station()
        station._manual_jig_in_progress = True
        stop_calls = []
        hw.request_jig_stop = lambda sid: (
            stop_calls.append(sid) or (True, "STOP")
        )
        StationController._handle_jig_state_ready(
            station, 2, {"status": JIG_SEQUENCE_STATUS_ERROR, "error": 102}
        )
        self.assertTrue(station._manual_jig_in_progress)
        self.assertEqual(stop_calls, [2])
        StationController._handle_jig_stop_finished(station, 2, True, "STOP")
        self.assertFalse(station._manual_jig_in_progress)

    def test_failed_queue_does_not_leave_new_owner(self):
        hw = HardwareService(dev_mode_modbus=True, dev_mode_gpio=True)
        try:
            hw._submit_jig_job = lambda *args: False
            ok, _ = hw.request_jig_start(1, "start_jig_part_release_sequence")
            self.assertFalse(ok)
            self.assertIsNone(hw._jig_owner_station)
            self.assertFalse(hw._jig_operation_pending)
        finally:
            hw.cleanup()

    def test_error_status_requires_stop_before_releasing_owner(self):
        hw = HardwareService(dev_mode_modbus=True, dev_mode_gpio=True)
        try:
            hw._jig_owner_station = 1
            hw._jig_state_pending = True
            hw._handle_jig_job_complete(
                "state", 1, {"status": JIG_SEQUENCE_STATUS_ERROR, "error": 5}
            )
            self.assertEqual(hw._jig_owner_station, 1)
            ok, _ = hw.request_jig_stop(1)
            self.assertTrue(ok)
            deadline = time.monotonic() + 2
            while hw.is_jig_busy() and time.monotonic() < deadline:
                self.app.processEvents()
                time.sleep(0.01)
            self.assertFalse(hw.is_jig_busy())
        finally:
            hw.cleanup()


class RuntimeLogTests(unittest.TestCase):
    def test_no_sensitive_or_unknown_fields_in_public_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            logger = RuntimeDiagnostics(directory=tmp, start_thread=False)
            try:
                logger.record(
                    "jig_manual_denied",
                    station=1,
                    program=32,
                    reason="pressure_release_active",
                    serial_number="SECRET_SERIAL",
                    operator="SECRET_OPERATOR",
                    message="SECRET MESSAGE",
                )
                lines = list(Path(tmp).glob("*.jsonl"))
                self.assertEqual(len(lines), 1)
                data = json.loads(lines[0].read_text(encoding="utf-8"))
                self.assertEqual(data["station"], 1)
                self.assertEqual(data["reason"], "pressure_release_active")
                self.assertNotIn("serial_number", data)
                self.assertNotIn("operator", data)
                self.assertNotIn("message", data)
            finally:
                logger.close()

    def test_upload_uses_diagnostics_branch_and_never_main(self):
        with tempfile.TemporaryDirectory() as tmp:
            logger = RuntimeDiagnostics(directory=tmp, start_thread=False)
            try:
                logger.record("fortest_status_changed", station=2, status=0)
                logger._token = lambda: "github_pat_TEST_ONLY"
                sent = []
                def fake_request(url, token, method="GET", data=None):
                    if method == "GET":
                        raise urllib.error.HTTPError(url, 404, "missing", {}, None)
                    sent.append((url, method, data))
                    return {"content": {"sha": "fake"}}

                logger._github_request = fake_request
                self.assertTrue(logger.upload_once())
                self.assertEqual(len(sent), 1)
                self.assertEqual(sent[0][1], "PUT")
                self.assertEqual(sent[0][2]["branch"], "diagnostics")
                body = base64.b64decode(sent[0][2]["content"])
                self.assertIn(b"fortest_status_changed", body)
                self.assertNotIn(b"SECRET", body)
            finally:
                logger.close()


if __name__ == "__main__":
    unittest.main()
