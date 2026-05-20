# controllers/station_controller.py
from datetime import datetime
from types import SimpleNamespace
import random

from PyQt5.QtCore import QObject, QTimer


class StationController(QObject):
    """
    Yhden ForTest-aseman logiikka.

    UI-komponentti: ForTestStation
    Fyysinen ForTest-yhteys: ForTestService
    GPIO/Opta/sensorit: HardwareService
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
        self.is_running = False
        self.results_started = False
        self.last_status = None
        self.last_shown_status = None
        self.results_read_counter = 0

        self._connect_ui()

        self.fortest_timer = QTimer(self)
        self.fortest_timer.timeout.connect(self.update_fortest_data)
        self.fortest_timer.start(1000)

    def _connect_ui(self):
        self.station_widget.select_program_button.clicked.connect(self.request_program_selection)
        self.station_widget.start_button.clicked.connect(self.start_test)
        self.station_widget.stop_button.clicked.connect(self.stop_test)

        if hasattr(self.station_widget, "dev_result_button"):
            self.station_widget.dev_result_button.clicked.connect(self.show_dev_fortest_result)
            self.station_widget.dev_result_button.setVisible(self.dev_mode_fortest)

    def request_program_selection(self):
        if hasattr(self.main_window, "show_program_selection"):
            self.main_window.show_program_selection(self.station_id)

    def set_program(self, program_data):
        if not program_data:
            return

        self.selected_program = program_data

        program_id = program_data.get("id", 0)
        program_name = program_data.get("name", f"Ohjelma {program_id}")
        description = program_data.get("description", "")

        self.program_number = int(program_id) if program_id else 0

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

    def check_ready_to_start(self):
        if self.program_number <= 0:
            return False

        if self.dev_mode_fortest:
            return True

        return self.fortest_service.is_connected(self.station_id)

    def start_test(self):
        if self.program_number <= 0:
            self.update_status("VIRHE: VALITSE OHJELMA", "ERROR")
            return

        if not self.dev_mode_fortest and not self.fortest_service.is_connected(self.station_id):
            self.update_status("FORTEST-YHTEYTTÄ EI SAATAVILLA", "ERROR")
            return

        if self.dev_mode_fortest:
            self._continue_start_test()
            return

        result = self.fortest_service.write_program(self.station_id, self.program_number)
        self.update_status(f"VAIHDETAAN OHJELMAAN {self.program_number}...", "INFO")

        if result:
            QTimer.singleShot(1000, self._continue_start_test)
        else:
            self.update_status("OHJELMAN VAIHTO EPÄONNISTUI", "ERROR")

    def _continue_start_test(self):
        self.results_started = True
        self.is_running = True

        self.station_widget.update_running_state(is_running=True, ready=False)
        self.update_status("TESTI KÄYNNISTETTY", "INFO")

        if not self.dev_mode_fortest:
            self.fortest_service.start_test(self.station_id)

        self._update_gpio_run_state()

    def stop_test(self):
        self.is_running = False
        ready = self.check_ready_to_start()

        self.station_widget.update_running_state(is_running=False, ready=ready)
        self.update_status("TESTI PYSÄYTETTY", "INFO")

        if not self.dev_mode_fortest:
            self.fortest_service.abort_test(self.station_id)

        self._update_gpio_run_state()

    def update_fortest_data(self):
        if self.dev_mode_fortest:
            ready = self.check_ready_to_start()
            self.station_widget.update_running_state(self.is_running, ready)
            return

        self.fortest_service.read_status(self.station_id)

        self.results_read_counter += 1
        if self.results_read_counter >= 5:
            self.fortest_service.read_results(self.station_id)
            self.results_read_counter = 0

        ready = False
        if not self.is_running:
            ready = self.check_ready_to_start()

        self.station_widget.update_running_state(self.is_running, ready)
        self._update_gpio_run_state()

    def update_status_from_fortest(self, result):
        if not result or not hasattr(result, "registers"):
            return

        if len(result.registers) < 2:
            return

        status_value = result.registers[1]

        if status_value == 0 and self.last_status in [1, 2, 3]:
            self.is_running = False
            self.fortest_service.read_results(self.station_id)

            ready = self.check_ready_to_start()
            self.station_widget.update_running_state(False, ready)
            self._update_gpio_run_state()

        self.last_status = status_value

        if status_value == 1 and self.last_shown_status != 1:
            self.update_status("TESTI KÄYNNISSÄ", "INFO")
            self.last_shown_status = 1
        elif status_value == 2 and self.last_shown_status != 2:
            self.update_status("AUTOZERO", "INFO")
            self.last_shown_status = 2
        elif status_value == 3 and self.last_shown_status != 3:
            self.update_status("PURKU", "INFO")
            self.last_shown_status = 3
        elif status_value == 0 and self.last_shown_status != 0:
            self.update_status("VALMIS", "SUCCESS")
            self.last_shown_status = 0

    def update_test_results(self, result):
        if not result or not hasattr(result, "registers"):
            return

        if self.program_number <= 0:
            return

        if len(result.registers) < 25:
            return

        test_result = result.registers[9]

        if test_result == 0 or test_result == 99:
            return

        if result.registers[6] != self.program_number:
            return

        if not self.results_started:
            return

        hours = result.registers[0]
        minutes = result.registers[1]
        seconds = result.registers[2]
        day = result.registers[3]
        month = result.registers[4]
        year = result.registers[5]

        timestamp = f"{day:02d}.{month:02d}.{year} {hours:02d}:{minutes:02d}:{seconds:02d}"
        result_id = f"{timestamp}-{test_result}-{result.registers[6]}-{result.registers[21]}"

        if hasattr(self, "last_result_id") and self.last_result_id == result_id:
            return

        self.last_result_id = result_id

        result_texts = {
            0: "Ei tulosta",
            1: "OK",
            2: "FAIL",
            3: "OK?",
            4: "NOK?",
            5: "Virheellinen referenssi",
            6: "Virheellinen täyttö",
            7: "Virtaus alle rajan",
            8: "Paine yli asteikon",
            9: "VOUT yli asteikon",
            10: "Paine alle toleranssin",
            11: "Paine yli toleranssin",
            12: "Painetasoa ei saavutettu",
            13: "Keskeytetty",
            14: "Virtaus yli rajan",
            15: "Täyttöaika min",
            16: "Virhe tilavuusreferenssi",
        }

        result_status = result_texts.get(test_result, f"TULOS: {test_result}")

        if test_result == 1:
            result_color = "#00FF00"
        elif test_result == 2:
            result_color = "red"
        elif test_result in [3, 4]:
            result_color = "orange"
        else:
            result_color = "red"

        decay_sign = result.registers[20]
        decay_value = result.registers[21]
        decay_unit_code = result.registers[23]
        decay_decimals = result.registers[24]

        if decay_decimals > 0:
            decay_value = decay_value / (10 ** decay_decimals)

        if decay_sign == 255:
            decay_value = -decay_value

        formatted_decay = f"{decay_value:.{decay_decimals}f}"

        units = {
            20: "mbar/s",
            21: "bar/s",
            22: "hPa/s",
            23: "Pa/s",
            24: "Psi/s",
            40: "cc/h",
            41: "cc/min",
            42: "l/h",
            43: "l/min",
            0: "mbar",
            1: "bar",
            2: "hPa",
            3: "Pa",
            4: "Psi",
            60: "s",
            61: "min",
            70: "cc",
            71: "l",
        }

        decay_unit = units.get(decay_unit_code, "mbar/s")

        if hasattr(result, "program_name") and result.program_name:
            program_text = result.program_name
        elif self.selected_program:
            program_text = f"{self.program_number}. {self.selected_program.get('name', '')}"
        else:
            program_text = f"{self.program_number}. Ohjelma {self.program_number}"

        room_temp_text = ""
        part_temp_text = ""

        if hasattr(result, "room_temp"):
            room_temp_text = f"{result.room_temp:.1f}°C"

        if hasattr(result, "part_temp"):
            part_temp_text = f"{result.part_temp:.1f}°C"

        self.station_widget.add_result_row(
            display_time=f"{hours:02d}:{minutes:02d}",
            program_text=program_text,
            decay_text=f"{formatted_decay} {decay_unit}",
            result_text=result_status,
            result_color=result_color,
            room_temp_text=room_temp_text,
            part_temp_text=part_temp_text,
        )

    def update_status(self, message, level="INFO"):
        self.station_widget.update_status(message, level)

    def _update_gpio_run_state(self):
        """
        Säilyttää vanhan yhden testerin GPIO-valologiikan asema 1:lle:
        GPIO 23 = vihreä, GPIO 24 = punainen vanhan koodin set_output(4/5)-kartalla.

        Asema 2:n fyysiset GPIO-valot pitää määrittää erikseen ennen käyttöönottoa.
        """
        if self.station_id != 1:
            return

        ready = self.check_ready_to_start()

        if self.is_running:
            self.hardware_service.set_output(4, False)
            self.hardware_service.set_output(5, True)
        elif ready:
            self.hardware_service.set_output(4, True)
            self.hardware_service.set_output(5, False)
        else:
            self.hardware_service.set_output(4, False)
            self.hardware_service.set_output(5, False)

    def show_dev_fortest_result(self):
        if self.program_number <= 0:
            self.update_status("VIRHE: VALITSE OHJELMA ENNEN DEV-TULOSTA", "ERROR")
            return

        self.results_started = True

        now = datetime.now()

        test_result = random.choice([1, 1, 1, 2])

        if test_result == 1:
            decay_value = random.randint(5, 180)
        else:
            decay_value = random.randint(210, 450)

        room_temp = round(random.uniform(20.8, 22.6), 1)
        part_temp = round(random.uniform(21.0, 23.0), 1)

        registers = [0] * 25

        registers[0] = now.hour
        registers[1] = now.minute
        registers[2] = now.second
        registers[3] = now.day
        registers[4] = now.month
        registers[5] = now.year

        registers[6] = self.program_number
        registers[9] = test_result

        registers[20] = 0
        registers[21] = decay_value
        registers[23] = 23
        registers[24] = 2

        program_name = f"{self.program_number}. {self.selected_program.get('name', '')}"

        fake_result = SimpleNamespace(
            registers=registers,
            program_name=program_name,
            room_temp=room_temp,
            part_temp=part_temp,
        )

        self.update_test_results(fake_result)
        self.update_status("DEV: EMULOITU TULOS LISÄTTY", "INFO")

    def cleanup(self):
        if self.fortest_timer:
            self.fortest_timer.stop()