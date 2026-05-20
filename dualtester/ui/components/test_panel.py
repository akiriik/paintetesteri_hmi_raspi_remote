# ui/components/test_panel.py
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QTextEdit, QFrame
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont 
import time

class TestPanel(QWidget):
    """Yksittäisen testin paneeli"""
    program_selection_requested = pyqtSignal(int)  # Signaali ohjelman valintapyynnölle
    status_message = pyqtSignal(str, int)  # Viesti, tyyppi
    def __init__(self, test_number, parent=None):
        super().__init__(parent)
        self.test_number = test_number
        self.selected_program = None
        self.is_active = True
        self.results_started = False
        self.modbus_register = 17000 + self.test_number

        self.setFixedSize(800, 610)
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                border-radius: 10px;
                border: 1px solid #dddddd;
            }
        """)

        # Tuloslista
        self.results_history = []

        # Tulosnäyttö
        self.pressure_result = QLabel("", self)
        self.pressure_result.setGeometry(0, 0, 800, 610)
        self.pressure_result.setAlignment(Qt.AlignCenter)
        self.pressure_result.setStyleSheet("""
            background-color: black;
            color: white;
            font-family: 'Digital-7', 'Consolas', monospace;
            font-size: 28px;
            text-align: left;
            border: 2px solid #444444;
            border-radius: 10px;
            padding: 18px;
        """)
        self.pressure_result.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        # Aktiivinen-nappi poistettu käytöstä, koska laitteella on jatkossa aina yksi aktiivinen testi
        self.active_btn = None

    
    def request_program_selection(self):
        """Pyydä ohjelman valintaa"""
        self.program_selection_requested.emit(self.test_number)
    
    def set_program(self, program_name):
        """Aseta valittu ohjelma"""
        self.selected_program = program_name
        # Poimi ohjelmanumero (esim. "7. Perustestaus" -> 7)
        import re
        match = re.match(r"(\d+)[\.\s]", program_name)
        if match:
            self.program_number = int(match.group(1))
        else:
            try:
                # Yritä vanhaa tapaa varmuuden vuoksi (esim. "Ohjelma 5" -> 5)
                self.program_number = int(program_name.split(" ")[1])
            except (IndexError, ValueError):
                self.program_number = 0
        # Ohjelman nimi näytetään jatkossa TestingScreenin infolaatikossa    
    @pyqtSlot()
    def toggle_active(self):
        """Vaihda aktiivisuustila ja päivitä vain UI ja GPIO"""
        self.is_active = not self.is_active
        self.update_button_style()
        
        # Aseta tulosten aloituslippu aktivoinnin yhteydessä
        if self.is_active:
            self.results_started = False  # Asetetaan True vasta testikäynnistyksessä
            # Älä tyhjennä tuloshistoriaa: self.results_history = []
            # Älä tyhjennä näyttöä: self.pressure_result.setText("")
        
        # Käytä GPIO-ohjausta
        if hasattr(self.parent(), 'gpio_handler') and self.parent().gpio_handler:
            self.parent().gpio_handler.set_output(self.test_number, self.is_active)

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
        """Aktiivisuusnappi on poistettu käytöstä yhden testin versiossa"""
        return

    def update_test_results(self, result):
        # Poistettu debug-tulostukset
        if not result or not hasattr(result, 'registers'):
            return
        
        if len(result.registers) >= 10:
            test_result = result.registers[9]
            
            if test_result == 0 or test_result == 99:  # 99 = "Test in progress"
                return
            
            if hasattr(self, 'program_number') and result.registers[6] != self.program_number:
                return
                    
            if not hasattr(self, 'results_started') or not self.results_started:
                return
                    
            hours = result.registers[0]
            minutes = result.registers[1]
            seconds = result.registers[2]
            day = result.registers[3]
            month = result.registers[4]
            year = result.registers[5]
            
            display_time = f"{hours:02d}:{minutes:02d}"
            
            timestamp = f"{day:02d}.{month:02d}.{year} {hours:02d}:{minutes:02d}:{seconds:02d}"
            current_result_id = f"{timestamp}-{test_result}-{result.registers[6]}-{result.registers[21]}"
            
            if hasattr(self, 'last_result_id') and self.last_result_id == current_result_id:
                return
                
            self.last_result_id = current_result_id
            
            # Määritä tulos, teksti ja väri
            result_texts = {
                0: "Ei tulosta",
                1: "OK", 
                2: "FAIL",
                3: "OK?",
                4: "NOK?",
                5: "Virheellinen referenssi",
                6: "Virheellinen täyttö",
                7: "Virtaus alle rajan",
                8: "Paine yli asteikon",
                9: "VOUT yli asteikon",
                10: "Paine alle toleranssin",
                11: "Paine yli toleranssin",
                12: "Painetasoa ei saavutettu",
                13: "Keskeytetty",
                14: "Virtaus yli rajan", 
                15: "Täyttöaika min",
                16: "Virhe tilavuusreferenssi"
            }
            
            result_status = result_texts.get(test_result, f"TULOS: {test_result}")
            
            # Väri ja näyttötapa
            if test_result == 1:
                result_color = "#00FF00"
            elif test_result == 2:
                result_color = "red"
            elif test_result in [3, 4]:
                result_color = "orange"
            else:
                result_color = "red"
                
            # Haetaan vuotoarvo
            decay_value = 0
            if len(result.registers) >= 25:
                decay_sign = result.registers[20]
                decay_value = result.registers[21]
                decay_unit_code = result.registers[23]
                decay_decimals = result.registers[24]
                
                if decay_decimals > 0:
                    decay_value = decay_value / (10 ** decay_decimals)
                
                if decay_sign == 255:
                    decay_value = -decay_value
                
                # Formatoi arvo käyttäen desimaalilukua
                formatted_decay = f"{decay_value:.{decay_decimals}f}"
                
                units = {
                    20: "mbar/s", 21: "bar/s", 22: "hPa/s", 23: "Pa/s", 24: "Psi/s",
                    40: "cc/h", 41: "cc/min", 42: "l/h", 43: "l/min",
                    0: "mbar", 1: "bar", 2: "hPa", 3: "Pa", 4: "Psi",
                    60: "s", 61: "min", 70: "cc", 71: "l"
                }
                
                decay_unit = units.get(decay_unit_code, "mbar/s")
            else:
                decay_unit = "mbar/s"
                formatted_decay = f"{decay_value:.3f}"
            
            # Luo tulos näytettävän tyypin mukaan
            if test_result in [1, 2, 3, 4]:
                # Näytetään normaali tulos kahdella rivillä:
                # 1. rivi: aika, vuoto, tulos
                # 2. rivi: ohjelma ja lämpötilat

                program_text = ""

                if hasattr(result, "program_name") and result.program_name:
                    program_text = result.program_name
                elif hasattr(self, "selected_program") and self.selected_program:
                    program_text = self.selected_program
                elif hasattr(self, "program_number"):
                    program_text = f"{self.program_number}. Ohjelma {self.program_number}"

                room_temp_text = ""
                part_temp_text = ""

                if hasattr(result, "room_temp"):
                    room_temp_text = f"HUONE {result.room_temp:.1f}°C"

                if hasattr(result, "part_temp"):
                    part_temp_text = f"KAPPALE {result.part_temp:.1f}°C"

                temp_text = ""

                if room_temp_text and part_temp_text:
                    temp_text = f"{room_temp_text}   {part_temp_text}"
                elif room_temp_text:
                    temp_text = room_temp_text
                elif part_temp_text:
                    temp_text = part_temp_text

                if temp_text:
                    second_line = f"{program_text}   {temp_text}"
                else:
                    second_line = program_text

                program_text = ""

                if hasattr(result, "program_name") and result.program_name:
                    program_text = result.program_name
                elif hasattr(self, "selected_program") and self.selected_program:
                    program_text = self.selected_program
                elif hasattr(self, "program_number"):
                    program_text = f"{self.program_number}. Ohjelma {self.program_number}"

                room_temp_text = ""
                part_temp_text = ""

                if hasattr(result, "room_temp"):
                    room_temp_text = f"{result.room_temp:.1f}°C"

                if hasattr(result, "part_temp"):
                    part_temp_text = f"{result.part_temp:.1f}°C"

                new_result = f"""
                <tr>
                    <td>{display_time}</td>
                    <td>{program_text}</td>
                    <td><span style="color:{result_color};">{formatted_decay}</span> {decay_unit}</td>
                    <td><span style="color:{result_color};">{result_status}</span></td>
                    <td>{room_temp_text}</td>
                    <td>{part_temp_text}</td>
                </tr>
                """
            else:
                # Näytetään vain virheilmoitus
                new_result = f"<span style='color:{result_color};'>{result_status}</span>"
            
            # Lisää uusi tulos historiaan
            if not hasattr(self, 'results_history'):
                self.results_history = []
                
            self.results_history.insert(0, new_result)

            if len(self.results_history) > 12:
                self.results_history.pop()

            # Rakenna näyttöteksti (uusin alimmaisena)
            display_html = f"""
            <table width="100%" cellspacing="0" cellpadding="6">
                <tr style="color:#888888; font-size:18px;">
                    <td>AIKA</td>
                    <td>OHJELMA</td>
                    <td>VUOTO</td>
                    <td>TULOS</td>
                    <td>HUONE</td>
                    <td>KAPPALE</td>
                </tr>
                {''.join(self.results_history)}
            </table>
            """
            # Päivitä tulosteksti
            self.pressure_result.setTextFormat(Qt.RichText)
            self.pressure_result.setAlignment(Qt.AlignTop | Qt.AlignLeft)
            self.pressure_result.setStyleSheet("""
                background-color: black;
                color: white;
                font-family: 'Consolas', monospace;
                font-size: 22px;
                border: 2px solid #444444;
                border-radius: 10px;
                padding: 12px;
            """)
            self.pressure_result.setText(display_html)