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

class ProgramSelectDialog(QDialog):
    """Ohjelman valintaikkuna"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Valitse ohjelma")
        self.setFixedSize(400, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: white;
                border: 2px solid #2196F3;
                border-radius: 10px;
            }
        """)
        
        # Layout
        layout = QVBoxLayout(self)
        
        # Lista ohjelmista
        self.program_list = QListWidget(self)
        self.program_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #dddddd;
                font-size: 18px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #eeeeee;
            }
            QListWidget::item:selected {
                background-color: #2196F3;
                color: white;
            }
        """)
        
        # Lisää ohjelmat 1-30
        for i in range(1, 31):
            self.program_list.addItem(f"Ohjelma {i}")
        
        layout.addWidget(self.program_list)
        
        # Valinnan vahvistus nappi
        self.select_button = QPushButton("Valitse", self)
        self.select_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                font-size: 18px;
                padding: 10px;
            }
        """)
        self.select_button.clicked.connect(self.accept)
        layout.addWidget(self.select_button)
        
        self.selected_program = None
    
    def accept(self):
        # Tallenna valittu ohjelma
        current_item = self.program_list.currentItem()
        if current_item:
            self.selected_program = current_item.text()
        super().accept()

class TestPanel(QWidget):
    """Yksittäisen testin paneeli"""
    program_selection_requested = pyqtSignal(int)  # Signaali ohjelman valintapyynnölle
    
    def __init__(self, test_number, parent=None):
        super().__init__(parent)
        self.test_number = test_number
        self.selected_program = None
        self.is_active = False
        
        self.setFixedSize(300, 250)
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
        layout.setSpacing(10)
        
        # Testin otsikko
        title = QLabel(f"TESTI {test_number}", self)
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 20, QFont.Bold))
        layout.addWidget(title)
        
        # Ohjelmatiedot
        self.program_label = QLabel("Ohjelma: -", self)
        self.program_label.setAlignment(Qt.AlignCenter)
        self.program_label.setFont(QFont("Arial", 14))
        layout.addWidget(self.program_label)
        
        # Valitse ohjelma nappi
        self.select_program_btn = QPushButton("VALITSE OHJELMA", self)
        self.select_program_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 5px;
                font-size: 14px;
                padding: 8px;
            }
        """)
        self.select_program_btn.clicked.connect(self.request_program_selection)
        layout.addWidget(self.select_program_btn)
        
        # Aktiivinen nappi
        self.active_btn = QPushButton("AKTIIVINEN", self)
        self.active_btn.setStyleSheet("""
            QPushButton {
                background-color: #888888;
                color: white;
                border-radius: 5px;
                font-size: 14px;
                padding: 8px;
            }
        """)
        self.active_btn.clicked.connect(self.toggle_active)
        layout.addWidget(self.active_btn)
    
    def request_program_selection(self):
        """Pyydä ohjelman valintaa"""
        self.program_selection_requested.emit(self.test_number)
    
    def set_program(self, program_name):
        """Aseta valittu ohjelma"""
        self.selected_program = program_name
        self.program_label.setText(f"Ohjelma: {program_name}")
    
    def toggle_active(self):
        """Vaihda aktiivisuustila"""
        self.is_active = not self.is_active
        if self.is_active:
            self.active_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 5px;
                    font-size: 14px;
                    padding: 8px;
                }
            """)
        else:
            self.active_btn.setStyleSheet("""
                QPushButton {
                    background-color: #888888;
                    color: white;
                    border-radius: 5px;
                    font-size: 14px;
                    padding: 8px;
                }
            """)

class BottomControl(QWidget):
    """Alareunassa oleva ohjauspaneeli"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # Painenäyttö
        self.pressure_display = QLabel("0.00", self)
        self.pressure_display.setFixedSize(200, 100)
        self.pressure_display.setStyleSheet("""
            background-color: black;
            color: #33FF33;
            font-family: 'Consolas', 'Courier', monospace;
            font-size: 48px;
            font-weight: bold;
            border: 2px solid #444444;
            border-radius: 10px;
        """)
        self.pressure_display.setAlignment(Qt.AlignCenter)
        
        # Nappulapaneeli
        button_container = QWidget(self)
        button_layout = QVBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)
        
        # Käynnistä nappi
        self.start_button = QPushButton("KÄYNNISTÄ", self)
        self.start_button.setFixedSize(150, 50)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        
        # Pysäytä nappi
        self.stop_button = QPushButton("PYSÄYTÄ", self)
        self.stop_button.setFixedSize(150, 50)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border-radius: 5px;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        
        layout.addWidget(self.pressure_display)
        layout.addWidget(button_container)

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
    def __init__(self, parent=None):
        super().__init__(parent)
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
        
        # Testipaneelit keskelle
        self.test_panels = []
        for i in range(1, 4):
            panel = TestPanel(i, self)
            panel.move(50 + (i-1)*400, 150)
            # Yhdistä signaalit
            panel.program_selection_requested.connect(self.start_program_selection)
            self.test_panels.append(panel)
        
        # Alareuna
        self.bottom_control = BottomControl(self)
        self.bottom_control.move(50, 600)
        
        # Yhdistä signaalit
        self.bottom_control.start_button.clicked.connect(self.start_test)
        self.bottom_control.stop_button.clicked.connect(self.stop_test)
    
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
        # Testi-logiikka tulee tänne
        pass
    
    def stop_test(self):
        """Pysäytä testi"""
        # Pysäytys-logiikka tulee tänne
        pass
    
    def cleanup(self):
        """Siivoa resursit"""
        pass