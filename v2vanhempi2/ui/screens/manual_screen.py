from PyQt5.QtWidgets import QPushButton, QLabel, QFrame
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont
from ui.screens.base_screen import BaseScreen
from utils.modbus_handler import ModbusHandler

class ManualScreen(BaseScreen):
    def __init__(self, parent=None, modbus=None):
        self.modbus = modbus  # Käytä annettua modbus-käsittelijää
        self.relay_buttons = []
        self.relay_states = [False] * 8  # Releiden tilat (False = pois, True = päällä)
        super().__init__(parent)
        
    def init_ui(self):
        # Page title
        self.title = self.create_title("KÄSIKÄYTTÖ")
        
        # Takaisin-nappi
        self.back_button = QPushButton("← TAKAISIN", self)
        self.back_button.setGeometry(20, 20, 150, 60)
        self.back_button.setStyleSheet("""
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
        """)
        self.back_button.clicked.connect(self.go_back)
        
        # Relay control panel
        relay_panel = QFrame(self)
        relay_panel.setGeometry(50, 150, 1180, 400)
        relay_panel.setStyleSheet("background-color: #f0f0f0; border-radius: 10px;")
        
        # Status label for user feedback
        self.relay_status_label = QLabel("Rele-ohjaukset", self)
        self.relay_status_label.setFont(QFont("Arial", 14))
        self.relay_status_label.setAlignment(Qt.AlignCenter)
        self.relay_status_label.setGeometry(0, 560, 1280, 30)
        
        # Relay buttons
        for i in range(8):
            row = i // 4
            col = i % 4
            
            # Luo relepainike
            btn = QPushButton(f"RELE {i+1}", relay_panel)
            btn.setGeometry(50 + col*280, 50 + row*150, 220, 100)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #888888;
                    color: white;
                    border-radius: 10px;
                    font-size: 18px;
                    font-weight: bold;
                }
                QPushButton:pressed {
                    background-color: #00aa00;
                }
            """)
            
            # Yhdistä napin painallus releen ohjaukseen
            btn.clicked.connect(lambda checked, idx=i: self.toggle_relay_button(idx))
            self.relay_buttons.append(btn)
            
    def toggle_relay_button(self, index):
        # Vaihda releen tila
        self.relay_states[index] = not self.relay_states[index]
        new_state = 1 if self.relay_states[index] else 0
        
        # Päivitä napin ulkoasu
        self.relay_buttons[index].setStyleSheet("""
            QPushButton {
                background-color: %s;
                color: white;
                border-radius: 10px;
                font-size: 18px;
                font-weight: bold;
            }
        """ % ("#00aa00" if self.relay_states[index] else "#888888"))
        
        # Lähetä Modbus-komento
        try:
            relay_num = index + 1
            success = self.modbus.toggle_relay(relay_num, new_state)
            if success:
                self.relay_status_label.setText(f"Rele {relay_num} {'PÄÄLLÄ' if new_state else 'POIS'}")
            else:
                self.relay_status_label.setText(f"Virhe releen {relay_num} ohjauksessa!")
                # Palauta napin tila, koska komento epäonnistui
                self.relay_states[index] = not self.relay_states[index]
                self.relay_buttons[index].setStyleSheet("""
                    QPushButton {
                        background-color: %s;
                        color: white;
                        border-radius: 10px;
                        font-size: 18px;
                        font-weight: bold;
                    }
                """ % ("#00aa00" if self.relay_states[index] else "#888888"))
        except Exception as e:
            print(f"Virhe releen {index+1} ohjauksessa: {e}")
            self.relay_status_label.setText(f"Virhe: {str(e)}")
            
    def go_back(self):
        """Palaa testaussivulle"""
        if hasattr(self.parent(), 'show_testing'):
            self.parent().show_testing()
    
    def cleanup(self):
        # Sulje Modbus-yhteys
        if hasattr(self, 'modbus'):
            self.modbus.close()