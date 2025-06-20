# ui/components/control_panel.py
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

class ControlPanel(QWidget):
    """Ohjauskomponentti testaustoiminnoille"""
    start_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Käynnistä nappi - aseta suoraan koordinaateilla
        self.start_button = QPushButton("I", self)
        self.start_button.setGeometry(0, 0, 80, 80)  # x, y, leveys, korkeus
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #888888;
                color: white;
                border-radius: 5px;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        self.start_button.clicked.connect(self.start_clicked.emit)
        
        # Pysäytä nappi
        self.stop_button = QPushButton("O", self)
        self.stop_button.setGeometry(100, 0, 80, 80)  # x, y, leveys, korkeus
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #888888;
                color: white;
                border-radius: 5px;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        self.stop_button.clicked.connect(self.stop_clicked.emit)
    
    def update_button_states(self, running=False, ready_to_start=False):
        """Päivitä nappien tyylit tilan mukaan"""
        if running:
            # Testeri käynnissä - punainen O-nappi, harmaa I-nappi
            self.start_button.setStyleSheet("""
                QPushButton {
                    background-color: #888888;
                    color: white;
                    border-radius: 5px;
                    font-size: 24px;
                    font-weight: bold;
                }
            """)
            self.stop_button.setStyleSheet("""
                QPushButton {
                    background-color: #F44336;
                    color: white;
                    border-radius: 5px;
                    font-size: 24px;
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
                    font-size: 24px;
                    font-weight: bold;
                }
            """)
            self.stop_button.setStyleSheet("""
                QPushButton {
                    background-color: #888888;
                    color: white;
                    border-radius: 5px;
                    font-size: 24px;
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
                    font-size: 24px;
                    font-weight: bold;
                }
            """)
            self.stop_button.setStyleSheet("""
                QPushButton {
                    background-color: #888888;
                    color: white;
                    border-radius: 5px;
                    font-size: 24px;
                    font-weight: bold;
                }
            """)