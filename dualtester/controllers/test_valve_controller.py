# controllers/test_valve_controller.py

from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from utils.runtime_diagnostics import record_event

from config.modbus_config import (
    FORTEST1_TEST_VALVE_REGISTER,
    FORTEST2_TEST_VALVE_REGISTER,
)


PRESSURE_RELEASE_HOLD_MS = 10000
JAKOTUKKI_PRESSURE_RELEASE_HOLD_MS = 5000


class TestValveController(QObject):
    stateConfirmed = pyqtSignal(int, bool)
    commandFailed = pyqtSignal(int, str)

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
        super().__init__()
        self.hardware_service = hardware_service
        self.desired_closed_by_station = {1: None, 2: None}
        self.pending_closed_by_station = {1: None, 2: None}
        self.release_completed_by_station = {1: False, 2: False}
        self.automatic_release_hold_ms_by_station = {
            1: PRESSURE_RELEASE_HOLD_MS,
            2: PRESSURE_RELEASE_HOLD_MS,
        }
        self.active_release_hold_ms_by_station = {
            1: PRESSURE_RELEASE_HOLD_MS,
            2: PRESSURE_RELEASE_HOLD_MS,
        }
        self._write_sequence_by_station = {1: 0, 2: 0}
        if self.hardware_service:
            self.hardware_service.writeAcknowledged.connect(
                self._handle_write_ack
            )
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
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(
                lambda sid=station_id: self._close_after_pressure_release(sid)
            )
            self.pressure_release_timers[station_id] = timer

    def _get_register(self, station_id):
        return self.TEST_VALVE_REGISTER_BY_STATION.get(station_id)

    def is_closed_confirmed(self, station_id):
        return (
            self.last_closed_state_by_station.get(station_id) is True
            and self.pending_closed_by_station.get(station_id) is None
        )

    def is_pressure_release_complete(self, station_id):
        """Vain ajastettu purku ja sulkukirjoitus, ei painemittaus."""
        timer = self._get_pressure_release_timer(station_id)
        return bool(
            self.release_completed_by_station.get(station_id)
            and not self.pressure_release_active_by_station.get(station_id)
            and not (timer and timer.isActive())
            and self.is_closed_confirmed(station_id)
        )

    def reset_release_for_new_test(self, station_id):
        self.release_completed_by_station[station_id] = False

    def configure_automatic_release_hold(self, station_id, hold_ms):
        """Aseta vain valmiiksi päättyvän testin purkuaika.

        Manuaalinen STOP käyttää edelleen 10 sekunnin purkua.
        """
        if station_id not in self.TEST_VALVE_REGISTER_BY_STATION:
            raise ValueError(f"Tuntematon ForTest-asema: {station_id}")
        if hold_ms not in (
            PRESSURE_RELEASE_HOLD_MS,
            JAKOTUKKI_PRESSURE_RELEASE_HOLD_MS,
        ):
            raise ValueError(f"Virheellinen purkuaika: {hold_ms}")
        self.automatic_release_hold_ms_by_station[station_id] = hold_ms

    def _write_closed_state(self, station_id, closed):
        register = self._get_register(station_id)

        if register is None:
            return False, f"ForTest {station_id}: venttiilirekisteri puuttuu"

        if not self.hardware_service:
            return False, "HardwareService ei ole käytössä"

        closed = bool(closed)
        self.desired_closed_by_station[station_id] = closed

        if self.pending_closed_by_station[station_id] is not None:
            # Vastauksen jälkeen käsitellään uusin haluttu tila.
            return True, ""

        if self.last_closed_state_by_station[station_id] == closed:
            return True, ""

        self.pending_closed_by_station[station_id] = closed
        value = 0 if closed else 1

        try:
            queued = bool(self.hardware_service.write_register(register, value))
        except Exception as e:
            queued = False
            error = str(e)
        else:
            error = f"Opta-venttiilirekisteriä {register} ei voitu jonottaa"

        if not queued:
            self.pending_closed_by_station[station_id] = None
            self.last_closed_state_by_station[station_id] = None
            record_event(
                "valve_queue_error", station=station_id,
                register=register, value=value,
            )
            self.commandFailed.emit(station_id, error)
            return False, error

        record_event(
            "valve_write_queued", station=station_id,
            register=register, value=value,
        )
        self._write_sequence_by_station[station_id] += 1
        token = self._write_sequence_by_station[station_id]
        QTimer.singleShot(
            3000,
            lambda sid=station_id, expected=closed, seq=token:
                self._handle_write_timeout(sid, expected, seq),
        )
        return True, ""

    def _handle_write_timeout(self, station_id, expected_closed, sequence):
        if sequence != self._write_sequence_by_station.get(station_id):
            return
        if self.pending_closed_by_station.get(station_id) != expected_closed:
            return

        self.pending_closed_by_station[station_id] = None
        self.last_closed_state_by_station[station_id] = None
        record_event(
            "valve_ack_timeout", station=station_id,
            register=self._get_register(station_id),
            value=0 if expected_closed else 1,
        )
        self.commandFailed.emit(
            station_id,
            "Optan venttiiliohjauksen kuittausta ei saatu 3 sekunnissa",
        )

    def _handle_write_ack(self, address, value, success, error_msg):
        for station_id, register in self.TEST_VALVE_REGISTER_BY_STATION.items():
            if address != register:
                continue

            expected = self.pending_closed_by_station.get(station_id)
            if expected is None or (0 if expected else 1) != value:
                return  # vanha tai toisen komennon kuittaus

            self.pending_closed_by_station[station_id] = None
            record_event(
                "valve_write_ack" if success else "valve_write_error",
                station=station_id, register=address,
                value=value, success=bool(success),
            )
            if success:
                self.last_closed_state_by_station[station_id] = expected
                if self.desired_closed_by_station[station_id] == expected:
                    self.stateConfirmed.emit(station_id, expected)
                    if (
                        not expected
                        and self.pressure_release_active_by_station[station_id]
                    ):
                        self._start_pressure_release_hold(station_id)
            else:
                self.last_closed_state_by_station[station_id] = None
                self.commandFailed.emit(
                    station_id,
                    error_msg or "Optan venttiilikirjoitus epäonnistui",
                )

            desired = self.desired_closed_by_station[station_id]
            if desired is not None and desired != expected:
                self._write_closed_state(station_id, desired)
            return

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
        if timer and not timer.isActive():
            timer.start(self.active_release_hold_ms_by_station[station_id])
            record_event(
                "pressure_release_timer_started", station=station_id,
                elapsed_ms=self.active_release_hold_ms_by_station[station_id],
            )

    def _close_after_pressure_release(self, station_id):
        record_event("pressure_release_timer_elapsed", station=station_id)
        self.pressure_release_active_by_station[station_id] = False
        self.release_completed_by_station[station_id] = True
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
        # STOP-painikkeen paineenpurkua ei lyhennetä.
        self.active_release_hold_ms_by_station[station_id] = PRESSURE_RELEASE_HOLD_MS
        self.release_completed_by_station[station_id] = False
        self.pressure_release_active_by_station[station_id] = True

        success, message = self._open_for_pressure_release(station_id)
        if not success:
            self.pressure_release_active_by_station[station_id] = False
        elif (
            self.last_closed_state_by_station[station_id] is False
            and self.pending_closed_by_station[station_id] is None
        ):
            self._start_pressure_release_hold(station_id)
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
            self.release_completed_by_station[station_id] = False
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
                # ABB JAKOTUKKI 5 s, muut testiohjelmat 10 s.
                # ForTestin PURKU/VALMIS-siirtymä on edelleen edellytys.
                self.active_release_hold_ms_by_station[station_id] = (
                    self.automatic_release_hold_ms_by_station[station_id]
                )
                self.release_completed_by_station[station_id] = False
                self.pressure_release_active_by_station[station_id] = True
                success, message = self._open_for_pressure_release(station_id)
                if (
                    success
                    and self.pending_closed_by_station[station_id] is None
                    and self.last_closed_state_by_station[station_id] is False
                ):
                    self._start_pressure_release_hold(station_id)
                return success, message

            timer = self._get_pressure_release_timer(station_id)

            if timer and timer.isActive():
                return True, ""

            return self.close_valve(station_id)

        return True, ""
