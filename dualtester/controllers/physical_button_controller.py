# controllers/physical_button_controller.py

import time

from config.gpio_config import (
    STATION_BUTTON_MAP,
    STATION_LIGHT_OUTPUTS,
    SPARE_BUTTONS,
)


class PhysicalButtonController:
    """
    Fyysisten nappien ja nappivalojen yhteinen controller.

    ForTest 1 / 2:
    - palautuva NO-kytkin maadoittaa GPIO-inputin
    - ensimmäinen painallus käynnistää testin
    - toinen painallus pysäyttää testin

    Valologiikka:
    - ohjelma valittu ja testi ei käy = vihreä
    - testi käy = punainen
    - ei valmis = valo pois

    Relelogiikka:
    - rele pois = vihreä
    - rele päällä = punainen
    """

    COLOR_READY_GREEN = False
    COLOR_RUNNING_RED = True

    def __init__(self, station_controllers, hardware_service):
        self.station_controllers = station_controllers
        self.hardware_service = hardware_service

        self.station_button_map = STATION_BUTTON_MAP
        self.station_light_outputs = STATION_LIGHT_OUTPUTS
        self.spare_buttons = SPARE_BUTTONS

        self.last_light_states = {}

    def handle_button_press(self, button_name, is_pressed):
        if not is_pressed:
            return

        if button_name in self.station_button_map:
            station_id = self.station_button_map[button_name]
            self.toggle_station(station_id)
            return

        if button_name == "EMERGENCY_STOP":
            self.handle_emergency_stop_button()
            return

        if button_name in self.spare_buttons:
            print(f"Vara-/lisänappi painettu: {button_name}")
            return

        print(f"Tuntematon fyysinen nappi: {button_name}")

    def toggle_station(self, station_id):
        station = self.station_controllers.get(station_id)

        if not station:
            print(f"Fyysinen nappi: asemaa {station_id} ei löydy")
            return

        if station.is_running:
            station.stop_test()
        else:
            station.start_test()

    def handle_emergency_stop_button(self):
        for station_id, station in self.station_controllers.items():
            if station:
                try:
                    station.stop_test()
                    station.update_status(
                        "HÄTÄSEIS-NAPPI PAINETTU, TESTI PYSÄYTETTY",
                        "ERROR",
                    )
                except Exception as e:
                    print(f"Hätäseis-napin käsittely epäonnistui asemalla {station_id}: {e}")

    def update_station_light_state(self, station_id, is_running, ready):
        outputs = self.station_light_outputs.get(station_id)

        if not outputs:
            return

        on_off_output = outputs.get("on_off")
        color_output = outputs.get("color")

        if on_off_output is None or color_output is None:
            return

        light_on = bool(is_running or ready)

        if is_running:
            color_state = self.COLOR_RUNNING_RED
        else:
            color_state = self.COLOR_READY_GREEN

        new_state = {
            "light_on": light_on,
            "color": color_state,
        }

        old_state = self.last_light_states.get(station_id)

        if old_state == new_state:
            return

        # Turvallinen värinvaihto:
        # 1. LED pois
        # 2. releen vaihto
        # 3. pieni viive
        # 4. LED päälle, jos asema on valmis/käynnissä
        self.hardware_service.set_output(on_off_output, False)
        self.hardware_service.set_output(color_output, color_state)

        if light_on:
            time.sleep(0.03)
            self.hardware_service.set_output(on_off_output, True)

        self.last_light_states[station_id] = new_state

    def cleanup(self):
        for outputs in self.station_light_outputs.values():
            try:
                self.hardware_service.set_output(outputs["on_off"], False)
                self.hardware_service.set_output(outputs["color"], False)
            except Exception:
                pass