from PyQt5.QtWidgets import QLabel, QPushButton, QFrame, QWidget, QMenu, QMessageBox, QScrollArea, QVBoxLayout, QHBoxLayout, QStyle, QDialog
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QFont, QIcon

from ui.screens.base_screen import BaseScreen
from ui.components.test_panel import TestPanel
from ui.components.control_panel import ControlPanel

class ShutdownDialog(QDialog):
    """Sammutusvalikko"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sammutusvalikko")
        self.setModal(True)
        self.setFixedSize(800, 400)
        self.result_value = None
        
        # Dialogin tyyli
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                color: black;
                background-color: white;
            }
        """)

        # Keskitä dialogi
        if parent:
            self.move(
                parent.width() // 2 - self.width() // 2,
                parent.height() // 2 - self.height() // 2
            )
        
        layout = QVBoxLayout(self)
        layout.setSpacing(30)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Otsikko
        title = QLabel("Valitse toiminto:", self)
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 20))
        layout.addWidget(title)
        
        # Nappuloiden layout
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(15)
        
        # Luo napit
        self.raspberry_btn = QPushButton("Sammuta Raspberry Pi")
        self.restart_btn = QPushButton("Käynnistä ohjelma uudelleen")
        self.close_btn = QPushButton("Sammuta ohjelma")
        self.cancel_btn = QPushButton("Peruuta")
        
        buttons = [self.raspberry_btn, self.restart_btn, self.close_btn, self.cancel_btn]
        
        for btn in buttons:
            btn.setFixedHeight(60)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    color: black;
                    border-radius: 5px;
                    padding: 10px;
                    font-size: 18px;
                    border: 1px solid #ccc;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """)
            buttons_layout.addWidget(btn)
        
        layout.addLayout(buttons_layout)
        
        # Yhdistä signaalit
        self.raspberry_btn.clicked.connect(lambda: self.set_result("raspberry"))
        self.restart_btn.clicked.connect(lambda: self.set_result("restart"))
        self.close_btn.clicked.connect(lambda: self.set_result("close"))
        self.cancel_btn.clicked.connect(lambda: self.set_result("cancel"))
        
        # Dialogin tyyli
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                color: black;
            }
        """)
    
    def set_result(self, value):
        self.result_value = value
        self.accept()
    
    def get_result(self):
        return self.result_value

class IconButton(QPushButton):
    """Kuvakepainike järjestelmäikoneilla"""
    def __init__(self, icon_style, tooltip, parent=None):
        super().__init__(parent)
        
        
        # Aseta järjestelmäikoni
        self.setIcon(self.style().standardIcon(icon_style))
        self.setIconSize(QSize(32, 32))
        
        if icon_style == QStyle.SP_DirIcon:  # Käsikäyttö
            self.setFixedSize(60, 60)
            self.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border-radius: 10px;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
        elif icon_style == QStyle.SP_DialogCancelButton:  # Sammuta
            self.setFixedSize(80, 80)
            self.setStyleSheet("""
                QPushButton {
                    background-color: #F44336;
                    color: white;
                    border-radius: 10px;
                }
                QPushButton:hover {
                    background-color: #D32F2F;
                }
            """)
        
        self.setToolTip(tooltip)

class TestingScreen(BaseScreen):
    program_selection_requested = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_test_panel = None
        self.is_running = False
        self.init_ui()

    def init_ui(self):
        # Aseta musta tausta testaussivulle
        self.setStyleSheet("background-color: black;")

        # Ikonipainikkeet
        # Käsikäyttö-painike
        self.manual_button = IconButton(QStyle.SP_DialogResetButton, "Käsikäyttö", self)
        self.manual_button.move(205, 5)
        self.manual_button.clicked.connect(self.show_manual)

        # New confirmation shutdown button
        self.system_status_button = IconButton(QStyle.SP_DialogCancelButton, "Järjestelmän tila", self)
        self.system_status_button.move(5, 5)
        self.system_status_button.clicked.connect(self.show_system_status)    
        
        # Testipaneelit
        self.test_panels = []
        for i in range(1, 4):

            # Testipaneeli
            panel = TestPanel(i, self)
            panel.move(5 + (i-1)*445, 130)
            panel.program_selection_requested.connect(self.start_program_selection)
            panel.status_message.connect(self.handle_status_message)
            self.test_panels.append(panel)
        
        # Ohjauskomponentti
        self.control_panel = ControlPanel(self)
        self.control_panel.move(1095, 5)
        self.control_panel.start_clicked.connect(self.start_test)
        self.control_panel.stop_clicked.connect(self.stop_test)
        
        # Tilaviestikenttä
        self.status_label = QLabel("", self)
        self.status_label.setGeometry(265, 5, 750, 40)  # Laajennettu korkeus, koska ei ole ulkoista kehystä
        self.status_label.setFont(QFont("Consolas", 14))
        self.status_label.setIndent(10)
        self.status_label.setStyleSheet("""
            color: #33FF33;
            background-color: black;
            border-radius: 5px;
            border: 1px solid #333333;
        """)
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
    
        # Ajastin statuksen päivitykseen
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_test_statuses)
        self.status_timer.start(1000)  # Päivitys sekunnin välein

        # Ajastin ForTest-datan päivitykseen
        self.fortest_timer = QTimer(self)
        self.fortest_timer.timeout.connect(self.update_fortest_data)
        self.fortest_timer.start(1000)  # Päivitys sekunnin välein

    def show_system_status(self):
        """Näytä system status -dialogi"""
        from ui.components.system_status_dialog import SystemStatusDialog
        dialog = SystemStatusDialog(self, self.parent().modbus_manager)
        dialog.exec_()

    def show_confirm_shutdown_dialog(self):
        """Show system shutdown confirmation dialog with custom layout"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QWidget
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Sammutuksen vahvistus")
        dialog.setModal(True)
        dialog.setFixedSize(600, 400)
        
        # Center the dialog
        dialog.move(
            self.width() // 2 - dialog.width() // 2,
            self.height() // 2 - dialog.height() // 2
        )
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                background-color: white;
                color: black;
            }
        """)

        # Question text
        question_label = QLabel("Haluatko sammuttaa järjestelmän?")
        question_label.setAlignment(Qt.AlignCenter)
        question_label.setFont(QFont("Arial", 24))
        layout.addWidget(question_label)
        
        layout.addStretch()
        
        # Main buttons (side by side)
        main_buttons_layout = QHBoxLayout()
        main_buttons_layout.setSpacing(20)
        
        peruuta_btn = QPushButton("PERUUTA")
        peruuta_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #333333;
                border-radius: 10px;
                padding: 15px;
                min-width: 200px;
                min-height: 80px;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        
        sammuta_btn = QPushButton("SAMMUTA")
        sammuta_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border-radius: 10px;
                padding: 15px;
                min-width: 200px;
                min-height: 80px;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)
        
        main_buttons_layout.addWidget(peruuta_btn)
        main_buttons_layout.addWidget(sammuta_btn)
        layout.addLayout(main_buttons_layout)
        
        layout.addSpacing(30)  # Väli
        
        # VAIHTOEHDOT button (centered, smaller height)
        vaihtoehdot_layout = QHBoxLayout()
        vaihtoehdot_layout.addStretch()
        
        vaihtoehdot_btn = QPushButton("VAIHTOEHDOT")
        vaihtoehdot_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 10px;
                padding: 10px;
                min-width: 200px;
                min-height: 40px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        
        vaihtoehdot_layout.addWidget(vaihtoehdot_btn)
        vaihtoehdot_layout.addStretch()
        layout.addLayout(vaihtoehdot_layout)
        
        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
            }
        """)
        
        # Connect buttons
        result_value = None
        
        def on_peruuta():
            nonlocal result_value
            result_value = "peruuta"
            dialog.accept()
        
        def on_sammuta():
            nonlocal result_value
            result_value = "sammuta"
            dialog.accept()
        
        def on_vaihtoehdot():
            nonlocal result_value
            result_value = "vaihtoehdot"
            dialog.accept()
        
        peruuta_btn.clicked.connect(on_peruuta)
        sammuta_btn.clicked.connect(on_sammuta)
        vaihtoehdot_btn.clicked.connect(on_vaihtoehdot)
        
        # Execute dialog and handle result
        dialog.exec_()
        
        # Handle different button clicks
        if result_value == "sammuta":
            # Set register 17999 high using modbus (USB0)
            if hasattr(self.parent(), 'modbus_manager'):
                self.parent().modbus_manager.write_register(17999, 1)
                self.update_status("Sammutetaan järjestelmä...", "INFO")
                
                # Add delay to allow register change to take effect
                QTimer.singleShot(2000, self.shutdown_system)
        elif result_value == "vaihtoehdot":
            # Avaa alkuperäinen sammutusvalikko
            self.show_shutdown_dialog()
        
    def shutdown_system(self):
        """Shutdown Raspberry Pi system"""
        import os
        os.system("sudo shutdown -h now")
    
    def show_shutdown_dialog(self):
        """Näytä sammutusvalikko"""
        dialog = ShutdownDialog(self)
        dialog.exec_()
        
        result = dialog.get_result()
        
        if result == "raspberry":
            self.update_status("Sammutetaan Raspberry Pi...", "INFO")
            import os
            os.system("sudo shutdown -h now")
        elif result == "restart":
            self.update_status("Käynnistetään ohjelma uudelleen...", "INFO")
            self.window().close()
            import os
            import sys
            os.execv(sys.executable, ['python'] + sys.argv)
        elif result == "close":
            self.update_status("Sammutetaan ohjelma...", "INFO")
            self.window().close()


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
        
        # Jos yhtään paneelia ei ole aktiivisena, testiä ei voi käynnistää
        if not active_panels:
            self.update_status("Valitse vähintään yksi testi aktiiviseksi ennen käynnistystä", "WARNING")
            return
        
        # Tarkista että modbus-yhteys on kunnossa
        if not hasattr(self.parent(), 'fortest_manager') or \
        not hasattr(self.parent().fortest_manager.worker, 'fortest') or \
        not hasattr(self.parent().fortest_manager.worker.fortest, 'modbus') or \
        not self.parent().fortest_manager.worker.fortest.modbus.connected:
            self.update_status("ForTest-yhteyttä ei saatavilla, testiä ei voi käynnistää", "ERROR")
            return

        if active_panels:
            # Tarkista että aktiivisissa paneeleissa on ohjelma valittuna
            for panel in active_panels:
                if not hasattr(panel, 'program_number') or panel.program_number <= 0:
                    self.update_status("Valitse ohjelma kaikille aktiivisille testeille", "WARNING")
                    return
            
            # Vaihda ohjelma ensimmäisen aktiivisen testin mukaan
            first_panel = active_panels[0]
            print(f"Vaihdetaan ohjelma: {first_panel.program_number}")
            
            # Ohjelman vaihto ForTestHandler-luokan kautta
            try:
                modbus = self.parent().fortest_manager.worker.fortest.modbus
                result = modbus.write_register(0x0060, first_panel.program_number)
                self.update_status(f"Vaihdetaan ohjelmaan {first_panel.program_number}...", "INFO")
                
                # Jos vaihto onnistui, jatka testiä viiveellä
                if result:
                    QTimer.singleShot(1000, self._continue_start_test)
                    return
                else:
                    self.update_status("Ohjelman vaihto epäonnistui", "ERROR")
            except Exception as e:
                self.update_status(f"Virhe ohjelman vaihdossa: {str(e)}", "ERROR")
                return

        # Merkitse aktiiviset paneelit keräämään tuloksia
        for panel in self.test_panels:
            if panel.is_active:
                panel.results_started = True

        # Jos ei onnistunut tai ei ole aktiivisia testejä, käynnistetään ilman ohjelman vaihtoa
        self._continue_start_test()

    def _continue_start_test(self):
        """Jatka testin käynnistystä ohjelmavaihdon jälkeen"""
        # Merkitse aktiiviset paneelit keräämään tuloksia
        for panel in self.test_panels:
            if panel.is_active:
                panel.results_started = True
                
        self.is_running = True
        self.control_panel.update_button_states(True, False)  # running=True, ready=False
        
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
        
        # Tarkista, onko laite valmis käynnistettäväksi ohjauksen päivitystä varten
        ready_to_start = self.check_ready_to_start()
        self.control_panel.update_button_states(False, ready_to_start)
        
        # Pysäytä testi ForTestManager-luokan avulla
        if hasattr(self.parent(), 'fortest_manager'):
            self.parent().fortest_manager.abort_test()
            
        # Aseta GPIO-pinnit testerin todellisen tilan mukaan
        if hasattr(self.parent(), 'gpio_handler') and self.parent().gpio_handler:
            if ready_to_start:
                self.parent().gpio_handler.set_output(4, True)   # GPIO 23 (vihreä) päälle
                self.parent().gpio_handler.set_output(5, False)  # GPIO 24 (punainen) pois
            else:
                self.parent().gpio_handler.set_output(4, False)  # GPIO 23 (vihreä) pois
                self.parent().gpio_handler.set_output(5, False)  # GPIO 24 (punainen) pois

    # Lisää uusi metodi tarkistamaan onko testeri valmis käynnistykseen
    def check_ready_to_start(self):
        """Tarkista onko testeri valmis käynnistykseen"""
        # Tarkista onko aktiivisia paneeleja
        active_panels = [panel for panel in self.test_panels if panel.is_active]
        if not active_panels:
            return False
        
        # Tarkista että aktiivisissa paneeleissa on ohjelma valittuna
        for panel in active_panels:
            if not hasattr(panel, 'program_number') or panel.program_number <= 0:
                return False
        
        # Tarkista modbus-yhteys
        if not hasattr(self.parent(), 'fortest_manager') or \
        not hasattr(self.parent().fortest_manager.worker, 'fortest') or \
        not hasattr(self.parent().fortest_manager.worker.fortest, 'modbus') or \
        not self.parent().fortest_manager.worker.fortest.modbus.connected:
            return False
        
        # Kaikki ok, testeri on valmis käynnistykseen
        return True


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
            style = "color: red; font-weight: normal;"
        elif message_type == "WARNING":
            style = "color: orange; font-weight: normal;"
        elif message_type == "SUCCESS":
            style = "color: #00FF00; font-weight: normal;"
                
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

    def handle_fortest_status(self, result):
        """Käsittele ForTest-laitteen tilatiedot"""
        if not result or not hasattr(result, 'registers'):
            return
        
        # Hae nykyinen tila (register 51)
        if len(result.registers) >= 2:
            status = result.registers[1]
            
            # Jos tila on "WAITING" (0) ja edellinen tila oli jokin muu, testi on päättynyt
            if status == 0 and hasattr(self, 'last_status') and self.last_status != 0:
                # Lue tulokset
                if hasattr(self.parent(), 'fortest_manager'):
                    self.parent().fortest_manager.read_results()
            
            # Tallenna nykyinen tila
            self.last_status = status

    def update_status_from_fortest(self, result):
        if not result or not hasattr(result, 'registers'):
            return
        
        if len(result.registers) >= 2:
            status_value = result.registers[1]
            
            # Tarkista tilamuutos testin päättymiselle
            if status_value == 0 and hasattr(self, 'last_status') and self.last_status in [1, 2, 3]:
                # Testin tila muuttui "WAITING" tilaan - testi on päättynyt
                self.is_running = False
                
                # Lue tulokset
                if hasattr(self.parent(), 'fortest_manager'):
                    self.parent().fortest_manager.read_results()
                
                # Päivitä GPIO-valot (vihreä päälle, punainen pois)
                if hasattr(self.parent(), 'gpio_handler') and self.parent().gpio_handler:
                    self.parent().gpio_handler.set_output(4, True)   # GPIO 23 (vihreä) päälle
                    self.parent().gpio_handler.set_output(5, False)  # GPIO 24 (punainen) pois
                
                # Päivitä nappien tila
                ready_to_start = self.check_ready_to_start()
                self.control_panel.update_button_states(False, ready_to_start)
            
            self.last_status = status_value
            
            # Näytä vain merkittävät tilamuutokset
            if status_value == 1 and (not hasattr(self, 'last_shown_status') or self.last_shown_status != 1):
                self.update_status("TESTI KÄYNNISSÄ", "INFO")
                self.last_shown_status = 1
            elif status_value == 2 and (not hasattr(self, 'last_shown_status') or self.last_shown_status != 2):
                self.update_status("AUTOZERO", "INFO")
                self.last_shown_status = 2
            elif status_value == 3 and (not hasattr(self, 'last_shown_status') or self.last_shown_status != 3):
                self.update_status("PURKU", "INFO")
                self.last_shown_status = 3
            elif status_value == 0 and (not hasattr(self, 'last_shown_status') or self.last_shown_status != 0):
                self.update_status("VALMIS", "SUCCESS")
                self.last_shown_status = 0

    def update_fortest_data(self):
        """Lue ForTest statustiedot ja tulokset"""
        if hasattr(self.parent(), 'fortest_manager'):
            # Lue ForTest tila
            self.parent().fortest_manager.read_status()
            
            # Lue myös tulokset säännöllisesti
            if hasattr(self, 'results_read_counter'):
                self.results_read_counter += 1
                # Lue tulokset harvemmin (esim. joka 5. kerta)
                if self.results_read_counter >= 5:
                    self.parent().fortest_manager.read_results()
                    self.results_read_counter = 0
            else:
                self.results_read_counter = 0
            
            # Päivitä nappien tila todellisen tilanteen mukaan
            ready_to_start = False
            if not self.is_running:
                ready_to_start = self.check_ready_to_start()
            
            # Päivitä nappien ja GPIO-pinnien tila
            self.control_panel.update_button_states(self.is_running, ready_to_start)
            
            # Päivitä GPIO-pinnit testerin todellisen tilan mukaan
            if hasattr(self.parent(), 'gpio_handler') and self.parent().gpio_handler:
                if self.is_running:
                    self.parent().gpio_handler.set_output(4, False)  # GPIO 23 (vihreä) pois
                    self.parent().gpio_handler.set_output(5, True)   # GPIO 24 (punainen) päälle
                elif ready_to_start:
                    self.parent().gpio_handler.set_output(4, True)   # GPIO 23 (vihreä) päälle
                    self.parent().gpio_handler.set_output(5, False)  # GPIO 24 (punainen) pois
                else:
                    self.parent().gpio_handler.set_output(4, False)  # GPIO 23 (vihreä) pois
                    self.parent().gpio_handler.set_output(5, False)  # GPIO 24 (punainen) pois

    def cleanup(self):
        """Siivoa resurssit"""
        pass