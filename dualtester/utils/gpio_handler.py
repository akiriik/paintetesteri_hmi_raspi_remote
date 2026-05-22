# utils/gpio_handler.py

import sys
import os
import RPi.GPIO as GPIO


class GPIOHandler:
    def __init__(self):
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        self._null_device = open(os.devnull, "w")

        sys.stdout = self._null_device
        sys.stderr = self._null_device

        try:
            GPIO.setmode(GPIO.BCM)

            # Ohjelman output-kanava -> Raspberry BCM GPIO
            self.pins = {
                1: 17,  # ForTest 1 LED ON/OFF, ruskea
                2: 27,  # ForTest 1 LED väri / rele, punainen
                3: 22,  # ForTest 2 LED ON/OFF, vihreä
                4: 23,  # ForTest 2 LED väri / rele, harmaa
            }

            for pin in self.pins.values():
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)

        finally:
            sys.stdout = self._original_stdout
            sys.stderr = self._original_stderr

    def set_output(self, output_number, state):
        if output_number not in self.pins:
            return

        sys.stdout = self._null_device
        sys.stderr = self._null_device

        try:
            pin = self.pins[output_number]
            GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)
        finally:
            sys.stdout = self._original_stdout
            sys.stderr = self._original_stderr

    def cleanup(self):
        sys.stdout = self._null_device
        sys.stderr = self._null_device

        try:
            GPIO.cleanup()
        finally:
            sys.stdout = self._original_stdout
            sys.stderr = self._original_stderr
            self._null_device.close()