# controllers/test_valve_controller.py

from config.modbus_config import (
    FORTEST1_TEST_VALVE_REGISTER,
    FORTEST2_TEST_VALVE_REGISTER,
)


class TestValveController:
    """
    ForTest-kohtaisten testiventtiilien ohjaus.

    Nämä venttiilit eivät kuulu jakotukkijigin sylinterisekvenssiin.

    Toiminta:
    - ForTest 1 -> Optan oma rele 3 -> rekisteri 18092
    - ForTest 2 -> Optan oma rele 4 -> rekisteri 18093

    Rele ON  = venttiili kiinni
    Rele OFF = venttiili auki / purku

    Huom:
    HardwareService.write_register() käyttää taustasäikeistä Modbus-kirjoitusta.
    Se voi palauttaa None, vaikka kirjoitus lähtee oikein.
    Siksi onnistumista ei arvioida paluuarvosta.
    """

    TEST_VALVE_REGISTER_BY_STATION = {
        1: FORTEST1_TEST_VALVE_REGISTER,
        2: FORTEST2_TEST_VALVE_REGISTER,
    }

    def __init__(self, hardware_service):
        self.hardware_service = hardware_service
        self.last_closed_state_by_station = {
            1: None,
            2: None,
        }

    def _get_register(self, station_id):
        return self.TEST_VALVE_REGISTER_BY_STATION.get(station_id)

    def set_closed(self, station_id, closed):
        register = self._get_register(station_id)

        if register is None:
            return False, f"ForTest {station_id}: testiventtiilille ei ole määritelty rekisteriä"

        closed_bool = bool(closed)

        if self.last_closed_state_by_station.get(station_id) == closed_bool:
            return True, ""

        if not self.hardware_service:
            return False, "HardwareService ei ole käytössä"

        value = 1 if closed_bool else 0

        try:
            self.hardware_service.write_register(register, value)
            self.last_closed_state_by_station[station_id] = closed_bool
            return True, ""

        except Exception as e:
            return False, f"ForTest {station_id}: testiventtiilin ohjaus epäonnistui: {e}"

    def open_valve(self, station_id):
        return self.set_closed(station_id, False)

    def close_valve(self, station_id):
        return self.set_closed(station_id, True)

    def update_from_fortest_status(self, station_id, status_value):
        """
        ForTest status:
        - 0 = valmis / waiting -> venttiili auki
        - 1 = testi käynnissä -> venttiili kiinni
        - 2 = autozero -> ei muuteta
        - 3 = purku -> venttiili auki
        """
        if status_value == 1:
            return self.close_valve(station_id)

        if status_value in (0, 3):
            return self.open_valve(station_id)

        return True, ""

    def open_all(self):
        self.open_valve(1)
        self.open_valve(2)