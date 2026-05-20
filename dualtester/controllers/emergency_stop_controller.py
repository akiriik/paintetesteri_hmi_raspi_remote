# controllers/emergency_stop_controller.py

from PyQt5.QtCore import QTimer

from ui.components.emergency_stop_dialog import EmergencyStopDialog


class EmergencyStopController:
    """
    Hätäseislogiikan oma controller.

    Tehtävät:
    - lukee hätäseistilan HardwareServicen kautta
    - avaa hätäseisdialogin
    - pysäyttää station 1 testin hätäseisissä
    - kuittaa tilan dialogin sulkeutuessa
    - pitää MainWindowin puhtaampana
    """

    def __init__(
        self,
        main_window,
        hardware_service,
        station_controllers,
        modbus_manager,
        poll_interval_ms=1000,
    ):
        self.main_window = main_window
        self.hardware_service = hardware_service
        self.station_controllers = station_controllers
        self.modbus_manager = modbus_manager

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
        station = self.station_controllers.get(1)

        if station:
            try:
                station.stop_test()
                station.update_status(
                    "HÄTÄSEIS AKTIVOITU, TESTI PYSÄYTETTY",
                    "ERROR",
                )
            except Exception as e:
                print(f"Virhe testin pysäytyksessä: {e}")

        self.emergency_dialog_open = True
        self._emergency_dialog = EmergencyStopDialog(
            self.main_window,
            self.modbus_manager,
        )
        self._emergency_dialog._is_emergency_stop_dialog = True
        self._emergency_dialog.finished.connect(self.on_emergency_dialog_closed)
        self._emergency_dialog.exec_()

    def close_emergency_dialog(self):
        if self._emergency_dialog is not None:
            self._emergency_dialog.accept()
            self._emergency_dialog = None

        self.emergency_dialog_open = False

    def on_emergency_dialog_closed(self, result):
        self.emergency_dialog_open = False

        station = self.station_controllers.get(1)

        if result == 1 and station:
            station.update_status("HÄTÄSEIS KUITATTU", "INFO")

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