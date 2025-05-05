from PyQt5.QtWidgets import QPushButton, QLabel, QFrame, QGridLayout
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from ui.screens.base_screen import BaseScreen

class ProgramSelectionScreen(BaseScreen):
    program_selected = pyqtSignal(str)  # Signaali valitulle ohjelmalle
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def init_ui(self):
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
        
        # Otsikko
        title = QLabel("VALITSE OHJELMA", self)
        title.setFont(QFont("Arial", 36, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setGeometry(0, 100, 1280, 60)
        
        # Grid-layout ohjelmapainikkeille
        self.grid_container = QFrame(self)
        self.grid_container.setGeometry(40, 200, 1200, 400)
        
        grid_layout = QGridLayout(self.grid_container)
        grid_layout.setSpacing(15)
        
        # Luo 30 ohjelmapainiketta
        self.program_buttons = []
        for i in range(1, 31):
            button = QPushButton(f"Ohjelma {i}", self.grid_container)
            button.setFixedSize(190, 80)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    color: #333333;
                    border-radius: 10px;
                    font-size: 20px;
                    font-weight: bold;
                    border: 1px solid #dddddd;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
                QPushButton:pressed {
                    background-color: #2196F3;
                    color: white;
                }
            """)
            
            # Paikkaindeksi: 5 riviä, 6 nappia per rivi
            row = (i - 1) // 6
            col = (i - 1) % 6
            
            # Yhdistä painallus signaaliin
            button.clicked.connect(lambda checked, prog_num=i: self.select_program(prog_num))
            
            grid_layout.addWidget(button, row, col)
            self.program_buttons.append(button)
    
    def select_program(self, program_number):
        """Valitse ohjelma ja lähetä signaali"""
        self.program_selected.emit(f"Ohjelma {program_number}")
        self.go_back()
    
    def go_back(self):
        """Palaa testaussivulle"""
        if hasattr(self.parent(), 'show_testing'):
            self.parent().show_testing()