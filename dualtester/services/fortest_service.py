# services/fortest_service.py
from PyQt5.QtCore import QObject

from utils.fortest_manager import ForTestManager


class ForTestService(QObject):
    """
    ForTest-laitteiden hallinta.

    Vastuu:
    - luo station-kohtaiset ForTestManagerit
    - reitittää managerien tulokset MainWindowille station_id:n kanssa
    - tarjoaa station-kohtaiset start/stop/status/result-metodit

    Tämä luokka ei päätä aseman ajotilaa eikä päivitä UI:ta.
    Aseman tila kuuluu StationControllerille.
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
        self.baudrate = baudrate

        if station_ports is None:
            station_ports = {
                1: "/dev/ttyUSB1",
                2: None,
            }

        self.station_ports = station_ports
        self.managers = {}

        self._init_managers()

    def _init_managers(self):
        if self.dev_mode_fortest:
            return

        for station_id, port in self.station_ports.items():
            if not port:
                continue

            try:
                manager = ForTestManager(port=port, baudrate=self.baudrate)

                if self.parent_window and hasattr(self.parent_window, "handle_fortest_result"):
                    manager.resultReady.connect(
                        lambda result, op_code, error_msg, sid=station_id:
                            self.parent_window.handle_fortest_result(
                                sid,
                                result,
                                op_code,
                                error_msg,
                            )
                    )

                self.managers[station_id] = manager

            except Exception as e:
                print(f"Varoitus: ForTest {station_id} alustus epäonnistui portissa {port}: {e}")

    def get_manager(self, station_id):
        return self.managers.get(station_id)

    def _get_manager_or_warn(self, station_id, operation_name):
        manager = self.get_manager(station_id)

        if manager:
            return manager

        if not self.dev_mode_fortest:
            print(f"ForTest {station_id}: ei manageria operaatiolle {operation_name}")

        return None

    def is_connected(self, station_id):
        manager = self.get_manager(station_id)

        if not manager:
            return False

        try:
            return (
                hasattr(manager, "worker")
                and hasattr(manager.worker, "fortest")
                and hasattr(manager.worker.fortest, "modbus")
                and manager.worker.fortest.modbus.connected
            )
        except Exception:
            return False

    def write_program(self, station_id, program_number):
        manager = self._get_manager_or_warn(station_id, "write_program")

        if not manager:
            return None

        try:
            modbus = manager.worker.fortest.modbus
            return modbus.write_register(0x0060, program_number)
        except Exception as e:
            print(f"Virhe ForTest {station_id} ohjelmanvaihdossa: {e}")
            return None

    def start_test(self, station_id):
        manager = self._get_manager_or_warn(station_id, "start_test")

        if manager:
            manager.start_test()

    def abort_test(self, station_id):
        manager = self._get_manager_or_warn(station_id, "abort_test")

        if manager:
            manager.abort_test()

    def read_status(self, station_id):
        manager = self._get_manager_or_warn(station_id, "read_status")

        if manager:
            manager.read_status()

    def read_results(self, station_id):
        manager = self._get_manager_or_warn(station_id, "read_results")

        if manager:
            manager.read_results()

    def cleanup(self):
        for manager in self.managers.values():
            manager.cleanup()