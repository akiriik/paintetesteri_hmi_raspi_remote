# utils/modbus_handler.py
from pymodbus.client import ModbusSerialClient


class ModbusHandler:
    """
    Yleinen matalan tason Modbus RTU -käsittelijä.

    Tämä luokka ei tunne Optaa, ForTestiä, rekisterikarttoja,
    releitä, hätäseisejä tai muita laitekohtaisia asioita.

    Laitekohtaiset osoitteet ja komennot kuuluvat ylemmille tasoille:
    - Opta: ModbusManager / HardwareService / config/modbus_config.py
    - ForTest: ForTestHandler / ForTestService / config/fortest_config.py
    """

    def __init__(self, port=None, baudrate=19200):
        if not port:
            raise ValueError("Modbus-portti puuttuu")

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
                parity="N",
                stopbits=1,
                timeout=1,
            )

            self.connected = self.client.connect()
            print(f"Modbus-yhteys ({self.port}): {'Onnistui' if self.connected else 'Epäonnistui'}")

        except Exception as e:
            self.connected = False
            print(f"Modbus-virhe: {e}")

    def write_register(self, address, value):
        """
        Kirjoita arvo Modbus holding registeriin.

        Palauttaa pymodbus-vastausobjektin tai False.
        Ylempi taso päättää, mitä osoite tarkoittaa.
        """
        if not self.connected:
            return False

        try:
            result = self.client.write_register(
                address=address,
                value=value,
            )

            return result

        except Exception as e:
            print(f"Rekisterin kirjoitusvirhe: {e}")
            return False

    def read_holding_registers(self, address, count):
        """
        Lue Modbus holding register -alue.

        Ylempi taso päättää, mitä osoite ja lukumäärä tarkoittavat.
        """
        if not self.connected:
            return None

        try:
            result = self.client.read_holding_registers(
                address=address,
                count=count,
            )

            return result

        except Exception as e:
            print(f"Rekisterien lukuvirhe: {e}")
            return None

    def write_coil(self, address, value):
        """
        Kirjoita Modbus coil.

        Säilytetty vanhan toimivan version mukainen True/False-arvon
        muunnos 0xFF00 / 0x0000 -arvoksi.
        """
        if not self.connected:
            return False

        try:
            if value:
                value_to_write = 0xFF00
            else:
                value_to_write = 0x0000

            result = self.client.write_coil(
                address=address,
                value=value_to_write,
            )

            success = not result.isError() if hasattr(result, "isError") else bool(result)
            return success

        except Exception as e:
            print(f"Coil-kirjoitusvirhe: {e}")
            return False

    def close(self):
        if self.client:
            self.client.close()
