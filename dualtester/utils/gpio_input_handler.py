# utils/gpio_input_handler.py

import sys
import os
import time
import RPi.GPIO as GPIO
from PyQt5.QtCore import QObject, pyqtSignal


class GPIOInputHandler(QObject):
    """Hallinnoi GPIO-sisääntuloja fyysisiä painikkeita varten."""

    button_changed = pyqtSignal(str, bool)  # signal: button_name, is_pressed

    def __init__(self):
        super().__init__()

        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        self._null_device = open(os.devnull, "w")

        sys.stdout = self._null_device
        sys.stderr = self._null_device

        try:
            GPIO.setmode(GPIO.BCM)

            # Fyysisten painikkeiden oletuspinnit.
            #
            # STATION1_START:
            #   ForTest 1 start/stop -painike.
            #
            # STATION2_START:
            #   ForTest 2 start/stop -painike.
            #
            # EMERGENCY_STOP:
            #   Ohjelmallinen hätäseisinput / tilatieto.
            #   Ei korvaa oikeaa turvapiiriä.
            #
            # SPARE1-4:
            #   Varapainikkeet tulevaa käyttöä varten.
            self.button_pins = {
                "STATION1_START": 5,
                "STATION2_START": 6,
                "EMERGENCY_STOP": 12,
                "SPARE1": 13,
                "SPARE2": 16,
                "SPARE3": 20,
                "SPARE4": 21,
            }

            for pin in self.button_pins.values():
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            self.button_states = {button: False for button in self.button_pins}
            self.last_press_time = {button: 0 for button in self.button_pins}
            self.debounce_time = 200

            for button, pin in self.button_pins.items():
                self.button_states[button] = not GPIO.input(pin)

            for button_name, pin in self.button_pins.items():
                GPIO.add_event_detect(
                    pin,
                    GPIO.BOTH,
                    callback=lambda channel, btn=button_name: self._button_callback(btn, channel),
                    bouncetime=100,
                )

        finally:
            sys.stdout = self._original_stdout
            sys.stderr = self._original_stderr

    def _button_callback(self, button_name, channel):
        current_time = time.time() * 1000
        last_time = self.last_press_time[button_name]

        if current_time - last_time < self.debounce_time:
            return

        is_pressed = not GPIO.input(channel)

        if is_pressed:
            self.last_press_time[button_name] = current_time
            self.button_changed.emit(button_name, True)

    def read_button_state(self, button_name):
        if button_name in self.button_pins:
            pin = self.button_pins[button_name]
            current_state = not GPIO.input(pin)

            if current_state != self.button_states[button_name]:
                self.button_states[button_name] = current_state

            return self.button_states[button_name]

        return False

    def cleanup(self):
        sys.stdout = self._null_device
        sys.stderr = self._null_device

        try:
            for pin in self.button_pins.values():
                try:
                    GPIO.remove_event_detect(pin)
                except Exception:
                    pass

        finally:
            sys.stdout = self._original_stdout
            sys.stderr = self._original_stderr
            self._null_device.close()