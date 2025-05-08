# ui/main_window.py
import sys
import os
import time
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeyEvent

from ui.screens.testing_screen import TestingScreen
from ui.screens.manual_screen import ManualScreen
from ui.screens.program_selection_screen import ProgramSelectionScreen
from ui.components.emergency_stop_dialog import EmergencyStopDialog
from ui.components.status_notifier import StatusNotifier

from utils.modbus_manager import ModbusManager
from utils.fortest_manager import ForTestManager
from utils.gpio_handler import GPIOHandler
from utils.program_manager import ProgramManager

class MainWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Painetestaus")
        self.setGeometry(0, 0, 1280, 720)
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                color: #333333;
            }
        """)

        self.modbus_manager = ModbusManager(port='/dev/ttyUSB0', baudrate=19200)
        self.fortest_manager = ForTestManager(port='/dev/ttyUSB1', baudrate=19200)
        self.program_manager = ProgramManager()

        self.modbus_manager.resultReady.connect(self.handle_modbus_result)
        self.fortest_manager.resultReady.connect(self.handle_fortest_result)

        self.status_notifier = StatusNotifier(self)

        try:
            self.gpio_handler = GPIOHandler()
        except Exception as e:
            print(f"Varoitus: GPIO-alustus epäonnistui: {e}")
            self.gpio_handler = None

        self.testing_screen = TestingScreen(self)
        self.testing_screen.setGeometry(0, 0, 1280, 720)
        self.testing_screen.program_selection_requested.connect(self.show_program_selection)

        self.manual_screen = ManualScreen(self)
        self.manual_screen.setGeometry(0, 0, 1280, 720)
        self.manual_screen.hide()

        self.program_selection_screen = ProgramSelectionScreen(self)
        self.program_selection_screen.setGeometry(0, 0, 1280, 720)
        self.program_selection_screen.hide()
        self.program_selection_screen.program_selected.connect(self.on_program_selected)

        self.emergency_stop_timer = QTimer(self)
        self.emergency_stop_timer.timeout.connect(self.check_emergency_stop)
        self.emergency_stop_timer.start(1000)

        self.emergency_dialog_open = False
        self._dialog_opened_time = 0

        self.switch_read_timer = QTimer(self)
        self.switch_read_timer.timeout.connect(self.check_switches)
        self.switch_read_timer.start(150)

    def check_emergency_stop(self):
        if not self.modbus_manager.is_connected():
            return

        status = self.modbus_manager.read_emergency_stop_status()

        if status == 1 and self.emergency_dialog_open:
            if hasattr(self, '_emergency_dialog') and self._emergency_dialog is not None:
                self._emergency_dialog.accept()
                self._emergency_dialog = None
                self.emergency_dialog_open = False

        elif status == 0 and not self.emergency_dialog_open:
            self.emergency_dialog_open = True
            self._emergency_dialog = EmergencyStopDialog(self, self.modbus_manager)
            self._emergency_dialog.finished.connect(self.on_emergency_dialog_closed)
            self._emergency_dialog.exec_()

    def on_emergency_dialog_closed(self):
        self.emergency_dialog_open = False
        self._emergency_dialog = None

    def handle_modbus_result(self, result, op_code, error_msg):
        if error_msg:
            self.status_notifier.show_message(error_msg, StatusNotifier.ERROR)
            if hasattr(self.testing_screen, 'log_panel'):
                self.testing_screen.log_panel.add_log_entry(error_msg, "ERROR")
            self._read_next_register()
            return

        if op_code == 1 and result and hasattr(result, 'registers') and len(result.registers) > 0:
            switch_state = result.registers[0]
            switch_reg = getattr(self, '_current_read_address', None)

            if switch_reg is None:
                self._read_next_register()
                return

            if switch_reg == 17000 and switch_state == 1:
                self.testing_screen.start_test()

            elif switch_reg == 16999 and switch_state == 1:
                self.testing_screen.stop_test()

            elif 17001 <= switch_reg <= 17003:
                test_idx = switch_reg - 17001
                panel = self.testing_screen.test_panels[test_idx]

                if hasattr(self.testing_screen, 'log_panel'):
                    self.testing_screen.log_panel.add_log_entry(
                        f"Testin {test_idx+1} kytkin tila: {'aktiivinen' if switch_state == 1 else 'ei-aktiivinen'}",
                        "INFO"
                    )

                if not hasattr(panel, '_last_register_value'):
                    panel._last_register_value = 0

                if switch_state == 1 and panel._last_register_value == 0:
                    panel.is_active = not panel.is_active
                    panel.update_button_style()
                    if self.gpio_handler:
                        self.gpio_handler.set_output(test_idx + 1, panel.is_active)

                panel._last_register_value = switch_state

        self._read_next_register()

    def handle_fortest_result(self, result, op_code, error_msg):
        if error_msg:
            self.status_notifier.show_message(error_msg, StatusNotifier.ERROR)
            if hasattr(self.testing_screen, 'log_panel'):
                self.testing_screen.log_panel.add_log_entry(error_msg, "ERROR")

        if result:
            msg = ""
            msg_type = StatusNotifier.INFO

            if op_code == 1:
                msg = "Testi käynnistetty onnistuneesti"
                msg_type = StatusNotifier.SUCCESS
            elif op_code == 2:
                msg = "Testi pysäytetty"
                msg_type = StatusNotifier.INFO

            if msg:
                self.status_notifier.show_message(msg, msg_type)
                if hasattr(self.testing_screen, 'log_panel'):
                    level = "INFO"
                    if msg_type == StatusNotifier.SUCCESS:
                        level = "SUCCESS"
                    elif msg_type == StatusNotifier.WARNING:
                        level = "WARNING"
                    elif msg_type == StatusNotifier.ERROR:
                        level = "ERROR"

                    self.testing_screen.log_panel.add_log_entry(msg, level)

    def check_switches(self):
        if not self.modbus_manager.is_connected():
            return

        self._pending_reads = [16999, 17000, 17001, 17002, 17003]
        self._read_next_register()

    def _read_next_register(self):
        if hasattr(self, '_pending_reads') and self._pending_reads:
            address = self._pending_reads.pop(0)
            self._current_read_address = address
            self.modbus_manager.read_register(address, 1)

    def on_program_selected(self, program_name):
        self.testing_screen.set_program_for_test(program_name)
        self.show_testing()

    def show_testing(self):
        self.manual_screen.hide()
        self.program_selection_screen.hide()
        self.testing_screen.show()

    def show_manual(self):
        self.testing_screen.hide()
        self.program_selection_screen.hide()
        self.manual_screen.show()

    def show_program_selection(self, test_number=None):
        if test_number is not None:
            self.testing_screen.current_test_panel = test_number

        self.testing_screen.hide()
        self.manual_screen.hide()
        self.program_selection_screen.show()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            if self.manual_screen.isVisible() or self.program_selection_screen.isVisible():
                self.show_testing()
            else:
                self.close()
        super().keyPressEvent(event)

    def show(self):
        self.showFullScreen()

    def closeEvent(self, event):
        self.testing_screen.cleanup()
        self.manual_screen.cleanup()
        self.modbus_manager.cleanup()
        self.fortest_manager.cleanup()
        if hasattr(self, 'gpio_handler') and self.gpio_handler:
            self.gpio_handler.cleanup()
        super().closeEvent(event)
