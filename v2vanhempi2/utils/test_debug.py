from ds18b20_bitbang import DS18B20BitBang
import RPi.GPIO as GPIO

ds = DS18B20BitBang(gpio_pin=4)
ds.setup_gpio()

print("Testing reset pulse...")
presence = ds.reset_pulse()
print(f"Presence detected: {presence}")

if presence:
    print("Device found! Trying to read...")
    ds.write_byte(0xCC)  # Skip ROM
    ds.write_byte(0x44)  # Convert T
    print("Conversion started, waiting...")
else:
    print("No device response")
    
    # Test GPIO manually
    print("Manual GPIO test:")
    GPIO.setup(4, GPIO.OUT)
    GPIO.output(4, GPIO.LOW)
    print("GPIO 4 set LOW")
    
    GPIO.setup(4, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    state = GPIO.input(4)
    print(f"GPIO 4 reads: {state}")
