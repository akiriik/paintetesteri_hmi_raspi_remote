# utils/modbus_handler.py
import time
from threading import RLock

from pymodbus.client import ModbusSerialClient


class ModbusHandler:
    """
    Yleinen Modbus RTU -sarjaliikenne.

    ModbusManager (Opta) käyttää auto_reconnect=True.
    ForTestHandler hoitaa oman reconnectinsa, joten se käyttää oletusta
    auto_reconnect=False. Kaikki clientin avaukset, sulut, luvut ja
    kirjoitukset ovat saman RLockin sisällä.
    """

    RECONNECT_INTERVAL_S = 2.0
    MAX_TRANSPORT_ERRORS = 2

    def __init__(self, port=None, baudrate=19200, auto_reconnect=False):
        if not port:
            raise ValueError("Modbus-portti puuttuu")

        self.port = port
        self.baudrate = baudrate
        self.auto_reconnect = bool(auto_reconnect)
        self.client = None
        self.connected = False
        self._io_lock = RLock()
        self._next_reconnect_at = 0.0
        self._consecutive_transport_errors = 0

        self.setup_modbus()

    def _close_locked(self):
        if self.client:
            try:
                self.client.close()
            except Exception as e:
                print(f"Modbus {self.port}: sulkuvirhe {e}")
        self.client = None
        self.connected = False

    def _connect_locked(self):
        self._close_locked()

        try:
            self.client = ModbusSerialClient(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=8,
                parity="N",
                stopbits=1,
                timeout=1,
            )
            self.connected = bool(self.client.connect())
        except Exception as e:
            print(f"Modbus {self.port}: avausvirhe {e}")
            self.connected = False

        if self.connected:
            self._next_reconnect_at = 0.0
            self._consecutive_transport_errors = 0
            print(f"Modbus-yhteys ({self.port}): Onnistui")
        else:
            self._next_reconnect_at = (
                time.monotonic() + self.RECONNECT_INTERVAL_S
            )
            print(f"Modbus-yhteys ({self.port}): Ei yhteyttä")

        return self.connected

    def setup_modbus(self):
        with self._io_lock:
            return self._connect_locked()

    def _ensure_connected_locked(self):
        if self.connected:
            return True

        if not self.auto_reconnect:
            return False

        if time.monotonic() < self._next_reconnect_at:
            return False

        print(f"Modbus {self.port}: reconnect-yritys")
        return self._connect_locked()

    def _record_transport_failure_locked(self):
        if not self.auto_reconnect:
            return

        self._consecutive_transport_errors += 1

        if self._consecutive_transport_errors < self.MAX_TRANSPORT_ERRORS:
            return

        print(
            f"Modbus {self.port}: {self.MAX_TRANSPORT_ERRORS} "
            "peräkkäistä siirtovirhettä, suljetaan yhteys"
        )
        self._close_locked()
        self._next_reconnect_at = (
            time.monotonic() + self.RECONNECT_INTERVAL_S
        )

    def _record_response_locked(self, response):
        if response is None or response is False:
            self._record_transport_failure_locked()
        else:
            # ForTest palauttaa itse virheen ylätason ForTestHandlerille.
            # Vastaanotettu Modbus-poikkeusvastaukseen ei liity USB-katkoon.
            self._consecutive_transport_errors = 0
        return response

    def write_register(self, address, value):
        with self._io_lock:
            if not self._ensure_connected_locked():
                return False

            try:
                result = self.client.write_register(
                    address=address, value=value
                )
                return self._record_response_locked(result)
            except Exception as e:
                print(f"Rekisterin kirjoitusvirhe ({self.port}): {e}")
                self._record_transport_failure_locked()
                return False

    def read_holding_registers(self, address, count):
        with self._io_lock:
            if not self._ensure_connected_locked():
                return None

            try:
                result = self.client.read_holding_registers(
                    address=address, count=count
                )
                return self._record_response_locked(result)
            except Exception as e:
                print(f"Rekisterien lukuvirhe ({self.port}): {e}")
                self._record_transport_failure_locked()
                return None

    def write_coil(self, address, value):
        # Säilytetään vanha ForTestin 0xFF00 / 0x0000 -koodaus.
        value_to_write = 0xFF00 if value else 0x0000

        with self._io_lock:
            if not self._ensure_connected_locked():
                return False

            try:
                result = self.client.write_coil(
                    address=address, value=value_to_write
                )
                self._record_response_locked(result)
                return (
                    not result.isError()
                    if hasattr(result, "isError")
                    else bool(result)
                )
            except Exception as e:
                print(f"Coil-kirjoitusvirhe ({self.port}): {e}")
                self._record_transport_failure_locked()
                return False

    def close(self):
        with self._io_lock:
            self._close_locked()
