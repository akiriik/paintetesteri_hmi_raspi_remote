# ui/main_window.py
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeyEvent

from ui.screens.main_screen import MainScreen
from ui.screens.manual_screen import ManualScreen
from ui.screens.program_selection_screen import ProgramSelectionScreen
from ui.components.environment_status_bar import EnvironmentStatusBar

from utils.program_manager import ProgramManager

from services.hardware_service import HardwareService
from services.fortest_service import ForTestService

from controllers.station_controller import StationController
from controllers.program_selection_controller import ProgramSelectionController
from controllers.emergency_stop_controller import EmergencyStopController
from controllers.button_input_controller import ButtonInputController
from controllers.modbus_result_controller import ModbusResultController
from controllers.fortest_result_controller import ForTestResultController


DEV_MODE_FORTEST = True
DEV_MODE_MODBUS = True
DEV_MODE_GPIO = True


class MainWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Painetestaus")

        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        self.screen_width = screen_geometry.width()
        self.screen_height = screen_geometry.height()

        self.setGeometry(0, 0, self.screen_width, self.screen_height)
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                color: #333333;
            }
        """)

        self.DEV_MODE_FORTEST = DEV_MODE_FORTEST
        self.DEV_MODE_MODBUS = DEV_MODE_MODBUS
        self.DEV_MODE_GPIO = DEV_MODE_GPIO

        self.program_manager = ProgramManager()

        self.main_screen = MainScreen(self)
        self.main_screen.setGeometry(0, 0, self.screen_width, self.screen_height)

        self.manual_screen = ManualScreen(self)
        self.manual_screen.setGeometry(0, 0, self.screen_width, self.screen_height)
        self.manual_screen.hide()

        self.program_selection_screen = ProgramSelectionScreen(self, self.program_manager)
        self.program_selection_screen.setGeometry(0, 0, self.screen_width, self.screen_height)
        self.program_selection_screen.hide()

        self.environment_status_bar = EnvironmentStatusBar(self)
        self.environment_status_bar.setGeometry(265, 50, 750, 40)
        self.environment_status_bar.hide()

        self.hardware_service = HardwareService(
            parent=self,
            dev_mode_modbus=DEV_MODE_MODBUS,
            dev_mode_gpio=DEV_MODE_GPIO,
            modbus_port="/dev/ttyUSB0",
            modbus_baudrate=19200,
        )

        self.fortest_service = ForTestService(
            parent=self,
            dev_mode_fortest=DEV_MODE_FORTEST,
            station_ports={
                1: "/dev/ttyUSB1",
                2: None,
            },
            baudrate=19200,
        )

        # Vanhojen komponenttien yhteensopivuus.
        self.modbus_manager = self.hardware_service.modbus_manager
        self.gpio_handler = self.hardware_service.gpio_handler
        self.gpio_input_handler = self.hardware_service.gpio_input_handler
        self.dfr0558_manager = self.hardware_service.dfr0558_manager

        # Vanhan yhden testerin yhteensopivuus station 1:lle.
        self.fortest_manager = self.fortest_service.get_manager(1)

        self.station_controllers = {
            1: StationController(
                station_id=1,
                station_widget=self.main_screen.fortest1,
                main_window=self,
                fortest_service=self.fortest_service,
                hardware_service=self.hardware_service,
                dev_mode_fortest=DEV_MODE_FORTEST,
                parent=self,
            ),
            2: StationController(
                station_id=2,
                station_widget=self.main_screen.fortest2,
                main_window=self,
                fortest_service=self.fortest_service,
                hardware_service=self.hardware_service,
                dev_mode_fortest=DEV_MODE_FORTEST,
                parent=self,
            ),
        }

        self.program_selection_controller = ProgramSelectionController(
            main_window=self,
            program_selection_screen=self.program_selection_screen,
            station_controllers=self.station_controllers,
        )

        self.emergency_stop_controller = EmergencyStopController(
            main_window=self,
            hardware_service=self.hardware_service,
            station_controllers=self.station_controllers,
            modbus_manager=self.modbus_manager,
        )

        self.button_input_controller = ButtonInputController(
            station_controllers=self.station_controllers,
        )

        self.modbus_result_controller = ModbusResultController(
            station_controllers=self.station_controllers,
            emergency_stop_controller=self.emergency_stop_controller,
        )

        self.fortest_result_controller = ForTestResultController(
            station_controllers=self.station_controllers,
        )

        self.top_bar_timer = QTimer(self)
        self.top_bar_timer.timeout.connect(self.update_top_bar_status)
        self.top_bar_timer.start(1000)

        self.update_top_bar_status()

    def update_environment_sensors(self):
        self.hardware_service.update_environment_sensors()

    def update_top_bar_status(self):
        if not hasattr(self, "main_screen"):
            return

        if not hasattr(self.main_screen, "environment_bar"):
            return

        environment_bar = self.main_screen.environment_bar

        if hasattr(self, "hardware_service") and self.hardware_service:
            environment_bar.update_hardware_status(
                self.hardware_service.get_connection_status_text()
            )

        fortest_status_text = self.get_fortest_status_text()
        environment_bar.update_fortest_status(fortest_status_text)

        if hasattr(self, "environment_status_bar") and self.environment_status_bar:
            self.environment_status_bar.update_main_environment_bar()

    def get_fortest_status_text(self):
        if self.DEV_MODE_FORTEST:
            return "FORTEST 1: DEV    FORTEST 2: DEV"

        f1_ok = self.fortest_service.is_connected(1)
        f2_ok = self.fortest_service.is_connected(2)

        f1_text = "FORTEST 1: OK" if f1_ok else "FORTEST 1: EI YHTEYTTÄ"

        station2_port = self.fortest_service.station_ports.get(2)
        if not station2_port:
            f2_text = "FORTEST 2: EI MÄÄRITETTY"
        else:
            f2_text = "FORTEST 2: OK" if f2_ok else "FORTEST 2: EI YHTEYTTÄ"

        return f"{f1_text}    {f2_text}"

    def handle_button_press(self, button_name, is_pressed):
        """
        Vanha yhteensopivuusrajapinta GPIOInputHandlerille.
        Varsinainen logiikka on ButtonInputControllerissa.
        """

        if hasattr(self, "button_input_controller") and self.button_input_controller:
            self.button_input_controller.handle_button_press(button_name, is_pressed)

    def handle_modbus_result(self, result, op_code, error_msg):
        """
        Vanha yhteensopivuusrajapinta ModbusManagerille.
        Varsinainen logiikka on ModbusResultControllerissa.
        """

        if hasattr(self, "modbus_result_controller") and self.modbus_result_controller:
            self.modbus_result_controller.handle_result(result, op_code, error_msg)

    def handle_fortest_result(self, station_id, result, op_code, error_msg):
        """
        Vanha yhteensopivuusrajapinta ForTestService / ForTestManagerille.
        Varsinainen logiikka on ForTestResultControllerissa.
        """

        if hasattr(self, "fortest_result_controller") and self.fortest_result_controller:
            self.fortest_result_controller.handle_result(
                station_id,
                result,
                op_code,
                error_msg,
            )

    def show_testing(self):
        self.environment_status_bar.hide()
        self.manual_screen.hide()
        self.program_selection_screen.hide()
        self.main_screen.show()
        self.update_top_bar_status()

    def show_manual(self):
        self.main_screen.hide()
        self.environment_status_bar.hide()
        self.program_selection_screen.hide()
        self.manual_screen.show()

    def show_program_selection(self, station_id=None):
        self.program_selection_controller.open_for_station(station_id)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            if self.manual_screen.isVisible() or self.program_selection_screen.isVisible():
                if self.program_selection_screen.isVisible():
                    self.program_selection_controller.cancel_selection()
                else:
                    self.show_testing()
            else:
                self.close()

        super().keyPressEvent(event)

    def show(self):
        self.showFullScreen()

    def closeEvent(self, event):
        try:
            if hasattr(self, "top_bar_timer") and self.top_bar_timer:
                self.top_bar_timer.stop()

            if hasattr(self, "fortest_result_controller") and self.fortest_result_controller:
                self.fortest_result_controller.cleanup()

            if hasattr(self, "modbus_result_controller") and self.modbus_result_controller:
                self.modbus_result_controller.cleanup()

            if hasattr(self, "button_input_controller") and self.button_input_controller:
                self.button_input_controller.cleanup()

            if hasattr(self, "emergency_stop_controller") and self.emergency_stop_controller:
                self.emergency_stop_controller.cleanup()

            for controller in self.station_controllers.values():
                controller.cleanup()

            if hasattr(self, "environment_status_bar") and self.environment_status_bar:
                self.environment_status_bar.cleanup()

            if hasattr(self, "manual_screen") and self.manual_screen:
                self.manual_screen.cleanup()

            if hasattr(self, "main_screen") and self.main_screen:
                if hasattr(self.main_screen, "cleanup"):
                    self.main_screen.cleanup()

            if hasattr(self, "fortest_service") and self.fortest_service:
                self.fortest_service.cleanup()

            if hasattr(self, "hardware_service") and self.hardware_service:
                self.hardware_service.cleanup()

        except Exception:
            print("Virhe sovelluksen sulkemisessa")

        super().closeEvent(event)