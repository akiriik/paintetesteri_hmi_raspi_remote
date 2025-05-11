# Muutokset tiedostoon ui/screens/testing_screen.py
from PyQt5.QtWidgets import QLabel, QPushButton, QFrame, QWidget, QMenu, QScrollArea
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from ui.screens.base_screen import BaseScreen
from ui.components.test_panel import TestPanel
from ui.components.control_panel import ControlPanel
# Poistettu tuonti: from ui.components.log_panel import LogPanel

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
    program_selection_requested = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_test_panel = None
        self.is_running = False
        self.init_ui()

    def init_ui(self):
        # Valikko-nappi
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
            # Testin otsikko
            title = QLabel(f"TESTI {i}", self)
            title.setFont(QFont("Arial", 24, QFont.Bold))
            title.setAlignment(Qt.AlignCenter)
            title.setGeometry(50 + (i-1)*380, 50, 300, 100)
            
            # Testipaneeli
            panel = TestPanel(i, self)
            panel.move(40 + (i-1)*380, 130)
            panel.program_selection_requested.connect(self.start_program_selection)
            panel.status_message.connect(self.handle_status_message)
            self.test_panels.append(panel)
        
        # Ohjauskomponentti
        self.control_panel = ControlPanel(self)
        self.control_panel.move(1100, 450)
        self.control_panel.start_clicked.connect(self.start_test)
        self.control_panel.stop_clicked.connect(self.stop_test)
        
        # Uusi tilaviestialue (korvaa LOG-paneelin)
        self.status_area = QFrame(self)
        self.status_area.setGeometry(50, 10, 920, 50)
        self.status_area.setStyleSheet("""
            QFrame {
                background-color: black;
                color: #33FF33;
                border-radius: 5px;
                border: 1px solid #333333;
            }
        """)
        
        # Tilaviestikenttä
        self.status_label = QLabel("", self.status_area)
        self.status_label.setGeometry(10, 8, 920, 30)
        self.status_label.setFont(QFont("Consolas", 16))
        self.status_label.setStyleSheet("color: #33FF33; background-color: transparent;")
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    
        # Add status update timer
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_test_statuses)
        self.status_timer.start(1000)  # Update every second

        # Ajastin statuksen päivitykseen
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_fortest_data)
        self.status_timer.start(1000)  # Päivitys sekunnin välein


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
        self.program_selection_requested.emit(test_number)
    
    def set_program_for_test(self, program_name):
        """Aseta ohjelma valitulle testille"""
        if self.current_test_panel:
            # Hae oikea paneeli ja aseta ohjelma
            panel = self.test_panels[self.current_test_panel - 1]
            panel.set_program(program_name)
            self.current_test_panel = None
            # Poistettu tarpeeton lokitus
    
    def start_test(self):
        """Käynnistä testi ForTestManager-luokan avulla, vaihda ensin ohjelmat"""
        # Tarkista, mitkä testipaneelit ovat aktiivisia
        active_panels = [panel for panel in self.test_panels if panel.is_active]

        if active_panels:
            # Vaihda ohjelma ensimmäisen aktiivisen testin mukaan
            first_panel = active_panels[0]
            if hasattr(first_panel, 'program_number') and first_panel.program_number > 0:
                print(f"Vaihdetaan ohjelma: {first_panel.program_number}")
                
                # Ohjelman vaihto ForTestHandler-luokan kautta
                # ForTest käyttää ttyUSB1 porttia
                if hasattr(self.parent(), 'fortest_manager'):
                    try:
                        # Käytä suoraan modbus_handler-objektia fortest_managerista
                        if hasattr(self.parent().fortest_manager.worker, 'fortest') and \
                        hasattr(self.parent().fortest_manager.worker.fortest, 'modbus'):
                            modbus = self.parent().fortest_manager.worker.fortest.modbus
                            result = modbus.write_register(0x0060, first_panel.program_number)
                            self.update_status(f"Vaihdetaan ohjelmaan {first_panel.program_number}...", "INFO")
                            
                            # Jos vaihto onnistui, jatka testiä viiveellä
                            if result:
                                QTimer.singleShot(1000, self._continue_start_test)
                                return
                            else:
                                self.update_status("Ohjelman vaihto epäonnistui", "ERROR")
                        else:
                            self.update_status("ForTest-yhteyttä ei saatavilla", "ERROR")
                    except Exception as e:
                        self.update_status(f"Virhe ohjelman vaihdossa: {str(e)}", "ERROR")
                else:
                    self.update_status("ForTest-manageria ei saatavilla", "ERROR")

        # Merkitse aktiiviset paneelit keräämään tuloksia
        for panel in self.test_panels:
            if panel.is_active:
                panel.results_started = True

        # Jos ei onnistunut tai ei ole aktiivisia testejä, käynnistetään ilman ohjelman vaihtoa
        self._continue_start_test()
        
    def _continue_start_test(self):
        """Jatka testin käynnistystä ohjelmavaihdon jälkeen"""
        self.is_running = True
        self.control_panel.update_button_states(True)
        
        # Käynnistä testi ForTestManager-luokan avulla
        if hasattr(self.parent(), 'fortest_manager'):
            self.parent().fortest_manager.start_test()
            
        # Aseta GPIO-pinnit
        if hasattr(self.parent(), 'gpio_handler') and self.parent().gpio_handler:
            self.parent().gpio_handler.set_output(4, False)  # GPIO 23 (vihreä) pois
            self.parent().gpio_handler.set_output(5, True)   # GPIO 24 (punainen) päälle

    def stop_test(self):
        """Pysäytä testi ForTestManager-luokan avulla"""
        self.is_running = False
        self.control_panel.update_button_states(False)
        
        # Pysäytä testi ForTestManager-luokan avulla
        if hasattr(self.parent(), 'fortest_manager'):
            self.parent().fortest_manager.abort_test()
            
        # Aseta GPIO-pinnit
        if hasattr(self.parent(), 'gpio_handler') and self.parent().gpio_handler:
            self.parent().gpio_handler.set_output(4, True)   # GPIO 23 (vihreä) päälle
            self.parent().gpio_handler.set_output(5, False)  # GPIO 24 (punainen) pois

    def toggle_active(self):
        """Vaihda aktiivisuustila ja lähetä signaali"""
        self.is_active = not self.is_active
        self.update_button_style()
        
        # Lähetä signaali pääikkunalle Modbus-käsittelyä varten
        if hasattr(self.parent(), 'toggle_test_active'):
            self.parent().toggle_test_active(self.test_number, self.is_active)
            
            # Aktivoi myös GPIO-lähtö
            if hasattr(self.parent().parent(), 'gpio_handler') and self.parent().parent().gpio_handler:
                self.parent().parent().gpio_handler.set_output(self.test_number, self.is_active)          
    
    def toggle_test_active(self, test_number, active):
        """Vaihda testin aktiivisuustila vain UI:n ja GPIO:n osalta"""
        # Varmista että test_number on sallituissa rajoissa
        if 1 <= test_number <= len(self.test_panels):
            panel = self.test_panels[test_number - 1]
            panel.is_active = active
            panel.update_button_style()

            # Ohjaa vain GPIO-lähtö
            if hasattr(self.parent(), 'gpio_handler') and self.parent().gpio_handler:
                self.parent().gpio_handler.set_output(test_number, active)
    
    def update_status(self, message, message_type="INFO"):
        """Päivitä tilaviesti suoraan näkymään"""
        print(f"update_status kutsuttu: {message}, {message_type}")
        style = "color: #33FF33;"  # Normaali viesti (vihreä)
        
        if message_type == "ERROR":
            style = "color: red; font-weight: bold;"
        elif message_type == "WARNING":
            style = "color: orange; font-weight: bold;"
        elif message_type == "SUCCESS":
            style = "color: #00FF00; font-weight: bold;"
                
        self.status_label.setStyleSheet(style + " background-color: transparent;")
        self.status_label.setText(message)
    
    def handle_status_message(self, message, message_type):        
        # Päivitä tilaviesti myös näkymään
        level = "INFO"
        if message_type == 1:
            level = "SUCCESS"
        elif message_type == 2:
            level = "WARNING"
        elif message_type == 3:
            level = "ERROR"
        
        self.update_status(message, level)

    def update_test_statuses(self):
        """Read and update test statuses from ForTest"""
        if hasattr(self.parent(), 'fortest_manager'):
            self.parent().fortest_manager.read_status()

    def handle_fortest_status(self, result, op_code):
        """Process ForTest status results"""
        if op_code == 3 and result:  # Status read operation
            # Update active test panels with status information
            for panel in self.test_panels:
                if panel.is_active:
                    panel.update_test_status(result)

    def update_status_from_fortest(self, result):
        """Päivitä tilatieto ForTest-datan perusteella"""
        if not result or not hasattr(result, 'registers'):
            return
        
        # Tarkista rekisterin 50-51 arvo (ForTest Position 3-4)
        if len(result.registers) >= 2:
            status_value = result.registers[1]  # Last active status
            
            if status_value == 0:
                self.update_status("VALMIS", "INFO")
            elif status_value == 1:
                self.update_status("TESTI KÄYNNISSÄ", "INFO") 
            elif status_value == 2:
                self.update_status("AUTOZERO", "INFO")
            elif status_value == 3:
                self.update_status("PURKU", "INFO")
            else:
                self.update_status(f"TILA: {status_value}", "INFO")

    def update_fortest_data(self):
        """Lue ForTest statustiedot ja tulokset"""
        if hasattr(self.parent(), 'fortest_manager'):
            # Lue ForTest tila
            self.parent().fortest_manager.read_status()
            # Lue ForTest tulokset
            self.parent().fortest_manager.read_results()

    def cleanup(self):
        """Siivoa resurssit"""
        pass