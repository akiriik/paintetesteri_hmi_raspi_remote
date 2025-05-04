#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ohjelmasivun sisältö painetestausjärjestelmälle
"""
from PyQt5.QtWidgets import (QWidget, QLabel, QPushButton, QFrame, QCheckBox, 
                            QListWidget, QDialog, QVBoxLayout, QHBoxLayout, 
                            QProgressBar, QListWidgetItem)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont
from ui.screens.base_screen import BaseScreen
from utils.modbus_handler import ModbusHandler
import time
import threading

class ProgramListDialog(QDialog):
    """Ohjelmalistan valintaikkuna"""
    # ProgramScreen-luokan konstruktori
    def __init__(self, parent=None, modbus=None):
        self.program_names = []
        self.program_names_loaded = False
        self.consecutive_failures = 0
        
        # Käytä annettua Modbus-käsittelijää
        self.modbus = modbus or ModbusHandler(port='/dev/ttyUSB0', baudrate=19200)
        
        # ForTest manuaalin mukaiset rekisterit
        self.PROGRAM_SELECT_REGISTER = 0x0060
        self.PROGRAM_NAME_BASE_ADDR = 0xEA74
        
        # Tallennetut ohjelmatiedot
        self.program_selection = {
            "program1": 1,
            "program2": 2,
            "program3": 3,
            "program2_enabled": True,
            "program3_enabled": True,
            "program1_name": "Ohjelma 1",
            "program2_name": "Ohjelma 2",
            "program3_name": "Ohjelma 3"
        }
        
        super().__init__(parent)

        # Asettelu
        layout = QVBoxLayout(self)
        
        # Otsikko
        title = QLabel("Valitse ohjelma", self)
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Ohjelmalista
        self.program_list = QListWidget(self)
        self.program_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #dddddd;
                border-radius: 5px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eeeeee;
            }
            QListWidget::item:selected {
                background-color: #2196F3;
                color: white;
            }
        """)
        
        # Lisää ohjelmat listaan
        if program_names and len(program_names) > 0:
            for i, name in enumerate(program_names):
                # Rajoita ohjelmanimen pituutta, jotta numero mahtuu
                max_length = 20  # Maksimipituus näytettävälle nimelle
                if len(name) > max_length:
                    display_name = name[:max_length-3] + "..."
                else:
                    display_name = name
                    
                item = QListWidgetItem(f"{display_name} ({i+1})")
                self.program_list.addItem(item)
        else:
            # Jos ohjelmanimiä ei ole, käytä oletusnimiä
            for i in range(30):
                item = QListWidgetItem(f"Ohjelma {i+1}")
                self.program_list.addItem(item)
        
        # Valitse nykyinen ohjelma
        if 0 <= current_index < self.program_list.count():
            self.program_list.setCurrentRow(current_index)
        
        self.program_list.itemClicked.connect(self.on_program_selected)
        layout.addWidget(self.program_list)
        
        # Napit
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Peruuta", self)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #dddddd;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        
        select_btn = QPushButton("Valitse", self)
        select_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        select_btn.clicked.connect(self.accept)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(select_btn)
        
        layout.addLayout(button_layout)
    
    def on_program_selected(self, item):
        """Käsittele ohjelman valinta"""
        self.selected_program = item.text()
        self.selected_index = self.program_list.currentRow()

class ProgramPanel(QFrame):
    """Ohjelmapaneeli yhden ohjelman valintaan"""
    
    program_selected = pyqtSignal(int, str)
    
    def __init__(self, title="Ohjelma", program_name="Ei valittu", program_id=0, parent=None):
        super().__init__(parent)
        
        self.program_id = program_id
        self.program_index = 0  # Oletusindeksi 0 (Ohjelma 1)
        
        # Ulkoasu
        self.setFixedSize(220, 220)
        self.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border-radius: 10px;
                border: 1px solid #dddddd;
            }
        """)
        
        # Otsikko
        self.title_label = QLabel(title, self)
        self.title_label.setGeometry(0, 10, 220, 30)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Arial", 14, QFont.Bold))
        
        # Ohjelman nimi
        self.name_label = QLabel(program_name, self)
        self.name_label.setGeometry(10, 50, 200, 60)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setFont(QFont("Arial", 12))
        self.name_label.setStyleSheet("color: #333333;")
        
        # Valintanappi
        self.select_btn = QPushButton("VALITSE OHJELMA", self)
        self.select_btn.setGeometry(10, 160, 200, 50)
        self.select_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.select_btn.clicked.connect(self.select_program)
    
    def select_program(self):
        """Näytä ohjelmavalintaikkuna"""
        # Käytä ohjelmanimiä jos ne on ladattu, muuten käytä oletusnimiä
        program_names = self.parent().parent().program_names if hasattr(self.parent(), 'parent') and hasattr(self.parent().parent(), 'program_names') and self.parent().parent().program_names_loaded else None
        
        dialog = ProgramListDialog(self.parent(), program_names, current_index=self.program_index)
        
        if dialog.exec_():
            if dialog.selected_program:
                # Tallenna ohjelman tiedot
                self.program_index = dialog.selected_index
                program_num = dialog.selected_index + 1  # Ohjelman numero (1-30)
                
                # Päivitä näytettävä nimi
                self.name_label.setText(dialog.selected_program)
                
                # Lähetä signaali valinnasta
                self.program_selected.emit(self.program_id, dialog.selected_program)
                
                # Päivitä myös ohjelmanumero program_selection-tietorakenteeseen
                if hasattr(self.parent(), 'parent'):
                    parent = self.parent().parent()
                    if hasattr(parent, 'program_selection'):
                        if self.program_id == 1:
                            parent.program_selection["program1"] = program_num
                        elif self.program_id == 2:
                            parent.program_selection["program2"] = program_num
                        elif self.program_id == 3:
                            parent.program_selection["program3"] = program_num
    
    def set_enabled(self, enabled):
        """Aseta paneelin käytettävyys"""
        self.setEnabled(enabled)
        opacity = "1.0" if enabled else "0.5"
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #f0f0f0;
                border-radius: 10px;
                border: 1px solid #dddddd;
                opacity: {opacity};
            }}
        """)

class ProgramScreen(BaseScreen):
    """Ohjelmasivu ohjelmien valintaan"""
    
    def __init__(self, parent=None, modbus=None):
        self.program_names = []
        self.program_names_loaded = False
        self.consecutive_failures = 0
        
        # Use provided ModbusHandler or create a new one
        self.modbus = modbus or ModbusHandler(port='/dev/ttyUSB0', baudrate=19200)
        
        # ForTest manuaalin mukaiset rekisterit
        self.PROGRAM_SELECT_REGISTER = 0x0060  # Ohjelman valintarekisteri
        self.PROGRAM_NAME_BASE_ADDR = 0xEA74   # Ohjelmanimien alkuosoite
        
        # Tallennetut ohjelmatiedot
        self.program_selection = {
            "program1": 1,
            "program2": 2,
            "program3": 3,
            "program2_enabled": True,
            "program3_enabled": True,
            "program1_name": "Ohjelma 1",
            "program2_name": "Ohjelma 2",
            "program3_name": "Ohjelma 3"
        }
        
        super().__init__(parent)
    
    def init_ui(self):
        # Sivun otsikko
        self.title = self.create_title("TESTAUSOHJELMAT")
        
        # Päivitysnappi
        self.update_btn = QPushButton("PÄIVITÄ", self)
        self.update_btn.setGeometry(30, 20, 120, 40)
        self.update_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.update_btn.clicked.connect(self.update_program_names)
        
        # Tilanilmaisin (spinner sijasta)
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setGeometry(160, 30, 150, 20)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #dddddd;
                border-radius: 5px;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 5px;
            }
        """)
        self.progress_bar.hide()
        
        # Tallennusnappi
        self.save_btn = QPushButton("TALLENNA", self)
        self.save_btn.setGeometry(620, 20, 150, 40)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        self.save_btn.clicked.connect(self.save_program_selection)
        
        # Ohjelmavalintapaneelit
        self.program1_panel = ProgramPanel(
            "Ohjelma 1", 
            self.program_selection["program1_name"], 
            1, 
            self
        )
        self.program1_panel.setGeometry(60, 80, 220, 220)
        self.program1_panel.program_selected.connect(self.on_program_selected)
        
        self.program2_panel = ProgramPanel(
            "Ohjelma 2", 
            self.program_selection["program2_name"], 
            2, 
            self
        )
        self.program2_panel.setGeometry(290, 80, 220, 220)
        self.program2_panel.program_selected.connect(self.on_program_selected)
        
        self.program3_panel = ProgramPanel(
            "Ohjelma 3", 
            self.program_selection["program3_name"], 
            3, 
            self
        )
        self.program3_panel.setGeometry(520, 80, 220, 220)
        self.program3_panel.program_selected.connect(self.on_program_selected)
        
        # Valintaruudut ohjelmien käyttöön
        self.program2_checkbox = QCheckBox("Käytössä", self)
        self.program2_checkbox.setGeometry(350, 310, 100, 30)
        self.program2_checkbox.setChecked(self.program_selection["program2_enabled"])
        self.program2_checkbox.stateChanged.connect(self.on_program2_checkbox_changed)
        
        self.program3_checkbox = QCheckBox("Käytössä", self)
        self.program3_checkbox.setGeometry(580, 310, 100, 30)
        self.program3_checkbox.setChecked(self.program_selection["program3_enabled"])
        self.program3_checkbox.stateChanged.connect(self.on_program3_checkbox_changed)
        
        # Tilarivi
        self.status_label = QLabel("", self)
        self.status_label.setGeometry(0, 350, 800, 30)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Arial", 12))
        
        # Päivitä ohjelmoiden käytettävyys valintaruutujen tilan mukaan
        self.update_program_panels_enabled()
    
    def on_program_selected(self, program_id, program_name):
        """Käsittele ohjelman valinta"""
        if program_id == 1:
            self.program_selection["program1_name"] = program_name
        elif program_id == 2:
            self.program_selection["program2_name"] = program_name
        elif program_id == 3:
            self.program_selection["program3_name"] = program_name
    
    def on_program2_checkbox_changed(self, state):
        """Käsittele Ohjelma 2 valintaruudun tilan muutos"""
        self.program_selection["program2_enabled"] = state == Qt.Checked
        self.update_program_panels_enabled()
    
    def on_program3_checkbox_changed(self, state):
        """Käsittele Ohjelma 3 valintaruudun tilan muutos"""
        self.program_selection["program3_enabled"] = state == Qt.Checked
        self.update_program_panels_enabled()
    
    def update_program_panels_enabled(self):
        """Päivitä paneelien käytettävyys valintaruutujen tilan mukaan"""
        self.program2_panel.set_enabled(self.program_selection["program2_enabled"])
        self.program3_panel.set_enabled(self.program_selection["program3_enabled"])
    
    def read_program_name(self, program_number):
        """Lue ohjelmanimi ForTest-laitteelta Modbus-RTU:lla
        
        Args:
            program_number: Ohjelman numero (0-29)
            
        Returns:
            Ohjelman nimi stringinä, tai oletusnimi jos lukeminen epäonnistuu
        """
        # Oletusnimi varmuuden vuoksi
        default_name = f"Ohjelma {program_number+1}"
        
        if not self.modbus.connected:
            print(f"Modbus-yhteyttä ei ole - käytetään oletusnimeä {default_name}")
            return default_name
        
        try:
            # Laske rekisteriosoite
            address = self.PROGRAM_NAME_BASE_ADDR + program_number
            print(f"Luetaan ohjelmanimi {program_number+1} osoitteesta 0x{address:04X}")
            
            # Lue 8 rekisteriä (16 merkkiä) ohjelman nimeä varten
            result = self.modbus.client.read_holding_registers(address, 8, slave=1)
            
            if not result.isError():
                registers = result.registers
                
                # Muunna rekisterit merkkijonoksi (2 ASCII-merkkiä per rekisteri)
                name = ""
                for reg in registers:
                    # Ylempi tavu
                    high_byte = (reg >> 8) & 0xFF
                    if high_byte >= 32 and high_byte < 127:  # Tulostettava merkki
                        name += chr(high_byte)
                    
                    # Alempi tavu
                    low_byte = reg & 0xFF
                    if low_byte >= 32 and low_byte < 127:  # Tulostettava merkki
                        name += chr(low_byte)
                
                # Siisti nimi
                name = name.strip()
                
                if name:
                    return name
                else:
                    return default_name
            else:
                print(f"Modbus-lukuvirhe: {result}")
                return default_name
        
        except Exception as e:
            print(f"Virhe ohjelman nimen lukemisessa: {e}")
            return default_name
    
    def update_program_names(self):
        """Päivitä ohjelmanimet laitteelta Modbus-väylän kautta"""
        self.status_label.setText("Haetaan ohjelmatietoja...")
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        
        # Ohjelmanimien haku taustasäikeessä
        def update_task():
            # Alusta perusnimet (jos varsinainen lukeminen ei onnistu)
            program_names = []
            for i in range(30):
                program_names.append(f"Ohjelma {i+1}")
            
            # Peräkkäisten virheiden laskuri
            self.consecutive_failures = 0
            successful_reads = 0
            
            # Haetaan ohjelmanimet yksi kerrallaan
            for i in range(30):
                # Päivitä UI pääsäikeessä
                progress = int((i / 30) * 100)
                QTimer.singleShot(0, lambda val=progress: self.progress_bar.setValue(val))
                
                # Päivitä tilarivi joka 5 ohjelman jälkeen
                if i % 5 == 0:
                    status = f"Haetaan ohjelmia... {progress}%"
                    QTimer.singleShot(0, lambda text=status: self.status_label.setText(text))
                
                # Lopeta, jos 5 peräkkäistä epäonnistumista
                if self.consecutive_failures >= 5:
                    print("Liian monta peräkkäistä epäonnistumista, lopetetaan")
                    break
                
                # Yritä lukea ohjelmanimi
                name = self.read_program_name(i)
                if name != f"Ohjelma {i+1}":  # Onnistui, ei ole oletusnimi
                    program_names[i] = name
                    successful_reads += 1
                    self.consecutive_failures = 0  # Nollaa laskuri onnistumisen jälkeen
                else:
                    self.consecutive_failures += 1
                
                # Pieni viive jokaisen lukemisen välillä
                time.sleep(0.1)
            
            # Merkitse onnistuneeksi, jos edes yksi luku onnistui
            self.program_names_loaded = (successful_reads > 0)
            
            # Päivitä UI valmiiksi
            QTimer.singleShot(0, lambda: self.update_complete(program_names, successful_reads))
        
        # Käynnistä päivitys taustasäikeessä
        threading.Thread(target=update_task, daemon=True).start()
    
    def update_complete(self, program_names, successful_reads=0):
        """Päivityksen valmistumisen käsittely"""
        self.program_names = program_names
        self.program_names_loaded = True
        self.progress_bar.hide()
        
        if successful_reads > 0:
            self.status_label.setText(f"Päivitetty {successful_reads}/30 ohjelmaa")
        else:
            self.status_label.setText("Ei ohjelmanimiä saatavilla")
    
    def save_program_selection(self):
        """Tallenna ohjelmavalinta ForTest-laitteelle Modbus-väylän kautta"""
        # Näytä tallennus ja tilapäivitys
        self.status_label.setText("Tallennetaan ohjelmavalintaa...")
        
        if not self.modbus.connected:
            self.status_label.setText("Virhe: Modbus-yhteyttä ei ole")
            return
        
        try:
            # Lähetetään Modbus-komento ohjelman 1 valitsemiseksi (osoite 0x0060)
            # TÄRKEÄÄ: ÄLÄ vähennä 1 ohjelmanumerosta - ForTest odottaa todellista ohjelmanumeroa
            result = self.modbus.client.write_register(self.PROGRAM_SELECT_REGISTER, 
                                                      self.program_selection["program1"], 
                                                      slave=1)
            
            if not result.isError():
                self.status_label.setText("Ohjelma valittu onnistuneesti")
                
                # Logaa valitut ohjelmat
                print(f"Tallennetaan ohjelmavalinnat:")
                print(f"Ohjelma 1: {self.program_selection['program1_name']} (ohjelma #{self.program_selection['program1']})")
                print(f"Ohjelma 2: {self.program_selection['program2_name']} (ohjelma #{self.program_selection['program2']}, käytössä: {self.program_selection['program2_enabled']})")
                print(f"Ohjelma 3: {self.program_selection['program3_name']} (ohjelma #{self.program_selection['program3']}, käytössä: {self.program_selection['program3_enabled']})")
            else:
                self.status_label.setText("Virhe ohjelman valinnassa!")
                print(f"Modbus-virhe ohjelman valinnassa: {result}")
        except Exception as e:
            self.status_label.setText(f"Virhe: {str(e)}")
            print(f"Virhe ohjelman valinnassa: {e}")