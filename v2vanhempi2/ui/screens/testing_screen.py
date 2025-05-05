#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testaussivun sisältö painetestausjärjestelmälle
"""
import sys
import os
from PyQt5.QtWidgets import (QLabel, QPushButton, QFrame, QWidget, 
                            QVBoxLayout, QHBoxLayout, QMenu, QDialog,
                            QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QTimer, QRect, pyqtSignal
from PyQt5.QtGui import QFont
from ui.screens.base_screen import BaseScreen
from utils.fortest_handler import ForTestHandler

class TestPanel(QWidget):
    """Yksittäisen testin paneeli"""
    program_selection_requested = pyqtSignal(int)  # Signaali ohjelman valintapyynnölle
    
    def __init__(self, test_number, parent=None):
        super().__init__(parent)
        self.test_number = test_number
        self.selected_program = None
        self.is_active = False
        
        self.setFixedSize(300, 600)
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border-radius: 10px;
                border: 1px solid #dddddd;
            }
        """)

        # Layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(30)
        
        # Painetulos laatikko (kasvatettu ylhäältä)
        self.pressure_result = QLabel("", self)
        self.pressure_result.setFixedSize(280, 250)  # Kasvatettu korkeutta
        self.pressure_result.setAlignment(Qt.AlignCenter)
        self.pressure_result.setStyleSheet("""
            background-color: black;
            color: #33FF33;
            font-family: 'Consolas', 'Courier', monospace;
            font-size: 40px;  # Kasvatettu fontti
            font-weight: bold;
            border: 2px solid #444444;
            border-radius: 10px;
        """)
        layout.addWidget(self.pressure_result)
        
        # Ohjelmatiedot
        self.program_label = QLabel("Ohjelma: --", self)
        self.program_label.setFixedSize(280, 60)
        self.program_label.setAlignment(Qt.AlignCenter)
        self.program_label.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(self.program_label)
        
        # Valitse ohjelma nappi
        self.select_program_btn = QPushButton("VALITSE OHJELMA", self)
        self.select_program_btn.setFixedSize(280, 80)
        self.select_program_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 5px;
                font-size: 20px;
                font-weight: bold;
                padding: 8px;
            }
        """)
        self.select_program_btn.clicked.connect(self.request_program_selection)
        layout.addWidget(self.select_program_btn)
        
        # Aktiivinen nappi
        self.active_btn = QPushButton("AKTIIVINEN", self)
        self.active_btn.setFixedSize(280, 80)
        self.active_btn.setStyleSheet("""
            QPushButton {
                background-color: #888888;
                color: white;
                border-radius: 5px;
                font-weight: bold;
                font-size: 20px;
                padding: 8px;
            }
        """)
        self.active_btn.clicked.connect(self.toggle_active)
        layout.addWidget(self.active_btn)
    
    # Lisää parent-metodin käyttö:
    def get_fortest(self):
        """Hae vanhemman ForTest-olio"""
        if hasattr(self.parent(), 'fortest'):
            return self.parent().fortest
        return None

    def request_program_selection(self):
        """Pyydä ohjelman valintaa"""
        self.program_selection_requested.emit(self.test_number)
    
    def set_program(self, program_name):
        """Aseta valittu ohjelma"""
        self.selected_program = program_name
        self.program_label.setText(f" {program_name}")
    
    def toggle_active(self):
        """Vaihda aktiivisuustila"""
        self.is_active = not self.is_active
        if self.is_active:
            self.active_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 20px;
                    padding: 8px;
                }
            """)
        else:
            self.active_btn.setStyleSheet("""
                QPushButton {
                    background-color: #888888;
                    color: white;
                    border-radius: 5px;
                    font-weight: bold;
                    font-size: 20px;
                    padding: 8px;
                }
            """)

class RightControl(QWidget):
    """Oikean reunan ohjauspaneeli"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        
        # Painenäyttö
        self.pressure_display = QLabel("0.00", self)
        self.pressure_display.setFixedSize(250, 150)
        self.pressure_display.setStyleSheet("""
            background-color: black;
            color: #33FF33;
            font-family: 'Consolas', 'Courier', monospace;
            font-size: 56px;
            font-weight: bold;
            border: 2px solid #444444;
            border-radius: 10px;
        """)
        self.pressure_display.setAlignment(Qt.AlignCenter)
        
        # Käynnistä nappi (saman levyinen kun painenäyttö)
        self.start_button = QPushButton("KÄYNNISTÄ", self)
        self.start_button.setFixedSize(250, 120)  # Sama leveys kun painenäyttö
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        
        # Pysäytä nappi (saman levyinen kun painenäyttö)
        self.stop_button = QPushButton("PYSÄYTÄ", self)
        self.stop_button.setFixedSize(250, 120)  # Sama leveys kun painenäyttö
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border-radius: 5px;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.pressure_display)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)

class MenuButton(QPushButton):
    """Valikko-nappi"""
    def __init__(self, parent=None):
        super().__init__("☰", parent)
        self.setFixedSize(60, 60)
        self.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 10px;
                font-size: 30px;
                font-weight: bold;
            }
        """)

class TestingScreen(BaseScreen):
    def __init__(self, parent=None, fortest=None):
        super().__init__(parent)
        self.fortest = fortest
        self.current_test_panel = None  # Muistaa minkä testin ohjelma valitaan
        
    def init_ui(self):
        # Valikko-nappi (oikea yläkulma)
        self.menu_button = MenuButton(self)
        self.menu_button.move(1200, 20)
        self.menu_button.clicked.connect(self.show_menu)
        
        # Luo menu
        self.menu = QMenu(self)
        self.menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 2px solid #2196F3;
                border-radius: 8px;
                font-size: 18px;
                min-width: 150px;
            }
            QMenu::item {
                padding: 10px 15px;
            }
            QMenu::item:selected {
                background-color: #2196F3;
                color: white;
            }
        """)
        
        # Valikon toiminnot
        program_action = self.menu.addAction("Ohjelmat")
        manual_action = self.menu.addAction("Käsikäyttö")
        self.menu.addSeparator()
        exit_action = self.menu.addAction("SAMMUTA")
        
        # Yhdistä toiminnot
        program_action.triggered.connect(self.show_programs)
        manual_action.triggered.connect(self.show_manual)
        exit_action.triggered.connect(self.close_application)
        
        # Testipaneelit
        self.test_panels = []
        for i in range(1, 4):
            # Luo testin otsikko yläreunaan
            title = QLabel(f"TESTI {i}", self)
            title.setFont(QFont("Arial", 24, QFont.Bold))
            title.setAlignment(Qt.AlignCenter)
            title.setGeometry(50 + (i-1)*320, 50, 300, 40)  # Siirretty ylös
            
            # Luo paneeli
            panel = TestPanel(i, self)
            panel.move(40 + (i-1)*320, 100)  # Siirretty ylös
            # Yhdistä signaalit
            panel.program_selection_requested.connect(self.start_program_selection)
            self.test_panels.append(panel) 
        
        # Oikean reunan ohjaus
        self.right_control = RightControl(self)
        self.right_control.move(1015, 150)  # Siirretty hieman vasemmalle (keskitys)
        
        # Yhdistä signaalit
        self.right_control.start_button.clicked.connect(self.start_test)
        self.right_control.stop_button.clicked.connect(self.stop_test)
    
    def show_menu(self):
        """Näytä popup-valikko"""
        pos = self.menu_button.mapToGlobal(self.menu_button.rect().bottomLeft())
        self.menu.exec_(pos)
    
    def show_programs(self):
        """Siirry ohjelmasivulle"""
        if hasattr(self.parent(), 'show_testing'):
            self.parent().show_testing()
    
    def show_manual(self):
        """Siirry käsikäyttösivulle"""
        if hasattr(self.parent(), 'show_manual'):
            self.parent().show_manual()
    
    def close_application(self):
        """Sulje sovellus"""
        self.window().close()
    
    def start_program_selection(self, test_number):
        """Käynnistä ohjelman valinta tietylle testille"""
        self.current_test_panel = test_number
        # Kerro pääikkunalle, että halutaan näyttää ohjelman valintasivu
        if hasattr(self.parent(), 'show_program_selection'):
            self.parent().show_program_selection()
    
    def set_program_for_test(self, program_name):
        """Aseta ohjelma valitulle testille"""
        if self.current_test_panel:
            # Hae oikea paneeli ja aseta ohjelma
            panel = self.test_panels[self.current_test_panel - 1]
            panel.set_program(program_name)
            self.current_test_panel = None
    
    def start_test(self):
        """Käynnistä testi"""
        if self.fortest is None:
            print("ForTest-yhteys ei ole käytettävissä")
            return
        
        success = self.fortest.start_test()
        if success:
            print("Testi käynnistetty")
        else:
            print("Testin käynnistys epäonnistui")

    def stop_test(self):
        """Pysäytä testi"""
        if self.fortest is None:
            print("ForTest-yhteys ei ole käytettävissä")
            return
        
        success = self.fortest.abort_test()
        if success:
            print("Testi pysäytetty")
        else:
            print("Testin pysäytys epäonnistui")
    
    def cleanup(self):
        """Siivoa resursit"""
        pass