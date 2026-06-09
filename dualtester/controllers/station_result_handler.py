# controllers/station_result_handler.py
from datetime import datetime
from types import SimpleNamespace
import random


class StationResultHandler:
    """
    Yhden ForTest-aseman tulosten käsittely.
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
        self.last_test_result = None

    def update_test_results(self, result):
        controller = self.controller

        if not result or not hasattr(result, "registers"):
            return None

        if controller.program_number <= 0:
            return None

        if len(result.registers) < 25:
            return None

        test_result = result.registers[9]

        if test_result == 0 or test_result == 99:
            return None

        if result.registers[6] != controller.program_number:
            return None

        if not controller.results_started:
            return None

        hours = result.registers[0]
        minutes = result.registers[1]
        seconds = result.registers[2]
        day = result.registers[3]
        month = result.registers[4]
        year = result.registers[5]

        timestamp = f"{day:02d}.{month:02d}.{year} {hours:02d}:{minutes:02d}:{seconds:02d}"
        result_id = f"{timestamp}-{test_result}-{result.registers[6]}-{result.registers[21]}"

        if self.last_result_id == result_id:
            return None

        self.last_result_id = result_id
        self.last_test_result = test_result

        result_status = self.RESULT_TEXTS.get(test_result, f"TULOS: {test_result}")
        result_color = self._get_result_color(test_result)

        formatted_decay, decay_unit = self._parse_decay_value(result.registers)
        environment_snapshot = self._get_environment_snapshot(result)

        program_text = self._get_program_text(result)
        room_temp_text = self._get_room_temp_text(environment_snapshot)
        part_temp_text = self._get_part_temp_text(environment_snapshot)

        controller.station_widget.add_result_row(
            display_time=f"{hours:02d}:{minutes:02d}",
            program_text=program_text,
            decay_text=f"{formatted_decay} {decay_unit}",
            result_text=result_status,
            result_color=result_color,
            room_temp_text=room_temp_text,
            part_temp_text=part_temp_text,
        )

        self._store_result_to_database(
            result=result,
            test_result=test_result,
            result_status=result_status,
            formatted_decay=formatted_decay,
            decay_unit=decay_unit,
            environment_snapshot=environment_snapshot,
            year=year,
            month=month,
            day=day,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
        )

        return test_result

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

    def _get_room_temp_text(self, environment_snapshot):
        room_temperature = environment_snapshot.get("room_temperature_c")

        if room_temperature is None:
            return ""

        try:
            return f"{float(room_temperature):.1f}°C"
        except Exception:
            return ""

    def _get_part_temp_text(self, environment_snapshot):
        part_temperature = environment_snapshot.get("part_temperature_c")

        if part_temperature is None:
            return ""

        try:
            return f"{float(part_temperature):.1f}°C"
        except Exception:
            return ""

    def _safe_float(self, value):
        if value is None or value == "":
            return None

        try:
            return float(value)
        except Exception:
            return None

    def _is_part_temperature_enabled(self):
        station_widget = getattr(self.controller, "station_widget", None)

        if not station_widget:
            return False

        if hasattr(station_widget, "is_part_temperature_enabled"):
            return station_widget.is_part_temperature_enabled()

        return bool(getattr(station_widget, "part_temperature_enabled", False))

    def _get_environment_snapshot(self, result):
        controller = self.controller
        main_window = getattr(controller, "main_window", None)
        environment_status_bar = getattr(main_window, "environment_status_bar", None)

        room_temperature = None
        room_humidity = None
        tank_temperature = None
        tank_humidity = None
        tank_pressure = None
        part_temperature = None

        if environment_status_bar:
            room_temperature = getattr(environment_status_bar, "room_temperature", None)
            room_humidity = getattr(environment_status_bar, "room_humidity", None)
            tank_temperature = getattr(environment_status_bar, "tank_temperature", None)
            tank_humidity = getattr(environment_status_bar, "tank_humidity", None)
            tank_pressure = getattr(environment_status_bar, "tank_pressure", None)
            part_temperature = getattr(environment_status_bar, "part_temperature", None)

        if hasattr(result, "room_temp"):
            room_temperature = result.room_temp

        if hasattr(result, "part_temp"):
            part_temperature = result.part_temp

        if not self._is_part_temperature_enabled():
            part_temperature = None

        return {
            "room_temperature_c": room_temperature,
            "room_humidity_percent": room_humidity,
            "tank_temperature_c": tank_temperature,
            "tank_humidity_percent": tank_humidity,
            "tank_pressure_bar": tank_pressure,
            "part_temperature_c": part_temperature,
        }

    def _get_result_datetime_parts(self, year, month, day, hours, minutes, seconds):
        try:
            result_datetime = datetime(
                int(year),
                int(month),
                int(day),
                int(hours),
                int(minutes),
                int(seconds),
            )
        except Exception:
            result_datetime = datetime.now()

        return (
            result_datetime.isoformat(timespec="seconds"),
            result_datetime.date().isoformat(),
            result_datetime.time().isoformat(timespec="seconds"),
        )

    def _store_result_to_database(
        self,
        result,
        test_result,
        result_status,
        formatted_decay,
        decay_unit,
        environment_snapshot,
        year,
        month,
        day,
        hours,
        minutes,
        seconds,
    ):
        controller = self.controller
        main_window = getattr(controller, "main_window", None)
        storage_service = getattr(main_window, "result_storage_service", None)

        if not storage_service:
            return

        selected_program = controller.selected_program or {}
        program_name = selected_program.get("name") or f"Ohjelma {controller.program_number}"
        pressure_mbar = selected_program.get("pressure_mbar")

        timestamp, date_text, time_text = self._get_result_datetime_parts(
            year,
            month,
            day,
            hours,
            minutes,
            seconds,
        )

        data = {
            "timestamp": timestamp,
            "date": date_text,
            "time": time_text,
            "station_id": controller.station_id,
            "tester_name": f"ForTest {controller.station_id}",
            "program_number": controller.program_number,
            "program_name": program_name,
            "product_name": program_name,
            "result_code": test_result,
            "result_text": result_status,
            "result_ok": 1 if test_result == 1 else 0,
            "pressure_mbar": self._safe_float(pressure_mbar),
            "decay_value": self._safe_float(formatted_decay),
            "decay_unit": decay_unit,
            "leak_value": self._safe_float(formatted_decay),
            "leak_unit": decay_unit,
            "room_temperature_c": self._safe_float(environment_snapshot.get("room_temperature_c")),
            "room_humidity_percent": self._safe_float(environment_snapshot.get("room_humidity_percent")),
            "tank_temperature_c": self._safe_float(environment_snapshot.get("tank_temperature_c")),
            "tank_humidity_percent": self._safe_float(environment_snapshot.get("tank_humidity_percent")),
            "tank_pressure_bar": self._safe_float(environment_snapshot.get("tank_pressure_bar")),
            "part_temperature_c": self._safe_float(environment_snapshot.get("part_temperature_c")),
            "raw_result": {
                "registers": list(result.registers),
            },
        }

        storage_service.save_test_result(data)

    def create_dev_result(self):
        controller = self.controller

        if controller.program_number <= 0:
            controller.update_status("VIRHE: VALITSE OHJELMA ENNEN DEV-TULOSTA", "ERROR")
            controller.refresh_station_state()
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

        added_result = self.update_test_results(fake_result)

        controller.is_running = False
        controller.update_status("DEV: EMULOITU TULOS LISÄTTY", "INFO")

        if added_result is not None:
            controller.handle_result_for_automatic_cycle(added_result)

        controller.refresh_station_state()
