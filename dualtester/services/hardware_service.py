# services/hardware_service.py
from PyQt5.QtCore import QObject, QTimer

from config.modbus_config import (
    SHUTDOWN_REQUEST_REGISTER,
    EMERGENCY_RESET_REGISTER,
    JIG_SEQUENCE_COMMAND_REGISTER,
    JIG_SEQUENCE_START_REGISTER,
    JIG_SEQUENCE_STOP_REGISTER,
    JIG_SEQUENCE_STATUS_REGISTER,
    JIG_SEQUENCE_STATE_REGISTER_COUNT,
    JIG_SEQUENCE_COMMAND_PART_CLAMP,
    JIG_SEQUENCE_COMMAND_PART_RELEASE,
    JIG_SEQUENCE_COMMAND_PART_REMOVE,
    JIG_SEQUENCE_COMMAND_AUTO_PART_CHANGE,
    JIG_SEQUENCE_STATUS_IDLE,
    JIG_SEQUENCE_STATUS_DONE,
    JIG_SEQUENCE_ERROR_NONE,
)

from utils.modbus_manager import ModbusManager
from utils.gpio_handler import GPIOHandler
from utils.gpio_input_handler import GPIOInputHandler
from utils.dfr0558_handler import DFR0558Manager


class HardwareService(QObject):
    """
    Yhteiset fyysiset I/O-rajapinnat.

    Vastuurajat:

    - Arduino Opta / RS485 Modbus:
      opta_modbus_manager

    - Raspberry Pi:n suorat GPIO-outputit:
      raspberry_gpio_output_handler

    - Raspberry Pi:n suorat GPIO-inputit:
      raspberry_gpio_input_handler

    - Raspberry Pi:n paikallinen kappalelämpötila-anturi:
      dfr0558_manager

    ForTest-laitteet eivät kuulu tähän serviceen.
    ForTest 1 ja ForTest 2 kuuluvat ForTestServiceen.
    """

    def __init__(
        self,
        parent=None,
        dev_mode_modbus=True,
        dev_mode_gpio=True,
        modbus_port=None,
        modbus_baudrate=19200,
    ):
        super().__init__(parent)

        self.parent_window = parent

        self.dev_mode_modbus = dev_mode_modbus
        self.dev_mode_gpio = dev_mode_gpio

        if not dev_mode_modbus and not modbus_port:
            raise ValueError("Opta Modbus -portti puuttuu, kun DEV_MODE_MODBUS=False")

        self.opta_modbus_port = modbus_port
        self.opta_modbus_baudrate = modbus_baudrate
        self.opta_modbus_manager = None

        self.raspberry_gpio_output_handler = None
        self.raspberry_gpio_input_handler = None

        self.dfr0558_manager = None

        self.dev_relay_states = [False] * 8
        self.dev_emergency_stop_status = None
        self.dev_jig_sequence_status = JIG_SEQUENCE_STATUS_IDLE
        self.dev_jig_sequence_step = 0
        self.dev_jig_sequence_error = JIG_SEQUENCE_ERROR_NONE

        self._init_opta_modbus()
        self._init_raspberry_gpio_outputs()
        self._init_raspberry_gpio_inputs()
        self._init_part_temperature_sensor()

    # ------------------------------------------------------------
    # Alustus
    # ------------------------------------------------------------

    def _init_opta_modbus(self):
        if self.dev_mode_modbus:
            return

        try:
            self.opta_modbus_manager = ModbusManager(
                port=self.opta_modbus_port,
                baudrate=self.opta_modbus_baudrate,
            )

            if self.parent_window and hasattr(self.parent_window, "handle_modbus_result"):
                self.opta_modbus_manager.resultReady.connect(
                    self.parent_window.handle_modbus_result
                )

        except Exception as e:
            print(f"Varoitus: Opta Modbus -alustus epäonnistui: {e}")
            self.opta_modbus_manager = None

    def _init_raspberry_gpio_outputs(self):
        if self.dev_mode_gpio:
            return

        try:
            self.raspberry_gpio_output_handler = GPIOHandler()
        except Exception as e:
            print(f"Varoitus: Raspberry GPIO-outputtien alustus epäonnistui: {e}")
            self.raspberry_gpio_output_handler = None

    def _init_raspberry_gpio_inputs(self):
        if self.dev_mode_gpio:
            return

        try:
            self.raspberry_gpio_input_handler = GPIOInputHandler()

            if self.parent_window and hasattr(self.parent_window, "handle_button_press"):
                self.raspberry_gpio_input_handler.button_changed.connect(
                    self.parent_window.handle_button_press
                )

        except Exception as e:
            print(f"Varoitus: Raspberry GPIO-inputtien alustus epäonnistui: {e}")
            self.raspberry_gpio_input_handler = None

    def _init_part_temperature_sensor(self):
        if self.dev_mode_gpio:
            return

        try:
            self.dfr0558_manager = DFR0558Manager()

            if self.parent_window and hasattr(self.parent_window, "environment_status_bar"):
                self.dfr0558_manager.data_updated.connect(
                    self.parent_window.environment_status_bar.update_part_temperature_data
                )
                self.dfr0558_manager.error_occurred.connect(
                    self.parent_window.environment_status_bar.show_part_temperature_error
                )

        except Exception as e:
            print(f"Varoitus: DFR0558-anturin alustus epäonnistui: {e}")
            self.dfr0558_manager = None

    # ------------------------------------------------------------
    # Sisäiset apumetodit
    # ------------------------------------------------------------

    def _get_opta_modbus_manager_or_none(self):
        if self.dev_mode_modbus:
            return None

        return self.opta_modbus_manager

    # ------------------------------------------------------------
    # Ympäristöanturit
    # ------------------------------------------------------------

    def update_environment_sensors(self):
        if self.dfr0558_manager:
            self.dfr0558_manager.read_once()

    # ------------------------------------------------------------
    # Raspberry Pi GPIO-outputit
    # ------------------------------------------------------------

    def set_output(self, output_number, state):
        if self.dev_mode_gpio:
            return True, "DEV GPIO: ohjaus ohitettu"

        if not self.raspberry_gpio_output_handler:
            return False, "Raspberry GPIO-output handler ei ole käytössä"

        try:
            self.raspberry_gpio_output_handler.set_output(output_number, state)
            return True, ""
        except Exception as e:
            return False, f"Raspberry GPIO-outputin {output_number} ohjaus epäonnistui: {e}"

    # ------------------------------------------------------------
    # Arduino Opta / yhteinen Modbus-väylä
    # ------------------------------------------------------------

    def write_register(self, address, value):
        if self.dev_mode_modbus:
            return True

        opta_modbus_manager = self._get_opta_modbus_manager_or_none()

        if not opta_modbus_manager:
            return None

        return opta_modbus_manager.write_register(address, value)

    def read_registers_direct(self, address, count=1):
        """
        Synkroninen Opta-rekisteriluku HardwareServicen sisäiseen käyttöön.

        Tätä käytetään automaattisyklin tilan lukemiseen.
        Ei käytetä ForTest-väylälle.
        """
        if self.dev_mode_modbus:
            return None

        opta_modbus_manager = self._get_opta_modbus_manager_or_none()

        if not opta_modbus_manager:
            return None

        if not hasattr(opta_modbus_manager, "modbus_handler"):
            return None

        modbus_handler = opta_modbus_manager.modbus_handler

        if not modbus_handler or not modbus_handler.connected:
            return None

        try:
            return modbus_handler.read_holding_registers(address, count)
        except Exception:
            return None

    def request_system_shutdown(self):
        try:
            return self.write_register(SHUTDOWN_REQUEST_REGISTER, 1)
        except Exception as e:
            print(f"Varoitus: sammutusrekisterin kirjoitus epäonnistui: {e}")
            return None

    def reset_emergency_stop(self):
        try:
            result = self.write_register(EMERGENCY_RESET_REGISTER, 1)

            QTimer.singleShot(
                300,
                lambda: self.write_register(EMERGENCY_RESET_REGISTER, 0),
            )

            return result

        except Exception as e:
            print(f"Hätäseis-kuittaus epäonnistui: {e}")
            return None

    # ------------------------------------------------------------
    # Arduino Opta / jig-sekvenssit
    # ------------------------------------------------------------

    def _start_jig_sequence(self, command, sequence_name):
        """
        Käynnistää Optan jig-sekvenssin.

        Dualtest ei aja ajoituksia.
        Dualtest vain lähettää Optalle:
        19200 = command
        19201 = 1
        """
        if self.dev_mode_modbus:
            self.dev_jig_sequence_status = JIG_SEQUENCE_STATUS_DONE
            self.dev_jig_sequence_step = 0
            self.dev_jig_sequence_error = JIG_SEQUENCE_ERROR_NONE
            return True, f"DEV OPTA MODBUS: {sequence_name} -SEKVENSSI KÄYNNISTETTY"

        opta_modbus_manager = self._get_opta_modbus_manager_or_none()

        if not opta_modbus_manager:
            return False, "Opta ModbusManager ei ole käytössä"

        try:
            self.write_register(
                JIG_SEQUENCE_COMMAND_REGISTER,
                command,
            )

            self.write_register(
                JIG_SEQUENCE_START_REGISTER,
                1,
            )

            return True, f"{sequence_name} -SEKVENSSI KÄYNNISTETTY"

        except Exception as e:
            return False, f"{sequence_name} -sekvenssin käynnistys epäonnistui: {e}"

    def start_jig_part_clamp_sequence(self):
        return self._start_jig_sequence(
            JIG_SEQUENCE_COMMAND_PART_CLAMP,
            "KAPPALE KIINNI",
        )

    def start_jig_part_release_sequence(self):
        return self._start_jig_sequence(
            JIG_SEQUENCE_COMMAND_PART_RELEASE,
            "KAPPALE IRTI",
        )

    def start_jig_part_remove_sequence(self):
        return self._start_jig_sequence(
            JIG_SEQUENCE_COMMAND_PART_REMOVE,
            "KAPPALEEN POISTO",
        )

    def start_jig_auto_part_change_sequence(self):
        return self._start_jig_sequence(
            JIG_SEQUENCE_COMMAND_AUTO_PART_CHANGE,
            "AUTOMAATTINEN KAPPALEENVAIHTO",
        )

    def stop_jig_sequence(self):
        if self.dev_mode_modbus:
            self.dev_jig_sequence_status = JIG_SEQUENCE_STATUS_IDLE
            self.dev_jig_sequence_step = 0
            self.dev_jig_sequence_error = JIG_SEQUENCE_ERROR_NONE
            return True, "DEV OPTA MODBUS: JIG-SEKVENSSI KESKEYTETTY"

        opta_modbus_manager = self._get_opta_modbus_manager_or_none()

        if not opta_modbus_manager:
            return False, "Opta ModbusManager ei ole käytössä"

        try:
            self.write_register(JIG_SEQUENCE_STOP_REGISTER, 1)
            return True, "JIG-SEKVENSSI KESKEYTETTY"

        except Exception as e:
            return False, f"Jig-sekvenssin keskeytys epäonnistui: {e}"

    def read_jig_sequence_state(self):
        """
        Lukee Optan jig-sekvenssin tilan.

        Palauttaa:
        {
            "status": 0...3,
            "step": vaihe,
            "error": virhekoodi
        }

        tai None, jos luku epäonnistui.
        """
        if self.dev_mode_modbus:
            return {
                "status": self.dev_jig_sequence_status,
                "step": self.dev_jig_sequence_step,
                "error": self.dev_jig_sequence_error,
            }

        result = self.read_registers_direct(
            JIG_SEQUENCE_STATUS_REGISTER,
            JIG_SEQUENCE_STATE_REGISTER_COUNT,
        )

        if not result or not hasattr(result, "registers"):
            return None

        if len(result.registers) < 3:
            return None

        return {
            "status": result.registers[0],
            "step": result.registers[1],
            "error": result.registers[2],
        }

    def read_emergency_stop_status(self):
        if self.dev_mode_modbus:
            return self.dev_emergency_stop_status

        opta_modbus_manager = self._get_opta_modbus_manager_or_none()

        if opta_modbus_manager:
            return opta_modbus_manager.read_emergency_stop_status()

        return None

    # ------------------------------------------------------------
    # Arduino Opta / käsikäytön releohjaus
    # ------------------------------------------------------------

    def control_relay(self, relay_num, state):
        """
        Käsikäytön releohjaus Arduino Optan kautta.

        relay_num = 1...8
        state = True/False tai 1/0

        Palauttaa:
        (success: bool, message: str)
        """
        if relay_num < 1 or relay_num > 8:
            return False, "Virheellinen releen numero"

        if self.dev_mode_modbus:
            self.dev_relay_states[relay_num - 1] = bool(state)
            return True, f"DEV OPTA MODBUS: Rele {relay_num} -> {'ON' if state else 'OFF'}"

        opta_modbus_manager = self._get_opta_modbus_manager_or_none()

        if not opta_modbus_manager:
            return False, "Opta ModbusManager ei ole käytössä"

        try:
            opta_modbus_manager.toggle_relay(relay_num, int(bool(state)))
            return True, f"Rele {relay_num} -> {'ON' if state else 'OFF'}"

        except Exception as e:
            return False, f"Releen {relay_num} ohjaus epäonnistui: {e}"

    def get_relay_state(self, relay_num):
        if relay_num < 1 or relay_num > 8:
            return False

        if self.dev_mode_modbus:
            return self.dev_relay_states[relay_num - 1]

        return False

    # ------------------------------------------------------------
    # Siivous
    # ------------------------------------------------------------

    def cleanup(self):
        if self.opta_modbus_manager:
            self.opta_modbus_manager.cleanup()

        if self.raspberry_gpio_output_handler:
            self.raspberry_gpio_output_handler.cleanup()

        if self.raspberry_gpio_input_handler:
            self.raspberry_gpio_input_handler.cleanup()