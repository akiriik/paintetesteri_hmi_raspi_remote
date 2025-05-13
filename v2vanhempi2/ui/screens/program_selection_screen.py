from PyQt5.QtWidgets import QPushButton, QLabel, QFrame, QGridLayout, QVBoxLayout, QHBoxLayout, QScrollArea, QWidget
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from ui.screens.base_screen import BaseScreen

class ProgramSelectionScreen(BaseScreen):
    program_selected = pyqtSignal(str)  # Signaali valitulle ohjelmalle
    
    def __init__(self, parent=None, program_manager=None):
        self.program_manager = program_manager
        super().__init__(parent)
        
    def init_ui(self):
        # Päälayout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Yläpalkki (takaisin-nappi ja otsikko)
        top_bar = QHBoxLayout()
        
        # Takaisin-nappi
        self.back_button = QPushButton("← TAKAISIN", self)
        self.back_button.setFixedSize(150, 60)
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
        top_bar.addWidget(self.back_button)
        
        # Otsikko
        title = QLabel("VALITSE OHJELMA", self)
        title.setFont(QFont("Arial", 30, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        top_bar.addWidget(title, 1)  # Lisää stretch factor jotta otsikko keskittyy
        
        # Lisää tyhjä widget oikealle puolelle tasapainottamaan
        spacer = QWidget()
        spacer.setFixedSize(150, 60)
        top_bar.addWidget(spacer)
        
        main_layout.addLayout(top_bar)
        
        # Vieritettävä ohjelmalista
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: #f0f0f0;
                width: 15px;
            }
            QScrollBar::handle:vertical {
                background: #cecece;
                min-height: 30px;
                border-radius: 7px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Ohjelmapainikkeiden container
        self.grid_container = QWidget()
        grid_layout = QGridLayout(self.grid_container)
        grid_layout.setSpacing(15)
        
        # Hae ohjelmalista
        program_list = []
        if self.program_manager:
            program_list = self.program_manager.get_program_list()
        else:
            program_list = [f"Ohjelma {i}" for i in range(1, 31)]
        
        # Luo ohjelmapainikkeet
        self.program_buttons = []
        for i, program_name in enumerate(program_list):
            button = QPushButton(program_name, self.grid_container)
            button.setFixedSize(230, 90)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    color: #333333;
                    border-radius: 10px;
                    font-size: 20px;
                    font-weight: bold;
                    border: 1px solid #dddddd;
                    text-align: left;
                    padding-left: 15px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
                QPushButton:pressed {
                    background-color: #2196F3;
                    color: white;
                }
            """)
            
            # Paikkaindeksi: 5 riviä, 5 nappia per rivi (muutettu 6->5 jotta napit olisivat isompia)
            row = i // 5
            col = i % 5
            
            # Yhdistä painallus signaaliin (i+1 on ohjelmanumero)
            button.clicked.connect(lambda checked, prog_name=program_name: self.select_program(prog_name))
            
            grid_layout.addWidget(button, row, col)
            self.program_buttons.append(button)
        
        scroll_area.setWidget(self.grid_container)
        main_layout.addWidget(scroll_area)
    
    def select_program(self, program_name):
        """Valitse ohjelma ja lähetä signaali"""
        self.program_selected.emit(program_name)
        self.go_back()
    
    def go_back(self):
        """Palaa testaussivulle"""
        if hasattr(self.parent(), 'show_testing'):
            self.parent().show_testing()
    
    def update_program_list(self, program_list):
        """Päivitä ohjelmalista dynaamisesti"""
        # Tyhjennä vanhat napit
        for button in self.program_buttons:
            button.deleteLater()
        self.program_buttons = []
        
        # Hae uusi layout
        grid_layout = self.grid_container.layout()
        
        # Luo uudet ohjelmapainikkeet
        for i, program_name in enumerate(program_list):
            button = QPushButton(program_name, self.grid_container)
            button.setFixedSize(230, 90)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    color: #333333;
                    border-radius: 10px;
                    font-size: 20px;
                    font-weight: bold;
                    border: 1px solid #dddddd;
                    text-align: left;
                    padding-left: 15px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
                QPushButton:pressed {
                    background-color: #2196F3;
                    color: white;
                }
            """)
            
            # Paikkaindeksi: riviä, 5 nappia per rivi
            row = i // 5
            col = i % 5
            
            # Yhdistä painallus signaaliin
            button.clicked.connect(lambda checked, prog_name=program_name: self.select_program(prog_name))
            
            grid_layout.addWidget(button, row, col)
            self.program_buttons.append(button)