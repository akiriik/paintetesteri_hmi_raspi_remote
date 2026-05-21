# utils/modbus_manager.py
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot, QMetaObject, Qt, Q_ARG

from config.modbus_config import (
    EMERGENCY_STATUS_REGISTER,
    EMERGENCY_STATUS_REGISTER_COUNT,
    OPTA_RELAY_REGISTER_BASE,
)

from utils.modbus_handler import ModbusHandler


class ModbusResultWrapper:
    """
    Pieni wrapper Modbus-vastausobjektille.

    Tavoite:
    - säilyttää pymodbus-vastauksen ominaisuudet
    - lisätä mukaan rekisteriosoite
    - tarjota isError()-metodi ModbusResultControllerille

    Tätä käytetään erityisesti siksi, että kirjoitustuloksista pitää voida
    tunnistaa esim. hätäseis-kuittausrekisteri.
    """

    def __init__(self, raw_result, address=None):
        self.raw_result = raw_result
        self.address = address

    def isError(self):
        if hasattr(self.raw_result, "isError"):
            return self.raw_result.isError()

        return not bool(self.raw_result)

    def __bool__(self):
        if self.raw_result is None:
            return False

        if self.isError():
            return False

        return True

    def __getattr__(self, name):
        return getattr(self.raw_result, name)


class ModbusWorker(QObject):
    resultReady = pyqtSignal(object, int, str)  # tulos, operaatiokoodi, virheviesti

    def __init__(self, modbus_handler):
        super().__init__()
        self.modbus = modbus_handler

    def _wrap_result(self, result, address=None):
        if result is None:
            return None

        return ModbusResultWrapper(
            raw_result=result,
            address=address,
        )

    @pyqtSlot(int, int)
    def read_register(self, address, count=1):
        if not self.modbus or not self.modbus.connected:
            self.resultReady.emit(None, 1, "Modbus ei yhteydessä")
            return

        try:
            result = self.modbus.read_holding_registers(address, count)
            wrapped_result = self._wrap_result(result, address)

            self.resultReady.emit(wrapped_result, 1, "")

        except Exception as e:
            self.resultReady.emit(None, 1, f"Virhe rekisterin lukemisessa: {str(e)}")

    @pyqtSlot(int, int)
    def write_register(self, address, value):
        """
        Kirjoita rekisteri taustasäikeessä.
        """
        if not self.modbus or not self.modbus.connected:
            self.resultReady.emit(False, 2, "Modbus ei yhteydessä")
            return

        try:
            result = self.modbus.write_register(address, value)
            wrapped_result = self._wrap_result(result, address)

            self.resultReady.emit(wrapped_result, 2, "")

        except Exception as e:
            self.resultReady.emit(False, 2, f"Virhe rekisterin kirjoittamisessa: {str(e)}")

    @pyqtSlot(int, int)
    def toggle_relay(self, relay_num, state):
        """
        Optan releen ohjaus taustasäikeessä.

        relay_num = 1...8
        register = OPTA_RELAY_REGISTER_BASE + relay_num
        """
        if not self.modbus or not self.modbus.connected:
            self.resultReady.emit(False, 3, "Modbus ei yhteydessä")
            return

        try:
            register = OPTA_RELAY_REGISTER_BASE + relay_num
            result = self.modbus.write_register(register, state)
            wrapped_result = self._wrap_result(result, register)

            self.resultReady.emit(wrapped_result, 3, "")

        except Exception as e:
            self.resultReady.emit(False, 3, f"Virhe releen ohjauksessa: {str(e)}")


class ModbusManager(QObject):
    """
    Arduino Optan Modbus-manageri.

    Tämä manageri käyttää yleistä ModbusHandleria, mutta tämän luokan
    julkiset metodit ovat Opta-käyttöön sovitettuja:
    - read_emergency_stop_status()
    - toggle_relay()
    - write_register()
    - read_register()

    ForTest-laitteet eivät käytä tätä manageria, vaan ForTestService /
    ForTestHandler -polkua.
    """

    resultReady = pyqtSignal(object, int, str)  # tulos, operaatiokoodi, virheviesti

    def __init__(self, port=None, baudrate=19200):
        super().__init__()

        if not port:
            raise ValueError("Opta Modbus -portti puuttuu")

        self.port = port
        self.baudrate = baudrate

        self.modbus_handler = ModbusHandler(
            port=self.port,
            baudrate=self.baudrate,
        )

        self.thread = QThread()
        self.worker = ModbusWorker(self.modbus_handler)

        self.worker.moveToThread(self.thread)
        self.worker.resultReady.connect(self.handle_result)

        self.thread.start()

    def handle_result(self, result, op_code, error_msg):
        """
        Välitä tulos eteenpäin.
        """
        self.resultReady.emit(result, op_code, error_msg)

    def read_register(self, address, count=1):
        """
        Lue rekisteri taustasäikeessä.

        Tätä käytetään vain Opta-väylän yleisiin lukuihin.
        """
        if not self.modbus_handler.connected:
            self.resultReady.emit(None, 1, "Modbus ei yhteydessä")
            return

        QMetaObject.invokeMethod(
            self.worker,
            "read_register",
            Qt.QueuedConnection,
            Q_ARG(int, address),
            Q_ARG(int, count),
        )

    def write_register(self, address, value):
        """
        Kirjoita rekisteri taustasäikeessä.

        Tätä käytetään Opta-väylän yksittäisiin rekisterikirjoituksiin.
        """
        if not self.modbus_handler.connected:
            self.resultReady.emit(False, 2, "Modbus ei yhteydessä")
            return

        QMetaObject.invokeMethod(
            self.worker,
            "write_register",
            Qt.QueuedConnection,
            Q_ARG(int, address),
            Q_ARG(int, value),
        )

    def read_emergency_stop_status(self):
        """
        Lue hätäseispiirin tila Optan Modbus-väylältä.

        Palautus:
        - 1 = hätäseis pois päältä
        - 0 = hätäseistila
        - None = ei yhteyttä / lukuvirhe
        """
        if not self.modbus_handler.connected:
            return None

        try:
            result = self.modbus_handler.read_holding_registers(
                EMERGENCY_STATUS_REGISTER,
                EMERGENCY_STATUS_REGISTER_COUNT,
            )

            if result and hasattr(result, "registers") and len(result.registers) > 0:
                return result.registers[0]

            return None

        except Exception:
            return None

    def toggle_relay(self, relay_num, state):
        """
        Optan releen ohjaus taustasäikeessä.

        relay_num = 1...8
        """
        if not self.modbus_handler.connected:
            self.resultReady.emit(False, 3, "Modbus ei yhteydessä")
            return

        QMetaObject.invokeMethod(
            self.worker,
            "toggle_relay",
            Qt.QueuedConnection,
            Q_ARG(int, relay_num),
            Q_ARG(int, state),
        )

    def is_connected(self):
        """
        Palauta Opta Modbus -yhteyden tila.
        """
        return self.modbus_handler.connected

    def cleanup(self):
        """
        Siivoa resurssit.
        """
        self.thread.quit()
        self.thread.wait()

        if self.modbus_handler:
            self.modbus_handler.close()