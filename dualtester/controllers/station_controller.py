# controllers/station_controller.py
from PyQt5.QtCore import QObject, QTimer

from controllers.station_result_handler import StationResultHandler
from controllers.station_status_handler import StationStatusHandler
from controllers.test_valve_controller import TestValveController


JAKOTUBBI_PROGRAM_NUMBER = 3
JAKOTUBBI_STATION_ID = 2


class StationController(QObject):
    """
    Yhden ForTest-aseman pääohjain.

    Tämä luokka vastaa:
    - ohjelman valinnasta
    - ohjelman kirjoittamisesta ForTestille ohjelman valinnan yhteydessä
    - start/stop-ohjauksesta
    - ajastimista
    - status- ja result-handlerien kutsumisesta
    - aseman käyttötilan päivittämisestä UI:lle
    - ForTest-kohtaisen testiventtiilin ohjauksesta
    - jigin sekvenssinappien ohjauksesta

    Fyysiset napit ja niiden valot hoidetaan PhysicalButtonControllerissa.
    """

    def __init__(
        self,
        station_id,
        station_widget,
        main_window,
        fortest_service,
        hardware_service,
        dev_mode_fortest=True,
        parent=None,
    ):
        super().__init__(parent)

        self.station_id = station_id
        self.station_widget = station_widget
        self.main_window = main_window
        self.fortest_service = fortest_service
        self.hardware_service = hardware_service
        self.dev_mode_fortest = dev_mode_fortest

        self.selected_program = None
        self.program_number = 0
        self.program_written_to_fortest = False

        self.is_running = False
        self.results_started = False
        self.results_read_counter = 0

        self.auto_part_change_enabled = False
        self.auto_part_change_in_progress = False

        self.test_valve_controller = TestValveController(self.hardware_service)

        self.result_handler = StationResultHandler(self)
        self.status_handler = StationStatusHandler(self)

        self._connect_ui()

        self.fortest_timer = QTimer(self)
        self.fortest_timer.timeout.connect(self.update_fortest_data)
        self.fortest_timer.start(1000)

        self.open_test_valve()
        self.refresh_station_state()

    def _connect_ui(self):
        self.station_widget.select_program_button.clicked.connect(self.request_program_selection)
        self.station_widget.start_button.clicked.connect(self.start_test)
        self.station_widget.stop_button.clicked.connect(self.stop_test)

        if hasattr(self.station_widget, "jig_part_clamp_button"):
            self.station_widget.jig_part_clamp_button.clicked.connect(
                self.start_jig_part_clamp_sequence
            )

        if hasattr(self.station_widget, "jig_part_release_button"):
            self.station_widget.jig_part_release_button.clicked.connect(
                self.start_jig_part_release_sequence
            )

        if hasattr(self.station_widget, "jig_part_remove_button"):
            self.station_widget.jig_part_remove_button.clicked.connect(
                self.start_jig_part_remove_sequence
            )

        if hasattr(self.station_widget, "dev_result_button"):
            self.station_widget.dev_result_button.clicked.connect(self.show_dev_fortest_result)
            self.station_widget.dev_result_button.setVisible(self.dev_mode_fortest)

    def request_program_selection(self):
        if hasattr(self.main_window, "show_program_selection"):
            self.main_window.show_program_selection(self.station_id)

    def set_program(self, program_data):
        if not program_data:
            return

        program_id = program_data.get("id", 0)
        program_number = int(program_id) if program_id else 0

        if program_number <= 0:
            self.selected_program = None
            self.program_number = 0
            self.program_written_to_fortest = False
            self.update_status("VIRHE: OHJELMAN ID PUUTTUU", "ERROR")
            self.update_jig_controls_visibility()
            self.refresh_station_state()
            return

        self.program_written_to_fortest = False

        if not self.dev_mode_fortest:
            if not self.fortest_service or not self.fortest_service.is_connected(self.station_id):
                self.selected_program = None
                self.program_number = 0
                self.update_status("FORTEST-YHTEYTTÄ EI SAATAVILLA", "ERROR")
                self.update_jig_controls_visibility()
                self.refresh_station_state()
                return

            self.update_status(f"VAIHDETAAN OHJELMAAN {program_number}...", "INFO")

            result = self.fortest_service.write_program(self.station_id, program_number)

            if not result:
                self.selected_program = None
                self.program_number = 0
                self.program_written_to_fortest = False
                self.update_status("OHJELMAN VAIHTO EPÄONNISTUI", "ERROR")
                self.update_jig_controls_visibility()
                self.refresh_station_state()
                return

            self.program_written_to_fortest = True
        else:
            self.program_written_to_fortest = True

        self.selected_program = program_data
        self.program_number = program_number

        program_name = program_data.get("name", f"Ohjelma {program_id}")
        description = program_data.get("description", "")

        pressure = program_data.get("pressure_mbar", "--")
        fill_time = program_data.get("fill_time_s", "--")
        settle_time = program_data.get("settle_time_s", "--")
        test_time = program_data.get("test_time_s", "--")
        volume = program_data.get("piece_volume_ml", "--")

        max_decay = program_data.get("max_decay", {})
        decay_value = max_decay.get("value", "--")
        decay_unit = max_decay.get("unit", "")
        decay_mode = max_decay.get("mode", "")

        if decay_unit:
            decay_text = f"{decay_value} {decay_unit}"
        else:
            decay_text = str(decay_value)

        if decay_mode:
            decay_text += f" ({decay_mode})"

        display_name = f"{program_id}. {program_name}"

        self.station_widget.update_program_info(
            display_name=display_name,
            description=description,
            pressure=pressure,
            volume=volume,
            fill_time=fill_time,
            settle_time=settle_time,
            test_time=test_time,
            decay_text=decay_text,
        )

        self.update_status("OHJELMA VALITTU", "SUCCESS")
        self.update_jig_controls_visibility()
        self.refresh_station_state()

    def has_selected_program(self):
        return (
            self.program_number > 0
            and self.selected_program is not None
            and self.program_written_to_fortest
        )

    def check_ready_to_start(self):
        if not self.has_selected_program():
            return False

        if self.is_running:
            return False

        if self.dev_mode_fortest:
            return True

        return self.fortest_service.is_connected(self.station_id)

    def update_jig_controls_visibility(self):
        """
        Näyttää jigin sekvenssinapit vain:
        - ForTest 2 -asemalla
        - kun valittu ohjelma on 3 / jakotubbi
        """
        visible = (
            self.station_id == JAKOTUBBI_STATION_ID
            and self.program_number == JAKOTUBBI_PROGRAM_NUMBER
        )

        if hasattr(self.station_widget, "set_jig_controls_visible"):
            self.station_widget.set_jig_controls_visible(visible)
            return

        if hasattr(self.station_widget, "set_jig_part_clamp_visible"):
            self.station_widget.set_jig_part_clamp_visible(visible)

    def _start_jig_sequence(self, hardware_method_name, sequence_name):
        """
        Käynnistää Optan jig-sekvenssin.
        """
        if self.station_id != JAKOTUBBI_STATION_ID:
            return

        if self.program_number != JAKOTUBBI_PROGRAM_NUMBER:
            self.update_status(f"{sequence_name} VAIN OHJELMALLA 3", "ERROR")
            return

        if not self.hardware_service:
            self.update_status("OPTA-OHJAUS EI OLE KÄYTÖSSÄ", "ERROR")
            return

        if not hasattr(self.hardware_service, hardware_method_name):
            self.update_status("JIG-SEKVENSSIN OHJAUS PUUTTUU HARDWARE SERVICESTÄ", "ERROR")
            return

        if hasattr(self.station_widget, "set_jig_controls_enabled"):
            self.station_widget.set_jig_controls_enabled(False)
        elif hasattr(self.station_widget, "set_jig_part_clamp_enabled"):
            self.station_widget.set_jig_part_clamp_enabled(False)

        self.update_status(f"KÄYNNISTETÄÄN {sequence_name} -SEKVENSSI...", "INFO")

        hardware_method = getattr(self.hardware_service, hardware_method_name)
        success, message = hardware_method()

        if success:
            self.update_status(message, "INFO")
        else:
            self.update_status(message, "ERROR")

        if hasattr(self.station_widget, "set_jig_controls_enabled"):
            self.station_widget.set_jig_controls_enabled(True)
        elif hasattr(self.station_widget, "set_jig_part_clamp_enabled"):
            self.station_widget.set_jig_part_clamp_enabled(True)

        self.refresh_station_state()

    def start_jig_part_clamp_sequence(self):
        self._start_jig_sequence(
            "start_jig_part_clamp_sequence",
            "KAPPALE KIINNI",
        )

    def start_jig_part_release_sequence(self):
        self._start_jig_sequence(
            "start_jig_part_release_sequence",
            "KAPPALE IRTI",
        )

    def start_jig_part_remove_sequence(self):
        self._start_jig_sequence(
            "start_jig_part_remove_sequence",
            "KAPPALEEN POISTO",
        )

    def set_auto_part_change_enabled(self, enabled):
        """
        Automaattisen kappaleenvaihdon päällä/pois-tila.

        Tätä ei vielä kytketä UI-nappiin.
        Kun UI-nappi lisätään, se kutsuu tätä metodia.
        """
        self.auto_part_change_enabled = bool(enabled)

        if self.auto_part_change_enabled:
            self.update_status("AUTOMAATTINEN KAPPALEENVAIHTO PÄÄLLÄ", "INFO")
        else:
            self.update_status("AUTOMAATTINEN KAPPALEENVAIHTO POIS", "WARNING")

        self.refresh_station_state()

    def can_start_auto_part_change_after_result(self):
        """
        Tarkistaa, saako testin valmistumisen jälkeen käynnistää
        automaattisen kappaleenvaihdon.
        """
        if not self.auto_part_change_enabled:
            return False

        if self.auto_part_change_in_progress:
            return False

        if self.station_id != JAKOTUBBI_STATION_ID:
            return False

        if self.program_number != JAKOTUBBI_PROGRAM_NUMBER:
            return False

        if self.is_running:
            return False

        if not self.hardware_service:
            return False

        if not hasattr(self.hardware_service, "start_jig_auto_part_change_sequence"):
            return False

        return True

    def start_auto_part_change_after_result(self):
        """
        Käynnistää Optan AUTO_PART_CHANGE-sekvenssin yhden kerran
        hyväksytyn/käsitellyn testituloksen jälkeen.
        """
        if not self.can_start_auto_part_change_after_result():
            return

        self.auto_part_change_in_progress = True

        if hasattr(self.station_widget, "set_jig_controls_enabled"):
            self.station_widget.set_jig_controls_enabled(False)

        self.update_status("AUTOMAATTINEN KAPPALEENVAIHTO KÄYNNISTYY...", "INFO")

        success, message = self.hardware_service.start_jig_auto_part_change_sequence()

        if success:
            self.update_status(message, "INFO")
        else:
            self.auto_part_change_in_progress = False
            self.update_status(message, "ERROR")

        self.refresh_station_state()

    def clear_auto_part_change_lock(self):
        """
        Vapauttaa automaattisyklin lukituksen.

        Huomio:
        Tässä vaiheessa lukitus vapautetaan vasta seuraavan testin STARTissa.
        Myöhemmin tämä kannattaa kytkeä Optan JIG_SEQUENCE_STATUS_REGISTER-lukuun,
        jolloin lukitus vapautetaan kun Opta ilmoittaa DONE tai ERROR.
        """
        self.auto_part_change_in_progress = False

    def close_test_valve(self):
        success, message = self.test_valve_controller.close_valve(self.station_id)

        if not success and message:
            self.update_status(message, "ERROR")

        return success

    def open_test_valve(self):
        success, message = self.test_valve_controller.open_valve(self.station_id)

        if not success and message:
            self.update_status(message, "ERROR")

        return success

    def update_test_valve_from_fortest_status(self, status_value):
        success, message = self.test_valve_controller.update_from_fortest_status(
            station_id=self.station_id,
            status_value=status_value,
        )

        if not success and message:
            self.update_status(message, "ERROR")

        return success

    def start_test(self):
        if self.is_running:
            return

        self.clear_auto_part_change_lock()

        if not self.has_selected_program():
            self.update_status("VIRHE: VALITSE OHJELMA", "ERROR")
            self.refresh_station_state()
            return

        if not self.dev_mode_fortest and not self.fortest_service.is_connected(self.station_id):
            self.open_test_valve()
            self.update_status("FORTEST-YHTEYTTÄ EI SAATAVILLA", "ERROR")
            self.refresh_station_state()
            return

        valve_ok = self.close_test_valve()

        if not valve_ok:
            self.is_running = False
            self.refresh_station_state()
            return

        QTimer.singleShot(200, self._continue_start_test)

    def _continue_start_test(self):
        self.results_started = True
        self.is_running = True

        self.update_status("TESTI KÄYNNISTETTY", "INFO")

        if not self.dev_mode_fortest:
            self.fortest_service.start_test(self.station_id)

        self.refresh_station_state()

    def stop_test(self):
        if not self.is_running:
            self.open_test_valve()
            self.refresh_station_state()
            return

        self.is_running = False
        self.update_status("TESTI PYSÄYTETTY", "INFO")

        if not self.dev_mode_fortest:
            self.fortest_service.abort_test(self.station_id)

        self.open_test_valve()
        self.refresh_station_state()

    def finish_test(self, status_message=None, level="INFO"):
        self.is_running = False
        self.open_test_valve()

        if status_message:
            self.update_status(status_message, level)

        self.refresh_station_state()

    def update_fortest_data(self):
        if self.dev_mode_fortest:
            self.refresh_station_state()
            return

        if not self.fortest_service or not self.fortest_service.has_station_port(self.station_id):
            self.open_test_valve()
            self.refresh_station_state()
            return

        self.fortest_service.read_status(self.station_id)

        self.results_read_counter += 1

        if self.results_read_counter >= 5:
            self.fortest_service.read_results(self.station_id)
            self.results_read_counter = 0

        self.refresh_station_state()

    def update_status_from_fortest(self, result):
        self.status_handler.update_status_from_fortest(result)
        self.refresh_station_state()

    def update_test_results(self, result):
        result_added = self.result_handler.update_test_results(result)

        if result_added:
            self.start_auto_part_change_after_result()

        self.refresh_station_state()

    def show_dev_fortest_result(self):
        self.result_handler.create_dev_result()
        self.open_test_valve()
        self.refresh_station_state()

    def update_status(self, message, level="INFO"):
        self.station_widget.update_status(message, level)

    def refresh_station_state(self):
        ready = self.check_ready_to_start()

        self.station_widget.update_running_state(
            is_running=self.is_running,
            ready=ready,
        )

        self.update_jig_controls_visibility()
        self._update_physical_button_light(ready)

    def _update_physical_button_light(self, ready=None):
        if ready is None:
            ready = self.check_ready_to_start()

        physical_button_controller = getattr(
            self.main_window,
            "physical_button_controller",
            None,
        )

        if physical_button_controller:
            physical_button_controller.update_station_light_state(
                station_id=self.station_id,
                is_running=self.is_running,
                ready=ready,
            )

    def cleanup(self):
        self.open_test_valve()

        if self.fortest_timer:
            self.fortest_timer.stop()