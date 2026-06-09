# controllers/emergency_stop_controller.py

from PyQt5.QtCore import QTimer

from ui.components.emergency_stop_dialog import EmergencyStopDialog


class EmergencyStopController:
    """
    Hätäseislogiikan oma controller.

    Tehtävät:
    - lukee hätäseistilan HardwareServicen kautta
    - avaa hätäseisdialogin
    - pysäyttää kaikki asemat hätäseisissä
    - nollaa automaattiajon tilat hätäseisissä
    - kuittaa tilan dialogin sulkeutuessa
    - pitää MainWindowin puhtaampana

    Huom:
    Tämä on ohjelmallinen hätäseis-/tilatietologiikka.
    Tämä ei korvaa oikeaa turvapiiriä.
    """

    def __init__(
        self,
        main_window,
        hardware_service,
        station_controllers,
        poll_interval_ms=1000,
    ):
        self.main_window = main_window
        self.hardware_service = hardware_service
        self.station_controllers = station_controllers

        self.emergency_dialog_open = False
        self._emergency_dialog = None

        self.timer = QTimer(main_window)
        self.timer.timeout.connect(self.check_emergency_stop)
        self.timer.start(poll_interval_ms)

    def is_emergency_dialog_active(self):
        return (
            self._emergency_dialog is not None
            and getattr(self._emergency_dialog, "_is_emergency_stop_dialog", False)
        )

    def check_emergency_stop(self):
        if not self.hardware_service.is_modbus_connected():
            return

        try:
            status = self.hardware_service.read_emergency_stop_status()

            if status == 1 and self.emergency_dialog_open:
                self.close_emergency_dialog()
                return

            if status == 0 and not self.emergency_dialog_open:
                self.open_emergency_dialog()

        except Exception as e:
            print(f"Virhe hätäseistilan tarkistuksessa: {e}")
            self.stop()

    def open_emergency_dialog(self):
        self.stop_all_stations()

        self.emergency_dialog_open = True
        self._emergency_dialog = EmergencyStopDialog(
            self.main_window,
            self.hardware_service,
        )
        self._emergency_dialog._is_emergency_stop_dialog = True
        self._emergency_dialog.finished.connect(self.on_emergency_dialog_closed)
        self._emergency_dialog.exec_()

    def stop_all_stations(self):
        for station_id, station in self.station_controllers.items():
            if not station:
                continue

            try:
                if hasattr(station, "disable_auto_part_change"):
                    station.disable_auto_part_change(
                        "HÄTÄSEIS - AUTOMAATTI POIS",
                        show_message=False,
                    )

                station.is_running = False
                station.results_started = False
                station.test_has_reached_active_status = False
                station.waiting_result_from_finished_test = False
                station.auto_part_change_in_progress = False
                station.auto_cycle_started_by_user = False

                if hasattr(station, "auto_cycle_phase"):
                    station.auto_cycle_phase = "IDLE"

                if not getattr(station, "dev_mode_fortest", True):
                    fortest_service = getattr(station, "fortest_service", None)

                    if fortest_service and fortest_service.is_connected(station_id):
                        fortest_service.abort_test(station_id)

                if hasattr(station, "open_test_valve"):
                    station.open_test_valve()

                station.update_status(
                    "HÄTÄSEIS AKTIVOITU, TESTI PYSÄYTETTY",
                    "ERROR",
                )
                station.refresh_station_state()

            except Exception as e:
                print(f"Virhe testin pysäytyksessä asemalla {station_id}: {e}")

    def close_emergency_dialog(self):
        if self._emergency_dialog is not None:
            self._emergency_dialog.accept()
            self._emergency_dialog = None

        self.emergency_dialog_open = False

    def on_emergency_dialog_closed(self, result):
        self.emergency_dialog_open = False

        if result == 1:
            for station in self.station_controllers.values():
                if station:
                    station.update_status("HÄTÄSEIS KUITATTU", "INFO")
                    station.refresh_station_state()

        self._emergency_dialog = None

    def stop(self):
        if self.timer:
            self.timer.stop()

    def cleanup(self):
        self.stop()

        if self._emergency_dialog is not None:
            try:
                self._emergency_dialog.close()
            except Exception:
                pass

        self._emergency_dialog = None
        self.emergency_dialog_open = False
