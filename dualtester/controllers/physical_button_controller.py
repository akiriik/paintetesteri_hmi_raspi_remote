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

    Normaalitila:
    - vihreä = ohjelma valittu / valmis STARTiin
    - punainen = testi käynnissä
    - pois = ei valmis

    Jakotukki-odotustilat:
    - vihreä vilkkuu = kappale puuttuu, painallus ajaa KAPPALE KIINNI
    - punainen vilkkuu = FAIL-kappale odottaa poistoa, painallus ajaa KAPPALEEN POISTO

    Vilkutus on rauhallinen, jotta releitä ei kuluteta turhaan.
    """

    COLOR_READY_GREEN = False
    COLOR_RUNNING_RED = True

    LIGHT_MODE_OFF = "off"
    LIGHT_MODE_GREEN = "green"
    LIGHT_MODE_RED = "red"
    LIGHT_MODE_GREEN_BLINK = "green_blink"
    LIGHT_MODE_RED_BLINK = "red_blink"

    BLINK_INTERVAL_S = 1.5

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

        if hasattr(station, "handle_physical_button_press"):
            handled = station.handle_physical_button_press()
            if handled:
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

    def _get_blink_on_state(self):
        phase = int(time.monotonic() / self.BLINK_INTERVAL_S)
        return (phase % 2) == 0

    def _resolve_light_state(self, light_mode, is_running, ready):
        if light_mode == self.LIGHT_MODE_GREEN_BLINK:
            return {
                "light_on": self._get_blink_on_state(),
                "color": self.COLOR_READY_GREEN,
                "mode": light_mode,
            }

        if light_mode == self.LIGHT_MODE_RED_BLINK:
            return {
                "light_on": self._get_blink_on_state(),
                "color": self.COLOR_RUNNING_RED,
                "mode": light_mode,
            }

        if light_mode == self.LIGHT_MODE_GREEN:
            return {
                "light_on": True,
                "color": self.COLOR_READY_GREEN,
                "mode": light_mode,
            }

        if light_mode == self.LIGHT_MODE_RED:
            return {
                "light_on": True,
                "color": self.COLOR_RUNNING_RED,
                "mode": light_mode,
            }

        if light_mode == self.LIGHT_MODE_OFF:
            return {
                "light_on": False,
                "color": self.COLOR_READY_GREEN,
                "mode": light_mode,
            }

        light_on = bool(is_running or ready)

        if is_running:
            color_state = self.COLOR_RUNNING_RED
        else:
            color_state = self.COLOR_READY_GREEN

        return {
            "light_on": light_on,
            "color": color_state,
            "mode": "auto",
        }

    def update_station_light_state(self, station_id, is_running, ready, light_mode=None):
        outputs = self.station_light_outputs.get(station_id)

        if not outputs:
            return

        on_off_output = outputs.get("on_off")
        color_output = outputs.get("color")

        if on_off_output is None or color_output is None:
            return

        new_state = self._resolve_light_state(
            light_mode=light_mode,
            is_running=is_running,
            ready=ready,
        )

        old_state = self.last_light_states.get(station_id)

        if old_state == new_state:
            return

        old_color = None
        if old_state:
            old_color = old_state.get("color")

        light_on = new_state["light_on"]
        color_state = new_state["color"]

        if old_color != color_state:
            self.hardware_service.set_output(on_off_output, False)
            self.hardware_service.set_output(color_output, color_state)

            if light_on:
                time.sleep(0.03)
                self.hardware_service.set_output(on_off_output, True)
        else:
            self.hardware_service.set_output(color_output, color_state)
            self.hardware_service.set_output(on_off_output, light_on)

        self.last_light_states[station_id] = new_state

    def cleanup(self):
        for outputs in self.station_light_outputs.values():
            try:
                self.hardware_service.set_output(outputs["on_off"], False)
                self.hardware_service.set_output(outputs["color"], False)
            except Exception:
                pass
