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
from utils.fortest_handler import DummyForTestHandler
from utils.modbus_manager import ModbusManager
from utils.fortest_manager import ForTestManager
from utils.gpio_handler import GPIOHandler
from utils.gpio_input_handler import GPIOInputHandler
from utils.program_manager import ProgramManager
from utils.temperature_handler import TemperatureHandler, DummyTemperatureHandler
from ui.components.temperature_widget import TemperatureWidget


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

        # Alusta ohjelmamanageri ensin
        self.program_manager = ProgramManager()

        # Näytöt
        self.testing_screen = TestingScreen(self)
        self.testing_screen.setGeometry(0, 0, 1280, 720)
        self.testing_screen.program_selection_requested.connect(self.show_program_selection)

        self.manual_screen = ManualScreen(self)
        self.manual_screen.setGeometry(0, 0, 1280, 720)
        self.manual_screen.hide()

        # Välitä ohjelmamanageri ohjelmanvalintanäkymälle
        self.program_selection_screen = ProgramSelectionScreen(self, self.program_manager)
        self.program_selection_screen.setGeometry(0, 0, 1280, 720)
        self.program_selection_screen.hide()
        self.program_selection_screen.program_selected.connect(self.on_program_selected)

        # Alusta modbus-hallinta
        self.modbus_manager = ModbusManager(port='/dev/ttyUSB0', baudrate=19200)
        self.fortest_manager = ForTestManager(port='/dev/ttyUSB1', baudrate=19200)

        # Yhdistä signaalit
        self.modbus_manager.resultReady.connect(self.handle_modbus_result)
        self.fortest_manager.resultReady.connect(self.handle_fortest_result)
        
        # Yhdistä ohjelmamanagerin signaali ohjelmiston päivitykseen
        self.program_manager.program_list_updated.connect(self.program_selection_screen.update_program_list)

        # Alusta GPIO jos mahdollista
        try:
            self.gpio_handler = GPIOHandler()
        except Exception as e:
            print(f"Varoitus: GPIO-alustus epäonnistui: {e}")
            self.gpio_handler = None
            
        # Alusta GPIO-nappulat
        try:
            self.gpio_input_handler = GPIOInputHandler()
            # Yhdistä nappulasignaalit
            self.gpio_input_handler.button_changed.connect(self.handle_button_press)
        except Exception as e:
            print(f"Varoitus: GPIO-nappuloiden alustus epäonnistui: {e}")
            self.gpio_input_handler = None

        # Alusta lämpötila-anturi (kokeile oikeaa ensin, sitten dummy)
        try:
            self.temperature_handler = TemperatureHandler()
            print("DS18B20 lämpötila-anturi käytössä")
        except Exception as e:
            print(f"DS18B20 ei saatavilla, käytetään dummy-dataa: {e}")
            self.temperature_handler = DummyTemperatureHandler()
        
        # Yhdistä lämpötilasignaali
        self.temperature_handler.temperature_updated.connect(self.update_temperature_display)


        # Ajastimet
        self.emergency_stop_timer = QTimer(self)
        self.emergency_stop_timer.timeout.connect(self.check_emergency_stop)
        self.emergency_stop_timer.start(1000)  # Tarkista hätäseis kerran sekunnissa

        self.emergency_dialog_open = False
        self._dialog_opened_time = 0
        
    def handle_button_press(self, button_name, is_pressed):
        """Käsittelee GPIO-nappulan painalluksen - reagoidaan vain painallukseen"""
        # Tässä tapauksessa is_pressed on aina True (vain painallus tulee signaalina)
        
        if button_name == "START":
            self.testing_screen.start_test()
        elif button_name == "STOP":
            self.testing_screen.stop_test()
        elif button_name == "TEST1":
            self.toggle_test(0)
        elif button_name == "TEST2":
            self.toggle_test(1)
        elif button_name == "TEST3":
            self.toggle_test(2)
                
    def toggle_test(self, panel_index):
        """Vaihda testin tila hallitusti"""
        panel = self.testing_screen.test_panels[panel_index]
        panel.is_active = not panel.is_active
        panel.update_button_style()
        
        # Aseta GPIO-lähtö uudessa tilassa
        if self.gpio_handler:
            self.gpio_handler.set_output(panel_index + 1, panel.is_active)

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
                # Lähetä heti pysäytyskäsky kun hätäseis aktivoituu
                if hasattr(self, 'fortest_manager') and self.fortest_manager:
                    try:
                        self.fortest_manager.abort_test()
                        self.testing_screen.update_status("HÄTÄSEIS AKTIVOITU, TESTI PYSÄYTETTY", "ERROR")
                    except Exception as e:
                        print(f"Virhe testin pysäytyksessä: {e}")
                
                # Avaa dialogi normaalisti
                self.emergency_dialog_open = True
                self._emergency_dialog = EmergencyStopDialog(self, self.modbus_manager)
                self._emergency_dialog._is_emergency_stop_dialog = True
                self._emergency_dialog.finished.connect(self.on_emergency_dialog_closed)
                self._emergency_dialog.exec_()
        except Exception as e:
            print(f"Virhe hätäseistilan tarkistuksessa: {e}")
            self.emergency_stop_timer.stop()

    def on_emergency_dialog_closed(self, result):
        """Hätäseisdialogin sulkemisen käsittely"""
        self.emergency_dialog_open = False
        if result == 1:  # QDialog.Accepted
            self.testing_screen.update_status("Hätäseis kuitattu", "INFO")
        self._emergency_dialog = None

    def handle_modbus_result(self, result, op_code, error_msg):
        """Käsittelee modbus-kyselyn tuloksen"""
        # Estä täysin rekisterin 19099 (hätäseis) kirjoitusten käsittely
        if op_code == 2 and hasattr(result, 'address') and result.address == 19099:
            return
            
        # Ohita myös jos kyseessä on hätäseisdialogi
        if hasattr(self, '_emergency_dialog') and getattr(self._emergency_dialog, '_is_emergency_stop_dialog', False):
            if op_code == 2:  # Rekisterin kirjoitus
                return
        
        if error_msg:
            # Päivitä tilaviesti päänäkymään
            self.testing_screen.update_status(error_msg, "ERROR")
            return
        
        if not result:
            return

        # Ohjelmanvaihdon tulos (Write Single Register, 0x06)
        if op_code == 2:  # Rekisterin kirjoitus
            if hasattr(result, 'isError') and not result.isError():
                # Ohjelmanvaihto onnistui, jatka testin käynnistystä
                self.testing_screen.update_status(f"Ohjelma vaihdettu onnistuneesti", "SUCCESS")
            else:
                # Ohjelmanvaihto epäonnistui
                self.testing_screen.update_status("Ohjelmanvaihto epäonnistui", "ERROR")
            return

    def handle_fortest_result(self, result, op_code, error_msg):
        # Rajoita tulostusta vain tärkeisiin tapahtumiin
        if op_code != 3 and op_code != 4:  # Älä tulosta status ja results kyselyjen tuloksia
            print(f"handle_fortest_result: op_code={op_code}, error_msg={error_msg}")
 
        """Käsittelee ForTest-laitteen operaatiotulokset"""
        if op_code == 999:  # Erityinen koodi yhteyden epäonnistumiselle
            self.testing_screen.update_status(error_msg, "WARNING")
            return

        if error_msg:
            self.testing_screen.update_status(error_msg, "ERROR")
            return

        if result:
            msg = ""
            level = "INFO"

            if op_code == 1:  # Testin käynnistys
                msg = "Testi käynnistetty onnistuneesti"
                level = "SUCCESS"
                # Käynnissä: punainen päällä, vihreä pois
                if self.gpio_handler:
                    self.gpio_handler.set_output(4, False)  # GPIO 23 (vihreä) pois
                    self.gpio_handler.set_output(5, True)   # GPIO 24 (punainen) päälle
            elif op_code == 2:  # Testin pysäytys
                msg = "Testi pysäytetty"
                level = "INFO"
                # Pysäytetty: vihreä päällä, punainen pois
                if self.gpio_handler:
                    self.gpio_handler.set_output(4, True)   # GPIO 23 (vihreä) päälle
                    self.gpio_handler.set_output(5, False)  # GPIO 24 (punainen) pois

            if msg:
                self.testing_screen.update_status(msg, level)

        if op_code == 3:  # Status read
            # Välitä status testingscreen:lle
            self.testing_screen.update_status_from_fortest(result)
        elif op_code == 4:  # Results read
            # Välitä tulokset aktiivisille paneeleille
            for panel in self.testing_screen.test_panels:
                if panel.is_active:
                    panel.update_test_results(result)

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

    # Lisää metodi lämpötilan päivitykseen:
    def update_temperature_display(self, temperatures):
        """Päivitä lämpötilanäyttö"""
        if hasattr(self.testing_screen, 'temperature_widget'):
            self.testing_screen.temperature_widget.update_temperatures(temperatures)


    def show(self):
        """Näyttää ikkunan koko ruudussa"""
        self.showFullScreen()

    def closeEvent(self, event):
        """Käsittelee sovelluksen sulkemisen"""
        try:
            # Siivoa ensin GPIO-nappuloiden tapahtumakuuntelijat
            if hasattr(self, 'gpio_input_handler') and self.gpio_input_handler:
                self.gpio_input_handler.cleanup()
                
            # Sitten muut resurssit
            self.testing_screen.cleanup()
            self.manual_screen.cleanup()
            self.modbus_manager.cleanup()
            self.fortest_manager.cleanup()
            
            # Lopuksi GPIO-outputit
            if hasattr(self, 'gpio_handler') and self.gpio_handler:
                self.gpio_handler.cleanup()

            # Siivoa lämpötila-anturi
            if hasattr(self, 'temperature_handler'):
                self.temperature_handler.cleanup()
                                
        except Exception as e:
            # Virhetilanteessa älä tulosta täyttä virhettä
            print("Virhe sovelluksen sulkemisessa")
        super().closeEvent(event)