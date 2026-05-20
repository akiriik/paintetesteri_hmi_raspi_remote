# utils/sht20_handler.py
import time
import smbus
from PyQt5.QtCore import QObject, QThread, pyqtSignal

class SHT20Handler(QObject):
    """SHT20 lämpötila- ja kosteus-anturin käsittelijä"""
    sensor_data_ready = pyqtSignal(dict)  # {temperature: float, humidity: float}
    sensor_error = pyqtSignal(str)
    
    def __init__(self, bus_number=1, address=0x40):
        super().__init__()
        self.bus_number = bus_number
        self.address = address
        self.bus = None
        self.connected = False
        self.init_sensor()
    
    def init_sensor(self):
        """Alustaa I2C-yhteyden SHT20-anturiin"""
        try:
            self.bus = smbus.SMBus(self.bus_number)
            # Testaa yhteys lukemalla anturin ID
            self.bus.write_byte(self.address, 0xE7)  # Read user register
            time.sleep(0.1)
            self.bus.read_byte(self.address)
            self.connected = True
            print("SHT20 anturi yhdistetty onnistuneesti")
        except Exception as e:
            self.connected = False
            print(f"SHT20 yhteyden muodostus epäonnistui: {e}")
    
    def trigger_temperature_measurement(self):
        """Käynnistää lämpötilamittauksen (no hold master)"""
        if not self.connected:
            return False
        try:
            self.bus.write_byte(self.address, 0xF3)  # Trigger T measurement (no hold master)
            return True
        except Exception as e:
            print(f"Lämpötilamittauksen käynnistys epäonnistui: {e}")
            return False
    
    def trigger_humidity_measurement(self):
        """Käynnistää kosteusmittauksen (no hold master)"""
        if not self.connected:
            return False
        try:
            self.bus.write_byte(self.address, 0xF5)  # Trigger RH measurement (no hold master)
            return True
        except Exception as e:
            print(f"Kosteusmittauksen käynnistys epäonnistui: {e}")
            return False
    
    def read_measurement_result(self):
        """Lukee mittauksen tuloksen"""
        if not self.connected:
            return None
        try:
            # Yritä lukea suoraan 3 tavua
            data = []
            for i in range(3):
                byte_val = self.bus.read_byte(self.address)
                data.append(byte_val)
            
            if len(data) >= 2:
                # Yhdistä MSB ja LSB, poista status bitit (2 LSB)
                raw_value = (data[0] << 8) | data[1]
                raw_value &= 0xFFFC  # Poista 2 alinta bittiä (status)
                return raw_value
            return None
        except OSError as e:
            if e.errno == 121:  # Remote I/O error
                # Mittaus ei ole vielä valmis, odota hieman
                time.sleep(0.01)
                return None
            print(f"I2C-lukuvirhe: {e}")
            return None
        except Exception as e:
            print(f"Mittauksen lukeminen epäonnistui: {e}")
            return None
    
    def convert_temperature(self, raw_temp):
        """Muuntaa raa'an lämpötila-arvon celsiusasteiksi"""
        if raw_temp is None:
            return None
        return -46.85 + 175.72 * (raw_temp / 65536.0)
    
    def convert_humidity(self, raw_humidity):
        """Muuntaa raa'an kosteus-arvon prosenteiksi"""
        if raw_humidity is None:
            return None
        humidity = -6.0 + 125.0 * (raw_humidity / 65536.0)
        # Rajoita 0-100% välille
        return max(0, min(100, humidity))
    
    def read_temperature_humidity(self):
        """Lukee sekä lämpötilan että kosteuden"""
        if not self.connected:
            self.sensor_error.emit("SHT20 ei ole yhdistetty")
            return
        
        try:
            # Lue lämpötila
            if not self.trigger_temperature_measurement():
                self.sensor_error.emit("Lämpötilamittauksen käynnistys epäonnistui")
                return
            
            # Odota ja yritä lukea tulosta
            raw_temp = None
            for attempt in range(10):  # Yritä max 10 kertaa
                time.sleep(0.01)  # 10ms odotus
                raw_temp = self.read_measurement_result()
                if raw_temp is not None:
                    break
            
            if raw_temp is None:
                self.sensor_error.emit("Lämpötilan lukeminen epäonnistui")
                return
            
            temperature = self.convert_temperature(raw_temp)
            
            # Lue kosteus
            if not self.trigger_humidity_measurement():
                self.sensor_error.emit("Kosteusmittauksen käynnistys epäonnistui")
                return
            
            # Odota ja yritä lukea tulosta
            raw_humidity = None
            for attempt in range(10):  # Yritä max 10 kertaa
                time.sleep(0.01)  # 10ms odotus
                raw_humidity = self.read_measurement_result()
                if raw_humidity is not None:
                    break
            
            if raw_humidity is None:
                self.sensor_error.emit("Kosteuden lukeminen epäonnistui")
                return
            
            humidity = self.convert_humidity(raw_humidity)
            
            # Lähetä tiedot
            sensor_data = {
                'temperature': round(temperature, 1) if temperature is not None else None,
                'humidity': round(humidity, 1) if humidity is not None else None
            }
            
            self.sensor_data_ready.emit(sensor_data)
            
        except Exception as e:
            self.sensor_error.emit(f"SHT20 lukuvirhe: {str(e)}")

class SHT20Worker(QObject):
    """Työntekijäluokka SHT20-lukemiseen taustasäikeessä"""
    data_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.sht20 = SHT20Handler()
        self.sht20.sensor_data_ready.connect(self.data_ready.emit)
        self.sht20.sensor_error.connect(self.error_occurred.emit)
        self.running = False
    
    def start_reading(self):
        """Aloita jatkuva lukeminen"""
        self.running = True
        self.read_sensor_data()
    
    def stop_reading(self):
        """Pysäytä lukeminen"""
        self.running = False
    
    def read_sensor_data(self):
        """Lue anturi kerran"""
        self.sht20.read_temperature_humidity()

class SHT20Manager(QObject):
    """SHT20-anturin manageri"""
    data_updated = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    read_request = pyqtSignal()  # Signaali lukupyynnölle
    
    def __init__(self):
        super().__init__()
        self.thread = QThread()
        self.worker = SHT20Worker()
        
        # Siirrä worker säikeeseen
        self.worker.moveToThread(self.thread)
        
        # Yhdistä signaalit
        self.worker.data_ready.connect(self.data_updated.emit)
        self.worker.error_occurred.connect(self.error_occurred.emit)
        self.read_request.connect(self.worker.read_sensor_data)
        
        # Käynnistä säie
        self.thread.start()
    
    def read_once(self):
        """Lue anturi kerran"""
        self.read_request.emit()
    
    def cleanup(self):
        """Siivoa resurssit"""
        self.worker.stop_reading()
        self.thread.quit()
        self.thread.wait()