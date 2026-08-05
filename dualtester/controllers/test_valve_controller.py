# controllers/test_valve_controller.py

from PyQt5.QtCore import QTimer

from config.modbus_config import (
    FORTEST1_TEST_VALVE_REGISTER,
    FORTEST2_TEST_VALVE_REGISTER,
)


FORTEST2_PRESSURE_RELEASE_HOLD_MS = 10000


class TestValveController:
    """
    ForTest-kohtaisten testiventtiilien ohjaus.

    Nämä venttiilit eivät kuulu jakotukkijigin sylinterisekvenssiin.

    Kytkennät:
    - ForTest 1 -> Optan oma rele 3 -> rekisteri 18092
      Rele ON  = venttiili kiinni
      Rele OFF = venttiili auki / purku

    - ForTest 2 -> Optan oma rele 4 -> rekisteri 18093
      VXA on NC-venttiili:
      Rele OFF = venttiili kiinni
      Rele ON  = venttiili auki / purku huoneilmaan

    ForTest 2:n VXA avataan vain ForTestin PURKU-tilassa. Kun ForTest
    palaa PURKU-tilasta VALMIS-tilaan, venttiili pidetään auki vielä
    10 sekuntia. Uuden testin aloitus sulkee venttiilin heti ja peruu
    jäljellä olevan purkuajan.

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
        self.last_fortest_status_by_station = {
            1: None,
            2: None,
        }

        self.fortest2_pressure_release_timer = QTimer()
        self.fortest2_pressure_release_timer.setSingleShot(True)
        self.fortest2_pressure_release_timer.timeout.connect(
            self._close_fortest2_after_pressure_release
        )

    def _get_register(self, station_id):
        return self.TEST_VALVE_REGISTER_BY_STATION.get(station_id)

    def _write_closed_state(self, station_id, closed):
        register = self._get_register(station_id)

        if register is None:
            return False, f"ForTest {station_id}: testiventtiilille ei ole määritelty rekisteriä"

        closed_bool = bool(closed)

        if self.last_closed_state_by_station.get(station_id) == closed_bool:
            return True, ""

        if not self.hardware_service:
            return False, "HardwareService ei ole käytössä"

        if station_id == 2:
            value = 0 if closed_bool else 1
        else:
            value = 1 if closed_bool else 0

        try:
            self.hardware_service.write_register(register, value)
            self.last_closed_state_by_station[station_id] = closed_bool
            return True, ""

        except Exception as e:
            return False, f"ForTest {station_id}: testiventtiilin ohjaus epäonnistui: {e}"

    def _cancel_fortest2_pressure_release_timer(self):
        if self.fortest2_pressure_release_timer.isActive():
            self.fortest2_pressure_release_timer.stop()

    def _open_fortest2_for_pressure_release(self):
        return self._write_closed_state(2, False)

    def _start_fortest2_pressure_release_hold(self):
        self.fortest2_pressure_release_timer.start(
            FORTEST2_PRESSURE_RELEASE_HOLD_MS
        )

    def _close_fortest2_after_pressure_release(self):
        self._write_closed_state(2, True)

    def set_closed(self, station_id, closed):
        if station_id == 2:
            self._cancel_fortest2_pressure_release_timer()

        return self._write_closed_state(station_id, closed)

    def open_valve(self, station_id):
        if station_id == 2:
            # Tester 2:n VXA:ta ei avata yleisellä open-komennolla.
            # Avaaminen sallitaan vain ForTestin PURKU-tilan perusteella.
            return self.set_closed(station_id, True)

        return self.set_closed(station_id, False)

    def close_valve(self, station_id):
        return self.set_closed(station_id, True)

    def update_from_fortest_status(self, station_id, status_value):
        """
        ForTest status:
        - 0 = valmis / waiting
        - 1 = testi käynnissä
        - 2 = autozero
        - 3 = purku
        """
        previous_status = self.last_fortest_status_by_station.get(station_id)
        self.last_fortest_status_by_station[station_id] = status_value

        if station_id == 2:
            if status_value in (1, 2):
                return self.close_valve(station_id)

            if status_value == 3:
                self._cancel_fortest2_pressure_release_timer()
                return self._open_fortest2_for_pressure_release()

            if status_value == 0:
                if previous_status == 3:
                    success, message = self._open_fortest2_for_pressure_release()

                    if success:
                        self._start_fortest2_pressure_release_hold()

                    return success, message

                if self.fortest2_pressure_release_timer.isActive():
                    return True, ""

                return self.close_valve(station_id)

            return True, ""

        if status_value == 1:
            return self.close_valve(station_id)

        if status_value in (0, 3):
            return self.open_valve(station_id)

        return True, ""

    def open_all(self):
        self.open_valve(1)
        self.close_valve(2)
