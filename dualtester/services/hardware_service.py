# services/hardware_service.py
import time

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
    JIG_SEQUENCE_STATUS_RUNNING,
    JIG_SEQUENCE_STATUS_DONE,
    JIG_SEQUENCE_STATUS_ERROR,
    JIG_SEQUENCE_ERROR_NONE,
)

from utils.modbus_manager import ModbusManager
from utils.gpio_handler import GPIOHandler
from utils.gpio_input_handler import GPIOInputHandler
from utils.dfr0558_handler import DFR0558Manager


JIG_START_CONFIRM_TIMEOUT_S = 2.0
JIG_SEQUENCE_MAX_RUNTIME_S = 15.0
JIG_SYNTHETIC_ERROR_STATE_LOST = 102
JIG_SYNTHETIC_ERROR_RUNTIME_TIMEOUT = 103


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

        self.active_jig_sequence_name = None
        self.active_jig_sequence_deadline = None

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

    def _get_opta_modbus_handler_or_none(self):
        opta_modbus_manager = self._get_opta_modbus_manager_or_none()

        if not opta_modbus_manager:
            return None

        modbus_handler = getattr(opta_modbus_manager, "modbus_handler", None)

        if not modbus_handler or not modbus_handler.connected:
            return None

        return modbus_handler

    def _write_register_direct(self, address, value):
        """
        Kriittinen synkroninen Opta-kirjoitus.

        Jig-sekvenssin command/start/stop tarvitsee todellisen Modbus-vastauksen,
        eikä pelkkää taustajonoon lisäämistä. ModbusHandler sarjallistaa tämän
        worker-säikeen liikenteen kanssa samalla I/O-lukolla.
        """
        if self.dev_mode_modbus:
            return True

        modbus_handler = self._get_opta_modbus_handler_or_none()

        if not modbus_handler:
            return False

        try:
            result = modbus_handler.write_register(address, value)
        except Exception:
            return False

        if not result:
            return False

        if hasattr(result, "isError") and result.isError():
            return False

        return True

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

        modbus_handler = self._get_opta_modbus_handler_or_none()

        if not modbus_handler:
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

    def _read_jig_sequence_state_raw(self):
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

    def _clear_active_jig_sequence(self):
        self.active_jig_sequence_name = None
        self.active_jig_sequence_deadline = None

    def _make_jig_error_state(self, error_code):
        return {
            "status": JIG_SEQUENCE_STATUS_ERROR,
            "step": 0,
            "error": error_code,
        }

    def _wait_for_jig_running(self, sequence_name):
        started_at = time.monotonic()
        deadline = started_at + JIG_START_CONFIRM_TIMEOUT_S

        while time.monotonic() < deadline:
            state = self._read_jig_sequence_state_raw()

            if state:
                status = state.get("status")

                if status == JIG_SEQUENCE_STATUS_RUNNING:
                    self.active_jig_sequence_name = sequence_name
                    self.active_jig_sequence_deadline = (
                        time.monotonic() + JIG_SEQUENCE_MAX_RUNTIME_S
                    )
                    return True, f"{sequence_name} -SEKVENSSI KÄYNNISSÄ"

                if (
                    status == JIG_SEQUENCE_STATUS_ERROR
                    and time.monotonic() - started_at >= 0.25
                ):
                    error = state.get("error")
                    return False, f"{sequence_name} - Opta ilmoitti virheen {error}"

            time.sleep(0.05)

        self._write_register_direct(JIG_SEQUENCE_STOP_REGISTER, 1)
        self._clear_active_jig_sequence()
        return (
            False,
            f"{sequence_name} - RUNNING-kuittausta ei saatu "
            f"{JIG_START_CONFIRM_TIMEOUT_S:.0f} sekunnissa",
        )

    def _start_jig_sequence(self, command, sequence_name):
        """
        Käynnistää Optan jig-sekvenssin varmennetusti.

        Ensin command- ja start-rekisterit kirjoitetaan synkronisesti ja
        niiden Modbus-vastaukset tarkistetaan. Onnistuminen palautetaan vasta,
        kun Opta on oikeasti ilmoittanut JIG_SEQUENCE_STATUS_RUNNING.
        """
        if self.dev_mode_modbus:
            self.dev_jig_sequence_status = JIG_SEQUENCE_STATUS_DONE
            self.dev_jig_sequence_step = 0
            self.dev_jig_sequence_error = JIG_SEQUENCE_ERROR_NONE
            return True, f"DEV OPTA MODBUS: {sequence_name} -SEKVENSSI KÄYNNISTETTY"

        if not self._get_opta_modbus_handler_or_none():
            return False, "Opta ModbusManager ei ole käytössä"

        current_state = self._read_jig_sequence_state_raw()

        if not current_state:
            return False, f"{sequence_name} - Optan jig-tilaa ei voitu lukea"

        if current_state.get("status") == JIG_SEQUENCE_STATUS_RUNNING:
            return False, "Optan jig-sekvenssi on jo käynnissä"

        self._clear_active_jig_sequence()

        if not self._write_register_direct(JIG_SEQUENCE_COMMAND_REGISTER, command):
            return False, f"{sequence_name} - komentorekisterin kirjoitus epäonnistui"

        if not self._write_register_direct(JIG_SEQUENCE_START_REGISTER, 1):
            self._write_register_direct(JIG_SEQUENCE_COMMAND_REGISTER, 0)
            return False, f"{sequence_name} - start-rekisterin kirjoitus epäonnistui"

        return self._wait_for_jig_running(sequence_name)

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
            self._clear_active_jig_sequence()
            return True, "DEV OPTA MODBUS: JIG-SEKVENSSI KESKEYTETTY"

        if not self._get_opta_modbus_handler_or_none():
            return False, "Opta ModbusManager ei ole käytössä"

        if not self._write_register_direct(JIG_SEQUENCE_STOP_REGISTER, 1):
            return False, "Jig-sekvenssin keskeytys epäonnistui"

        self._clear_active_jig_sequence()
        return True, "JIG-SEKVENSSI KESKEYTETTY"

    def read_jig_sequence_state(self):
        """
        Lukee Optan jig-sekvenssin tilan ja valvoo jo RUNNING-kuitattua ajoa.

        Jos kuitattu sekvenssi putoaa IDLE-tilaan ilman DONE-tilaa tai jää
        RUNNING-tilaan yli 15 sekunniksi, palautetaan hallittu ERROR. Tällöin
        StationController purkaa automaattiajon eikä jää odottamaan ikuisesti.
        """
        if self.dev_mode_modbus:
            return {
                "status": self.dev_jig_sequence_status,
                "step": self.dev_jig_sequence_step,
                "error": self.dev_jig_sequence_error,
            }

        state = self._read_jig_sequence_state_raw()

        if not self.active_jig_sequence_name:
            return state

        if not state:
            if (
                self.active_jig_sequence_deadline is not None
                and time.monotonic() >= self.active_jig_sequence_deadline
            ):
                self._write_register_direct(JIG_SEQUENCE_STOP_REGISTER, 1)
                self._clear_active_jig_sequence()
                return self._make_jig_error_state(
                    JIG_SYNTHETIC_ERROR_RUNTIME_TIMEOUT
                )

            return None

        status = state.get("status")

        if status in (JIG_SEQUENCE_STATUS_DONE, JIG_SEQUENCE_STATUS_ERROR):
            self._clear_active_jig_sequence()
            return state

        if status == JIG_SEQUENCE_STATUS_IDLE:
            self._clear_active_jig_sequence()
            return self._make_jig_error_state(
                JIG_SYNTHETIC_ERROR_STATE_LOST
            )

        if (
            self.active_jig_sequence_deadline is not None
            and time.monotonic() >= self.active_jig_sequence_deadline
        ):
            self._write_register_direct(JIG_SEQUENCE_STOP_REGISTER, 1)
            self._clear_active_jig_sequence()
            return self._make_jig_error_state(
                JIG_SYNTHETIC_ERROR_RUNTIME_TIMEOUT
            )

        return state

    def read_emergency_stop_status(self):
        if self.dev_mode_modbus:
            return self.dev_emergency_stop_status

        opta_modbus_manager = self._get_opta_modbus_manager_or_none()

        if opta_modbus_manager:
            return opta_modbus_manager.read_emergency_stop_status()

        return None

    def get_connection_status_text(self):
        """
        Palauttaa yläpalkille Opta / hardware-yhteyden tilatekstin.

        Tätä kutsuu TopBarController.
        """
        if self.dev_mode_modbus:
            opta_text = "OPTA: DEV"
        elif self.opta_modbus_manager and self.opta_modbus_manager.is_connected():
            opta_text = "OPTA: OK"
        else:
            opta_text = "OPTA: EI YHTEYTTÄ"

        if self.dev_mode_gpio:
            gpio_text = "GPIO: DEV"
        else:
            gpio_ok = (
                self.raspberry_gpio_output_handler is not None
                or self.raspberry_gpio_input_handler is not None
            )
            gpio_text = "GPIO: OK" if gpio_ok else "GPIO: EI KÄYTÖSSÄ"

        return f"{opta_text}    {gpio_text}"

    def is_modbus_connected(self):
        """
        Palauttaa Opta Modbus -yhteyden tilan.

        Tätä kutsuu EmergencyStopController.
        """
        if self.dev_mode_modbus:
            return True

        if not self.opta_modbus_manager:
            return False

        return self.opta_modbus_manager.is_connected()

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
        self._clear_active_jig_sequence()

        if self.opta_modbus_manager:
            self.opta_modbus_manager.cleanup()

        if self.raspberry_gpio_output_handler:
            self.raspberry_gpio_output_handler.cleanup()

        if self.raspberry_gpio_input_handler:
            self.raspberry_gpio_input_handler.cleanup()
