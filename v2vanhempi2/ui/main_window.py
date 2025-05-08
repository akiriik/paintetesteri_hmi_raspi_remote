# ui/main_window.py
import sys
import os
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
from utils.pressure_reader import PressureReaderThread

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
        
        # Alusta paineanturin lukijasäie
        self.setup_pressure_reader()

        # Lisää ajastin kytkimien tilojen tarkistamiseen
        self.switch_read_timer = QTimer(self)
        self.switch_read_timer.timeout.connect(self.check_switches)
        self.switch_read_timer.start(150)  # Tarkista 150ms välein        

    def setup_pressure_reader(self):
        """Alusta paineanturi ja sen lukijasäie"""
        try:
            from utils.pressure_sensor import PressureSensor
            sensor = PressureSensor()
            self.pressure_reader = PressureReaderThread(sensor)
            self.pressure_reader.pressureUpdated.connect(self.on_pressure_updated)
            self.pressure_reader.start()
        except Exception as e:
            print(f"Varoitus: Paineanturin alustus epäonnistui: {e}")
    
    def on_pressure_updated(self, pressure):
        """Käsittele painelukema"""
        if hasattr(self.testing_screen, 'update_pressure_display'):
            self.testing_screen.update_pressure_display(pressure)

    def check_emergency_stop(self):
        """Tarkista hätäseispiirin tila"""
        if not self.modbus_manager.is_connected():
            return
        
        # Aseta rekisteri ennen lukua, että handle_modbus_result tunnistaa sen
        self._last_register_read = 19100
        # Lue rekisteri
        self.modbus_manager.read_register(19100, 1)
        


    def on_emergency_dialog_closed(self):
        """Dialogi suljettu, nollataan lippu"""
        self.emergency_dialog_open = False

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
                        
                        # Tulosta arvo debuggausta varten
                        print(f"Hätäseis rekisterin 19100 arvo: {emergency_status}")
                        
                        if emergency_status == 0:
                            # Hätäseis aktiivinen
                            if not self.emergency_dialog_open:
                                self.emergency_dialog_open = True
                                self._emergency_dialog = EmergencyStopDialog(self, self.modbus_manager)
                                self._emergency_dialog.finished.connect(self.on_emergency_dialog_closed)
                                self._emergency_dialog.exec_()
                        else:
                            # Hätäseis ei aktiivinen, sulje dialogi jos se on avoinna
                            if self.emergency_dialog_open:
                                print("Hätäseis ei enää aktiivinen, suljetaan dialogi")
                                if hasattr(self, '_emergency_dialog') and self._emergency_dialog is not None:
                                    self._emergency_dialog.accept()
                                    self._emergency_dialog = None
                                self.emergency_dialog_open = False


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
        
        # Lue rekisterit 17001-17003 (kolme testiä)
        for i in range(3):
            reg = 17001 + i
            self.modbus_manager.read_register(reg, 1)
            self._last_switch_read = reg

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
        
        # Pysäytä säikeet
        if hasattr(self, 'pressure_reader'):
            self.pressure_reader.stop()
            self.pressure_reader.wait()
        
        self.modbus_manager.cleanup()
        self.fortest_manager.cleanup()
        
        # Siivoa GPIO-resurssit
        if hasattr(self, 'gpio_handler') and self.gpio_handler:
            self.gpio_handler.cleanup()
            
        super().closeEvent(event)