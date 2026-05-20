# controllers/fortest_result_controller.py


class ForTestResultController:
    """
    ForTest-tulosten ja statusten vastaanottokäsittely.

    Säilyttää nykyisen MainWindow.handle_fortest_result()-toiminnan:
    - hakee oikean StationControllerin station_id:n perusteella
    - näyttää ForTest-virheet oikealla asemalla
    - käsittelee START/STOP-kuittaukset
    - ohjaa statusrekisterit StationControllerille
    - ohjaa tulosrekisterit StationControllerille
    """

    def __init__(self, station_controllers):
        self.station_controllers = station_controllers

    def handle_result(self, station_id, result, op_code, error_msg):
        station = self.station_controllers.get(station_id)

        if not station:
            return

        if op_code != 3 and op_code != 4:
            print(f"ForTest {station_id}: op_code={op_code}, error_msg={error_msg}")

        if op_code == 999:
            station.update_status(error_msg, "WARNING")
            return

        if error_msg:
            station.update_status(error_msg, "ERROR")
            return

        if result:
            if op_code == 1:
                station.update_status("TESTI KÄYNNISTETTY ONNISTUNEESTI", "SUCCESS")
            elif op_code == 2:
                station.update_status("TESTI PYSÄYTETTY", "INFO")

        if op_code == 3:
            station.update_status_from_fortest(result)
        elif op_code == 4:
            station.update_test_results(result)

    def cleanup(self):
        pass