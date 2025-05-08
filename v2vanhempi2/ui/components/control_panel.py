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
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)
        
        # Painenäyttö
        self.pressure_display = QLabel("0.00", self)
        self.pressure_display.setFixedSize(250, 150)
        self.pressure_display.setStyleSheet("""
            background-color: black;
            color: #33FF33;
            font-family: Consolas, Courier, monospace;
            font-size: 56px;
            font-weight: bold;
            border: 2px solid #444444;
            border-radius: 10px;
        """)
        self.pressure_display.setAlignment(Qt.AlignCenter)

        # Käynnistä nappi
        self.start_button = QPushButton("KÄYNNISTÄ", self)
        self.start_button.setFixedSize(250, 120)
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        self.start_button.clicked.connect(self.start_clicked.emit)
        
        # Pysäytä nappi
        self.stop_button = QPushButton("PYSÄYTÄ", self)
        self.stop_button.setFixedSize(250, 120)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border-radius: 5px;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        self.stop_button.clicked.connect(self.stop_clicked.emit)
        
        layout.addWidget(self.pressure_display)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)
    
    def set_pressure(self, value):
        """Päivitä painenäyttö"""
        try:
            self.pressure_display.setText(f"{float(value):.2f}")
        except (ValueError, TypeError):
            self.pressure_display.setText("0.00")
    
    def update_button_states(self, running=False):
        """Päivitä nappien tyylit tilan mukaan"""
        if running:
            self.start_button.setStyleSheet("""
                QPushButton {
                    background-color: #388E3C;
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
        else:
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
                    background-color: #D32F2F;
                    color: white;
                    border-radius: 5px;
                    font-size: 24px;
                    font-weight: bold;
                }
            """)