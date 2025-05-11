# utils/gpio_input_handler.py

import sys
import os
import time
import RPi.GPIO as GPIO
from PyQt5.QtCore import QObject, pyqtSignal

class GPIOInputHandler(QObject):
    """Hallinnoi GPIO-sisääntuloja nappuloita varten"""
    button_changed = pyqtSignal(str, bool)  # signal: button_name, is_pressed
    
    def __init__(self):
        super().__init__()
        # Ohjaa kaikki mahdolliset GPIO-tulosteet /dev/null -laitteeseen
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        self._null_device = open(os.devnull, 'w')
        
        # Aseta GPIO-pinnien numerointi
        sys.stdout = self._null_device
        sys.stderr = self._null_device
        
        try:
            GPIO.setmode(GPIO.BCM)
            
            # Määritä nappien pinnit
            self.button_pins = {
                "START": 5,   # GPIO 5 (START-kytkin)
                "STOP": 6,    # GPIO 6 (STOP-kytkin)
                "TEST1": 12,  # GPIO 12 (TEST1-kytkin)
                "TEST2": 13,  # GPIO 13 (TEST2-kytkin)
                "TEST3": 16   # GPIO 16 (TEST3-kytkin)
            }
            
            # Alusta pinnit sisääntuloiksi pullup-vastuksilla
            for pin in self.button_pins.values():
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Tallenna nappien tilat ja ajastimet
            self.button_states = {button: False for button in self.button_pins}
            self.last_press_time = {button: 0 for button in self.button_pins}
            self.debounce_time = 200  # 200ms debounce aika
            
            # Lue alkutilat
            for button, pin in self.button_pins.items():
                self.button_states[button] = not GPIO.input(pin)
                
            # Lisää vain yksi tapahtumakäsittelijä jokaiselle napille
            for button_name, pin in self.button_pins.items():
                GPIO.add_event_detect(
                    pin, 
                    GPIO.BOTH,  # Tarkkaile molempia reunoja
                    callback=lambda channel, btn=button_name: self._button_callback(btn, channel),
                    bouncetime=100  # Lyhyempi bouncetime, sillä käsittelemme debounce-logiikan itse
                )
                
        finally:
            # Palauta tulosteet
            sys.stdout = self._original_stdout
            sys.stderr = self._original_stderr
    
    def _button_callback(self, button_name, channel):
        """Käsittele napin painallus reagoiden vain laskevaan reunaan"""
        current_time = time.time() * 1000  # millisekunteina
        last_time = self.last_press_time[button_name]
        
        # Tarkista onko debounce-aika kulunut
        if current_time - last_time < self.debounce_time:
            return
            
        # Lue pinnin tila (aktiivinen alhaalla, joten käännä logiikka)
        is_pressed = not GPIO.input(channel)
        
        # Reagoi vain painallukseen (laskeva reuna, nappi painettu alas)
        if is_pressed:
            # Päivitä viimeinen painallus aika
            self.last_press_time[button_name] = current_time
            
            # Lähetä signaali napista riippumatta edellisestä tilasta
            self.button_changed.emit(button_name, True)
    
    def read_button_state(self, button_name):
        """Lue napin tämänhetkinen tila"""
        if button_name in self.button_pins:
            # Lue nykyinen tila pinnistä
            pin = self.button_pins[button_name]
            current_state = not GPIO.input(pin)  # Käänteinen logiikka (aktiivinen alhaalla)
            
            # Päivitä tallennettu tila vain jos eri
            if current_state != self.button_states[button_name]:
                self.button_states[button_name] = current_state
                
            return self.button_states[button_name]
        return False
    
    def cleanup(self):
        """Siivoa GPIO-resurssit"""
        sys.stdout = self._null_device
        sys.stderr = self._null_device
        try:
            # Poista tapahtumakäsittelijät
            for pin in self.button_pins.values():
                GPIO.remove_event_detect(pin)
                
            # Nollaa GPIO-asetukset
            GPIO.cleanup()
        finally:
            sys.stdout = self._original_stdout
            sys.stderr = self._original_stderr
            self._null_device.close()