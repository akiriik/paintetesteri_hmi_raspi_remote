#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testaussivun sisältö painetestausjärjestelmälle
Modulaarinen rakenne helpottaen myöhempiä laajennuksia
"""
import sys
import os
from PyQt5.QtWidgets import (QLabel, QPushButton, QFrame, QWidget, 
                            QVBoxLayout, QHBoxLayout, QMenu, QDialog)
from PyQt5.QtCore import Qt, QTimer, QRect
from PyQt5.QtGui import QFont
from ui.screens.base_screen import BaseScreen

class PressureDisplay(QWidget):
    """Painenäytön komponentti"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 80)
        
        # Painelukema
        self.value_label = QLabel("0.00", self)
        self.value_label.setStyleSheet("""
            background-color: black;
            color: #33FF33;
            font-family: 'Consolas', 'Courier', monospace;
            font-size: 40px;
            font-weight: bold;
            border: 2px solid #444444;
            border-radius: 10px;
            padding: 5px;
        """)
        self.value_label.setAlignment(Qt.AlignCenter)
        self.value_label.setGeometry(0, 0, 200, 80)
    
    def update_pressure(self, value, color="#33FF33"):
        """Päivitä paineen arvo ja väri"""
        self.value_label.setText(f"{value:.2f}")
        self.value_label.setStyleSheet(f"""
            background-color: black;
            color: {color};
            font-family: 'Consolas', 'Courier', monospace;
            font-size: 40px;
            font-weight: bold;
            border: 2px solid #444444;
            border-radius: 10px;
            padding: 5px;
        """)

class TestResultDisplay(QWidget):
    """Testitulospaineen näyttö"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(480, 140)
        
        # Paine-näyttö
        self.pressure_label = QLabel("", self)
        self.pressure_label.setStyleSheet("""
            background-color: black;
            color: #33FF33;
            font-family: 'Consolas', 'Courier', monospace;
            font-size: 60px;
            font-weight: bold;
            border: 2px solid #444444;
            border-radius: 10px;
            padding: 10px;
        """)
        self.pressure_label.setAlignment(Qt.AlignCenter)
        self.pressure_label.setGeometry(0, 0, 480, 100)
        
        # Yksikkö
        self.unit_label = QLabel("mbar", self)
        self.unit_label.setStyleSheet("""
            color: #666666;
            font-family: 'Arial', sans-serif;
            font-size: 18px;
        """)
        self.unit_label.setAlignment(Qt.AlignCenter)
        self.unit_label.setGeometry(0, 110, 480, 30)
    
    def update_result(self, pressure, unit="mbar"):
        """Päivitä tulos"""
        self.pressure_label.setText(f"{pressure:.3f}")
        self.unit_label.setText(unit)

class TestControlPanel(QWidget):
    """Testin hallintapaneeli"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(380, 80)
        
        # Layout napeille
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # Käynnistys-nappi
        self.start_button = QPushButton("KÄYNNISTÄ", self)
        self.start_button.setFixedSize(180, 80)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 10px;
                font-size: 22px;
                font-weight: bold;
            }
        """)
        
        # Pysäytys-nappi
        self.stop_button = QPushButton("PYSÄYTÄ", self)
        self.stop_button.setFixedSize(180, 80)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border-radius: 10px;
                font-size: 22px;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)

class StatusDisplay(QWidget):
    """Tilantietojen näyttö"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(680, 80)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Tuloslabel
        self.result_label = QLabel("", self)
        self.result_label.setStyleSheet("""
            color: #333333;
            font-family: 'Arial', sans-serif;
            font-size: 30px;
            font-weight: bold;
        """)
        self.result_label.setAlignment(Qt.AlignCenter)
        
        # Tilalabel  
        self.status_label = QLabel("", self)
        self.status_label.setStyleSheet("""
            color: #666666;
            font-family: 'Arial', sans-serif;
            font-size: 18px;
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(self.result_label)
        layout.addWidget(self.status_label)
    
    def update_status(self, result="", status="", result_color="#333333"):
        """Päivitä tilantiedot"""
        self.result_label.setText(result)
        self.result_label.setStyleSheet(f"""
            color: {result_color};
            font-family: 'Arial', sans-serif;
            font-size: 30px;
            font-weight: bold;
        """)
        self.status_label.setText(status)

# Päivitetty MenuButton luokka isommalla painikkeella:
class MenuButton(QPushButton):
    """Valikko-nappi kosketusnäytölle sopiva"""
    def __init__(self, parent=None):
        super().__init__("☰", parent)
        self.setFixedSize(80, 80)  # Suurennettu koko
        self.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 10px;
                font-size: 36px;  /* Isompi ikoni */
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
class ProgramDialog(QDialog):
    """Ohjelman valintaikkuna"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ohjelmat")
        self.setFixedSize(800, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 2px solid #2196F3;
                border-radius: 10px;
            }
        """)
        
        # UI sisältö tulee tänne
        self.title = QLabel("OHJELMAT", self)
        self.title.setGeometry(0, 20, 800, 50)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFont(QFont("Arial", 24, QFont.Bold))
        
        # Sulje-nappi
        self.close_button = QPushButton("Sulje", self)
        self.close_button.setGeometry(350, 540, 100, 40)
        self.close_button.clicked.connect(self.close)

class ManualDialog(QDialog):
    """Käsikäytön ikkuna"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Käsikäyttö")
        self.setFixedSize(800, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 2px solid #2196F3;
                border-radius: 10px;
            }
        """)
        
        # UI sisältö tulee tänne
        self.title = QLabel("KÄSIKÄYTTÖ", self)
        self.title.setGeometry(0, 20, 800, 50)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFont(QFont("Arial", 24, QFont.Bold))
        
        # Sulje-nappi
        self.close_button = QPushButton("Sulje", self)
        self.close_button.setGeometry(350, 540, 100, 40)
        self.close_button.clicked.connect(self.close)

class TestingScreen(BaseScreen):
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def init_ui(self):
        # Sivun otsikko
        self.title = self.create_title("TESTAUS")
        
        # Valikko-nappi (oikea yläkulma)
        self.menu_button = MenuButton(self)
        self.menu_button.move(1180, 20)
        self.menu_button.clicked.connect(self.show_menu)
        
        # Luo menu (aluksi piilotettu)
        self.menu = QMenu(self)
        self.menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 2px solid #2196F3;
                border-radius: 8px;
                font-size: 24px;
                min-width: 200px;
            }
            QMenu::item {
                padding: 15px 20px;
                min-height: 40px;
            }
            QMenu::item:selected {
                background-color: #2196F3;
                color: white;
            }
            QMenu::item:hover {
                background-color: #E3F2FD;
            }
        """)
        
        # Lisää toiminnot valikkoon
        program_action = self.menu.addAction("Ohjelmat")
        program_action.setFont(QFont("Arial", 18, QFont.Bold))
        
        manual_action = self.menu.addAction("Käsikäyttö") 
        manual_action.setFont(QFont("Arial", 18, QFont.Bold))
        
        # SAMMUTA-nappi valikon viimeiseksi
        self.menu.addSeparator()  # Erotin erottamaan muista
        
        exit_action = self.menu.addAction("SAMMUTA")
        exit_action.setFont(QFont("Arial", 18, QFont.Bold))
        
        # Yhdistä toiminnot
        program_action.triggered.connect(self.show_program_dialog)
        manual_action.triggered.connect(self.show_manual_dialog)
        exit_action.triggered.connect(self.close_application)
        
        # Komponentit
        self.pressure_display = PressureDisplay(self)
        self.pressure_display.move(20, 80)
        
        self.test_result = TestResultDisplay(self)
        self.test_result.move(400, 300)
        
        self.control_panel = TestControlPanel(self)
        self.control_panel.move(450, 450)
        
        self.status_display = StatusDisplay(self)
        self.status_display.move(300, 150)
        
        # Yhdistä signaalit
        self.control_panel.start_button.clicked.connect(self.start_test)
        self.control_panel.stop_button.clicked.connect(self.stop_test)
    
    def show_menu(self):
        """Näytä popup-valikko"""
        # Positioi valikko napin alle
        pos = self.menu_button.mapToGlobal(self.menu_button.rect().bottomLeft())
        self.menu.exec_(pos)
    
    def show_program_dialog(self):
        """Näytä ohjelman valintaikkuna"""
        dialog = ProgramDialog(self)
        dialog.exec_()
    
    def show_manual_dialog(self):
        """Näytä käsikäytön ikkuna"""
        dialog = ManualDialog(self)
        dialog.exec_()
    
    def close_application(self):
        """Sulje sovellus"""
        self.window().close()  # Sulje pääikkuna
    
    def start_test(self):
        """Käynnistä testi"""
        # Testi-logiikka tulee tänne
        self.status_display.update_status(result="TESTAUS KÄYNNISSÄ", 
                                        status="Käynnistetään...", 
                                        result_color="#2196F3")
    
    def stop_test(self):
        """Pysäytä testi"""
        # Pysäytys-logiikka tulee tänne
        self.status_display.update_status(result="", 
                                        status="Testi keskeytetty")
    
    def cleanup(self):
        """Siivoa resursit"""
        # Siivous-koodi tulee tänne
        pass