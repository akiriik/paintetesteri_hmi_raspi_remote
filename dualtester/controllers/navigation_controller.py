# controllers/navigation_controller.py

from PyQt5.QtCore import Qt


class NavigationController:
    """
    Näkymänvaihdon controller.

    Tehtävät:
    - päänäkymään palaaminen
    - käsikäytön avaaminen
    - ohjelmanvalinnan avaaminen
    - ESC-näppäimen navigointilogiikka
    """

    def __init__(
        self,
        main_window,
        main_screen,
        manual_screen,
        program_selection_screen,
        environment_status_bar,
        program_selection_controller,
    ):
        self.main_window = main_window
        self.main_screen = main_screen
        self.manual_screen = manual_screen
        self.program_selection_screen = program_selection_screen
        self.environment_status_bar = environment_status_bar
        self.program_selection_controller = program_selection_controller

    def show_testing(self):
        self.environment_status_bar.hide()
        self.manual_screen.hide()
        self.program_selection_screen.hide()
        self.main_screen.show()
        self.main_window.update_top_bar_status()

    def show_manual(self):
        self.main_screen.hide()
        self.environment_status_bar.hide()
        self.program_selection_screen.hide()

        if hasattr(self.manual_screen, "refresh"):
            self.manual_screen.refresh()

        self.manual_screen.show()

    def show_program_selection(self, station_id=None):
        self.program_selection_controller.open_for_station(station_id)

    def handle_escape_key(self):
        if self.manual_screen.isVisible() or self.program_selection_screen.isVisible():
            if self.program_selection_screen.isVisible():
                self.program_selection_controller.cancel_selection()
            else:
                self.show_testing()
        else:
            self.main_window.close()

    def handle_key_press(self, event):
        if event.key() == Qt.Key_Escape:
            self.handle_escape_key()
            return True

        return False

    def cleanup(self):
        pass