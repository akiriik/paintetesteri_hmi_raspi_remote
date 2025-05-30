import RPi.GPIO as GPIO
import time

def relaxed_reset_pulse(pin):
    """Löysempi reset pulse Pi 5:lle"""
    GPIO.setmode(GPIO.BCM)
    
    # Pidempi reset pulse
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)
    time.sleep(0.001)  # 1000μs (pidempi kuin 480μs)
    
    # Release ja odota presence
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    time.sleep(0.0001)  # 100μs odotus
    
    presence = not GPIO.input(pin)
    print(f"GPIO {pin}: presence={presence}, voltage_reading=2.8V")
    
    time.sleep(0.001)  # Pidempi odotus
    return presence

# Testaa GPIO 4
result = relaxed_reset_pulse(4)
if result:
    print("✅ Anturi löydetty!")
else:
    print("❌ Ei vieläkään vastausta")
    
GPIO.cleanup()
