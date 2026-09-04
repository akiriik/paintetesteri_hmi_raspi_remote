# controllers/test_valve_controller.py

from PyQt5.QtCore import QTimer

from config.modbus_config import (
    FORTEST1_TEST_VALVE_REGISTER,
    FORTEST2_TEST_VALVE_REGISTER,
)


PRESSURE_RELEASE_HOLD_MS = 10000


class TestValveController:
    """
    ForTest-kohtaisten testiventtiilien ohjaus.

    Nämä venttiilit eivät kuulu jakotukkijigin sylinterisekvenssiin.

    Kytkennät:
    - ForTest 1 -> Optan oma rele 3 -> rekisteri 18092
    - ForTest 2 -> Optan oma rele 4 -> rekisteri 18093

    Molemmissa asemissa on NC-tyyppinen VXA-venttiili:
    - Rele OFF = venttiili kiinni
    - Rele ON  = venttiili auki / purku huoneilmaan

    VXA avataan ForTestin PURKU-tilassa. Kun aktiivinen testi päättyy ja
    ForTest palaa VALMIS-tilaan, venttiili avataan tai pidetään auki
    10 sekuntia, vaikka lyhyt PURKU-tila jäisi statuskyselyjen väliin.
    Myös käyttäjän STOP-komento avaa venttiilin 10 sekunniksi. Uuden testin
    aloitus sulkee venttiilin heti ja peruu jäljellä olevan purkuajan.

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
        self.pressure_release_active_by_station = {
            1: False,
            2: False,
        }
        self.pressure_release_timers = {}

        for station_id in self.TEST_VALVE_REGISTER_BY_STATION:
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(
                lambda sid=station_id: self._close_after_pressure_release(sid)
            )
            self.pressure_release_timers[station_id] = timer

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

        # Molemmat testerit käyttävät samanlaista NC VXA -venttiiliä:
        # rele OFF (0) = kiinni, rele ON (1) = auki / purku.
        value = 0 if closed_bool else 1

        try:
            self.hardware_service.write_register(register, value)
            self.last_closed_state_by_station[station_id] = closed_bool
            return True, ""

        except Exception as e:
            return False, f"ForTest {station_id}: testiventtiilin ohjaus epäonnistui: {e}"

    def _get_pressure_release_timer(self, station_id):
        return self.pressure_release_timers.get(station_id)

    def _cancel_pressure_release_timer(self, station_id):
        timer = self._get_pressure_release_timer(station_id)

        if timer and timer.isActive():
            timer.stop()

    def _open_for_pressure_release(self, station_id):
        return self._write_closed_state(station_id, False)

    def _start_pressure_release_hold(self, station_id):
        timer = self._get_pressure_release_timer(station_id)

        if timer:
            timer.start(PRESSURE_RELEASE_HOLD_MS)

    def _close_after_pressure_release(self, station_id):
        self.pressure_release_active_by_station[station_id] = False
        self._write_closed_state(station_id, True)

    def set_closed(self, station_id, closed):
        self._cancel_pressure_release_timer(station_id)
        self.pressure_release_active_by_station[station_id] = False

        return self._write_closed_state(station_id, closed)

    def open_valve(self, station_id):
        # Yleistä open_valve()-kutsua käytetään muualla ohjelmassa
        # valmius-/vikatilan palautukseen. Molemmilla NC VXA -venttiileillä
        # turvallinen normaali tila on kiinni.
        return self.set_closed(station_id, True)

    def close_valve(self, station_id):
        return self.set_closed(station_id, True)

    def release_pressure_after_stop(self, station_id):
        self._cancel_pressure_release_timer(station_id)
        self.pressure_release_active_by_station[station_id] = True

        success, message = self._open_for_pressure_release(station_id)

        if success:
            self._start_pressure_release_hold(station_id)
        else:
            self.pressure_release_active_by_station[station_id] = False

        return success, message

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

        if self.pressure_release_active_by_station.get(station_id, False):
            return self._open_for_pressure_release(station_id)

        if status_value in (1, 2):
            return self.close_valve(station_id)

        if status_value == 3:
            self._cancel_pressure_release_timer(station_id)
            return self._open_for_pressure_release(station_id)

        if status_value == 0:
            # Testi on päättynyt aina, kun aktiivisesta testitilasta
            # 1/2/3 palataan valmiustilaan. Purku käynnistetään myös
            # suorassa 1->0 tai 2->0 siirtymässä, koska ForTestin lyhyt
            # PURKU=3 voi jäädä yhden sekunnin statuskyselyjen väliin.
            if previous_status in (1, 2, 3):
                success, message = self._open_for_pressure_release(station_id)

                if success:
                    self._start_pressure_release_hold(station_id)

                return success, message

            timer = self._get_pressure_release_timer(station_id)

            if timer and timer.isActive():
                return True, ""

            return self.close_valve(station_id)

        return True, ""
