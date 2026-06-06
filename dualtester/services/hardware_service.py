# services/hardware_service.py
from PyQt5.QtCore import QObject, QTimer

from config.modbus_config import (
    SHUTDOWN_REQUEST_REGISTER,
    EMERGENCY_RESET_REGISTER,
    JIG_SEQUENCE_COMMAND_REGISTER,
    JIG_SEQUENCE_START_REGISTER,
    JIG_SEQUENCE_STOP_REGISTER,
    JIG_SEQUENCE_COMMAND_PART_CLAMP,
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

        # Arduino Optan RS485 / Modbus RTU -väylä
        self.opta_modbus_port = modbus_port
        self.opta_modbus_baudrate = modbus_baudrate
        self.opta_modbus_manager = None

        # Raspberry Pi:n suorat GPIO-rajapinnat
        self.raspberry_gpio_output_handler = None
        self.raspberry_gpio_input_handler = None

        # Raspberry Pi:hin liitetty paikallinen anturi
        self.dfr0558_manager = None

        # DEV-tilan sisäiset tilat
        self.dev_relay_states = [False] * 8
        self.dev_emergency_stop_status = None

        self._init_opta_modbus()
        self._init_raspberry_gpio_outputs()
        self._init_raspberry_gpio_inputs()
        self._init_part_temperature_sensor()

    # ------------------------------------------------------------
    # Alustus
    # ------------------------------------------------------------

    def _init_opta_modbus(self):
        """
        Alustaa Arduino Optan RS485 / Modbus RTU -väylän.

        Tämä väylä ei ole ForTest-väylä.
        """
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
        """
        Alustaa Raspberry Pi:n suorat GPIO-outputit.

        Nämä eivät ole Optan I/O:ta.
        """
        if self.dev_mode_gpio:
            return

        try:
            self.raspberry_gpio_output_handler = GPIOHandler()
        except Exception as e:
            print(f"Varoitus: Raspberry GPIO-outputtien alustus epäonnistui: {e}")
            self.raspberry_gpio_output_handler = None

    def _init_raspberry_gpio_inputs(self):
        """
        Alustaa Raspberry Pi:n suorat GPIO-inputit.

        Nämä eivät ole Optan I/O:ta.
        """
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
        """
        Alustaa Raspberry Pi:hin liitetyn DFR0558-kappalelämpötila-anturin.
        """
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
        """
        Palauttaa Arduino Optan Modbus-managerin, jos se on käytössä.

        DEV-tilassa palauttaa None, koska fyysistä Opta-väylää ei käytetä.
        """
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
        """
        Raspberry Pi:n suoran GPIO-outputin ohjaus.

        output_number käyttää samaa numerointia kuin vanha GPIOHandler.
        """
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
        """
        Matala Opta Modbus -rekisterikirjoitus HardwareServicen sisäiseen käyttöön
        ja yksittäisiin yhteisiin järjestelmätoimintoihin.

        Tätä ei käytetä ForTest-laitteille.
        """
        if self.dev_mode_modbus:
            return True

        opta_modbus_manager = self._get_opta_modbus_manager_or_none()

        if not opta_modbus_manager:
            return None

        return opta_modbus_manager.write_register(address, value)

    def request_system_shutdown(self):
        """
        Lähettää järjestelmän sammutuspyynnön Arduino Optalle.
        """
        try:
            return self.write_register(SHUTDOWN_REQUEST_REGISTER, 1)
        except Exception as e:
            print(f"Varoitus: sammutusrekisterin kirjoitus epäonnistui: {e}")
            return None

    def reset_emergency_stop(self):
        """
        Kuittaa ohjelmallisen hätäseistilan Arduino Optan kautta.
        """
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

    def start_jig_part_clamp_sequence(self):
        """
        Käynnistää Optan jig-sekvenssin:
        kappale kiinni.

        Dualtest ei aja ajoituksia.
        Dualtest vain lähettää Optalle:
        19200 = 1
        19201 = 1
        """
        if self.dev_mode_modbus:
            return True, "DEV OPTA MODBUS: KAPPALE KIINNI -SEKVENSSI KÄYNNISTETTY"

        opta_modbus_manager = self._get_opta_modbus_manager_or_none()

        if not opta_modbus_manager:
            return False, "Opta ModbusManager ei ole käytössä"

        try:
            self.write_register(
                JIG_SEQUENCE_COMMAND_REGISTER,
                JIG_SEQUENCE_COMMAND_PART_CLAMP,
            )
            self.write_register(
                JIG_SEQUENCE_START_REGISTER,
                1,
            )

            return True, "KAPPALE KIINNI -SEKVENSSI KÄYNNISTETTY"

        except Exception as e:
            return False, f"Kappale kiinni -sekvenssin käynnistys epäonnistui: {e}"

    def stop_jig_sequence(self):
        """
        Keskeyttää Optan jig-sekvenssin.
        """
        if self.dev_mode_modbus:
            return True, "DEV OPTA MODBUS: JIG-SEKVENSSI KESKEYTETTY"

        opta_modbus_manager = self._get_opta_modbus_manager_or_none()

        if not opta_modbus_manager:
            return False, "Opta ModbusManager ei ole käytössä"

        try:
            self.write_register(JIG_SEQUENCE_STOP_REGISTER, 1)
            return True, "JIG-SEKVENSSI KESKEYTETTY"

        except Exception as e:
            return False, f"Jig-sekvenssin keskeytys epäonnistui: {e}"

    def read_emergency_stop_status(self):
        """
        Lukee ohjelmallisen hätäseistilan Arduino Optalta.
        """
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
            return False, f"Virheellinen rele: {relay_num}"

        state_bool = bool(state)
        state_int = 1 if state_bool else 0

        if self.dev_mode_modbus:
            self.dev_relay_states[relay_num - 1] = state_bool
            return True, f"DEV OPTA MODBUS: RELE {relay_num} {'PÄÄLLÄ' if state_bool else 'POIS'}"

        opta_modbus_manager = self._get_opta_modbus_manager_or_none()

        if not opta_modbus_manager:
            return False, "Opta ModbusManager ei ole käytössä"

        try:
            opta_modbus_manager.toggle_relay(relay_num, state_int)
            return True, f"RELE {relay_num} {'PÄÄLLÄ' if state_bool else 'POIS'}"
        except Exception as e:
            return False, f"Releen {relay_num} ohjaus epäonnistui: {e}"

    def toggle_relay(self, relay_num, state):
        """
        Yhteensopivuus vanhan kutsutavan kanssa.

        Uusi koodi käyttää control_relay().
        """
        success, message = self.control_relay(relay_num, state)
        return success

    # ------------------------------------------------------------
    # Yhteystilat
    # ------------------------------------------------------------

    def is_modbus_connected(self):
        """
        Palauttaa Arduino Optan Modbus-yhteyden tilan.

        Tämä ei kerro ForTest-yhteyksien tilaa.
        """
        if self.dev_mode_modbus:
            return False

        opta_modbus_manager = self._get_opta_modbus_manager_or_none()

        if not opta_modbus_manager:
            return False

        if hasattr(opta_modbus_manager, "is_connected"):
            return opta_modbus_manager.is_connected()

        return False

    def get_connection_status_text(self):
        if self.dev_mode_modbus:
            modbus_text = "OPTA MODBUS: DEV"
        elif self.is_modbus_connected():
            modbus_text = "OPTA MODBUS: OK"
        else:
            modbus_text = "OPTA MODBUS: EI YHTEYTTÄ"

        if self.dev_mode_gpio:
            gpio_text = "RASPI GPIO: DEV"
        elif self.raspberry_gpio_output_handler:
            gpio_text = "RASPI GPIO: OK"
        else:
            gpio_text = "RASPI GPIO: EI KÄYTÖSSÄ"

        if self.dev_mode_gpio:
            sensor_text = "ANTURI: DEV"
        elif self.dfr0558_manager:
            sensor_text = "ANTURI: OK"
        else:
            sensor_text = "ANTURI: EI KÄYTÖSSÄ"

        return f"{modbus_text}    {gpio_text}    {sensor_text}"

    # ------------------------------------------------------------
    # Sulkeminen
    # ------------------------------------------------------------

    def cleanup(self):
        if self.dfr0558_manager:
            self.dfr0558_manager.cleanup()

        if self.raspberry_gpio_input_handler:
            self.raspberry_gpio_input_handler.cleanup()

        if self.opta_modbus_manager:
            self.opta_modbus_manager.cleanup()

        if self.raspberry_gpio_output_handler:
            self.raspberry_gpio_output_handler.cleanup()