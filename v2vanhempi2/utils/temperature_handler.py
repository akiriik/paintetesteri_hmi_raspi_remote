# utils/temperature_handler.py
import os
import glob
import time
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot, QTimer

class TemperatureWorker(QObject):
    """Taustasäikeessä toimiva lämpötilanlukija"""
    temperature_ready = pyqtSignal(dict)  # {sensor_id: temperature}
    
    def __init__(self):
        super().__init__()
        self.base_dir = '/sys/bus/w1/devices/'
        self.running = True
        
    def scan_sensors(self):
        """Etsi kaikki DS18B20 anturit"""
        try:
            return glob.glob(self.base_dir + '28*')
        except Exception as e:
            print(f"Virhe anturien skannauksessa: {e}")
            return []
    
    def read_raw_data(self, device_file):
        """Lue raakadata anturilta"""
        try:
            with open(device_file, 'r') as f:
                lines = f.readlines()
            return lines
        except Exception as e:
            print(f"Virhe tiedoston lukemisessa {device_file}: {e}")
            return None
    
    def parse_temperature(self, lines):
        """Parsii lämpötilan raakadatasta"""
        if not lines or len(lines) < 2:
            return None
            
        # Tarkista CRC
        if not lines[0].strip().endswith('YES'):
            return None
            
        # Etsi lämpötilatieto
        temp_line = lines[1]
        temp_pos = temp_line.find('t=')
        if temp_pos == -1:
            return None
            
        try:
            temp_string = temp_line[temp_pos + 2:]
            temp_c = float(temp_string) / 1000.0
            return temp_c
        except ValueError:
            return None
    
    @pyqtSlot()
    def read_temperatures(self):
        """Lue kaikkien anturien lämpötilat"""
        if not self.running:
            return
            
        temperatures = {}
        device_folders = self.scan_sensors()
        
        for folder in device_folders:
            device_id = os.path.basename(folder)
            device_file = os.path.join(folder, 'w1_slave')
            
            lines = self.read_raw_data(device_file)
            if lines:
                temp = self.parse_temperature(lines)
                if temp is not None:
                    temperatures[device_id] = temp
                else:
                    temperatures[device_id] = "VIRHE"
            else:
                temperatures[device_id] = "EI YHTEYTTÄ"
        
        self.temperature_ready.emit(temperatures)
    
    def stop(self):
        """Pysäytä lukeminen"""
        self.running = False

class TemperatureHandler(QObject):
    """Lämpötila-anturien hallinta"""
    temperature_updated = pyqtSignal(dict)  # {sensor_id: temperature}
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Luo säie ja työluokka
        self.thread = QThread()
        self.worker = TemperatureWorker()
        
        # Siirrä työluokka säikeeseen
        self.worker.moveToThread(self.thread)
        
        # Yhdistä signaalit
        self.worker.temperature_ready.connect(self.handle_temperature_update)
        
        # Ajastin säännölliseen lukemiseen
        self.timer = QTimer()
        self.timer.timeout.connect(self.worker.read_temperatures)
        
        # Käynnistä säie
        self.thread.start()
        
        # Käynnistä automaattinen lukeminen (5 sekunnin välein)
        self.start_reading(5000)
    
    def handle_temperature_update(self, temperatures):
        """Käsittele lämpötilapäivitys"""
        self.temperature_updated.emit(temperatures)
    
    def start_reading(self, interval_ms=5000):
        """Käynnistä automaattinen lukeminen"""
        self.timer.start(interval_ms)
    
    def stop_reading(self):
        """Pysäytä automaattinen lukeminen"""
        self.timer.stop()
    
    def read_once(self):
        """Lue lämpötilat kerran"""
        self.worker.read_temperatures()
    
    def cleanup(self):
        """Siivoa resurssit"""
        self.stop_reading()
        self.worker.stop()
        self.thread.quit()
        self.thread.wait()

# Dummy-versio testikäyttöön jos ei ole antureita
class DummyTemperatureHandler(QObject):
    """Väliaikainen dummy-versio testikäyttöön"""
    temperature_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = QTimer()
        self.timer.timeout.connect(self.generate_dummy_data)
        
    def generate_dummy_data(self):
        """Luo keinotekoista dataa testausta varten"""
        import random
        dummy_temps = {
            "28-dummy001": round(20 + random.uniform(-2, 5), 1),
            "28-dummy002": round(22 + random.uniform(-1, 3), 1)
        }
        self.temperature_updated.emit(dummy_temps)
    
    def start_reading(self, interval_ms=5000):
        self.timer.start(interval_ms)
    
    def stop_reading(self):
        self.timer.stop()
    
    def read_once(self):
        self.generate_dummy_data()
    
    def cleanup(self):
        self.timer.stop()