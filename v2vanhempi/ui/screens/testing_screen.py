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
        
        # Testin tulospaine-näyttö (kuten MPX-näyttö)
        self.test_pressure_label = QLabel("", self)
        self.test_pressure_label.setStyleSheet("""
            background-color: black;
            color: #33FF33;
            font-family: 'Consolas', 'Courier', monospace;
            font-size: 60px;
            font-weight: bold;
            border: 2px solid #444444;
            border-radius: 10px;
            padding: 10px;
        """)
        self.test_pressure_label.setAlignment(Qt.AlignCenter)
        self.test_pressure_label.setGeometry(400, 300, 480, 100)
        
        # Testiyksikkö-label tulospaineen alle
        self.test_unit_label = QLabel("mbar", self)
        self.test_unit_label.setStyleSheet("""
            color: #666666;
            font-family: 'Arial', sans-serif;
            font-size: 18px;
        """)
        self.test_unit_label.setAlignment(Qt.AlignCenter)
        self.test_unit_label.setGeometry(400, 410, 480, 30)
        
        # Käynnistys-nappi
        self.start_button = QPushButton("KÄYNNISTÄ", self)
        self.start_button.setGeometry(440, 450, 180, 80)
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
        self.stop_button.setGeometry(640, 450, 180, 80)
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
        
        # Tulos-label
        self.result_label = QLabel("", self)
        self.result_label.setStyleSheet("""
            color: #333333;
            font-family: 'Arial', sans-serif;
            font-size: 30px;
            font-weight: bold;
        """)
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setGeometry(300, 150, 680, 50)
        
        # Testerin tilatieto  
        self.test_status_label = QLabel("", self)
        self.test_status_label.setStyleSheet("""
            color: #666666;
            font-family: 'Arial', sans-serif;
            font-size: 18px;
        """)
        self.test_status_label.setAlignment(Qt.AlignCenter)
        self.test_status_label.setGeometry(300, 200, 680, 30)

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
        self.test_pressure_label.setText("")
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
            # Lue tila-rekisterit (0x30)
            status_result = self.fortest_modbus.read_holding_registers(0x30, 32)
            
            if status_result and hasattr(status_result, 'registers') and len(status_result.registers) >= 32:
                # Register mappings (from PDF Table - Status Value Mapping):
                errors_mask = status_result.registers[0]  # Position 1
                last_status = status_result.registers[2]  # Position 3
                last_substatus = status_result.registers[4]  # Position 5
                last_result_phase = status_result.registers[6]  # Position 7
                
                print(f"DEBUG: Status={last_status}, SubStatus={last_substatus}, Phase={last_result_phase}")
                
                # Tarkista onko testi käynnissä (status 1-26)
                if last_status in [1, 3, 11, 12, 14, 15, 22, 26]:  # Test phases from Table - Phase of test
                    self.test_running = True
                    self.result_label.setText("TESTAUS KÄYNNISSÄ")
                    self.result_label.setStyleSheet("color: #2196F3; font-size: 30px; font-weight: bold;")
                    
                    # Näytä testitilanne last_status mukaan  
                    if last_status == 1:
                        self.test_status_label.setText("Aloitus")
                    elif last_status == 3:
                        self.test_status_label.setText("Esi-täyttö")
                    elif last_status == 11:
                        self.test_status_label.setText("Täyttö")
                    elif last_status == 14:
                        self.test_status_label.setText("Asettuminen")
                    elif last_status == 26:
                        self.test_status_label.setText("Testausvaihe")
                    else:
                        self.test_status_label.setText(f"Vaihe {last_status}")
                        
                    self.test_pressure_label.setText("")
                    
                elif last_status == 0:  # Waiting
                    if self.test_running:
                        # Test ended, check results
                        self.test_running = False
                        self.test_status_label.setText("Testi valmis")
                        self.read_test_results()
                    else:
                        self.test_status_label.setText("Valmiustila")
                        
                elif last_status == 2:  # Autozero
                    self.test_status_label.setText("Kalibrointi")
                elif last_status == 30:  # Discharge
                    self.test_status_label.setText("Purku")
                    
            else:
                self.test_status_label.setText("Ei vastausta testilaitteelta")
                
        except Exception as e:
            print(f"Status error: {e}")
            self.test_status_label.setText("Yhteysvirhe")
    
    def read_test_results(self):
        """Lue testitulokset"""
        try:
            # Lue tulokset (0x40)
            result_regs = self.fortest_modbus.read_holding_registers(0x40, 70)
            
            if result_regs and hasattr(result_regs, 'registers') and len(result_regs.registers) >= 60:
                # Check if registers have data  
                if any(result_regs.registers):
                    # Result value is at position 19 (index 18)
                    result_value = result_regs.registers[18]
                    
                    # Table - Result of Test
                    if result_value == 1:
                        self.result_label.setText("HYVÄ")
                        self.result_label.setStyleSheet("color: #4CAF50; font-size: 30px; font-weight: bold;")
                    elif result_value == 2:
                        self.result_label.setText("HYLÄTTY")
                        self.result_label.setStyleSheet("color: #F44336; font-size: 30px; font-weight: bold;")
                    elif result_value == 13:
                        self.result_label.setText("KESKEYTETTY")
                        self.result_label.setStyleSheet("color: #FF9800; font-size: 30px; font-weight: bold;")
                    else:
                        self.result_label.setText(f"Tulos: {result_value}")
                    
                    # Pressure at end of test - from register 51 (position 33)
                    pressure_high = result_regs.registers[32]  # Position 33
                    pressure_low = result_regs.registers[34]   # Position 35
                    
                    # Combine high and low bytes
                    pressure_value = (pressure_high << 16) | pressure_low
                    
                    # Decimal points from register 39 (position 39)
                    decimal_points = result_regs.registers[38]  # Position 39
                    
                    # Convert pressure value using decimal points
                    actual_pressure = pressure_value / (10 ** decimal_points)
                    
                    # Show pressure value
                    self.test_pressure_label.setText(f"{actual_pressure:.3f}")
                    
                    # Unit from register 37 (position 37)
                    unit_measure = result_regs.registers[36]  # Position 37
                    
                    # Show unit
                    if unit_measure == 0:
                        unit_text = "mbar"
                    elif unit_measure == 1:
                        unit_text = "bar"
                    elif unit_measure == 4:
                        unit_text = "psi"
                    else:
                        unit_text = "mbar"  # default
                        
                    self.test_unit_label.setText(unit_text)
                    self.test_status_label.setText("Testi valmis")
                else:
                    # No results yet
                    self.test_status_label.setText("Odotetaan tuloksia...")
                    self.test_pressure_label.setText("")
            else:
                self.test_status_label.setText("Ei tuloksia saatavissa")
        except Exception as e:
            print(f"Result reading error: {e}")
            self.test_status_label.setText("Tuloslukuvirhe")
            self.test_pressure_label.setText("")
    
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