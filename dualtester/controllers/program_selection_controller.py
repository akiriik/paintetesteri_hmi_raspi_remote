# controllers/program_selection_controller.py

class ProgramSelectionController:
    """
    Ohjaa ohjelmanvalintanäkymän toimintaa.

    Tehtävät:
    - muistaa mille asemalle ohjelmaa ollaan valitsemassa
    - vastaanottaa ProgramSelectionScreenin program_selected(dict) signaalin
    - välittää ohjelma oikealle StationControllerille
    - palauttaa päänäkymään
    - estää ohjelman valinta ilman aktiivista asemaa
    """

    def __init__(self, main_window, program_selection_screen, station_controllers):
        self.main_window = main_window
        self.program_selection_screen = program_selection_screen
        self.station_controllers = station_controllers

        self.active_station_id = None

        self.program_selection_screen.program_selected.connect(self.on_program_selected)

    def open_for_station(self, station_id):
        """
        Avaa ohjelmanvalinnan tietylle asemalle.
        """

        if station_id not in self.station_controllers:
            print(f"Ohjelmanvalintaa ei avattu: tuntematon asema {station_id}")
            self.active_station_id = None
            self.main_window.show_testing()
            return

        self.active_station_id = station_id

        self.main_window.environment_status_bar.hide()
        self.main_window.main_screen.hide()
        self.main_window.manual_screen.hide()
        self.main_window.program_selection_screen.show()

    def on_program_selected(self, program_data):
        """
        Vastaanottaa valitun ohjelman ja välittää sen aktiiviselle asemalle.
        """

        if self.active_station_id is None:
            print("Ohjelmaa ei asetettu: aktiivista asemaa ei ole")
            self.main_window.show_testing()
            return

        station = self.station_controllers.get(self.active_station_id)

        if not station:
            print(f"Ohjelmaa ei asetettu: asemaa {self.active_station_id} ei löydy")
            self.active_station_id = None
            self.main_window.show_testing()
            return

        station.set_program(program_data)

        self.active_station_id = None
        self.main_window.show_testing()

    def cancel_selection(self):
        """
        Nollaa aktiivisen aseman ja palaa päänäkymään.
        """

        self.active_station_id = None
        self.main_window.show_testing()