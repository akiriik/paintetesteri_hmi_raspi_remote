# services/hardware_service.py
import time
from concurrent.futures import ThreadPoolExecutor

from PyQt5.QtCore import QObject, QTimer, pyqtSignal, Qt

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

    emergencyStatusReady = pyqtSignal(object)
    writeAcknowledged = pyqtSignal(int, int, bool, str)
    jigStartFinished = pyqtSignal(int, bool, str)
    jigStateReady = pyqtSignal(int, object)
    jigStopFinished = pyqtSignal(int, bool, str)
    _jigJobComplete = pyqtSignal(str, int, object)

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

        # Kaikki jig-operaatiot suoritetaan järjestyksessä omassa workerissä.
        # Qt-pääsäikeeseen ei tehdä yhtään suoraa jig-Modbus-operaatiota.
        self._jig_executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="opta-jig",
        )
        self._jig_owner_station = None
        self._jig_operation_pending = False
        self._jig_state_pending = False
        self._jig_stop_pending = False
        # Aina queued: myös välittömästi valmistuvan futuren kuittaus
        # käsitellään vasta, kun pyynnön lähettäjä on asettanut oman tilansa.
        self._jigJobComplete.connect(
            self._handle_jig_job_complete, Qt.QueuedConnection
        )

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

            self.opta_modbus_manager.emergencyStatusReady.connect(
                self.emergencyStatusReady.emit
            )
            self.opta_modbus_manager.writeAcknowledged.connect(
                self.writeAcknowledged.emit
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
        """Jonota Opta-kirjoitus; paluuarvo ei tarkoita laitteen kuittausta."""
        if self.dev_mode_modbus:
            QTimer.singleShot(
                0,
                lambda: self.writeAcknowledged.emit(
                    int(address), int(value), True, ""
                ),
            )
            return True

        manager = self._get_opta_modbus_manager_or_none()
        if not manager:
            return False

        return bool(manager.write_register(address, value))

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
    # Asynkroninen jigin omistajuus ja tehtäväjono
    # ------------------------------------------------------------

    def _submit_jig_job(self, kind, station_id, method):
        try:
            future = self._jig_executor.submit(method)
            def complete(f):
                try:
                    result = f.result()
                except Exception as exc:
                    result = (
                        (False, f"Optan jig-worker: {exc}")
                        if kind != "state"
                        else None
                    )
                self._jigJobComplete.emit(kind, station_id, result)
            future.add_done_callback(complete)
            return True
        except Exception as exc:
            print(f"Optan jig-tehtävän jonotusvirhe: {exc}")
            return False

    def is_jig_busy(self):
        """Varattu jigi estää molempien asemien uuden paineistuksen."""
        return self._jig_owner_station is not None

    def request_jig_start(self, station_id, hardware_method_name):
        """Jigin voi varata vain yksi asema kerrallaan."""
        stations = getattr(self.parent_window, "station_controllers", {}) or {}
        for other_id, station in stations.items():
            if (
                station.is_running
                or getattr(station, "_start_request_pending", False)
                or getattr(station, "waiting_result_from_finished_test", False)
            ):
                return False, f"JIGI ESTETTY: TESTI KÄYNNISSÄ ASEMALLA {other_id}"
        if hardware_method_name not in {
            "start_jig_part_clamp_sequence",
            "start_jig_part_release_sequence",
            "start_jig_part_remove_sequence",
        }:
            return False, "Tuntematon jig-sekvenssi"

        if (
            self._jig_owner_station is not None
            and self._jig_owner_station != station_id
        ):
            return False, f"Jigi on käytössä asemalla {self._jig_owner_station}"

        if self._jig_operation_pending or self._jig_stop_pending:
            return False, "Edellinen jig-komento on vielä käsittelyssä"

        self._jig_owner_station = station_id
        self._jig_operation_pending = True

        method = getattr(self, hardware_method_name)
        if not self._submit_jig_job("start", station_id, method):
            self._jig_operation_pending = False
            return False, "Optan jig-komennon jonotus epäonnistui"

        return True, "JIG-KOMENTO LÄHETETTY - ODOTETAAN RUNNING-KUITTAUSTA"

    def request_jig_state(self, station_id):
        if self._jig_owner_station != station_id:
            return False
        if self._jig_state_pending or self._jig_operation_pending or self._jig_stop_pending:
            return False

        self._jig_state_pending = True
        if not self._submit_jig_job(
            "state", station_id, self.read_jig_sequence_state
        ):
            self._jig_state_pending = False
            return False
        return True

    def _stop_jig_confirmed(self):
        if self.dev_mode_modbus:
            return self.stop_jig_sequence()

        success, message = self.stop_jig_sequence()
        if not success:
            return False, message

        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            state = self._read_jig_sequence_state_raw()
            if state and state.get("status") != JIG_SEQUENCE_STATUS_RUNNING:
                return True, "JIG PYSÄYTETTY JA OPTA KUITANNUT"
            time.sleep(0.1)

        return False, "Optan jig-pysäytyksen tilakuittaus puuttuu"

    def request_jig_stop(self, station_id):
        if self._jig_owner_station not in (None, station_id):
            return False, "Toinen asema varaa jigin"
        if self._jig_stop_pending:
            return True, "JIG STOP JO JONOSSA"

        self._jig_stop_pending = True
        self._jig_owner_station = station_id

        if not self._submit_jig_job(
            "stop", station_id, self._stop_jig_confirmed
        ):
            self._jig_stop_pending = False
            return False, "JIG STOP EI MENNYT JONOON"

        return True, "JIG STOP JONOSSA"

    def _handle_jig_job_complete(self, kind, station_id, result):
        if kind == "start":
            self._jig_operation_pending = False
            success, message = result
            self.jigStartFinished.emit(station_id, bool(success), message)
            if not success:
                # Vikatilassa omistajuutta ei vapauteta ilman pysäytyskuittausta.
                print(f"Opta jig-asema {station_id}: {message}")
            return

        if kind == "state":
            self._jig_state_pending = False
            self.jigStateReady.emit(station_id, result)
            if (
                result
                and result.get("status") in (
                    JIG_SEQUENCE_STATUS_DONE,
                    JIG_SEQUENCE_STATUS_ERROR,
                )
                and self._jig_owner_station == station_id
                and not self._jig_operation_pending
                and not self._jig_stop_pending
            ):
                self._jig_owner_station = None
            return

        if kind == "stop":
            self._jig_stop_pending = False
            success, message = result
            if success and self._jig_owner_station == station_id:
                self._jig_owner_station = None
            self.jigStopFinished.emit(station_id, bool(success), message)

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
        # Optan firmware tukee yksittäiset REMOVE ja CLAMP -komennot;
        # koko automaattinen kappaleenvaihto on StationControllerin tilakone.
        # Ei lähetetä firmwarelle tukematonta komentoa 5.
        return False, (
            "AUTOMAATTINEN KAPPALEENVAIHTO TOTEUTETAAN "
            "RASPILLA REMOVE + CLAMP -SEKVENSSINÄ"
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

    def request_emergency_stop_status(self):
        """Tilaa hätäseistilan luku taustasäikeeseen (ei blokkaa UI:ta)."""
        if self.dev_mode_modbus:
            self.emergencyStatusReady.emit(self.dev_emergency_stop_status)
            return True

        manager = self._get_opta_modbus_manager_or_none()

        if not manager:
            self.emergencyStatusReady.emit(None)
            return False

        return manager.request_emergency_stop_status()

    def read_emergency_stop_status(self):
        """Yhteensopivuusmetodi: vain välimuistissa oleva arvo."""
        if self.dev_mode_modbus:
            return self.dev_emergency_stop_status

        manager = self._get_opta_modbus_manager_or_none()
        if not manager:
            return None

        return manager.read_emergency_stop_status()

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
        self._jig_executor.shutdown(wait=False, cancel_futures=True)
        self._clear_active_jig_sequence()

        if self.opta_modbus_manager:
            self.opta_modbus_manager.cleanup()

        if self.raspberry_gpio_output_handler:
            self.raspberry_gpio_output_handler.cleanup()

        if self.raspberry_gpio_input_handler:
            self.raspberry_gpio_input_handler.cleanup()
