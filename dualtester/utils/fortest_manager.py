# utils/fortest_manager.py
from collections import deque
from PyQt5.QtCore import (
    QObject,
    QThread,
    pyqtSignal,
    pyqtSlot,
    QMetaObject,
    Qt,
    Q_ARG,
)

from utils.fortest_handler import ForTestHandler, DummyForTestHandler


class ForTestWorker(QObject):
    resultReady = pyqtSignal(object, int, str)
    connectionStateChanged = pyqtSignal(bool, str)

    def __init__(self, port="/dev/ttyUSB1", baudrate=19200):
        super().__init__()

        try:
            self.fortest = ForTestHandler(
                port=port,
                baudrate=baudrate,
            )
        except Exception as e:
            print(f"ForTest-yhteyden alustus epäonnistui: {e}")
            self.fortest = DummyForTestHandler()

    def _connection_state(self):
        try:
            connected = bool(self.fortest.is_connected())
        except Exception:
            connected = False

        try:
            error = self.fortest.get_last_error() or ""
        except Exception:
            error = ""

        return connected, error

    def _finish_operation(self, result, op_code, fallback_error):
        operation_ok = bool(
            getattr(self.fortest, "last_operation_ok", False)
        )

        connected, connection_error = self._connection_state()

        if operation_ok:
            error_msg = ""
        else:
            error_msg = connection_error or fallback_error

        # Päivitä managerin yhteystila ennen kuin tulos käsitellään UI:ssa.
        self.connectionStateChanged.emit(connected, connection_error)
        self.resultReady.emit(result, op_code, error_msg)

    @pyqtSlot(int)
    def write_program(self, program_number):
        try:
            result = self.fortest.write_program(program_number)
            self._finish_operation(
                result,
                5,
                "ForTest-ohjelman vaihto epäonnistui",
            )
        except Exception as e:
            self.connectionStateChanged.emit(False, str(e))
            self.resultReady.emit(
                False,
                5,
                f"Virhe ohjelman vaihdossa: {e}",
            )

    @pyqtSlot()
    def start_test(self):
        try:
            result = self.fortest.start_test()
            self._finish_operation(
                result,
                1,
                "ForTest-testin käynnistys epäonnistui",
            )
        except Exception as e:
            self.connectionStateChanged.emit(False, str(e))
            self.resultReady.emit(
                False,
                1,
                f"Virhe testin käynnistyksessä: {e}",
            )

    @pyqtSlot()
    def abort_test(self):
        try:
            result = self.fortest.abort_test()
            self._finish_operation(
                result,
                2,
                "ForTest-testin keskeytys epäonnistui",
            )
        except Exception as e:
            self.connectionStateChanged.emit(False, str(e))
            self.resultReady.emit(
                False,
                2,
                f"Virhe testin keskeytyksessä: {e}",
            )

    @pyqtSlot()
    def read_status(self):
        try:
            result = self.fortest.read_status()
            self._finish_operation(
                result,
                3,
                "ForTest-statuksen luku epäonnistui",
            )
        except Exception as e:
            self.connectionStateChanged.emit(False, str(e))
            self.resultReady.emit(
                None,
                3,
                f"Virhe testin tilan lukemisessa: {e}",
            )

    @pyqtSlot()
    def read_results(self):
        try:
            result = self.fortest.read_results()
            self._finish_operation(
                result,
                4,
                "ForTest-tulosten luku epäonnistui",
            )
        except Exception as e:
            self.connectionStateChanged.emit(False, str(e))
            self.resultReady.emit(
                None,
                4,
                f"Virhe testin tulosten lukemisessa: {e}",
            )

    @pyqtSlot()
    def cleanup(self):
        try:
            self.fortest.close()
        except Exception:
            pass


class ForTestManager(QObject):
    """
    Yhden ForTest-laitteen worker-jonon hallinta.

    Pollauspyyntöjä ei koskaan jonoteta, jos edellinen operaatio on vielä
    kesken. START/STOP/ohjelmanvaihto säilytetään korkeintaan yhtenä
    odottavana ohjauskomentona ja suoritetaan heti käynnissä olevan
    operaation valmistuttua.
    """

    resultReady = pyqtSignal(object, int, str)

    def __init__(self, port="/dev/ttyUSB1", baudrate=19200):
        super().__init__()

        self.port = port
        self.thread = QThread()
        self.worker = ForTestWorker(port, baudrate)

        self._busy = False
        self._pending_controls = deque()
        self._connected = False
        self._last_connection_error = ""

        try:
            self._connected = bool(self.worker.fortest.is_connected())
        except Exception:
            self._connected = False

        self.worker.moveToThread(self.thread)
        self.worker.resultReady.connect(self.handle_result)
        self.worker.connectionStateChanged.connect(
            self.handle_connection_state
        )

        self.thread.start()

    def handle_connection_state(self, connected, error_msg):
        previous = self._connected
        self._connected = bool(connected)
        self._last_connection_error = error_msg or ""

        if previous != self._connected:
            state_text = "YHTEYS PALAUTUI" if self._connected else "YHTEYS KATKESI"
            print(f"ForTest {self.port}: {state_text}")

    def handle_result(self, result, op_code, error_msg):
        self._busy = False

        # STOP on aina etusijalla, myös jos statusvastauksen käsittelijä
        # lähettäisi heti uuden tuloslukupyynnön.
        if (
            self._pending_controls
            and self._pending_controls[0][0] == "abort_test"
        ):
            self._dispatch_pending_control()

        # Muut kuittaukset on käsiteltävä ennen seuraavaa ohjauskomentoa.
        self.resultReady.emit(result, op_code, error_msg)
        self._dispatch_pending_control()

    def _invoke_worker(self, method_name, program_number=None):
        if self._busy:
            return False

        self._busy = True

        try:
            if program_number is None:
                dispatched = QMetaObject.invokeMethod(
                    self.worker,
                    method_name,
                    Qt.QueuedConnection,
                )
            else:
                dispatched = QMetaObject.invokeMethod(
                    self.worker,
                    method_name,
                    Qt.QueuedConnection,
                    Q_ARG(int, int(program_number)),
                )

            if dispatched is False:
                raise RuntimeError("Qt-worker ei hyväksynyt kutsua")

            return True

        except Exception as e:
            self._busy = False
            print(f"ForTest worker-kutsu epäonnistui ({method_name}): {e}")
            return False

    def _queue_control(self, method_name, program_number=None):
        """Säilytä ohjauskäskyt järjestyksessä; STOP syrjäyttää jonon."""
        if method_name == "abort_test":
            # STOP ei saa jäädä odottavan STARTin/ohjelmanvaihdon taakse.
            # Jo suorituksessa olevaa sarjaliikennettä ei voi keskeyttää.
            self._pending_controls.clear()
            if not self._busy:
                return self._invoke_worker("abort_test")
            self._pending_controls.append(("abort_test", None))
            return True

        if any(method == "abort_test" for method, _ in self._pending_controls):
            return False

        if not self._busy and not self._pending_controls:
            return self._invoke_worker(method_name, program_number)

        # Hallitusti rajattu jono: ei hiljaista komentojen korvaamista.
        if len(self._pending_controls) >= 4:
            print(f"ForTest {self.port}: ohjausjono täynnä ({method_name})")
            return False

        self._pending_controls.append((method_name, program_number))
        return True

    def _dispatch_pending_control(self):
        if self._busy or not self._pending_controls:
            return

        method_name, program_number = self._pending_controls.popleft()
        if not self._invoke_worker(method_name, program_number):
            print(f"ForTest {self.port}: odottavan komennon lähetys epäonnistui")

    def is_connected(self):
        return bool(self._connected)

    def get_last_connection_error(self):
        return self._last_connection_error

    def write_program(self, program_number):
        return self._queue_control(
            "write_program",
            program_number,
        )

    def start_test(self):
        return self._queue_control("start_test")

    def abort_test(self):
        return self._queue_control("abort_test")

    def read_status(self):
        # Statuspollaus jätetään väliin, jos mikä tahansa operaatio on kesken.
        if self._busy or self._pending_controls:
            return False

        return self._invoke_worker("read_status")

    def read_results(self):
        # Tulospyyntöä ei jonoteta vanhojen pyyntöjen perään.
        if self._busy or self._pending_controls:
            return False

        return self._invoke_worker("read_results")

    def cleanup(self):
        self._pending_controls.clear()
        if self.thread.isRunning():
            # Älä blokkaa käyttöliittymää ikuisesti, jos sarjaportti on jumissa.
            try:
                QMetaObject.invokeMethod(self.worker, "cleanup", Qt.QueuedConnection)
            except Exception:
                pass
            self.thread.quit()
            if not self.thread.wait(2000):
                print(f"ForTest {self.port}: worker ei sulkeutunut 2 sekunnissa")
