# controllers/top_bar_controller.py

from PyQt5.QtCore import QTimer


class TopBarController:
    """
    Yläpalkin tilapäivitysten controller.

    Tehtävät:
    - päivittää hardware-yhteystilat EnvironmentBarille
    - muodostaa ForTest 1 / ForTest 2 tilatekstin
    - välittää EnvironmentStatusBarin arvot EnvironmentBarille
    - pitää omaa päivitystimeriä
    """

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

        self.timer = QTimer(parent)
        self.timer.timeout.connect(self.update_status)
        self.timer.start(update_interval_ms)

        self.update_status()

    def update_environment_sensors(self):
        self.hardware_service.update_environment_sensors()

    def update_status(self):
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