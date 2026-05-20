# services/hardware_service.py
from PyQt5.QtCore import QObject

from utils.modbus_manager import ModbusManager
from utils.gpio_handler import GPIOHandler
from utils.gpio_input_handler import GPIOInputHandler
from utils.dfr0558_handler import DFR0558Manager


class HardwareService(QObject):
    """
    Yhteiset fyysiset I/O-rajapinnat:
    - Opta / Modbus RTU
    - GPIO-outputit
    - GPIO-inputit
    - DFR0558 kappalelämpötila-anturi

    Tämä luokka ei sisällä UI-logiikkaa.
    """

    def __init__(
        self,
        parent=None,
        dev_mode_modbus=True,
        dev_mode_gpio=True,
        modbus_port="/dev/ttyUSB0",
        modbus_baudrate=19200,
    ):
        super().__init__(parent)

        self.parent_window = parent
        self.dev_mode_modbus = dev_mode_modbus
        self.dev_mode_gpio = dev_mode_gpio

        self.modbus_manager = None
        self.gpio_handler = None
        self.gpio_input_handler = None
        self.dfr0558_manager = None

        self._init_modbus(modbus_port, modbus_baudrate)
        self._init_gpio_outputs()
        self._init_gpio_inputs()
        self._init_part_temperature_sensor()

    def _init_modbus(self, port, baudrate):
        if self.dev_mode_modbus:
            return

        try:
            self.modbus_manager = ModbusManager(port=port, baudrate=baudrate)

            if self.parent_window and hasattr(self.parent_window, "handle_modbus_result"):
                self.modbus_manager.resultReady.connect(self.parent_window.handle_modbus_result)

        except Exception as e:
            print(f"Varoitus: ModbusManager-alustus epäonnistui: {e}")
            self.modbus_manager = None

    def _init_gpio_outputs(self):
        if self.dev_mode_gpio:
            return

        try:
            self.gpio_handler = GPIOHandler()
        except Exception as e:
            print(f"Varoitus: GPIO-outputtien alustus epäonnistui: {e}")
            self.gpio_handler = None

    def _init_gpio_inputs(self):
        if self.dev_mode_gpio:
            return

        try:
            self.gpio_input_handler = GPIOInputHandler()

            if self.parent_window and hasattr(self.parent_window, "handle_button_press"):
                self.gpio_input_handler.button_changed.connect(self.parent_window.handle_button_press)

        except Exception as e:
            print(f"Varoitus: GPIO-inputtien alustus epäonnistui: {e}")
            self.gpio_input_handler = None

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

    def update_environment_sensors(self):
        if self.dfr0558_manager:
            self.dfr0558_manager.read_once()

    def set_output(self, output_number, state):
        if self.gpio_handler:
            self.gpio_handler.set_output(output_number, state)

    def write_register(self, address, value):
        if self.modbus_manager:
            return self.modbus_manager.write_register(address, value)
        return None

    def toggle_relay(self, relay_num, state):
        if self.modbus_manager:
            return self.modbus_manager.toggle_relay(relay_num, state)
        return None

    def read_emergency_stop_status(self):
        if self.modbus_manager:
            return self.modbus_manager.read_emergency_stop_status()
        return None

    def is_modbus_connected(self):
        if not self.modbus_manager:
            return False

        if hasattr(self.modbus_manager, "is_connected"):
            return self.modbus_manager.is_connected()

        return False

    def cleanup(self):
        if self.dfr0558_manager:
            self.dfr0558_manager.cleanup()

        if self.gpio_input_handler:
            self.gpio_input_handler.cleanup()

        if self.modbus_manager:
            self.modbus_manager.cleanup()

        if self.gpio_handler:
            self.gpio_handler.cleanup()