# ui/main_window.py
from PyQt5.QtWidgets import QWidget, QApplication
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
from controllers.physical_button_controller import PhysicalButtonController
from controllers.modbus_result_controller import ModbusResultController
from controllers.fortest_result_controller import ForTestResultController
from controllers.top_bar_controller import TopBarController
from controllers.application_cleanup_controller import ApplicationCleanupController
from controllers.navigation_controller import NavigationController


DEV_MODE_FORTEST = True
DEV_MODE_MODBUS = True
DEV_MODE_GPIO = True


class MainWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setup_window()
        self.create_managers()
        self.create_screens()
        self.create_services()
        self.create_compatibility_refs()
        self.create_station_controllers()
        self.create_controllers()

    def setup_window(self):
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

    def create_managers(self):
        self.program_manager = ProgramManager()

    def create_screens(self):
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

    def create_services(self):
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

    def create_compatibility_refs(self):
        # Vanhojen komponenttien yhteensopivuus.
        self.modbus_manager = self.hardware_service.modbus_manager
        self.gpio_handler = self.hardware_service.gpio_handler
        self.gpio_input_handler = self.hardware_service.gpio_input_handler
        self.dfr0558_manager = self.hardware_service.dfr0558_manager

        # Vanhan yhden testerin yhteensopivuus station 1:lle.
        self.fortest_manager = self.fortest_service.get_manager(1)

    def create_station_controllers(self):
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

    def create_controllers(self):
        self.program_selection_controller = ProgramSelectionController(
            main_window=self,
            program_selection_screen=self.program_selection_screen,
            station_controllers=self.station_controllers,
        )

        self.navigation_controller = NavigationController(
            main_window=self,
            main_screen=self.main_screen,
            manual_screen=self.manual_screen,
            program_selection_screen=self.program_selection_screen,
            environment_status_bar=self.environment_status_bar,
            program_selection_controller=self.program_selection_controller,
        )

        self.emergency_stop_controller = EmergencyStopController(
            main_window=self,
            hardware_service=self.hardware_service,
            station_controllers=self.station_controllers,
            modbus_manager=self.modbus_manager,
        )

        self.physical_button_controller = PhysicalButtonController(
            station_controllers=self.station_controllers,
            hardware_service=self.hardware_service,
        )


        self.modbus_result_controller = ModbusResultController(
            station_controllers=self.station_controllers,
            emergency_stop_controller=self.emergency_stop_controller,
        )

        self.fortest_result_controller = ForTestResultController(
            station_controllers=self.station_controllers,
        )

        self.top_bar_controller = TopBarController(
            main_screen=self.main_screen,
            environment_status_bar=self.environment_status_bar,
            hardware_service=self.hardware_service,
            fortest_service=self.fortest_service,
            dev_mode_fortest=DEV_MODE_FORTEST,
            parent=self,
        )

        self.application_cleanup_controller = ApplicationCleanupController(
            main_window=self,
        )

    def update_environment_sensors(self):
        """
        Vanha yhteensopivuusrajapinta sensoripäivityksille.
        Varsinainen logiikka on TopBarControllerissa.
        """

        if hasattr(self, "top_bar_controller") and self.top_bar_controller:
            self.top_bar_controller.update_environment_sensors()

    def update_top_bar_status(self):
        """
        Vanha yhteensopivuusrajapinta yläpalkin päivitykselle.
        Varsinainen logiikka on TopBarControllerissa.
        """

        if hasattr(self, "top_bar_controller") and self.top_bar_controller:
            self.top_bar_controller.update_status()

    def handle_button_press(self, button_name, is_pressed):
        """
        Vanha yhteensopivuusrajapinta GPIOInputHandlerille.
        Varsinainen logiikka on PhysicalButtonControllerissa.
        """

        if hasattr(self, "physical_button_controller") and self.physical_button_controller:
            self.physical_button_controller.handle_button_press(button_name, is_pressed)

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
        """
        Vanha yhteensopivuusrajapinta päänäkymään palaamiselle.
        Varsinainen logiikka on NavigationControllerissa.
        """

        if hasattr(self, "navigation_controller") and self.navigation_controller:
            self.navigation_controller.show_testing()

    def show_manual(self):
        """
        Vanha yhteensopivuusrajapinta käsikäytön avaamiselle.
        Varsinainen logiikka on NavigationControllerissa.
        """

        if hasattr(self, "navigation_controller") and self.navigation_controller:
            self.navigation_controller.show_manual()

    def show_program_selection(self, station_id=None):
        """
        Vanha yhteensopivuusrajapinta ohjelmanvalinnan avaamiselle.
        Varsinainen logiikka on NavigationControllerissa.
        """

        if hasattr(self, "navigation_controller") and self.navigation_controller:
            self.navigation_controller.show_program_selection(station_id)

    def keyPressEvent(self, event: QKeyEvent):
        handled = False

        if hasattr(self, "navigation_controller") and self.navigation_controller:
            handled = self.navigation_controller.handle_key_press(event)

        if not handled:
            super().keyPressEvent(event)

    def show(self):
        self.showFullScreen()

    def closeEvent(self, event):
        if hasattr(self, "application_cleanup_controller") and self.application_cleanup_controller:
            self.application_cleanup_controller.cleanup()

        super().closeEvent(event)