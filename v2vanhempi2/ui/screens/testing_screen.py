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
        self.modbus_register = 17000 + self.test_number  # PAINE 1-3 AKTIIVINEN rekisterit: 17001-17003
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
            font-family: 'Digital-7', 'Consolas', monospace;
            font-size: 40px;
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
        
        # Ajastin rekisterien tilan tarkistukseen
        self.modbus_timer = QTimer(self)
        self.modbus_timer.timeout.connect(self.check_modbus_state)
        self.modbus_timer.start(150)  # Tarkista kerran sekunnissa
    
    # Lisää parent-metodin käyttö:
    def get_fortest(self):
        """Hae vanhemman ForTest-olio"""
        if hasattr(self.parent(), 'fortest'):
            return self.parent().fortest
        return None
    
    def get_modbus(self):
        """Hae vanhemman Modbus-olio"""
        if hasattr(self.parent(), 'parent') and hasattr(self.parent().parent(), 'modbus'):
            return self.parent().parent().modbus
        return None

    def request_program_selection(self):
        """Pyydä ohjelman valintaa"""
        self.program_selection_requested.emit(self.test_number)
    
    def set_program(self, program_name):
        """Aseta valittu ohjelma"""
        self.selected_program = program_name
        self.program_label.setText(f" {program_name}")
    
    def toggle_active(self):
        """Vaihda aktiivisuustila ja lähetä Modbus-käsky"""
        self.is_active = not self.is_active
        self.update_button_style()
        
        # Lähetä tila modbus-rekisteriin
        modbus = self.get_modbus()
        if modbus and modbus.connected:
            value = 1 if self.is_active else 0
            result = modbus.write_register(self.modbus_register, value)
            if not result:
                # Vaihda tila takaisin jos epäonnistui
                self.is_active = not self.is_active
                self.update_button_style()
        
        # Aktivoi vastaava GPIO-pinni
        if hasattr(self.parent().parent(), 'gpio_handler') and self.parent().parent().gpio_handler:
            self.parent().parent().gpio_handler.set_output(self.test_number, self.is_active)
    
    def update_button_style(self):
        """Päivitä napin tyyli tilan mukaan"""
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
    
    def check_modbus_state(self):
        """Tarkista aktiivisuustila modbus-rekisteristä"""
        modbus = self.get_modbus()
        if modbus and modbus.connected:
            try:
                result = modbus.read_holding_registers(self.modbus_register, 1)
                if result and hasattr(result, 'registers') and len(result.registers) > 0:
                    # Jos rekisterissä on 1, vaihdetaan tilaa (toggle)
                    if result.registers[0] == 1:
                        # Vaihda tila päinvastaiseksi vain kerran rekisteriarvon ollessa 1
                        if not hasattr(self, '_last_register_value') or self._last_register_value != 1:
                            self.is_active = not self.is_active
                            self.update_button_style()
                            
                            # Päivitä GPIO-tila
                            if hasattr(self.parent().parent(), 'gpio_handler') and self.parent().parent().gpio_handler:
                                self.parent().parent().gpio_handler.set_output(self.test_number, self.is_active)
                                
                            print(f"Testin {self.test_number} aktiivisuustila vaihdettiin: {self.is_active}")
                        
                    # Tallenna tämä rekisteriarvo muistiin seuraavaa tarkistusta varten
                    self._last_register_value = result.registers[0]
            except Exception as e:
                print(f"Virhe modbus-rekisterin {self.modbus_register} lukemisessa: {e}")

class RightControl(QWidget):
    """Oikean reunan ohjauspaneeli"""
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Modbus-rekisterit käynnistys- ja pysäytysohjaukselle
        self.start_register = 17000
        self.stop_register = 16999
        
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
            font-family: Consolas, Courier, monospace;
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
        
        # Ajastin rekisterien tilan tarkistukseen
        self.modbus_timer = QTimer(self)
        self.modbus_timer.timeout.connect(self.check_control_registers)
        self.modbus_timer.start(150)  # Tarkista 150 millisekunnin välein
        
        # Käynnissä tila
        self.is_running = False
        
    def get_modbus(self):
        """Hae modbus-yhteys pääikkunalta"""
        if hasattr(self.parent(), 'parent') and hasattr(self.parent().parent(), 'modbus'):
            return self.parent().parent().modbus
        return None
    
    def get_gpio_handler(self):
        """Hae GPIO-käsittelijä pääikkunalta"""
        if hasattr(self.parent(), 'parent') and hasattr(self.parent().parent(), 'gpio_handler'):
            return self.parent().parent().gpio_handler
        return None
    
    def check_control_registers(self):
        """Tarkista käynnistys- ja pysäytysrekisterien tila"""
        modbus = self.get_modbus()
        if modbus and modbus.connected:
            try:
                # Tarkista käynnistysrekisteri (17000)
                start_result = modbus.read_holding_registers(self.start_register, 1)
                if start_result and hasattr(start_result, 'registers') and len(start_result.registers) > 0:
                    # Kun rekisterissä on 1, käynnistä testi jos se ei ole jo käynnissä
                    if start_result.registers[0] == 1:
                        # Vain jos edellinen arvo ei ollut 1, vaihdetaan tilaa
                        if not hasattr(self, '_last_start_value') or self._last_start_value != 1:
                            if not self.is_running:
                                self.is_running = True
                                self.update_buttons()
                                # Käynnistä testi ForTest-laitteella
                                if hasattr(self.parent(), 'start_test'):
                                    self.parent().start_test()
                                # Aktivoi GPIO 23 (ulostulo 4) käynnistyksen yhteydessä
                                gpio_handler = self.get_gpio_handler()
                                if gpio_handler:
                                    gpio_handler.set_output(4, True)  # Aseta ulostulo 4 päälle
                                    # Aseta ajastin sammuttamaan GPIO 200ms:n kuluttua
                                    QTimer.singleShot(200, lambda: gpio_handler.set_output(4, False))
                    
                    # Tallenna tämä rekisteriarvo seuraavaa tarkistusta varten
                    self._last_start_value = start_result.registers[0]
                
                # Tarkista pysäytysrekisteri (16999)
                stop_result = modbus.read_holding_registers(self.stop_register, 1)
                if stop_result and hasattr(stop_result, 'registers') and len(stop_result.registers) > 0:
                    # Kun rekisterissä on 1, pysäytä testi jos se on käynnissä
                    if stop_result.registers[0] == 1:
                        # Vain jos edellinen arvo ei ollut 1, pysäytetään testi
                        if not hasattr(self, '_last_stop_value') or self._last_stop_value != 1:
                            if self.is_running:
                                self.is_running = False
                                self.update_buttons()
                                # Pysäytä testi ForTest-laitteella
                                if hasattr(self.parent(), 'stop_test'):
                                    self.parent().stop_test()
                                # Aktivoi GPIO 24 (ulostulo 5) pysäytyksen yhteydessä
                                gpio_handler = self.get_gpio_handler()
                                if gpio_handler:
                                    gpio_handler.set_output(5, True)  # Aseta ulostulo 5 päälle
                                    # Aseta ajastin sammuttamaan GPIO 200ms:n kuluttua
                                    QTimer.singleShot(200, lambda: gpio_handler.set_output(5, False))
                    
                    # Tallenna tämä rekisteriarvo seuraavaa tarkistusta varten
                    self._last_stop_value = stop_result.registers[0]
                    
            except Exception as e:
                pass  # Älä tulosta virheilmoituksia
    
    def update_buttons(self):
        """Päivitä nappien tyylit tilan mukaan"""
        if self.is_running:
            self.start_button.setStyleSheet("""
                QPushButton {
                    background-color: #388E3C;  /* Tummempi vihreä */
                    color: white;
                    border-radius: 5px;
                    font-size: 24px;
                    font-weight: bold;
                }
            """)
            self.stop_button.setStyleSheet("""
                QPushButton {
                    background-color: #F44336;
                    color: white;
                    border-radius: 5px;
                    font-size: 24px;
                    font-weight: bold;
                }
            """)
        else:
            self.start_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 5px;
                    font-size: 24px;
                    font-weight: bold;
                }
            """)
            self.stop_button.setStyleSheet("""
                QPushButton {
                    background-color: #D32F2F;  /* Tummempi punainen */
                    color: white;
                    border-radius: 5px;
                    font-size: 24px;
                    font-weight: bold;
                }
            """)
    
    def reset_register(self, register):
        """Nollaa rekisteri takaisin nollatilaan"""
        modbus = self.get_modbus()
        if modbus and modbus.connected:
            modbus.write_register(register, 0)
    
    def set_start_state(self, state):
        """Aseta käynnistystila ja päivitä modbus-rekisteri"""
        modbus = self.get_modbus()
        if modbus and modbus.connected:
            # Käyttäjän painaessa käynnistysnappia
            value = 1 if state else 0
            result = modbus.write_register(self.start_register, value)
            
            # Aktivoi GPIO 23 (ulostulo 4) käynnistyksen yhteydessä
            gpio_handler = self.get_gpio_handler()
            if gpio_handler and state:
                gpio_handler.set_output(4, True)
            
            # Jos kyseessä on käynnistyskomento, päivitetään tila
            if state and result:
                self.is_running = True
                self.update_buttons()
            
            # Jos arvo on 1 (käynnistys), nollataan se lyhyen viiveen jälkeen
            if value == 1:
                QTimer.singleShot(100, lambda: self.reset_register(self.start_register))
                # Aseta myös ulostulo 4 pois päältä viiveellä (momentary-tyylisesti)
                if gpio_handler:
                    QTimer.singleShot(150, lambda: gpio_handler.set_output(4, False))
    
    def set_stop_state(self, state):
        """Aseta pysäytystila ja päivitä modbus-rekisteri"""
        modbus = self.get_modbus()
        gpio_handler = self.get_gpio_handler()
        
        # Varmista ensin, että ulostulo 5 on pois päältä (korjaa mahdollisen jumittuneen tilan)
        if gpio_handler:
            gpio_handler.set_output(5, False)
        
        if modbus and modbus.connected:
            # Käyttäjän painaessa pysäytysnappia
            value = 1 if state else 0
            result = modbus.write_register(self.stop_register, value)
            
            # Aktivoi GPIO 24 (ulostulo 5) pysäytyksen yhteydessä
            if gpio_handler and state:
                gpio_handler.set_output(5, True)
                # Varmista että GPIO 24 sammuu tietyn ajan kuluttua (käytä pidempää aikaa)
                QTimer.singleShot(200, lambda: gpio_handler.set_output(5, False))
            
            # Jos kyseessä on pysäytyskomento ja se onnistui
            if state and result:
                self.is_running = False
                self.update_buttons()
                # Pysäytä testi ForTest-laitteella
                if hasattr(self.parent(), 'stop_test'):
                    self.parent().stop_test()
            
            # Jos arvo on 1 (pysäytys), nollataan se lyhyen viiveen jälkeen
            if value == 1:
                QTimer.singleShot(100, lambda: self.reset_register(self.stop_register))

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
        """Käynnistä testi ja päivitä modbus-rekisteri"""
        # Päivitä modbus-rekisteri
        self.right_control.set_start_state(True)
        
        # Käynnistä testi ForTest-laitteella jos saatavilla
        if self.fortest is None:
            return
        
        self.fortest.start_test()

    def stop_test(self):
        """Pysäytä testi ja päivitä modbus-rekisteri"""
        # Päivitä modbus-rekisteri
        self.right_control.set_stop_state(True)
        
        # Pysäytä testi ForTest-laitteella jos saatavilla
        if self.fortest is None:
            return
        
        self.fortest.abort_test()
    
    def cleanup(self):
        """Siivoa resursit"""
        pass