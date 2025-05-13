# utils/modbus_manager.py
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot, QMetaObject, Qt, Q_ARG
from utils.modbus_handler import ModbusHandler

class ModbusWorker(QObject):
    resultReady = pyqtSignal(object, int, str)  # tulos, operaatiokoodi, virheviesti
    
    def __init__(self, modbus_handler):
        super().__init__()
        self.modbus = modbus_handler
    
    @pyqtSlot(int, int)
    def read_register(self, address, count=1):
        if not self.modbus or not self.modbus.connected:
            self.resultReady.emit(None, 1, "Modbus ei yhteydessä")
            return
            
        try:
            result = self.modbus.read_holding_registers(address, count)
            # Lisää osoite result-objektiin
            if result:
                result.address = address
            self.resultReady.emit(result, 1, "")
        except Exception as e:
            self.resultReady.emit(None, 1, f"Virhe rekisterin lukemisessa: {str(e)}")
    
    @pyqtSlot(int, int)
    def write_register(self, address, value):
        """Kirjoita rekisteri taustasäikeessä"""
        if not self.modbus or not self.modbus.connected:
            self.resultReady.emit(False, 2, "Modbus ei yhteydessä")
            return
            
        try:
            result = self.modbus.write_register(address, value)
            # Lisää osoite tulokseen, jotta voidaan tunnistaa hätäseis-kuittaus
            result.address = address
            self.resultReady.emit(result, 2, "")
        except Exception as e:
            self.resultReady.emit(False, 2, f"Virhe rekisterin kirjoittamisessa: {str(e)}")
    
    @pyqtSlot(int, int)
    def toggle_relay(self, relay_num, state):
        """Releen ohjaus taustasäikeessä"""
        if not self.modbus or not self.modbus.connected:
            self.resultReady.emit(False, 3, "Modbus ei yhteydessä")
            return
            
        try:
            register = 18098 + relay_num
            result = self.modbus.write_register(register, state)
            self.resultReady.emit(result, 3, "")
        except Exception as e:
            self.resultReady.emit(False, 3, f"Virhe releen ohjauksessa: {str(e)}")

class ModbusManager(QObject):
    """Hallinnoi Modbus-operaatioita ja säikeitä"""
    resultReady = pyqtSignal(object, int, str)  # tulos, operaatiokoodi, virheviesti
    
    def __init__(self, port='/dev/ttyUSB0', baudrate=19200):
        super().__init__()
        
        # Luo varsinainen Modbus-käsittelijä
        self.modbus_handler = ModbusHandler(port, baudrate)
        
        # Luo säie ja työluokka
        self.thread = QThread()
        self.worker = ModbusWorker(self.modbus_handler)
        
        # Siirrä työluokka säikeeseen
        self.worker.moveToThread(self.thread)
        
        # Yhdistä signaalit
        self.worker.resultReady.connect(self.handle_result)
        
        # Käynnistä säie
        self.thread.start()
    
    def handle_result(self, result, op_code, error_msg):
        """Välitä tulos eteenpäin"""
        self.resultReady.emit(result, op_code, error_msg)
    
    def read_register(self, address, count=1):
        """Lue rekisteri taustasäikeessä"""
        if not self.modbus_handler.connected:
            self.resultReady.emit(None, 1, "Modbus ei yhteydessä")
            return
        
        # Kutsu työluokan metodia
        QMetaObject.invokeMethod(
            self.worker, 
            "read_register",
            Qt.QueuedConnection, 
            Q_ARG(int, address), 
            Q_ARG(int, count)
        )
    
    def write_register(self, address, value):
        """Kirjoita rekisteri taustasäikeessä"""
        if not self.modbus_handler.connected:
            self.resultReady.emit(False, 2, "Modbus ei yhteydessä")
            return
            
        QMetaObject.invokeMethod(
            self.worker, 
            "write_register",
            Qt.QueuedConnection, 
            Q_ARG(int, address), 
            Q_ARG(int, value)
        )
    
    def read_emergency_stop_status(self):
        """Lue hätäseispiirin tila"""
        if not self.modbus_handler.connected:
            return None
        
        # Lue rekisteri synkronisesti heti (ei taustasäikeessä)
        try:
            result = self.modbus_handler.read_holding_registers(19100, 1)
            if result and hasattr(result, 'registers') and len(result.registers) > 0:
                return result.registers[0]
            return None
        except Exception as e:
            return None

    def toggle_relay(self, relay_num, state):
        """Releen ohjaus taustasäikeessä"""
        if not self.modbus_handler.connected:
            self.resultReady.emit(False, 3, "Modbus ei yhteydessä")
            return
            
        QMetaObject.invokeMethod(
            self.worker, 
            "toggle_relay",
            Qt.QueuedConnection, 
            Q_ARG(int, relay_num), 
            Q_ARG(int, state)
        )
    
    def is_connected(self):
        """Palauta yhteyden tila"""
        return self.modbus_handler.connected
    
    def cleanup(self):
        """Siivoa resurssit"""
        self.thread.quit()
        self.thread.wait()
        if self.modbus_handler:
            self.modbus_handler.close()