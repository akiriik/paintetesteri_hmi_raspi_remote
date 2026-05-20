# controllers/station_status_handler.py


class StationStatusHandler:
    """
    Yhden ForTest-aseman statuksen käsittely.

    Tämä luokka:
    - tulkitsee ForTest statusrekisterin
    - tunnistaa testin päättymisen
    - pyytää tulokset testin päättyessä
    - päivittää aseman tilatekstin
    """

    def __init__(self, controller):
        self.controller = controller
        self.last_status = None
        self.last_shown_status = None

    def update_status_from_fortest(self, result):
        controller = self.controller

        if not result or not hasattr(result, "registers"):
            return

        if len(result.registers) < 2:
            return

        status_value = result.registers[1]

        # 0 = WAITING / valmis.
        # Jos edellinen tila oli testiin liittyvä tila, testi on juuri päättynyt.
        if status_value == 0 and self.last_status in [1, 2, 3]:
            controller.is_running = False
            controller.fortest_service.read_results(controller.station_id)

            ready = controller.check_ready_to_start()
            controller.station_widget.update_running_state(False, ready)
            controller._update_gpio_run_state()

        self.last_status = status_value

        if status_value == 1 and self.last_shown_status != 1:
            controller.update_status("TESTI KÄYNNISSÄ", "INFO")
            self.last_shown_status = 1

        elif status_value == 2 and self.last_shown_status != 2:
            controller.update_status("AUTOZERO", "INFO")
            self.last_shown_status = 2

        elif status_value == 3 and self.last_shown_status != 3:
            controller.update_status("PURKU", "INFO")
            self.last_shown_status = 3

        elif status_value == 0 and self.last_shown_status != 0:
            controller.update_status("VALMIS", "SUCCESS")
            self.last_shown_status = 0

    def reset(self):
        self.last_status = None
        self.last_shown_status = None