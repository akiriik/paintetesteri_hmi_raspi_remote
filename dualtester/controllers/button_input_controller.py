# controllers/button_input_controller.py


class ButtonInputController:
    """
    Fyysisten painikkeiden ohjauslogiikka.

    Säilyttää vanhan toiminnan:
    - START käynnistää station 1 testin
    - STOP pysäyttää station 1 testin
    - TEST1 ei tee tässä vaiheessa mitään

    Myöhemmin tähän voidaan lisätä asemapohjainen logiikka,
    jos fyysiset napit jaetaan ForTest 1 / ForTest 2 asemille.
    """

    def __init__(self, station_controllers):
        self.station_controllers = station_controllers

    def handle_button_press(self, button_name, is_pressed):
        if not is_pressed:
            return

        station = self.station_controllers.get(1)

        if not station:
            return

        if button_name == "START":
            station.start_test()

        elif button_name == "STOP":
            station.stop_test()

        elif button_name == "TEST1":
            return

    def cleanup(self):
        pass