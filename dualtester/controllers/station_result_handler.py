# controllers/station_result_handler.py
from datetime import datetime
from types import SimpleNamespace
import random


class StationResultHandler:
    """
    Yhden ForTest-aseman tulosten käsittely.

    Tämä luokka:
    - tarkistaa tulosrekisterit
    - estää duplikaattitulokset
    - tulkitsee tuloskoodin
    - laskee vuotoarvon ja yksikön
    - lähettää rivin ForTestStation UI-komponentille
    """

    RESULT_TEXTS = {
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

    UNITS = {
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

    def __init__(self, controller):
        self.controller = controller
        self.last_result_id = None

    def update_test_results(self, result):
        controller = self.controller

        if not result or not hasattr(result, "registers"):
            return

        if controller.program_number <= 0:
            return

        if len(result.registers) < 25:
            return

        test_result = result.registers[9]

        if test_result == 0 or test_result == 99:
            return

        if result.registers[6] != controller.program_number:
            return

        if not controller.results_started:
            return

        hours = result.registers[0]
        minutes = result.registers[1]
        seconds = result.registers[2]
        day = result.registers[3]
        month = result.registers[4]
        year = result.registers[5]

        timestamp = f"{day:02d}.{month:02d}.{year} {hours:02d}:{minutes:02d}:{seconds:02d}"
        result_id = f"{timestamp}-{test_result}-{result.registers[6]}-{result.registers[21]}"

        if self.last_result_id == result_id:
            return

        self.last_result_id = result_id

        result_status = self.RESULT_TEXTS.get(test_result, f"TULOS: {test_result}")
        result_color = self._get_result_color(test_result)

        formatted_decay, decay_unit = self._parse_decay_value(result.registers)

        program_text = self._get_program_text(result)
        room_temp_text = self._get_room_temp_text(result)
        part_temp_text = self._get_part_temp_text(result)

        controller.station_widget.add_result_row(
            display_time=f"{hours:02d}:{minutes:02d}",
            program_text=program_text,
            decay_text=f"{formatted_decay} {decay_unit}",
            result_text=result_status,
            result_color=result_color,
            room_temp_text=room_temp_text,
            part_temp_text=part_temp_text,
        )

    def _get_result_color(self, test_result):
        if test_result == 1:
            return "#00FF00"

        if test_result == 2:
            return "red"

        if test_result in [3, 4]:
            return "orange"

        return "red"

    def _parse_decay_value(self, registers):
        decay_sign = registers[20]
        decay_value = registers[21]
        decay_unit_code = registers[23]
        decay_decimals = registers[24]

        if decay_decimals > 0:
            decay_value = decay_value / (10 ** decay_decimals)

        if decay_sign == 255:
            decay_value = -decay_value

        formatted_decay = f"{decay_value:.{decay_decimals}f}"
        decay_unit = self.UNITS.get(decay_unit_code, "mbar/s")

        return formatted_decay, decay_unit

    def _get_program_text(self, result):
        controller = self.controller

        if hasattr(result, "program_name") and result.program_name:
            return result.program_name

        if controller.selected_program:
            return f"{controller.program_number}. {controller.selected_program.get('name', '')}"

        return f"{controller.program_number}. Ohjelma {controller.program_number}"

    def _get_room_temp_text(self, result):
        if hasattr(result, "room_temp"):
            return f"{result.room_temp:.1f}°C"

        return ""

    def _get_part_temp_text(self, result):
        if hasattr(result, "part_temp"):
            return f"{result.part_temp:.1f}°C"

        return ""

    def create_dev_result(self):
        controller = self.controller

        if controller.program_number <= 0:
            controller.update_status("VIRHE: VALITSE OHJELMA ENNEN DEV-TULOSTA", "ERROR")
            return

        controller.results_started = True

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

        registers[6] = controller.program_number
        registers[9] = test_result

        registers[20] = 0
        registers[21] = decay_value
        registers[23] = 23
        registers[24] = 2

        program_name = f"{controller.program_number}. {controller.selected_program.get('name', '')}"

        fake_result = SimpleNamespace(
            registers=registers,
            program_name=program_name,
            room_temp=room_temp,
            part_temp=part_temp,
        )

        self.update_test_results(fake_result)
        controller.update_status("DEV: EMULOITU TULOS LISÄTTY", "INFO")