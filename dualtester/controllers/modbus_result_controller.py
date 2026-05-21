# controllers/modbus_result_controller.py

from services.hardware_service import HardwareService


class ModbusResultController:
    """
    Modbus-tulosten käsittely.

    Nykyinen vastuu:
    - hätäseisrekisterin kirjoitustulos ohitetaan
    - hätäseisdialogin aikana op_code 2 ohitetaan
    - virheilmoitus näytetään station 1:llä
    - onnistunut kirjoitus näyttää MODBUS-KIRJOITUS OK
    - epäonnistunut kirjoitus näyttää MODBUS-KIRJOITUS EPÄONNISTUI

    Tämä käsittelee vain yleisiä Modbus-kuittauksia.
    Varsinainen hardware-rajapinta on HardwareService.
    """

    def __init__(self, station_controllers, emergency_stop_controller=None):
        self.station_controllers = station_controllers
        self.emergency_stop_controller = emergency_stop_controller

    def set_emergency_stop_controller(self, emergency_stop_controller):
        self.emergency_stop_controller = emergency_stop_controller

    def handle_result(self, result, op_code, error_msg):
        if self._is_emergency_reset_write_result(result, op_code):
            return

        if self._should_ignore_during_emergency_dialog(op_code):
            return

        station = self.station_controllers.get(1)

        if error_msg:
            if station:
                station.update_status(error_msg, "ERROR")
            return

        if not result:
            return

        if op_code == 2:
            self._handle_write_result(station, result)

    def _is_emergency_reset_write_result(self, result, op_code):
        return (
            op_code == 2
            and hasattr(result, "address")
            and result.address == HardwareService.EMERGENCY_RESET_REGISTER
        )

    def _should_ignore_during_emergency_dialog(self, op_code):
        if not self.emergency_stop_controller:
            return False

        if not self.emergency_stop_controller.is_emergency_dialog_active():
            return False

        return op_code == 2

    def _handle_write_result(self, station, result):
        if not station:
            return

        if hasattr(result, "isError") and not result.isError():
            station.update_status("MODBUS-KIRJOITUS OK", "SUCCESS")
        else:
            station.update_status("MODBUS-KIRJOITUS EPÄONNISTUI", "ERROR")

    def cleanup(self):
        pass