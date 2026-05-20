# ui/components/control_panel.py
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

class ControlPanel(QWidget):
    """Ohjauskomponentti testaustoiminnoille"""
    start_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    dev_result_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Käynnistä nappi - aseta suoraan koordinaateilla
        self.start_button = QPushButton("START", self)
        self.start_button.setGeometry(20, 0, 160, 100)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #888888;
                color: white;
                border-radius: 10px;
                font-size: 30px;
                font-weight: bold;
            }
        """)
        self.start_button.clicked.connect(self.start_clicked.emit)
        
        # Pysäytä nappi
        self.stop_button = QPushButton("STOP", self)
        self.stop_button.setGeometry(265, 0, 160, 100)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #888888;
                color: white;
                border-radius: 10px;
                font-size: 30px;
                font-weight: bold;
            }
        """)
        self.stop_button.clicked.connect(self.stop_clicked.emit)

        # DEV tulosnappi - näkyy vain ForTest devmodessa
        self.dev_result_button = QPushButton("TULOS", self)
        self.dev_result_button.setGeometry(190, 15, 65, 70)
        self.dev_result_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: black;
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FBC02D;
            }
        """)
        self.dev_result_button.clicked.connect(self.dev_result_clicked.emit)
        self.dev_result_button.hide()
    
    def update_button_states(self, running=False, ready_to_start=False):
        """Päivitä nappien tyylit tilan mukaan"""
        if running:
            # Testeri käynnissä - punainen O-nappi, harmaa I-nappi
            self.start_button.setStyleSheet("""
                QPushButton {
                    background-color: #888888;
                    color: white;
                    border-radius: 5px;
                    font-size: 30px;
                    font-weight: bold;
                }
            """)
            self.stop_button.setStyleSheet("""
                QPushButton {
                    background-color: #F44336;
                    color: white;
                    border-radius: 5px;
                    font-size: 30px;
                    font-weight: bold;
                }
            """)
        elif ready_to_start:
            # Valmis käynnistykseen - vihreä I-nappi, harmaa O-nappi
            self.start_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 5px;
                    font-size: 30px;
                    font-weight: bold;
                }
            """)
            self.stop_button.setStyleSheet("""
                QPushButton {
                    background-color: #888888;
                    color: white;
                    border-radius: 5px;
                    font-size: 30px;
                    font-weight: bold;
                }
            """)
        else:
            # Ei valmis käynnistykseen, molemmat napit harmaita
            self.start_button.setStyleSheet("""
                QPushButton {
                    background-color: #888888;
                    color: white;
                    border-radius: 5px;
                    font-size: 30px;
                    font-weight: bold;
                }
            """)
            self.stop_button.setStyleSheet("""
                QPushButton {
                    background-color: #888888;
                    color: white;
                    border-radius: 5px;
                    font-size: 30px;
                    font-weight: bold;
                }
            """)

    def set_dev_mode(self, enabled):
        """Näytä/piilota DEV-tulosnappi"""
        self.dev_result_button.setVisible(enabled)