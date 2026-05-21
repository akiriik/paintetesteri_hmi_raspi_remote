# services/fortest_service.py
from PyQt5.QtCore import QObject

from config.fortest_config import FORTEST_PROGRAM_REGISTER
from utils.fortest_manager import ForTestManager


class ForTestService(QObject):
    """
    ForTest 1 ja ForTest 2 -laitteiden hallinta.

    Vastuu:
    - luo station-kohtaiset ForTestManagerit
    - reitittää ForTest-managerien tulokset MainWindowille station_id:n kanssa
    - tarjoaa station-kohtaiset start/stop/status/result-metodit
    - hoitaa ForTest-ohjelmanvaihdon ForTestin omalla väylällä

    Tämä service ei käytä Arduino Optan Modbus-väylää.
    Tämä service ei ohjaa Raspberry Pi:n GPIO:ta.

    Aseman ajotila kuuluu StationControllerille.
    """

    def __init__(
        self,
        parent=None,
        dev_mode_fortest=True,
        station_ports=None,
        baudrate=19200,
    ):
        super().__init__(parent)

        self.parent_window = parent
        self.dev_mode_fortest = dev_mode_fortest
        self.fortest_baudrate = baudrate

        if station_ports is None:
            station_ports = {}

        self.fortest_station_ports = station_ports
        self.fortest_managers = {}

        self._init_fortest_managers()

    # ------------------------------------------------------------
    # Alustus
    # ------------------------------------------------------------

    def _init_fortest_managers(self):
        if self.dev_mode_fortest:
            return

        for station_id, fortest_port in self.fortest_station_ports.items():
            if not fortest_port:
                continue

            try:
                fortest_manager = ForTestManager(
                    port=fortest_port,
                    baudrate=self.fortest_baudrate,
                )

                if self.parent_window and hasattr(self.parent_window, "handle_fortest_result"):
                    fortest_manager.resultReady.connect(
                        lambda result, op_code, error_msg, sid=station_id:
                            self.parent_window.handle_fortest_result(
                                sid,
                                result,
                                op_code,
                                error_msg,
                            )
                    )

                self.fortest_managers[station_id] = fortest_manager

            except Exception as e:
                print(f"Varoitus: ForTest {station_id} alustus epäonnistui portissa {fortest_port}: {e}")

    # ------------------------------------------------------------
    # ForTest-managerien haku
    # ------------------------------------------------------------

    def get_manager(self, station_id):
        """
        Palauttaa station_id:tä vastaavan ForTestManagerin.

        Julkinen metodinimi pidetään ennallaan yhteensopivuuden vuoksi.
        """
        return self.fortest_managers.get(station_id)

    def _get_fortest_manager_or_warn(self, station_id, operation_name):
        fortest_manager = self.get_manager(station_id)

        if fortest_manager:
            return fortest_manager

        if not self.dev_mode_fortest:
            print(f"ForTest {station_id}: ei manageria operaatiolle {operation_name}")

        return None

    def _get_fortest_modbus_or_none(self, station_id, operation_name):
        """
        Palauttaa ForTest-laitteen oman Modbus-rajapinnan.

        Tämä ei ole Arduino Optan Modbus-väylä.
        """
        fortest_manager = self._get_fortest_manager_or_warn(station_id, operation_name)

        if not fortest_manager:
            return None

        try:
            return fortest_manager.worker.fortest.modbus
        except Exception as e:
            print(f"ForTest {station_id}: ForTest Modbus -rajapintaa ei saatu operaatiolle {operation_name}: {e}")
            return None

    def has_station_port(self, station_id):
        return bool(self.fortest_station_ports.get(station_id))

    # ------------------------------------------------------------
    # ForTest-yhteystila
    # ------------------------------------------------------------

    def is_connected(self, station_id):
        fortest_manager = self.get_manager(station_id)

        if not fortest_manager:
            return False

        try:
            return (
                hasattr(fortest_manager, "worker")
                and hasattr(fortest_manager.worker, "fortest")
                and hasattr(fortest_manager.worker.fortest, "modbus")
                and fortest_manager.worker.fortest.modbus.connected
            )
        except Exception:
            return False

    # ------------------------------------------------------------
    # ForTest-ohjelma
    # ------------------------------------------------------------

    def write_program(self, station_id, program_number):
        fortest_modbus = self._get_fortest_modbus_or_none(station_id, "write_program")

        if not fortest_modbus:
            return None

        try:
            return fortest_modbus.write_register(FORTEST_PROGRAM_REGISTER, program_number)
        except Exception as e:
            print(f"Virhe ForTest {station_id} ohjelmanvaihdossa: {e}")
            return None

    # ------------------------------------------------------------
    # ForTest-testin ohjaus
    # ------------------------------------------------------------

    def start_test(self, station_id):
        fortest_manager = self._get_fortest_manager_or_warn(station_id, "start_test")

        if fortest_manager:
            fortest_manager.start_test()

    def abort_test(self, station_id):
        fortest_manager = self._get_fortest_manager_or_warn(station_id, "abort_test")

        if fortest_manager:
            fortest_manager.abort_test()

    # ------------------------------------------------------------
    # ForTest-luennat
    # ------------------------------------------------------------

    def read_status(self, station_id):
        fortest_manager = self._get_fortest_manager_or_warn(station_id, "read_status")

        if fortest_manager:
            fortest_manager.read_status()

    def read_results(self, station_id):
        fortest_manager = self._get_fortest_manager_or_warn(station_id, "read_results")

        if fortest_manager:
            fortest_manager.read_results()

    # ------------------------------------------------------------
    # Sulkeminen
    # ------------------------------------------------------------

    def cleanup(self):
        for fortest_manager in self.fortest_managers.values():
            fortest_manager.cleanup()