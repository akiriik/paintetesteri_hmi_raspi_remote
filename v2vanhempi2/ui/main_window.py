import sys
import os
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent

# Omat komponentit
from ui.screens.testing_screen import TestingScreen
from ui.screens.manual_screen import ManualScreen
from ui.screens.program_selection_screen import ProgramSelectionScreen
from utils.modbus_handler import ModbusHandler
from utils.fortest_handler import ForTestHandler


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
        
        try:
            self.fortest = ForTestHandler(port='/dev/ttyUSB1', baudrate=19200)
        except Exception as e:
            print(f"Varoitus: ForTest-yhteys epäonnistui: {e}")
            # Luo dummy-ForTestHandler joka ei tee mitään
            self.fortest = DummyForTestHandler()

        # Välitä fortest aina testaussivulle
        self.testing_screen = TestingScreen(self, self.fortest)
        self.testing_screen.setGeometry(0, 0, 1280, 720)

        # Luo Modbus-käsittelijä
        self.modbus = ModbusHandler(port='/dev/ttyUSB0', baudrate=19200)
        
        # Luo käsikäyttösivu
        self.manual_screen = ManualScreen(self, self.modbus)
        self.manual_screen.setGeometry(0, 0, 1280, 720)
        self.manual_screen.hide()
        
        # Luo ohjelman valintasivu
        self.program_selection_screen = ProgramSelectionScreen(self)
        self.program_selection_screen.setGeometry(0, 0, 1280, 720)
        self.program_selection_screen.hide()
        
        # Yhdistä signaalit
        self.program_selection_screen.program_selected.connect(self.on_program_selected)
    
    def on_program_selected(self, program_name):
        """Käsittele valittu ohjelma"""
        # Anna valittu ohjelma testaussivulle
        self.testing_screen.set_program_for_test(program_name)
        # Palaa testaussivulle
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
    
    def show_program_selection(self):
        """Näytä ohjelman valintasivu"""
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
        super().closeEvent(event)