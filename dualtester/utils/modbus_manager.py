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
    resultReady = pyqtSignal(object, int, str)
    writeAcknowledged = pyqtSignal(int, int, bool, str)  # tulos, operaatiokoodi, virheviesti

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
        """Kirjoita rekisteri ja ilmoita myös todellinen Modbus-kuittaus."""
        if not self.modbus or not self.modbus.connected:
            error = "Modbus ei yhteydessä"
            self.writeAcknowledged.emit(address, value, False, error)
            self.resultReady.emit(self._wrap_result(False, address), 2, error)
            return

        try:
            result = self.modbus.write_register(address, value)
            wrapped_result = self._wrap_result(result, address)
            success = bool(wrapped_result)
            error = "" if success else f"Opta rekisteri {address}: kirjoitusta ei kuitattu"

            self.writeAcknowledged.emit(address, value, success, error)
            self.resultReady.emit(wrapped_result, 2, error)
        except Exception as e:
            error = f"Rekisterin {address} kirjoitusvirhe: {e}"
            self.writeAcknowledged.emit(address, value, False, error)
            self.resultReady.emit(self._wrap_result(False, address), 2, error)

    @pyqtSlot()
    def read_emergency_stop_status_async(self):
        """Lue hätäseis vain Modbus-workerissä, ei Qt:n pääsäikeessä."""
        if not self.modbus:
            self.resultReady.emit(None, 4, "Opta Modbus-handler puuttuu")
            return

        try:
            response = self.modbus.read_holding_registers(
                EMERGENCY_STATUS_REGISTER,
                EMERGENCY_STATUS_REGISTER_COUNT,
            )

            if (
                not response
                or (hasattr(response, "isError") and response.isError())
                or not hasattr(response, "registers")
                or len(response.registers) < 1
            ):
                self.resultReady.emit(None, 4, "Hätäseistilan Modbus-luku epäonnistui")
                return

            self.resultReady.emit(response.registers[0], 4, "")
        except Exception as e:
            self.resultReady.emit(None, 4, f"Hätäseistilan lukuvirhe: {e}")

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
    emergencyStatusReady = pyqtSignal(object)
    writeAcknowledged = pyqtSignal(int, int, bool, str)

    def __init__(self, port=None, baudrate=19200):
        super().__init__()

        if not port:
            raise ValueError("Opta Modbus -portti puuttuu")

        self.port = port
        self.baudrate = baudrate
        self._emergency_read_pending = False
        self._last_emergency_status = None
        self._emergency_last_error = ""

        self.modbus_handler = ModbusHandler(
            port=self.port,
            baudrate=self.baudrate,
            auto_reconnect=True,
        )

        self.thread = QThread()
        self.worker = ModbusWorker(self.modbus_handler)

        self.worker.moveToThread(self.thread)
        self.worker.resultReady.connect(self.handle_result)
        self.worker.writeAcknowledged.connect(self.writeAcknowledged.emit)

        self.thread.start()

    def handle_result(self, result, op_code, error_msg):
        """Välitä workerin vastaus oikeaan vastaanottajaan."""
        if op_code == 4:
            self._emergency_read_pending = False
            self._last_emergency_status = result

            # Lokiin vain virhetilan muutos, ei samaa virhettä 1 s välein.
            if error_msg and error_msg != self._emergency_last_error:
                print(f"Opta: {error_msg}")
            elif not error_msg and self._emergency_last_error:
                print("Opta: hätäseistilan luku palautui")

            self._emergency_last_error = error_msg
            self.emergencyStatusReady.emit(result)
            return

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
        """Palauta True vain jos kirjoitus saatiin työntekijän jonoon.

        Varsinainen kuittaus tulee writeAcknowledged-signaalista.
        """
        if not self.modbus_handler.connected:
            return False

        try:
            return bool(QMetaObject.invokeMethod(
                self.worker,
                "write_register",
                Qt.QueuedConnection,
                Q_ARG(int, int(address)),
                Q_ARG(int, int(value)),
            ))
        except Exception as e:
            print(f"Opta Modbus kirjoituksen jonotusvirhe: {e}")
            return False

    def request_emergency_stop_status(self):
        """Tilaa hätäseisluenta taustasäikeestä; enintään yksi pyyntö jonossa."""
        # Workerin ModbusHandler saa yrittää reconnectia myös silloin,
        # kun connected=False. Muutoin Opta ei palautu koskaan.
        if self._emergency_read_pending:
            return False

        self._emergency_read_pending = True

        try:
            QMetaObject.invokeMethod(
                self.worker,
                "read_emergency_stop_status_async",
                Qt.QueuedConnection,
            )
            return True
        except Exception as e:
            self._emergency_read_pending = False
            print(f"Opta: hätäseisluennan jonotus epäonnistui: {e}")
            self.emergencyStatusReady.emit(None)
            return False

    def read_emergency_stop_status(self):
        """Vanha API: palauta viimeisin luettu tila ilman pääsäikeen I/O:ta."""
        self.request_emergency_stop_status()
        return self._last_emergency_status

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