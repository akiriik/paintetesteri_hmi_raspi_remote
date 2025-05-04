from PyQt5.QtWidgets import QLabel, QPushButton, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from ui.screens.base_screen import BaseScreen
from utils.modbus_handler import ModbusHandler

class ModbusScreen(BaseScreen):
    def __init__(self, parent=None, modbus=None):
        self.modbus = modbus  # Käytä annettua modbus-käsittelijää
        super().__init__(parent)
        
    def init_ui(self):
        # Page title
        self.title = self.create_title("MODBUS")
        
        # Status label
        self.status_label = QLabel("Modbus-ohjaukset", self)
        self.status_label.setFont(QFont("Arial", 14))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setGeometry(0, 80, 1280, 30)
        
        # Nollaus-nappi
        self.reset_button = QPushButton("NOLLAA", self)
        self.reset_button.setGeometry(550, 150, 180, 60)
        self.reset_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 10px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self.reset_button.clicked.connect(self.calibrate_sensor)
        
    def calibrate_sensor(self):
        """Kalibroi paineanturi näyttämään 0 kPa"""
        if not self.modbus.connected:
            self.status_label.setText("Modbus-yhteyttä ei ole!")
            return
            
        try:
            # Käytä Write Single Coil -komentoa rekisteriin 0x1E (30)
            # ForTest manuaalin mukaan autozero rekisteri on 0x1E ja arvo 0xFF00
            result = self.modbus.client.write_coil(0x1E, True, slave=1)
            
            if not result.isError():
                self.status_label.setText("Anturi nollattu")
                
                # Palauta teksti takaisin normaaliksi hetken kuluttua
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(3000, lambda: self.status_label.setText("Modbus-ohjaukset"))
                
            else:
                self.status_label.setText(f"Virhe nollauksessa: {result}")
        except Exception as e:
            self.status_label.setText(f"Virhe: {str(e)}")