# ui/components/test_panel.py
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont 

class TestPanel(QWidget):
    """Yksittäisen testin paneeli"""
    program_selection_requested = pyqtSignal(int)  # Signaali ohjelman valintapyynnölle
    status_message = pyqtSignal(str, int)  # Viesti, tyyppi
    
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
        layout.setSpacing(10)

        # Tuloslista, max 3 riviä
        self.results_history = []  # Tallentaa max 3 viimeisintä tulosta        

        # Painetulos laatikko
        self.pressure_result = QLabel("", self)
        self.pressure_result.setFixedSize(280, 250)
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
        
        # Tuloshistoriaa varten käytetään QLabel + vieritys
        self.results_area = QTextEdit(self.result_frame)
        self.results_area.setGeometry(10, 60, 260, 180)
        self.results_area.setReadOnly(True)
        self.results_area.setStyleSheet("""
            background-color: transparent;
            color: #33FF33;
            font-size: 16px;
            border: none;
        """)

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
    
    def request_program_selection(self):
        """Pyydä ohjelman valintaa"""
        self.program_selection_requested.emit(self.test_number)
    
    def set_program(self, program_name):
        """Aseta valittu ohjelma"""
        self.selected_program = program_name
        # Poimi ohjelmanumero (esim. "Ohjelma 5" -> 5)
        try:
            self.program_number = int(program_name.split(" ")[1])
        except (IndexError, ValueError):
            self.program_number = 0
        self.program_label.setText(f" {program_name}")
    
    # Korjattu TestPanel.toggle_active (ui/components/test_panel.py)
    @pyqtSlot()
    def toggle_active(self):
        """Vaihda aktiivisuustila ja päivitä vain UI ja GPIO"""
        self.is_active = not self.is_active
        self.update_button_style()
        
        # Käytä vain GPIO-ohjausta, EI ForTest-kommunikointia
        if hasattr(self.parent().parent(), 'gpio_handler') and self.parent().parent().gpio_handler:
            self.parent().parent().gpio_handler.set_output(self.test_number, self.is_active)
        
        # Poistettu kaikki modbus- ja fortest-viittaukset

    @pyqtSlot(bool, str)
    def handle_toggle_result(self, success, error_msg):
        """Käsittele taustasäikeestä tullut tulos"""
        if not success:
            # Aktivointi epäonnistui, vaihda tila takaisin
            self.is_active = not self.is_active
            self.update_button_style()
            # Lähetä virheviesti
            self.status_message.emit(error_msg, 3)  # 3 = ERROR
        else:
            # Aktivointi onnistui
            if error_msg:
                self.status_message.emit(error_msg, 1)  # 1 = SUCCESS
    
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

    def update_test_status(self, status_data):
        """Update the test status display based on ForTest data"""
        if not status_data or not hasattr(status_data, 'registers'):
            return
        
        # Get status information from registers
        # Based on the ForTest protocol document:
        # Status register (0x0030)
        # ForTest Position 3-4: Last active status
        # Values: 0 = Waiting, 1 = Test in progress, etc.
        if len(status_data.registers) >= 3:
            last_active_status = status_data.registers[1]  # Position 3-4 maps to register index 1
            
            if last_active_status == 1:  # Test in progress
                self.pressure_result.setText("TESTI KÄYNNISSÄ")
            elif last_active_status == 0:  # Waiting
                self.pressure_result.setText("VALMIS")
            elif last_active_status == 2:  # Autozero
                self.pressure_result.setText("AUTOZERO")
            elif last_active_status == 3:  # Discharge
                self.pressure_result.setText("PURKU")
            else:
                self.pressure_result.setText(f"TILA: {last_active_status}")

        # Show pressure and decay when test is complete
        if last_active_status == 0 and len(status_data.registers) >= 36:
            # Check if pressure and decay values are available
            pressure_sign = status_data.registers[15]  # Position 31-32 maps to register index 15
            pressure_high = status_data.registers[16]  # Position 33-34 maps to register index 16
            pressure_low = status_data.registers[17]   # Position 35-36 maps to register index 17
            decay_sign = status_data.registers[20]     # Position 41-42 maps to register index 20
            decay_high = status_data.registers[21]     # Position 43-44 maps to register index 21
            decay_low = status_data.registers[22]      # Position 45-46 maps to register index 22
            
            # Combine high and low to get the full value
            pressure_value = (pressure_high << 16) | pressure_low
            decay_value = (decay_high << 16) | decay_low
            
            # Apply sign
            if pressure_sign == 1:
                pressure_value = -pressure_value
            if decay_sign == 1:
                decay_value = -decay_value
            
            # Display values
            self.pressure_result.setText(f"P: {pressure_value/1000:.3f} mbar\nV: {decay_value/1000:.3f} mbar/s")

    def update_test_results(self, result):
        if not result or not hasattr(result, 'registers'):
            return
        
        if len(result.registers) >= 10:
            test_result = result.registers[9]
            
            if test_result == 0:
                return
            
            # Hae aika testeriltä
            hours = result.registers[0]
            minutes = result.registers[1]
            seconds = result.registers[2]
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            result_text = ""
            if test_result == 1:  # Good
                self.pressure_result.setStyleSheet("""
                    background-color: black;
                    color: #00FF00;
                    font-size: 20px;
                    font-weight: bold;
                    text-align: left;
                """)
                # OK vasemmalla, aika oikealla
                result_text = f"OK{' '*40}{time_str}"
            elif test_result == 2:  # Bad
                self.pressure_result.setStyleSheet("""
                    background-color: black;
                    color: red;
                    font-size: 20px;
                    font-weight: bold;
                    text-align: left;
                """)
                # FAIL vasemmalla, aika oikealla
                result_text = f"FAIL{' '*38}{time_str}"
            else:
                self.pressure_result.setStyleSheet("""
                    background-color: black;
                    color: orange;
                    font-size: 12px;
                    font-weight: bold;
                    text-align: left;
                """)
                # Muu tulos vasemmalla, aika oikealla
                result_text = f"TULOS: {test_result}{' '*32}{time_str}"
            
            # Haetaan vuotoarvo
            decay_value = 0
            if len(result.registers) >= 24:
                decay_sign = result.registers[20]
                decay_value = result.registers[21]
                decay_decimals = result.registers[24]
                
                if decay_decimals > 0:
                    decay_value = decay_value / (10 ** decay_decimals)
                
                if decay_sign == 255:
                    decay_value = -decay_value
            
            # Lisää tulos historiaan
            result_status = "OK" if test_result == 1 else "FAIL" if test_result == 2 else f"TULOS: {test_result}"
            new_result = f"Vuoto: {decay_value:.3f} mbar/s ({time_str})"
            
            # Rajoita historia 3 tulokseen
            self.results_history.insert(0, f"{result_status} - {new_result}")
            if len(self.results_history) > 3:
                self.results_history.pop()
            
            # Näytä tulokset historiassa (uusin alimpana)
            results_text = ""
            for idx, res in enumerate(reversed(self.results_history)):
                results_text += f"{res}\n"
            
            self.results_area.setText(results_text)