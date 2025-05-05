import sys
import os
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeyEvent

# Omat komponentit
from ui.screens.testing_screen import TestingScreen

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
        
        # Luo testaussivu
        self.testing_screen = TestingScreen(self)
        self.testing_screen.setGeometry(0, 0, 1280, 720)
    
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.close()  # Sulje sovellus ESC-näppäimellä
        super().keyPressEvent(event)
    
    def show(self):
        # Käynnistä kokoruututilassa
        self.showFullScreen()

    def closeEvent(self, event):
        # Siivoa resurssit
        self.testing_screen.cleanup()
        super().closeEvent(event)