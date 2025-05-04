from pymodbus.client import ModbusSerialClient

class ModbusHandler:
    def __init__(self, port='/dev/ttyUSB0', baudrate=19200):
        self.port = port
        self.baudrate = baudrate
        self.client = None
        self.connected = False
        self.setup_modbus()
        
    def setup_modbus(self):
        try:
            self.client = ModbusSerialClient(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=1.0
            )
            self.connected = self.client.connect()
            print(f"Modbus-yhteys ({self.port}): {'Onnistui' if self.connected else 'Epäonnistui'}")
        except Exception as e:
            self.connected = False
            print(f"Modbus-virhe: {e}")
            
    def toggle_relay(self, relay_num, state):
        if not self.connected:
            return False
        try:
            register = 18098 + relay_num
            print(f"Ohjataan relettä {relay_num}, rekisteri {register}, tila {state}")
            # Poistettu unit parametri
            result = self.client.write_register(address=register, value=state)
            return result.isError() == False if hasattr(result, 'isError') else bool(result)
        except Exception as e:
            print(f"Releen ohjausvirhe: {e}")
            return False
    
    def read_holding_registers(self, address, count):
        if not self.connected:
            return None
        try:
            # Poistettu unit parametri
            result = self.client.read_holding_registers(address=address, count=count)
            return result
        except Exception as e:
            print(f"Rekisterien lukuvirhe: {e}")
            return None
    
    def write_coil(self, address, value):
        if not self.connected:
            print(f"Modbus ei yhteydessä. Ei voida kirjoittaa coiliin {address}")
            return False
        try:
            print(f"write_coil - Address: {address}, Value: {value}")
            
            # ForTest manuaalin mukaan coil-komennossa pitää käyttää arvoa 0xFF00 (True)
            if value:
                value_to_write = 0xFF00
            else:
                value_to_write = 0x0000
                
            # Poistettu unit parametri
            result = self.client.write_coil(address=address, value=value_to_write)
            
            # Tarkista tulos
            success = not result.isError() if hasattr(result, 'isError') else bool(result)
            print(f"write_coil tulos: {result}, onnistui: {success}")
            
            return success
        except Exception as e:
            print(f"Coil-kirjoitusvirhe: {e}")
            return False
    
    def close(self):
        if self.client:
            self.client.close()