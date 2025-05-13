# ui/components/emergency_stop_dialog.py
from PyQt5.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QFrame
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

class EmergencyStopDialog(QDialog):
    def __init__(self, parent=None, modbus=None):
        super().__init__(parent)
        self.modbus = modbus
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setStyleSheet("background-color: transparent;")
        self.setFixedSize(700, 500)
        
        # Keskitetään dialog
        if parent:
            self.move(
                parent.width() // 2 - self.width() // 2,
                parent.height() // 2 - self.height() // 2
            )
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Valkoinen laatikko paksulla punaisella reunalla
        self.red_frame = QFrame(self)
        self.red_frame.setStyleSheet("""
            background-color: white; 
            border-radius: 20px; 
            border: 16px solid red;
        """)
        frame_layout = QVBoxLayout(self.red_frame)
        frame_layout.setContentsMargins(20, 20, 20, 20)
        frame_layout.setSpacing(40)
        
        # Keskikohdan täyteväli
        frame_layout.addStretch()
        
        # Laatikko HÄTÄSEIS-tekstille punaisella reunalla
        self.text_container = QFrame(self.red_frame)
        self.text_container.setFixedSize(400, 100)
        self.text_container.setStyleSheet("""
            background-color: white;
            border-radius: 20px;
            border: 4px solid red;
        """)
        
        # HÄTÄSEIS-teksti 
        self.title = QLabel("HÄTÄSEIS", self.text_container)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setGeometry(0, 0, 400, 100)
        font = QFont("Arial", 36, QFont.Bold)
        self.title.setFont(font)
        self.title.setStyleSheet("color: black; background-color: transparent;")
        
        # Lisää container keskelle
        frame_layout.addWidget(self.text_container, 0, Qt.AlignCenter)
        
        # Täyteväli
        frame_layout.addStretch()
        
        # KUITTAUS-nappi ilman punaista reunaa
        self.reset_button = QPushButton("KUITTAUS", self.red_frame)
        self.reset_button.setFixedSize(300, 80)
        self.reset_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 20px;
                font-size: 24px;
                font-weight: bold;
                border: none;  /* Ei reunaa */
            }
        """)
        self.reset_button.clicked.connect(self.reset_emergency_stop)
        frame_layout.addWidget(self.reset_button, 0, Qt.AlignCenter)
        
        layout.addWidget(self.red_frame)
        
        # Ajastin tekstin vilkuttamiseen
        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.toggle_blink)
        self.blink_timer.start(500)
        self.is_visible = True
        
    def toggle_blink(self):
        """Vilkutus toiminto"""
        self.is_visible = not self.is_visible
        if self.is_visible:
            self.text_container.setStyleSheet("""
                background-color: white;
                border-radius: 20px;
                border: 4px solid red;
            """)
        else:
            self.text_container.setStyleSheet("""
                background-color: red;
                border-radius: 20px;
                border: 4px solid red;
            """)
    
    def reset_emergency_stop(self):
        """Kuittaa hätäseis"""
        if self.modbus:
            # ModbusManager - käytä aina momentary toimintaa
            if hasattr(self.modbus, 'write_register'):
                # Lisää lisäattribuutti ModbusWorker-luokkaan
                try:
                    # Aseta apuattribuutti
                    self.modbus.emergency_reset_active = True
                    
                    # Kuittaa hätäseis
                    result = self.modbus.write_register(19099, 1)
                    if hasattr(result, 'address'):
                        print(f"Debug: result.address = {result.address}")
                    
                    # Nollaa rekisteri hetken kuluttua
                    QTimer.singleShot(300, lambda: self.modbus.write_register(19099, 0))
                    
                    # Check status after a short delay to allow the system to update
                    QTimer.singleShot(500, self.check_status_after_reset)
                finally:
                    # Poista apuattribuutti
                    if hasattr(self.modbus, 'emergency_reset_active'):
                        delattr(self.modbus, 'emergency_reset_active')

    def reset_emergency_register_to_zero(self):
        """Palauta kuittausrekisteri takaisin nollaan"""
        if self.modbus:
            result = self.modbus.write_register(19099, 0)
            if result:
                print("Kuittausrekisteri palautettu arvoon 0")
            else:
                print("Kuittausrekisterin nollaus epäonnistui")
    
    def check_status_after_reset(self):
        """Tarkista tila kuittauksen jälkeen"""
        if self.modbus:
            status = self.modbus.read_emergency_stop_status()
            if status == 1:
                # Hätäseis on nyt pois päältä, voidaan sulkea dialogi
                self.accept()
            else:
                # Hätäseis on edelleen päällä, älä sulje dialogia
                # Päivitä nappi ilmoittamaan tilanteesta
                self.reset_button.setText("KUITTAUS (HÄTÄSEIS EDELLEEN AKTIIVINEN)")
                self.reset_button.setStyleSheet("""
                    QPushButton {
                        background-color: #FFC107;
                        color: black;
                        border-radius: 20px;
                        font-size: 18px;
                        font-weight: bold;
                    }
                """)