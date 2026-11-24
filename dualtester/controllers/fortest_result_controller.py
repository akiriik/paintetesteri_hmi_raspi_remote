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
    OP_PROGRAM_WRITE_ACK = 5
    OP_CONNECTION_ERROR = 999

    def __init__(self, station_controllers):
        self.station_controllers = station_controllers

    def handle_result(self, station_id, result, op_code, error_msg):
        station = self.station_controllers.get(station_id)

        if not station:
            return

        if op_code == self.OP_CONNECTION_ERROR:
            station.update_status(error_msg, "WARNING")
            station.refresh_station_state()
            return

        # Ohjauskuittaukset käsitellään myös virheellisissä vastauksissa,
        # jotta tilakone ei jää pysyvästi START/ohjelmanvaihtotilaan.
        if op_code == self.OP_PROGRAM_WRITE_ACK:
            station.handle_program_write_ack(bool(result) and not error_msg, error_msg)
            return

        if op_code == self.OP_START_ACK:
            station.handle_start_ack(bool(result) and not error_msg, error_msg)
            return

        if error_msg:
            station.update_status(error_msg, "ERROR")
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

    def cleanup(self):
        pass
