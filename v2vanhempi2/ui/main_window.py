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
from utils.fortest_handler import DummyForTestHandler
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

        # Alusta hallintamanagerit
        self.modbus_manager = ModbusManager(port='/dev/ttyUSB0', baudrate=19200)
        self.fortest_manager = ForTestManager(port='/dev/ttyUSB1', baudrate=19200)
        if isinstance(self.fortest_manager.worker.fortest, DummyForTestHandler):
            self.testing_screen.update_status("ForTest-yhteys epäonnistui - laite ei ole kytkettynä", "WARNING")
        self.program_manager = ProgramManager()

        # Yhdistä signaalit
        self.modbus_manager.resultReady.connect(self.handle_modbus_result)
        self.fortest_manager.resultReady.connect(self.handle_fortest_result)

        # Tilaviestien näyttö
        self.status_notifier = StatusNotifier(self)

        # Alusta GPIO jos mahdollista
        try:
            self.gpio_handler = GPIOHandler()
        except Exception as e:
            print(f"Varoitus: GPIO-alustus epäonnistui: {e}")
            self.gpio_handler = None

        # Näytöt
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

        # Ajastimet
        self.emergency_stop_timer = QTimer(self)
        self.emergency_stop_timer.timeout.connect(self.check_emergency_stop)
        self.emergency_stop_timer.start(1000)  # Tarkista hätäseis kerran sekunnissa

        self.emergency_dialog_open = False
        self._dialog_opened_time = 0

        # Kytkimien lukuajastin
        self.switch_read_timer = QTimer(self)
        self.switch_read_timer.timeout.connect(self.check_switches)
        self.switch_read_timer.start(200)  # Tarkista kytkimet 150ms välein
        
        # Kytkimien muistit
        self.switch_memories = {
            16999: 0,  # STOP
            17000: 0,  # START
            17001: 0,  # TEST1
            17002: 0,  # TEST2
            17003: 0   # TEST3
        }

        # Tarkista käynnistyksen jälkeen yhteydet
        if not self.modbus_manager.is_connected():
            self.testing_screen.update_status("Modbus-yhteys epäonnistui", "WARNING")
        
        if isinstance(self.fortest_manager.worker.fortest, DummyForTestHandler):
            self.testing_screen.update_status("ForTest-laite ei kytkettynä", "WARNING")
            
    def check_emergency_stop(self):
        """Tarkista hätäseistila"""
        if not hasattr(self, 'modbus_manager') or not self.modbus_manager or not self.modbus_manager.is_connected():
            return

        try:
            status = self.modbus_manager.read_emergency_stop_status()
            
            # Jos hätäseis ei ole päällä, mutta dialog on auki, sulje se
            if status == 1 and self.emergency_dialog_open:
                if hasattr(self, '_emergency_dialog') and self._emergency_dialog is not None:
                    self._emergency_dialog.accept()
                    self._emergency_dialog = None
                    self.emergency_dialog_open = False

            # Jos hätäseis on päällä, mutta dialog ei ole auki, avaa se
            elif status == 0 and not self.emergency_dialog_open:
                self.emergency_dialog_open = True
                self._emergency_dialog = EmergencyStopDialog(self, self.modbus_manager)
                self._emergency_dialog.finished.connect(self.on_emergency_dialog_closed)
                self._emergency_dialog.exec_()
        except Exception as e:
            print(f"Virhe hätäseistilan tarkistuksessa: {e}")
            # Suljetaan timer jos yhteys katkeaa
            self.emergency_stop_timer.stop()

    def on_emergency_dialog_closed(self):
        """Hätäseisdialogin sulkemisen käsittely"""
        self.emergency_dialog_open = False
        self._emergency_dialog = None


    def check_switches(self):
        """Lukee kytkimien tilat modbus-rekistereistä yhdellä kutsulla"""
        if not self.modbus_manager.is_connected():
            return
        
        # Lue kaikki 5 rekisteriä (16999-17003) yhdellä kutsulla
        self.modbus_manager.read_register(16999, 5)

    def handle_modbus_result(self, result, op_code, error_msg):
        """Käsittelee modbus-kyselyn tuloksen"""
        if error_msg:
            # Päivitä tilaviesti päänäkymään
            self.testing_screen.update_status(error_msg, "ERROR")
            return
        
        if not result or not hasattr(result, 'registers'):
            return

        if op_code == 1:  # Rekisterin luku
            base_address = 16999
            
            # Käsittele kaikki rekisterit
            for offset, value in enumerate(result.registers):
                switch_reg = base_address + offset
                switch_state = value
                
                # Haetaan vanha tila
                old_state = self.switch_memories.get(switch_reg, 0)
                
                # Talleta uusi tila muistiin
                self.switch_memories[switch_reg] = switch_state
                
                # KÄSITTELE NOUSEVA REUNA (0->1)
                if switch_state == 1 and old_state == 0:
                    if switch_reg == 17000:  # START
                        self.testing_screen.start_test()
                    elif switch_reg == 16999:  # STOP
                        self.testing_screen.stop_test()
                    elif 17001 <= switch_reg <= 17003:  # TESTI 1-3
                        test_idx = switch_reg - 17001
                        panel = self.testing_screen.test_panels[test_idx]
                        panel.is_active = not panel.is_active
                        panel.update_button_style()
                        if self.gpio_handler:
                            self.gpio_handler.set_output(test_idx + 1, panel.is_active)

    def handle_fortest_result(self, result, op_code, error_msg):
        """Käsittelee ForTest-laitteen operaatiotulokset"""
        if op_code == 999:  # Erityinen koodi yhteyden epäonnistumiselle
            self.status_notifier.show_message(error_msg, StatusNotifier.WARNING)
            self.testing_screen.update_status(error_msg, "WARNING")
            return

        if result:
            msg = ""
            msg_type = StatusNotifier.INFO
            level = "INFO"

            if op_code == 1:  # Testin käynnistys
                msg = "Testi käynnistetty onnistuneesti"
                msg_type = StatusNotifier.SUCCESS
                level = "SUCCESS"
            elif op_code == 2:  # Testin pysäytys
                msg = "Testi pysäytetty"
                msg_type = StatusNotifier.INFO

            if msg:
                self.status_notifier.show_message(msg, msg_type)
                # Päivitä tilaviesti myös päänäkymään
                self.testing_screen.update_status(msg, level)

    def toggle_test_active(self, test_number, active):
        """Vaihda testin aktiivisuustila vain UI:n ja GPIO:n osalta"""
        # Varmista että test_number on sallituissa rajoissa
        if 1 <= test_number <= len(self.testing_screen.test_panels):
            panel = self.testing_screen.test_panels[test_number - 1]
            panel.is_active = active
            panel.update_button_style()

            # Ohjaa vain GPIO-lähtö
            if self.gpio_handler:
                self.gpio_handler.set_output(test_number, active)

    def on_program_selected(self, program_name):
        """Käsittelee ohjelman valinnan"""
        self.testing_screen.set_program_for_test(program_name)
        self.show_testing()

    def show_testing(self):
        """Näyttää testaussivun"""
        self.manual_screen.hide()
        self.program_selection_screen.hide()
        self.testing_screen.show()

    def show_manual(self):
        """Näyttää käsikäyttösivun"""
        self.testing_screen.hide()
        self.program_selection_screen.hide()
        self.manual_screen.show()

    def show_program_selection(self, test_number=None):
        """Näyttää ohjelman valintasivun"""
        if test_number is not None:
            self.testing_screen.current_test_panel = test_number

        self.testing_screen.hide()
        self.manual_screen.hide()
        self.program_selection_screen.show()

    def keyPressEvent(self, event: QKeyEvent):
        """Käsittelee näppäimistötapahtumat"""
        if event.key() == Qt.Key_Escape:
            if self.manual_screen.isVisible() or self.program_selection_screen.isVisible():
                self.show_testing()
            else:
                self.close()
        super().keyPressEvent(event)

    def show(self):
        """Näyttää ikkunan koko ruudussa"""
        self.showFullScreen()

    def closeEvent(self, event):
        """Käsittelee sovelluksen sulkemisen"""
        try:
            self.testing_screen.cleanup()
            self.manual_screen.cleanup()
            self.modbus_manager.cleanup()
            self.fortest_manager.cleanup()
            if self.gpio_handler:
                self.gpio_handler.cleanup()
        except Exception as e:
            print(f"Virhe sulkemisvaiheessa: {e}")
        super().closeEvent(event)