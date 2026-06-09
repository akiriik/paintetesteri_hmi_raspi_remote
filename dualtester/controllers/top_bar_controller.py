# controllers/top_bar_controller.py

from PyQt5.QtCore import QTimer

from utils.sen0332_handler import SEN0332Manager


class TopBarController:
    def __init__(
        self,
        main_screen,
        environment_status_bar,
        hardware_service,
        fortest_service,
        dev_mode_fortest,
        parent=None,
        update_interval_ms=1000,
    ):
        self.main_screen = main_screen
        self.environment_status_bar = environment_status_bar
        self.hardware_service = hardware_service
        self.fortest_service = fortest_service
        self.dev_mode_fortest = dev_mode_fortest
        self.sen0332_manager = None

        self._init_room_sensor()

        self.timer = QTimer(parent)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(update_interval_ms)

        self.update_status()

    def _init_room_sensor(self):
        if not self.environment_status_bar:
            return

        if self.hardware_service and getattr(self.hardware_service, "dev_mode_gpio", False):
            return

        try:
            self.sen0332_manager = SEN0332Manager()
            self.sen0332_manager.data_updated.connect(
                self.environment_status_bar.update_room_sensor_data
            )
            self.sen0332_manager.error_occurred.connect(
                self.environment_status_bar.show_room_sensor_error
            )
        except Exception as e:
            print(f"Varoitus: SEN0332-huoneanturin alustus epäonnistui: {e}")
            self.sen0332_manager = None

    def update_environment_sensors(self):
        if self.hardware_service:
            self.hardware_service.update_environment_sensors()

        if self.sen0332_manager:
            self.sen0332_manager.read_once()

    def update_status(self):
        self.update_environment_sensors()

        if not self.main_screen:
            return

        if not hasattr(self.main_screen, "environment_bar"):
            return

        environment_bar = self.main_screen.environment_bar

        if self.hardware_service:
            environment_bar.update_hardware_status(
                self.hardware_service.get_connection_status_text()
            )

        environment_bar.update_fortest_status(
            self.get_fortest_status_text()
        )

        if self.environment_status_bar:
            self.environment_status_bar.update_main_environment_bar()

    def get_fortest_status_text(self):
        if self.dev_mode_fortest:
            return "FORTEST 1: DEV    FORTEST 2: DEV"

        if not self.fortest_service:
            return "FORTEST 1: EI PALVELUA    FORTEST 2: EI PALVELUA"

        f1_ok = self.fortest_service.is_connected(1)
        f2_ok = self.fortest_service.is_connected(2)

        f1_text = "FORTEST 1: OK" if f1_ok else "FORTEST 1: EI YHTEYTTÄ"

        station_ports = getattr(self.fortest_service, "fortest_station_ports", {})
        station2_port = station_ports.get(2)

        if not station2_port:
            f2_text = "FORTEST 2: EI MÄÄRITETTY"
        else:
            f2_text = "FORTEST 2: OK" if f2_ok else "FORTEST 2: EI YHTEYTTÄ"

        return f"{f1_text}    {f2_text}"

    def cleanup(self):
        if self.timer:
            self.timer.stop()

        if self.sen0332_manager:
            self.sen0332_manager.cleanup()
