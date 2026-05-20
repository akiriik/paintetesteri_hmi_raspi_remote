# utils/gpio_handler.py

import sys
import os
import RPi.GPIO as GPIO

class GPIOHandler:
    def __init__(self):
        # Ohjaa kaikki mahdolliset GPIO-tulosteet /dev/null -laitteeseen
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        self._null_device = open(os.devnull, 'w')
        
        # Aseta GPIO-pinnien numerointi
        sys.stdout = self._null_device
        sys.stderr = self._null_device
        try:
            GPIO.setmode(GPIO.BCM)
            
            # Määritä käytettävät pinnit
            self.pins = {
                1: 17,  # PAINE1 -> GPIO17
                2: 27,  # PAINE2 -> GPIO27
                3: 22,  # PAINE3 -> GPIO22
                4: 23,   # Ylimääräinen -> GPIO23
                5: 24   # Uusi ylimääräinen -> GPIO24
            }
            
            # Alusta pinnit ulostuloksi
            for pin in self.pins.values():
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.LOW)  # Aseta aluksi LOW-tilaan
        finally:
            # Palauta tulosteet
            sys.stdout = self._original_stdout
            sys.stderr = self._original_stderr
    
    def set_output(self, test_number, state):
        """Aseta GPIO-ulostulo tilan mukaan"""
        if test_number in self.pins:
            sys.stdout = self._null_device
            sys.stderr = self._null_device
            try:
                pin = self.pins[test_number]
                GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)
            finally:
                sys.stdout = self._original_stdout
                sys.stderr = self._original_stderr
    
    def cleanup(self):
        """Siivoa GPIO-resurssit"""
        sys.stdout = self._null_device
        sys.stderr = self._null_device
        try:
            GPIO.cleanup()
        finally:
            sys.stdout = self._original_stdout
            sys.stderr = self._original_stderr
            self._null_device.close()