# controllers/modbus_result_controller.py


class ModbusResultController:
    """
    Modbus-tulosten käsittely.

    Säilyttää nykyisen toiminnan:
    - hätäseisrekisterin 19099 kirjoitustulos ohitetaan
    - hätäseisdialogin aikana op_code 2 ohitetaan
    - virheilmoitus näytetään station 1:llä
    - onnistunut kirjoitus näyttää MODBUS-KIRJOITUS OK
    - epäonnistunut kirjoitus näyttää MODBUS-KIRJOITUS EPÄONNISTUI

    Tämä vastaa vanhaa MainWindow.handle_modbus_result()-logiikkaa.
    """

    def __init__(self, station_controllers, emergency_stop_controller=None):
        self.station_controllers = station_controllers
        self.emergency_stop_controller = emergency_stop_controller

    def set_emergency_stop_controller(self, emergency_stop_controller):
        self.emergency_stop_controller = emergency_stop_controller

    def handle_result(self, result, op_code, error_msg):
        if op_code == 2 and hasattr(result, "address") and result.address == 19099:
            return

        if self.emergency_stop_controller:
            if self.emergency_stop_controller.is_emergency_dialog_active():
                if op_code == 2:
                    return

        station = self.station_controllers.get(1)

        if error_msg:
            if station:
                station.update_status(error_msg, "ERROR")
            return

        if not result:
            return

        if op_code == 2:
            if hasattr(result, "isError") and not result.isError():
                if station:
                    station.update_status("MODBUS-KIRJOITUS OK", "SUCCESS")
            else:
                if station:
                    station.update_status("MODBUS-KIRJOITUS EPÄONNISTUI", "ERROR")

    def cleanup(self):
        pass