# controllers/physical_button_controller.py

import time

from PyQt5.QtCore import QObject, QTimer

from config.gpio_config import (
    STATION_BUTTON_MAP,
    STATION_LIGHT_OUTPUTS,
    SPARE_BUTTONS,
)


class PhysicalButtonController(QObject):
    """
    Fyysisten nappien ja nappivalojen yhteinen controller.

    Normaalitila:
    - vihreä = ohjelma valittu / valmis STARTiin
    - punainen = testi käynnissä
    - pois = ei valmis

    Jakotukki-odotustilat:
    - vihreä vilkkuu = kappale puuttuu, painallus ajaa KAPPALE KIINNI
    - punainen vilkkuu = FAIL-kappale odottaa poistoa, painallus ajaa KAPPALEEN POISTO

    Vilkutus tehdään omalla 0,5 s QTimer-ajastimella. Ajastin vaihtaa vain
    LED ON/OFF -ohjausta, ei värirelettä joka syklillä.
    """

    COLOR_READY_GREEN = False
    COLOR_RUNNING_RED = True

    LIGHT_MODE_OFF = "off"
    LIGHT_MODE_GREEN = "green"
    LIGHT_MODE_RED = "red"
    LIGHT_MODE_GREEN_BLINK = "green_blink"
    LIGHT_MODE_RED_BLINK = "red_blink"

    BLINK_INTERVAL_MS = 500

    def __init__(self, station_controllers, hardware_service):
        super().__init__()

        self.station_controllers = station_controllers
        self.hardware_service = hardware_service

        self.station_button_map = STATION_BUTTON_MAP
        self.station_light_outputs = STATION_LIGHT_OUTPUTS
        self.spare_buttons = SPARE_BUTTONS

        self.last_light_states = {}
        self.active_blink_states = {}
        self.blink_light_on = False

        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self._blink_timer_tick)

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

    def _is_blink_mode(self, light_mode):
        return light_mode in [
            self.LIGHT_MODE_GREEN_BLINK,
            self.LIGHT_MODE_RED_BLINK,
        ]

    def _blink_color_for_mode(self, light_mode):
        if light_mode == self.LIGHT_MODE_RED_BLINK:
            return self.COLOR_RUNNING_RED

        return self.COLOR_READY_GREEN

    def _set_light_safely(self, station_id, light_on, color_state, mode):
        outputs = self.station_light_outputs.get(station_id)

        if not outputs:
            return

        on_off_output = outputs.get("on_off")
        color_output = outputs.get("color")

        if on_off_output is None or color_output is None:
            return

        old_state = self.last_light_states.get(station_id)
        old_color = old_state.get("color") if old_state else None

        if old_color != color_state:
            self.hardware_service.set_output(on_off_output, False)
            self.hardware_service.set_output(color_output, color_state)

            if light_on:
                time.sleep(0.03)
                self.hardware_service.set_output(on_off_output, True)
        else:
            self.hardware_service.set_output(on_off_output, light_on)

        self.last_light_states[station_id] = {
            "light_on": bool(light_on),
            "color": color_state,
            "mode": mode,
        }

    def _start_blink_mode(self, station_id, light_mode):
        color_state = self._blink_color_for_mode(light_mode)

        current_blink_state = self.active_blink_states.get(station_id)
        if current_blink_state and current_blink_state.get("mode") == light_mode:
            return

        self.active_blink_states[station_id] = {
            "mode": light_mode,
            "color": color_state,
        }

        self._set_light_safely(
            station_id=station_id,
            light_on=True,
            color_state=color_state,
            mode=light_mode,
        )
        self.blink_light_on = True

        if not self.blink_timer.isActive():
            self.blink_timer.start(self.BLINK_INTERVAL_MS)

    def _stop_blink_mode(self, station_id):
        if station_id in self.active_blink_states:
            del self.active_blink_states[station_id]

        if not self.active_blink_states and self.blink_timer.isActive():
            self.blink_timer.stop()
            self.blink_light_on = False

    def _blink_timer_tick(self):
        if not self.active_blink_states:
            self.blink_timer.stop()
            self.blink_light_on = False
            return

        self.blink_light_on = not self.blink_light_on

        for station_id, blink_state in list(self.active_blink_states.items()):
            self._set_light_safely(
                station_id=station_id,
                light_on=self.blink_light_on,
                color_state=blink_state["color"],
                mode=blink_state["mode"],
            )

    def _resolve_static_light_state(self, light_mode, is_running, ready):
        if light_mode == self.LIGHT_MODE_GREEN:
            return True, self.COLOR_READY_GREEN, light_mode

        if light_mode == self.LIGHT_MODE_RED:
            return True, self.COLOR_RUNNING_RED, light_mode

        if light_mode == self.LIGHT_MODE_OFF:
            return False, self.COLOR_READY_GREEN, light_mode

        light_on = bool(is_running or ready)

        if is_running:
            color_state = self.COLOR_RUNNING_RED
        else:
            color_state = self.COLOR_READY_GREEN

        return light_on, color_state, "auto"

    def update_station_light_state(self, station_id, is_running, ready, light_mode=None):
        if self._is_blink_mode(light_mode):
            self._start_blink_mode(station_id, light_mode)
            return

        self._stop_blink_mode(station_id)

        light_on, color_state, mode = self._resolve_static_light_state(
            light_mode=light_mode,
            is_running=is_running,
            ready=ready,
        )

        new_state = {
            "light_on": bool(light_on),
            "color": color_state,
            "mode": mode,
        }

        old_state = self.last_light_states.get(station_id)

        if old_state == new_state:
            return

        self._set_light_safely(
            station_id=station_id,
            light_on=light_on,
            color_state=color_state,
            mode=mode,
        )

    def cleanup(self):
        if self.blink_timer and self.blink_timer.isActive():
            self.blink_timer.stop()

        self.active_blink_states.clear()
        self.blink_light_on = False

        for outputs in self.station_light_outputs.values():
            try:
                self.hardware_service.set_output(outputs["on_off"], False)
                self.hardware_service.set_output(outputs["color"], False)
            except Exception:
                pass
