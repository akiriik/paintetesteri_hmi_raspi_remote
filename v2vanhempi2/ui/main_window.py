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

        # Konfiguroi pääikkuna
        self.setWindowTitle("Painetestaus")
        self.setGeometry(0, 0, 1280, 720)
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                color: #333333;
            }
        """)

        # Alusta managerit
        self.modbus_manager = ModbusManager(port='/dev/ttyUSB0', baudrate=19200)
        self.fortest_manager = ForTestManager(port='/dev/ttyUSB1', baudrate=19200)
        self.program_manager = ProgramManager()
        
        # Yhdistä signaalit
        self.modbus_manager.resultReady.connect(self.handle_modbus_result)
        self.fortest_manager.resultReady.connect(self.handle_fortest_result)
        
        # Luo statusilmoitin
        self.status_notifier = StatusNotifier(self)

        # Alusta GPIO-käsittelijä
        try:
            self.gpio_handler = GPIOHandler()
        except Exception as e:
            print(f"Varoitus: GPIO-alustus epäonnistui: {e}")
            self.gpio_handler = None

        # Luo näytöt
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

        # Lisää ajastin hätäseispiirin tilan tarkistamiseen
        self.emergency_stop_timer = QTimer(self)
        self.emergency_stop_timer.timeout.connect(self.check_emergency_stop)
        self.emergency_stop_timer.start(1000)  # Tarkista joka sekunti

        # Hätäseis-dialogi ei ole vielä avoinna
        self.emergency_dialog_open = False
        self._dialog_opened_time = 0  # Tallentaa milloin dialogi avattiin
        
        # Lisää ajastin kytkimien tilojen tarkistamiseen
        self.switch_read_timer = QTimer(self)
        self.switch_read_timer.timeout.connect(self.check_switches)
        self.switch_read_timer.start(150)  # Tarkista 150ms välein        


    def check_emergency_stop(self):
        """Tarkista hätäseispiirin tila"""
        if not self.modbus_manager.is_connected():
            return
        
        # Käytä synkronista lukua
        status = self.modbus_manager.read_emergency_stop_status()
        
        # Jos status on 1 ja dialogi on avoinna, sulje se
        if status == 1 and self.emergency_dialog_open:
            if hasattr(self, '_emergency_dialog') and self._emergency_dialog is not None:
                self._emergency_dialog.accept()
                self._emergency_dialog = None
                self.emergency_dialog_open = False
        
        # Jos status on 0, hätäseispiiri on aktiivinen
        elif status == 0 and not self.emergency_dialog_open:
            self.emergency_dialog_open = True
            self._emergency_dialog = EmergencyStopDialog(self, self.modbus_manager)
            self._emergency_dialog.finished.connect(self.on_emergency_dialog_closed)
            self._emergency_dialog.exec_()

    def on_emergency_dialog_closed(self):
        """Dialogi suljettu, nollataan lippu"""
        self.emergency_dialog_open = False
        self._emergency_dialog = None

    def handle_modbus_result(self, result, op_code, error_msg):
        """Käsittele Modbus-operaation tulos"""
        if error_msg:
            # Näytä virheviesti
            self.status_notifier.show_message(error_msg, StatusNotifier.ERROR)
            if hasattr(self.testing_screen, 'log_panel'):
                self.testing_screen.log_panel.add_log_entry(error_msg, "ERROR")
    
        # Rekisterin luku
        if op_code == 1:  # Rekisterin luku
            if result and hasattr(result, 'registers') and len(result.registers) > 0:
                if hasattr(self, '_last_register_read') and self._last_register_read is not None:
                    if self._last_register_read == 19100:
                        # Hätäseisrekisterin arvo (0=aktiivinen, 1=ei aktiivinen)
                        emergency_status = result.registers[0]
                        
                        # Tallennetaan viimeisin tila, ei tulosteta terminaaliin
                        self._last_emergency_state = emergency_status
                        
                        if emergency_status == 0 and not self.emergency_dialog_open:
                            # Hätäseis aktiivinen
                            self.emergency_dialog_open = True
                            self._dialog_opened_time = time.time()  # Tallenna avausaika
                            self._emergency_dialog = EmergencyStopDialog(self, self.modbus_manager)
                            self._emergency_dialog.finished.connect(self.on_emergency_dialog_closed)
                            self._emergency_dialog.exec_()
                        elif emergency_status == 1 and self.emergency_dialog_open:
                            # Hätäseis ei aktiivinen, mutta estetään vilkkuminen
                            # Suljetaan dialogi vain jos se on ollut auki vähintään 2 sekuntia
                            if hasattr(self, '_dialog_opened_time') and time.time() - self._dialog_opened_time > 2:
                                if hasattr(self, '_emergency_dialog') and self._emergency_dialog is not None:
                                    self._emergency_dialog.accept()
                                    self._emergency_dialog = None
                                self.emergency_dialog_open = False

        # Kytkimien tilojen käsittely (testien aktiivinen-tila)
        if op_code == 1 and result and hasattr(result, 'registers') and len(result.registers) > 0:
            if hasattr(self, '_last_switch_read') and 17001 <= self._last_switch_read <= 17003:
                test_idx = self._last_switch_read - 17001
                switch_state = result.registers[0]
                
                # Päivitä testipaneelin tila vain jos se poikkeaa nykyisestä
                if self.testing_screen.test_panels[test_idx].is_active != bool(switch_state):
                    self.testing_screen.test_panels[test_idx].is_active = bool(switch_state)
                    self.testing_screen.test_panels[test_idx].update_button_style()
                    
                    # Ohjaa GPIO-lähtö
                    if hasattr(self, 'gpio_handler') and self.gpio_handler:
                        self.gpio_handler.set_output(test_idx + 1, bool(switch_state))                                

        # START/STOP-kytkimien käsittely
        if op_code == 1 and result and hasattr(result, 'registers') and len(result.registers) > 0:
            if hasattr(self, '_last_switch_read'):
                if self._last_switch_read == 17000 and result.registers[0] == 1:
                    # START-kytkin painettu
                    self.testing_screen.start_test()
                elif self._last_switch_read == 16999 and result.registers[0] == 1:
                    # STOP-kytkin painettu
                    self.testing_screen.stop_test()

    def handle_fortest_result(self, result, op_code, error_msg):
        """Käsittele ForTest-operaation tulos"""
        if error_msg:
            # Näytä virheviesti
            self.status_notifier.show_message(error_msg, StatusNotifier.ERROR)
            if hasattr(self.testing_screen, 'log_panel'):
                self.testing_screen.log_panel.add_log_entry(error_msg, "ERROR")
        
        # Käsittele onnistuneet operaatiot
        if result:
            msg = ""
            msg_type = StatusNotifier.INFO
            
            if op_code == 1:  # Käynnistys
                msg = "Testi käynnistetty onnistuneesti"
                msg_type = StatusNotifier.SUCCESS
            elif op_code == 2:  # Pysäytys
                msg = "Testi pysäytetty"
                msg_type = StatusNotifier.INFO
            elif op_code == 3:  # Tilan luku
                # Käsittele tila
                pass
            elif op_code == 4:  # Tulosten luku
                # Käsittele tulokset
                pass
            
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
        """Tarkista kytkinten tilat"""
        if not self.modbus_manager.is_connected():
            return
        
        # Lue rekisterit 17001-17003 (testien aktiiviset tilat)
        for i in range(3):
            reg = 17001 + i
            self.modbus_manager.read_register(reg, 1)
            self._last_switch_read = reg
        
        # Lue START-kytkin (17000)
        self.modbus_manager.read_register(17000, 1)
        self._last_switch_read = 17000
        
        # Lue STOP-kytkin (16999)
        self.modbus_manager.read_register(16999, 1)
        self._last_switch_read = 16999

    def on_program_selected(self, program_name):
        """Käsittele valittu ohjelma"""
        self.testing_screen.set_program_for_test(program_name)
        self.show_testing()
    
    def show_testing(self):
        """Näytä testaussivu"""
        self.manual_screen.hide()
        self.program_selection_screen.hide()
        self.testing_screen.show()
    
    def show_manual(self):
        """Näytä käsikäyttösivu"""
        self.testing_screen.hide()
        self.program_selection_screen.hide()
        self.manual_screen.show()
    
    def show_program_selection(self, test_number=None):
        """Näytä ohjelman valintasivu"""
        if test_number is not None:
            self.testing_screen.current_test_panel = test_number
        
        self.testing_screen.hide()
        self.manual_screen.hide()
        self.program_selection_screen.show()
    
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            # ESC palauttaa testaussivulle
            if self.manual_screen.isVisible() or self.program_selection_screen.isVisible():
                self.show_testing()
            else:
                self.close()
        super().keyPressEvent(event)
    
    def show(self):
        # Käynnistä kokoruututilassa
        self.showFullScreen()

    def closeEvent(self, event):
        # Siivoa resurssit
        self.testing_screen.cleanup()
        self.manual_screen.cleanup()
        
        self.modbus_manager.cleanup()
        self.fortest_manager.cleanup()
        
        # Siivoa GPIO-resurssit
        if hasattr(self, 'gpio_handler') and self.gpio_handler:
            self.gpio_handler.cleanup()
            
        super().closeEvent(event)