# utils/gpio_handler.py

import RPi.GPIO as GPIO

class GPIOHandler:
    def __init__(self):
        # Aseta GPIO-pinnien numerointi
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
    
    def set_output(self, test_number, state):
        """Aseta GPIO-ulostulo tilan mukaan"""
        if test_number in self.pins:
            pin = self.pins[test_number]
            GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)
            print(f"GPIO {pin} set to {'HIGH' if state else 'LOW'}")
    
    def cleanup(self):
        """Siivoa GPIO-resurssit"""
        GPIO.cleanup()