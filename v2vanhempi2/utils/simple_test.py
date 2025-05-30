import RPi.GPIO as GPIO
import time

def test_presence(pin):
    GPIO.setmode(GPIO.BCM)
    
    print(f"Testing GPIO {pin}")
    
    # Reset pulse
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)
    time.sleep(0.0005)  # 500μs reset
    
    # Release and wait for presence
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    time.sleep(0.00007)  # 70μs wait
    
    presence = not GPIO.input(pin)
    print(f"GPIO {pin} presence: {presence}")
    
    time.sleep(0.0005)  # Wait for end
    return presence

# Test different pins
for pin in [4, 18, 22]:
    test_presence(pin)
    time.sleep(0.1)
    
GPIO.cleanup()
