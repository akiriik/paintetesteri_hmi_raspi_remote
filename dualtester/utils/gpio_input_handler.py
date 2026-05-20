# utils/gpio_input_handler.py

import sys
import os
import time
import RPi.GPIO as GPIO
from PyQt5.QtCore import QObject, pyqtSignal

from config.gpio_config import (
    GPIO_DEBOUNCE_TIME_MS,
    GPIO_EVENT_BOUNCETIME_MS,
    GPIO_INPUT_ACTIVE_LOW,
    GPIO_INPUT_PULL_UP,
    PHYSICAL_BUTTON_PINS,
)


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

            self.button_pins = PHYSICAL_BUTTON_PINS
            self.button_states = {button: False for button in self.button_pins}
            self.last_press_time = {button: 0 for button in self.button_pins}
            self.debounce_time = GPIO_DEBOUNCE_TIME_MS

            pull_mode = GPIO.PUD_UP if GPIO_INPUT_PULL_UP else GPIO.PUD_DOWN

            for pin in self.button_pins.values():
                GPIO.setup(pin, GPIO.IN, pull_up_down=pull_mode)

            for button, pin in self.button_pins.items():
                self.button_states[button] = self._read_gpio_pressed(pin)

            for button_name, pin in self.button_pins.items():
                GPIO.add_event_detect(
                    pin,
                    GPIO.BOTH,
                    callback=lambda channel, btn=button_name: self._button_callback(btn, channel),
                    bouncetime=GPIO_EVENT_BOUNCETIME_MS,
                )

        finally:
            sys.stdout = self._original_stdout
            sys.stderr = self._original_stderr

    def _read_gpio_pressed(self, pin):
        gpio_state = GPIO.input(pin)

        if GPIO_INPUT_ACTIVE_LOW:
            return not gpio_state

        return bool(gpio_state)

    def _button_callback(self, button_name, channel):
        current_time = time.time() * 1000
        last_time = self.last_press_time[button_name]

        if current_time - last_time < self.debounce_time:
            return

        is_pressed = self._read_gpio_pressed(channel)

        if is_pressed:
            self.last_press_time[button_name] = current_time
            self.button_changed.emit(button_name, True)

    def read_button_state(self, button_name):
        if button_name in self.button_pins:
            pin = self.button_pins[button_name]
            current_state = self._read_gpio_pressed(pin)

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