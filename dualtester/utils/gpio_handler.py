# utils/gpio_handler.py
import RPi.GPIO as GPIO


class GPIOHandler:
    """Raspberryn fyysisten nappivalojen GPIO-ohjaus."""

    def __init__(self):
        # Älä muuta sys.stdout/sys.stderr -globaaleja tiedostovirtoja:
        # muut säikeet voivat kirjoittaa lokia samanaikaisesti.
        GPIO.setmode(GPIO.BCM)
        self.pins = {
            1: 17,  # ForTest 1 LED ON/OFF, ruskea
            2: 27,  # ForTest 1 LED väri / rele, punainen
            3: 22,  # ForTest 2 LED ON/OFF, vihreä
            4: 23,  # ForTest 2 LED väri / rele, harmaa
        }

        for pin in self.pins.values():
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

    def set_output(self, output_number, state):
        pin = self.pins.get(output_number)
        if pin is None:
            return
        GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)

    def cleanup(self):
        GPIO.cleanup()
