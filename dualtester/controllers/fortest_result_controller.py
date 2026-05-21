# controllers/fortest_result_controller.py


class ForTestResultController:
    """
    ForTest-tulosten ja statusten vastaanottokäsittely.

    Vastuu:
    - hakee oikean StationControllerin station_id:n perusteella
    - näyttää ForTest-virheet oikealla asemalla
    - reitittää statusrekisterit StationControllerille
    - reitittää tulosrekisterit StationControllerille

    Tämä luokka ei päätä aseman ajotilaa.
    Aseman tila kuuluu StationControllerille.
    """

    OP_START_ACK = 1
    OP_ABORT_ACK = 2
    OP_STATUS_READ = 3
    OP_RESULTS_READ = 4
    OP_CONNECTION_ERROR = 999

    def __init__(self, station_controllers):
        self.station_controllers = station_controllers

    def handle_result(self, station_id, result, op_code, error_msg):
        station = self.station_controllers.get(station_id)

        if not station:
            print(f"ForTest: tuntematon station_id {station_id}")
            return

        if op_code not in [self.OP_STATUS_READ, self.OP_RESULTS_READ]:
            print(f"ForTest {station_id}: op_code={op_code}, error_msg={error_msg}")

        if op_code == self.OP_CONNECTION_ERROR:
            station.update_status(error_msg, "WARNING")
            station.refresh_station_state()
            return

        if error_msg:
            station.update_status(error_msg, "ERROR")
            station.refresh_station_state()
            return

        if op_code == self.OP_START_ACK:
            station.update_status("FORTEST START KUITATTU", "SUCCESS")
            station.refresh_station_state()
            return

        if op_code == self.OP_ABORT_ACK:
            station.update_status("FORTEST STOP KUITATTU", "INFO")
            station.refresh_station_state()
            return

        if op_code == self.OP_STATUS_READ:
            station.update_status_from_fortest(result)
            return

        if op_code == self.OP_RESULTS_READ:
            station.update_test_results(result)
            return

        print(f"ForTest {station_id}: tuntematon op_code {op_code}")

    def cleanup(self):
        pass