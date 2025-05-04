import sys
import os
from PyQt5.QtWidgets import QWidget, QPushButton, QStackedWidget, QLabel, QFrame
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QRect
from PyQt5.QtGui import QKeyEvent, QFont

# Omat komponentit
from ui.screens.home_screen import HomeScreen
from ui.screens.program_screen import ProgramScreen
from ui.screens.testing_screen import TestingScreen
from ui.screens.manual_screen import ManualScreen
from ui.screens.modbus_screen import ModbusScreen
from ui.components.navbar import NavigationBar

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
            QPushButton#closeButton {
                background-color: #F44336;
                color: white;
                border-radius: 25px;
                font-weight: bold;
                font-size: 18px;
            }
            QPushButton#closeButton:hover {
                background-color: #D32F2F;
            }
        """)
        
        # Luo Modbus-käsittelijä
        from utils.modbus_handler import ModbusHandler
        self.modbus = ModbusHandler(port='/dev/ttyUSB0', baudrate=19200)
        
        # Luo stacked widget sisältösivuille
        self.stacked_widget = QStackedWidget(self)
        self.stacked_widget.setGeometry(0, 0, 1280, 650)
        
        # Luo näytöt
        self.screens = [
        HomeScreen(self),
        ProgramScreen(self, self.modbus),
        TestingScreen(self, self.modbus),
        ManualScreen(self, self.modbus),
        ModbusScreen(self, self.modbus)
        ]
        
        # Lisää näytöt stacked widgetiin
        for screen in self.screens:
            self.stacked_widget.addWidget(screen)
        
        # Luo navigointipalkki
        self.navbar = NavigationBar(self)
        self.navbar.setGeometry(0, 650, 1280, 70)
        
        # Yhdistä navigointisignaalit
        self.navbar.screen_changed.connect(self.change_screen)
        
        # Luo sulje-nappi (vasemmassa yläkulmassa, suurempi koko)
        self.close_btn = QPushButton("X", self)
        self.close_btn.setObjectName("closeButton")
        self.close_btn.setGeometry(20, 20, 50, 50)
        self.close_btn.clicked.connect(self.close)
        
        # Nykyinen sivu
        self.current_index = 0
    
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.close()  # Sulje sovellus ESC-näppäimellä
        super().keyPressEvent(event)
    
    def change_screen(self, index):
        # Yksinkertaistettu näytön vaihto ilman animaatiota
        self.stacked_widget.setCurrentIndex(index)
        self.current_index = index
        
        # Näytä tai piilota sulje-nappi riippuen sivusta
        if index == 0:  # Etusivu
            self.close_btn.show()
        else:
            self.close_btn.hide()
    
    def show(self):
        # Käynnistä kokoruututilassa
        self.showFullScreen()

    def closeEvent(self, event):
        # Siivoa kaikki näytöt ennen sulkemista
        for screen in self.screens:
            screen.cleanup()
        super().closeEvent(event)