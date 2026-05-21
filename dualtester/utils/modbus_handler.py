# utils/modbus_handler.py
from pymodbus.client import ModbusSerialClient

from config.modbus_config import (
    EMERGENCY_STATUS_REGISTER,
    EMERGENCY_STATUS_REGISTER_COUNT,
    OPTA_RELAY_REGISTER_BASE,
)


class ModbusHandler:
    """
    Matalan tason Modbus RTU -käsittelijä.

    Tätä käytetään sekä Optan että ForTestin Modbus-yhteyksissä.
    Siksi tänne ei pidä laittaa laitekohtaisia fyysisiä portteja.
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

    def read_emergency_stop_status(self):
        """
        Lue hätäseispiirin tila Optan rekisteristä.

        Huom:
        Tämä metodi on Opta-kohtainen yhteensopivuusmetodi.
        Uusi ylempi koodi lukee tämän yleensä ModbusManagerin kautta.
        """
        if not self.connected:
            return None

        try:
            result = self.client.read_holding_registers(
                address=EMERGENCY_STATUS_REGISTER,
                count=EMERGENCY_STATUS_REGISTER_COUNT,
            )

            if result and hasattr(result, "registers") and len(result.registers) > 0:
                return result.registers[0]

            return None

        except Exception as e:
            print(f"Hätäseispiirin lukuvirhe: {e}")
            return None

    def write_register(self, address, value):
        """
        Kirjoita arvo rekisteriin.
        """
        if not self.connected:
            return False

        try:
            result = self.client.write_register(
                address=address,
                value=value,
            )

            return result.isError() == False if hasattr(result, "isError") else bool(result)

        except Exception as e:
            print(f"Rekisterin kirjoitusvirhe: {e}")
            return False

    def toggle_relay(self, relay_num, state):
        """
        Optan releohjaus.

        relay_num = 1...8
        """
        if not self.connected:
            return False

        try:
            register = OPTA_RELAY_REGISTER_BASE + relay_num

            print(f"Ohjataan relettä {relay_num}, rekisteri {register}, tila {state}")

            result = self.client.write_register(
                address=register,
                value=state,
            )

            return result.isError() == False if hasattr(result, "isError") else bool(result)

        except Exception as e:
            print(f"Releen ohjausvirhe: {e}")
            return False

    def read_holding_registers(self, address, count):
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

            result = self.client.write_coil(
                address=address,
                value=value_to_write,
            )

            success = not result.isError() if hasattr(result, "isError") else bool(result)
            print(f"write_coil tulos: {result}, onnistui: {success}")

            return success

        except Exception as e:
            print(f"Coil-kirjoitusvirhe: {e}")
            return False

    def close(self):
        if self.client:
            self.client.close()