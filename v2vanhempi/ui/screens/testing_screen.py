#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testaussivun sisältö painetestausjärjestelmälle
Käyttää suoraa USB-yhteyttä ForTest-testilaitteeseen
"""
import sys
import os
from PyQt5.QtWidgets import QLCDNumber, QLabel, QPushButton, QFrame
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QColor
from ui.screens.base_screen import BaseScreen
from utils.pressure_reader import PressureReaderThread
from utils.modbus_handler import ModbusHandler

# Yritä tuoda anturimoduuli
try:
    from utils.mpx5700.DFROBOT_MPX5700 import DFRobot_MPX5700_I2C
except ImportError:
    print("Varoitus: DFRobot_MPX5700_I2C-moduulia ei löydy")
    DFRobot_MPX5700_I2C = None

class TestingScreen(BaseScreen):
    def __init__(self, parent=None, modbus=None):
        self.sensor = None
        self.pressure_thread = None
        self.fortest_modbus = ModbusHandler(port='/dev/ttyUSB1', baudrate=19200)
        self.test_result = ""
        self.test_running = False
        super().__init__(parent)
        
        # Alusta paineanturi
        self.init_pressure_sensor()
        
        # Ajastin testauksen tilan tarkistamiseksi
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.check_test_status)
        self.status_timer.start(1000)  # Tarkista 1s välein
    
    def init_ui(self):
        # Sivun otsikko
        self.title = self.create_title("TESTAUS")
        
        # Luo painenäyttö (pieni, vasen yläkulma)
        self.pressure_label = QLabel("0.00", self)
        self.pressure_label.setStyleSheet("""
            background-color: black;
            color: #33FF33;
            font-family: 'Consolas', 'Courier', monospace;
            font-size: 40px;
            font-weight: bold;
            border: 2px solid #444444;
            border-radius: 10px;
            padding: 5px;
        """)
        self.pressure_label.setAlignment(Qt.AlignCenter)
        self.pressure_label.setGeometry(20, 80, 200, 80)
        
        # Tilan indikaattori
        self.status_indicator = QFrame(self)
        self.status_indicator.setGeometry(230, 105, 20, 20)
        self.status_indicator.setStyleSheet("""
            background-color: #4CAF50; 
            border-radius: 10px;
            border: 2px solid #388E3C;
        """)
        
        # Tulos-label keskelle ylös
        self.result_label = QLabel("", self)
        self.result_label.setStyleSheet("""
            color: #333333;
            font-family: 'Arial', sans-serif;
            font-size: 30px;
            font-weight: bold;
        """)
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setGeometry(300, 150, 680, 50)
        
        # Numeraalinen testitulos
        self.test_value_label = QLabel("", self)
        self.test_value_label.setStyleSheet("""
            color: #333333;
            font-family: 'Consolas', monospace;
            font-size: 24px;
            font-weight: bold;
        """)
        self.test_value_label.setAlignment(Qt.AlignCenter)
        self.test_value_label.setGeometry(300, 200, 680, 40)
        
        # Testerin tilatieto  
        self.test_status_label = QLabel("", self)
        self.test_status_label.setStyleSheet("""
            color: #666666;
            font-family: 'Arial', sans-serif;
            font-size: 18px;
        """)
        self.test_status_label.setAlignment(Qt.AlignCenter)
        self.test_status_label.setGeometry(300, 240, 680, 30)
        
        # Käynnistys-nappi
        self.start_button = QPushButton("KÄYNNISTÄ", self)
        self.start_button.setGeometry(440, 300, 180, 80)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 10px;
                font-size: 22px;
                font-weight: bold;
            }
        """)
        self.start_button.clicked.connect(self.start_test)
        
        # Pysäytys-nappi
        self.stop_button = QPushButton("PYSÄYTÄ", self)
        self.stop_button.setGeometry(640, 300, 180, 80)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border-radius: 10px;
                font-size: 22px;
                font-weight: bold;
            }
        """)
        self.stop_button.clicked.connect(self.stop_test)

    def init_pressure_sensor(self):
        if DFRobot_MPX5700_I2C is not None:
            try:
                self.sensor = DFRobot_MPX5700_I2C(1, 0x16)
                self.sensor.set_mean_sample_size(5)
                
                # Aloita paineen lukeminen erillisessä säikeessä
                self.pressure_thread = PressureReaderThread(self.sensor)
                self.pressure_thread.pressureUpdated.connect(self.update_pressure)
                self.pressure_thread.start()
            except Exception as e:
                self.sensor = None
                if hasattr(self, 'status_indicator'):
                    self.status_indicator.setStyleSheet("""
                        background-color: #F44336; 
                        border-radius: 10px;
                        border: 2px solid #D32F2F;
                    """)
    
    def update_pressure(self, value):
        """Päivitä painelukema näytölle"""
        self.pressure_label.setText(f"{value:.2f}")
        
        # Muuta väri paineen mukaan
        if value > 500:
            color = "#F44336"  # Punainen
        elif value > 300:
            color = "#FFC107"  # Keltainen
        else:
            color = "#33FF33"  # Vihreä
            
        self.pressure_label.setStyleSheet(f"""
            background-color: black;
            color: {color};
            font-family: 'Consolas', 'Courier', monospace;
            font-size: 40px;
            font-weight: bold;
            border: 2px solid #444444;
            border-radius: 10px;
            padding: 5px;
        """)
    
    def start_test(self):
        """Käynnistä testi"""
        if not self.fortest_modbus.connected:
            self.result_label.setText("Testilaite ei yhteydessä!")
            return
            
        # Tyhjennä edelliset tulokset
        self.result_label.setText("")
        self.test_value_label.setText("")
        self.test_status_label.setText("Käynnistetään...")
        
        try:
            result = self.fortest_modbus.write_coil(0x0A, True)
            if result:
                self.test_running = True
                self.test_status_label.setText("Testi käynnistetty")
            else:
                self.result_label.setText("Virhe testin käynnistyksessä")
        except Exception as e:
            self.result_label.setText(f"Virhe: {str(e)}")
    
    def stop_test(self):
        """Pysäytä testi"""
        if not self.fortest_modbus.connected:
            self.result_label.setText("Testilaite ei yhteydessä!")
            return
            
        try:
            result = self.fortest_modbus.write_coil(0x14, True)
            if result:
                self.test_running = False
                self.test_status_label.setText("Testi keskeytetty")
            else:
                self.result_label.setText("Virhe testin pysäytyksessä")
        except Exception as e:
            self.result_label.setText(f"Virhe: {str(e)}")
    
    def check_test_status(self):
        """Tarkista testin tila"""
        if not self.fortest_modbus.connected:
            self.test_status_label.setText("Ei yhteyttä testilaitteeseen")
            return
            
        try:
            # Lue tila-rekisterit (50 ja 51)
            status_result = self.fortest_modbus.read_holding_registers(0x30, 6)
            
            if status_result and hasattr(status_result, 'registers') and len(status_result.registers) >= 6:
                # Rekisteri 50 (indeksi 1): testin vaihe
                test_phase = status_result.registers[1]
                # Rekisteri 51 (indeksi 2): testi käynnissä/standby
                test_active = status_result.registers[2]
                
                # Tilan tulkinta
                if test_phase == 0 and test_active == 1:
                    # Standby-tila - tarkista onko tuloksia
                    if self.test_running:
                        # Testi on juuri päättynyt
                        self.test_running = False
                        self.test_status_label.setText("Testi valmis")
                        self.read_test_results()
                    else:
                        # Normaalisti valmiustilassa
                        self.test_status_label.setText("Valmiustila")
                        
                elif test_active == 99:
                    # Testi käynnissä
                    self.test_running = True
                    self.result_label.setText("TESTAUS KÄYNNISSÄ")
                    self.result_label.setStyleSheet("color: #2196F3; font-size: 30px; font-weight: bold;")
                    
                    # Näytä testin vaihe
                    if test_phase == 1:
                        self.test_status_label.setText("Täyttö")
                    elif test_phase == 12:
                        self.test_status_label.setText("Täytön aloitus")
                    elif test_phase == 15:
                        self.test_status_label.setText("Asettuminen")
                    elif test_phase == 26:
                        self.test_status_label.setText("Testausvaihe")
                    elif test_phase == 99:
                        self.test_status_label.setText("Testaus käynnissä")
                    else:
                        self.test_status_label.setText(f"Vaihe {test_phase}")
                    
                    # Tyhjennä edelliset tulokset
                    self.test_value_label.setText("")
                else:
                    # Epäselvä tila
                    self.test_status_label.setText(f"Tila {test_phase}/{test_active}")
            else:
                self.test_status_label.setText("Ei vastausta testilaitteelta")
                
        except Exception as e:
            self.test_status_label.setText("Yhteysvirhe")
    
    def read_test_results(self):
        """Lue testitulokset"""
        try:
            # Lue tulokset (0x40 = 64 desimaalista)
            result_regs = self.fortest_modbus.read_holding_registers(0x40, 20)
            
            if result_regs and hasattr(result_regs, 'registers') and len(result_regs.registers) >= 19:
                # Tarkista että tulokset eivät ole tyhjiä
                if any(result_regs.registers):
                    # Lue tuloksen arvo (indeksi 18)
                    result_value = result_regs.registers[18]
                    
                    # Näytä tulos
                    if result_value == 1:
                        self.result_label.setText("HYVÄ TULOS")
                        self.result_label.setStyleSheet("color: #4CAF50; font-size: 30px; font-weight: bold;")
                    elif result_value == 2:
                        self.result_label.setText("HYLÄTTY")
                        self.result_label.setStyleSheet("color: #F44336; font-size: 30px; font-weight: bold;")
                    elif result_value == 13:
                        self.result_label.setText("KESKEYTETTY")
                        self.result_label.setStyleSheet("color: #FF9800; font-size: 30px; font-weight: bold;")
                    else:
                        self.result_label.setText(f"Tulos: {result_value}")
                    
                    # Lue testerin painearvo ja näytä testerin tilakentässä
                    if len(result_regs.registers) >= 35:
                        pressure_high = result_regs.registers[32]
                        pressure_low = result_regs.registers[34]
                        pressure_value = (pressure_high << 16) | pressure_low
                        
                        # Muunna paine oikeaksi (oletetaan 2 desimaalia)
                        pressure_value = pressure_value / 100
                        
                        # Näytä testerin paine tilarivissä
                        self.test_status_label.setText(f"Testiarvo: {pressure_value:.2f} mbar")
                    
                    # Tyhjennä numeroarvo-kenttä
                    self.test_value_label.setText("")
                else:
                    # Ei tuloksia vielä
                    self.test_status_label.setText("Odotetaan tuloksia...")
        except Exception as e:
            self.test_status_label.setText("Tuloslukuvirhe")
    
    def cleanup(self):
        # Pysäytä säie jos se on käynnissä
        if self.pressure_thread is not None:
            self.pressure_thread.stop()
            self.pressure_thread.wait()
            self.pressure_thread = None
        
        # Pysäytä ajastin
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()
        
        # Sulje ForTest-yhteys
        if hasattr(self, 'fortest_modbus'):
            self.fortest_modbus.close()