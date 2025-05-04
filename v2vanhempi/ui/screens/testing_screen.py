#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Testaussivun sisältö painetestausjärjestelmälle
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
        self.modbus = modbus or ModbusHandler(port='/dev/ttyUSB0', baudrate=19200)
        self.test_result = ""
        self.test_running = False
        super().__init__(parent)
        
        # Alusta paineanturi
        self.init_pressure_sensor()
        
        # Ajastin testauksen tilan tarkistamiseksi
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.check_test_status)
        self.status_timer.start(500)  # Tarkista 500ms välein
    
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
        
        # Käynnistys-nappi (keskellä)
        self.start_button = QPushButton("KÄYNNISTÄ", self)
        self.start_button.setGeometry(440, 250, 180, 80)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 10px;
                font-size: 22px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
            QPushButton:pressed {
                background-color: #1B5E20;
            }
        """)
        self.start_button.clicked.connect(self.start_test)
        
        # Pysäytys-nappi (käynnistys-napin vieressä)
        self.stop_button = QPushButton("PYSÄYTÄ", self)
        self.stop_button.setGeometry(640, 250, 180, 80)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border-radius: 10px;
                font-size: 22px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
            QPushButton:pressed {
                background-color: #B71C1C;
            }
        """)
        self.stop_button.clicked.connect(self.stop_test)

    def init_pressure_sensor(self):
        if DFRobot_MPX5700_I2C is not None:
            try:
                self.sensor = DFRobot_MPX5700_I2C(1, 0x16)
                self.sensor.set_mean_sample_size(5)  # Kasvatettu tasaisuuden parantamiseksi
                print("Paineanturi alustettu onnistuneesti")
                
                # Aloita paineen lukeminen erillisessä säikeessä
                self.pressure_thread = PressureReaderThread(self.sensor)
                self.pressure_thread.pressureUpdated.connect(self.update_pressure)
                self.pressure_thread.start()
            except Exception as e:
                print(f"Paineanturin alustusvirhe: {e}")
                self.sensor = None
                if hasattr(self, 'status_indicator'):
                    self.status_indicator.setStyleSheet("""
                        background-color: #F44336; 
                        border-radius: 10px;
                        border: 2px solid #D32F2F;
                    """)
    
    def update_pressure(self, value):
        """Päivitä painelukema näytölle"""
        # Päivitä arvo digitaalinäyttöön
        self.pressure_label.setText(f"{value:.2f}")
        
        # Muuta väri paineen mukaan (vihreä=normaali, keltainen=korkea, punainen=kriittinen)
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
        """Käynnistä testi Modbus-komennolla"""
        if not self.modbus.connected:
            self.result_label.setText("Modbus-yhteyttä ei ole!")
            return
            
        try:
            # Päivitetty pymodbus 3.9.2 -syntaksille: käytä handler-luokan metodia
            result = self.modbus.write_coil(0x0A, True)
            
            if result:
                self.result_label.setText("Testi käynnistetty")
                self.test_running = True
            else:
                self.result_label.setText("Virhe testin käynnistyksessä")
        except Exception as e:
            self.result_label.setText(f"Virhe: {str(e)}")
    
    def stop_test(self):
        """Pysäytä testi Modbus-komennolla"""
        if not self.modbus.connected:
            self.result_label.setText("Modbus-yhteyttä ei ole!")
            return
            
        try:
            # Päivitetty pymodbus 3.9.2 -syntaksille: käytä handler-luokan metodia
            result = self.modbus.write_coil(0x14, True)
            
            if result:
                self.result_label.setText("Testi pysäytetty")
                self.test_running = False
            else:
                self.result_label.setText("Virhe testin pysäytyksessä")
        except Exception as e:
            self.result_label.setText(f"Virhe: {str(e)}")
    
    def check_test_status(self):
        """Tarkista testin tila ja tulos"""
        if not self.modbus.connected:
            return
            
        try:
            # Päivitetty pymodbus 3.9.2 -syntaksille: käytä handler-luokan metodia
            status_result = self.modbus.read_holding_registers(0x30, 10)
            
            if status_result and not hasattr(status_result, 'isError'):
                status_value = status_result.registers[0]
                
                # Tilan tulkinta rekisteristä (0 = odottaa, 1 = testi käynnissä, jne.)
                if status_value == 0:
                    # Odotustila
                    self.test_running = False
                elif status_value == 1:
                    # Testi käynnissä
                    self.test_running = True
                
                # Jos testi on käynnissä, näytä "TESTAUS KÄYNNISSÄ"
                if self.test_running:
                    self.result_label.setText("TESTAUS KÄYNNISSÄ")
                    self.result_label.setStyleSheet("color: #2196F3; font-size: 30px; font-weight: bold;")
                
                # Jos testi ei ole käynnissä, tarkista onko tulos saatavilla
                if not self.test_running:
                    # Lue tulos rekisteristä 0x40
                    result_regs = self.modbus.read_holding_registers(0x40, 40)
                    
                    if result_regs and result_regs.registers[0] != 0:
                        # Tuloksen tulkinta (19 = tulos OK, muut arvot ovat eri virheitä)
                        result_value = result_regs.registers[18]  # Rekisteri 0x40 + 18 = tuloksen tieto
                        
                        # Hae mitattu painearvo (rekisteri 0x40 + 32, 0x40 + 34)
                        pressure_high = result_regs.registers[32]  # Paineen ylempi osa
                        pressure_low = result_regs.registers[34]   # Paineen alempi osa
                        
                        # Paineen yksikkö ja desimaalipisteiden määrä
                        pressure_unit = result_regs.registers[36]
                        pressure_decimals = result_regs.registers[38]
                        
                        # Laske kokonaispainearvo
                        pressure_value = (pressure_high << 16) | pressure_low
                        
                        # Skaalaa desimaalipisteiden mukaan
                        if pressure_decimals > 0:
                            pressure_value = pressure_value / (10 ** pressure_decimals)
                        
                        # Määritä yksikkö
                        unit_text = "mbar"  # Oletus
                        if pressure_unit == 1:
                            unit_text = "bar"
                        elif pressure_unit == 2:
                            unit_text = "hPa"
                        elif pressure_unit == 3:
                            unit_text = "Pa"
                        elif pressure_unit == 4:
                            unit_text = "psi"
                        
                        # Näytä tulos ja painearvo
                        result_text = ""
                        if result_value == 1:  # Good
                            result_text = f"HYVÄ TULOS - {pressure_value:.2f} {unit_text}"
                            self.result_label.setStyleSheet("color: #4CAF50; font-size: 30px; font-weight: bold;")
                        elif result_value == 2:  # Bad
                            result_text = f"HYLÄTTY - {pressure_value:.2f} {unit_text}"
                            self.result_label.setStyleSheet("color: #F44336; font-size: 30px; font-weight: bold;")
                        elif result_value == 13:  # Abort
                            result_text = f"KESKEYTETTY - {pressure_value:.2f} {unit_text}"
                            self.result_label.setStyleSheet("color: #FF9800; font-size: 30px; font-weight: bold;")
                        
                        self.result_label.setText(result_text)
                        
        except Exception as e:
            print(f"Virhe tilan tarkistuksessa: {e}")
    
    def cleanup(self):
        # Pysäytä säie jos se on käynnissä
        if self.pressure_thread is not None:
            self.pressure_thread.stop()
            self.pressure_thread.wait()
            self.pressure_thread = None
        
        # Pysäytä ajastin
        if hasattr(self, 'status_timer'):
            self.status_timer.stop()