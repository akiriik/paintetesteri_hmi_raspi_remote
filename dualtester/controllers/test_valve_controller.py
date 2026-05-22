# controllers/test_valve_controller.py


class TestValveController:
    """
    ForTest-kohtaisten testiventtiilien ohjaus.

    Nämä venttiilit eivät kuulu jakotukkijigin sylinterisekvenssiin.

    Toiminta:
    - ForTest 1 -> Opta D1608 rele 1
    - ForTest 2 -> Opta D1608 rele 2

    Rele ON  = venttiili kiinni
    Rele OFF = venttiili auki / purku
    """

    TEST_VALVE_RELAY_BY_STATION = {
        1: 1,
        2: 2,
    }

    def __init__(self, hardware_service):
        self.hardware_service = hardware_service
        self.last_closed_state_by_station = {
            1: None,
            2: None,
        }

    def _get_relay_num(self, station_id):
        return self.TEST_VALVE_RELAY_BY_STATION.get(station_id)

    def set_closed(self, station_id, closed):
        """
        Aseta aseman testiventtiilin tila.

        closed=True:
            rele ON, venttiili kiinni

        closed=False:
            rele OFF, venttiili auki
        """
        relay_num = self._get_relay_num(station_id)

        if relay_num is None:
            return False, f"ForTest {station_id}: testiventtiilille ei ole määritelty relettä"

        closed_bool = bool(closed)

        if self.last_closed_state_by_station.get(station_id) == closed_bool:
            return True, ""

        if not self.hardware_service:
            return False, "HardwareService ei ole käytössä"

        success, message = self.hardware_service.control_relay(
            relay_num=relay_num,
            state=closed_bool,
        )

        if success:
            self.last_closed_state_by_station[station_id] = closed_bool

        return success, message

    def open_valve(self, station_id):
        """
        Avaa testiventtiili.

        Tätä käytetään:
        - valmis-tilassa
        - purkuvaiheessa
        - stopissa
        - virheessä
        - hätäseisissä
        - ohjelman sulkemisessa
        """
        return self.set_closed(station_id, False)

    def close_valve(self, station_id):
        """
        Sulje testiventtiili.

        Tätä käytetään:
        - ennen ForTest START -komentoa
        - kun ForTestin tila kertoo testin olevan käynnissä
        """
        return self.set_closed(station_id, True)

    def update_from_fortest_status(self, station_id, status_value):
        """
        Ohjaa testiventtiiliä ForTestin statusarvon perusteella.

        Nykyinen statuskäsittely:
        - 0 = valmis / waiting
        - 1 = testi käynnissä
        - 2 = autozero
        - 3 = purku

        Venttiililogiikka:
        - 1 -> kiinni
        - 3 -> auki
        - 0 -> auki
        - 2 -> ei muuteta tilaa

        Autozero-tilassa venttiilin tilaa ei vaihdeta, koska START sulkee
        venttiilin jo ennen ForTestin käynnistystä.
        """
        if status_value == 1:
            return self.close_valve(station_id)

        if status_value in (0, 3):
            return self.open_valve(station_id)

        return True, ""

    def open_all(self):
        self.open_valve(1)
        self.open_valve(2)