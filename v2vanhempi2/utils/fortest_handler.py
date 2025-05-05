# utils/fortest_handler.py
from utils.modbus_handler import ModbusHandler

class ForTestHandler:
    def __init__(self, port='/dev/ttyUSB1', baudrate=19200):
        self.modbus = ModbusHandler(port=port, baudrate=baudrate)
        
    def start_test(self):
        """Start test command (0x0A)"""
        return self.modbus.write_coil(0x0A, True)
    
    def abort_test(self):
        """Abort test command (0x14)"""
        return self.modbus.write_coil(0x14, True)
    
    def read_status(self):
        """Read device status (0x0030)"""
        return self.modbus.read_holding_registers(0x0030, 32)
    
    def read_results(self):
        """Read test results (0x0040)"""
        return self.modbus.read_holding_registers(0x0040, 32)

class DummyForTestHandler:
    def start_test(self):
        print("DummyForTest: Testi käynnistetty (ei oikeaa laitetta)")
        return True
    
    def abort_test(self):
        print("DummyForTest: Testi pysäytetty (ei oikeaa laitetta)")
        return True
    
    def read_status(self):
        return None
    
    def read_results(self):
        return None