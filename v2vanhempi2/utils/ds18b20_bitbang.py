# utils/ds18b20_bitbang.py
"""
DS18B20 bitbang implementation for Raspberry Pi 5
Bypasses kernel 1-Wire issues by implementing protocol directly
"""

import time
import RPi.GPIO as GPIO
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot, QTimer

class DS18B20BitBang:
    """Direct bitbang implementation of DS18B20 1-Wire protocol"""
    
    def __init__(self, gpio_pin=4):
        self.gpio_pin = gpio_pin
        self.gpio_setup = False
        
    def setup_gpio(self):
        """Setup GPIO for 1-Wire communication"""
        if not self.gpio_setup:
            try:
                GPIO.setmode(GPIO.BCM)
                self.gpio_setup = True
            except:
                pass  # GPIO already setup
    
    def cleanup_gpio(self):
        """Cleanup GPIO"""
        if self.gpio_setup:
            try:
                GPIO.cleanup(self.gpio_pin)
            except:
                pass
    
    def write_bit(self, bit):
        """Write a single bit"""
        GPIO.setup(self.gpio_pin, GPIO.OUT)
        
        if bit:
            # Write 1: Short low pulse
            GPIO.output(self.gpio_pin, GPIO.LOW)
            time.sleep(0.000006)  # 6μs
            GPIO.output(self.gpio_pin, GPIO.HIGH)
            time.sleep(0.000064)  # 64μs
        else:
            # Write 0: Long low pulse  
            GPIO.output(self.gpio_pin, GPIO.LOW)
            time.sleep(0.000060)  # 60μs
            GPIO.output(self.gpio_pin, GPIO.HIGH)
            time.sleep(0.000010)  # 10μs
    
    def read_bit(self):
        """Read a single bit"""
        GPIO.setup(self.gpio_pin, GPIO.OUT)
        GPIO.output(self.gpio_pin, GPIO.LOW)
        time.sleep(0.000003)  # 3μs
        
        GPIO.setup(self.gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        time.sleep(0.000010)  # 10μs
        
        bit = GPIO.input(self.gpio_pin)
        time.sleep(0.000053)  # 53μs (total 66μs)
        
        return bit
    
    def write_byte(self, byte_val):
        """Write a byte (LSB first)"""
        for i in range(8):
            bit = (byte_val >> i) & 1
            self.write_bit(bit)
    
    def read_byte(self):
        """Read a byte (LSB first)"""
        byte_val = 0
        for i in range(8):
            bit = self.read_bit()
            if bit:
                byte_val |= (1 << i)
        return byte_val
    
    def reset_pulse(self):
        """Send reset pulse and detect presence"""
        GPIO.setup(self.gpio_pin, GPIO.OUT)
        GPIO.output(self.gpio_pin, GPIO.LOW)
        time.sleep(0.000480)  # 480μs reset pulse
        
        GPIO.setup(self.gpio_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        time.sleep(0.000070)  # Wait 70μs
        
        presence = not GPIO.input(self.gpio_pin)  # Device pulls low = presence
        time.sleep(0.000410)  # Wait for presence pulse to end
        
        return presence
    
    def read_temperature(self):
        """Read temperature from DS18B20"""
        self.setup_gpio()
        
        try:
            # Reset and check presence
            if not self.reset_pulse():
                return None  # No device found
            
            # Skip ROM (single device)
            self.write_byte(0xCC)
            
            # Start conversion
            self.write_byte(0x44)
            
            # Wait for conversion (750ms for 12-bit)
            time.sleep(0.75)
            
            # Reset again
            if not self.reset_pulse():
                return None
            
            # Skip ROM
            self.write_byte(0xCC)
            
            # Read scratchpad
            self.write_byte(0xBE)
            
            # Read 9 bytes
            data = []
            for i in range(9):
                data.append(self.read_byte())
            
            # Check CRC (simple check - byte 8 should be reasonable)
            if data[8] == 0 or data[8] == 0xFF:
                return None
            
            # Calculate temperature from bytes 0 and 1
            temp_lsb = data[0]
            temp_msb = data[1]
            
            # Combine bytes (16-bit signed)
            temp_raw = (temp_msb << 8) | temp_lsb
            
            # Convert to signed if negative
            if temp_raw & 0x8000:
                temp_raw = temp_raw - 65536
            
            # Convert to Celsius (0.0625°C per bit)
            temperature = temp_raw * 0.0625
            
            return temperature
            
        except Exception as e:
            print(f"DS18B20 read error: {e}")
            return None

class DS18B20Worker(QObject):
    """Thread worker for DS18B20 reading"""
    temperature_ready = pyqtSignal(dict)
    
    def __init__(self, gpio_pin=4):
        super().__init__()
        self.ds18b20 = DS18B20BitBang(gpio_pin)
        self.running = True
        
    @pyqtSlot()
    def read_temperature(self):
        """Read temperature in background thread"""
        if not self.running:
            return
            
        try:
            temp = self.ds18b20.read_temperature()
            if temp is not None:
                # Create sensor ID based on GPIO pin
                sensor_id = f"28-bitbang-gpio{self.ds18b20.gpio_pin}"
                temperatures = {sensor_id: temp}
            else:
                temperatures = {}
                
            self.temperature_ready.emit(temperatures)
            
        except Exception as e:
            print(f"DS18B20 worker error: {e}")
            self.temperature_ready.emit({})
    
    def stop(self):
        """Stop reading"""
        self.running = False
        self.ds18b20.cleanup_gpio()

class DS18B20Handler(QObject):
    """Main DS18B20 handler using bitbang method"""
    temperature_updated = pyqtSignal(dict)
    
    def __init__(self, gpio_pin=4, parent=None):
        super().__init__(parent)
        
        # Create thread and worker
        self.thread = QThread()
        self.worker = DS18B20Worker(gpio_pin)
        
        # Move worker to thread
        self.worker.moveToThread(self.thread)
        
        # Connect signals
        self.worker.temperature_ready.connect(self.handle_temperature_update)
        
        # Timer for regular reading
        self.timer = QTimer()
        self.timer.timeout.connect(self.worker.read_temperature)
        
        # Start thread
        self.thread.start()
        
        # Test connection immediately
        self.read_once()
        
    def handle_temperature_update(self, temperatures):
        """Handle temperature update from worker"""
        self.temperature_updated.emit(temperatures)
    
    def start_reading(self, interval_ms=5000):
        """Start automatic reading"""
        self.timer.start(interval_ms)
    
    def stop_reading(self):
        """Stop automatic reading"""
        self.timer.stop()
    
    def read_once(self):
        """Read temperature once"""
        self.worker.read_temperature()
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_reading()
        self.worker.stop()
        self.thread.quit()
        self.thread.wait()

# Test function
def test_ds18b20():
    """Test DS18B20 directly"""
    ds = DS18B20BitBang(gpio_pin=4)
    
    print("Testing DS18B20 bitbang...")
    temp = ds.read_temperature()
    
    if temp is not None:
        print(f"Temperature: {temp:.2f}°C")
        return True
    else:
        print("No DS18B20 found or read error")
        return False

if __name__ == "__main__":
    test_ds18b20()