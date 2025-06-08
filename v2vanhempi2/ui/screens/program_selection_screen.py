from PyQt5.QtWidgets import (QPushButton, QLabel, QFrame, QGridLayout, QVBoxLayout, 
                           QHBoxLayout, QScrollArea, QWidget)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QFontMetrics
from ui.screens.base_screen import BaseScreen

class ProgramSelectionScreen(BaseScreen):
    program_selected = pyqtSignal(str)  # Signaali valitulle ohjelmalle
    
    def __init__(self, parent=None, program_manager=None):
        self.program_manager = program_manager
        self.current_page = 0
        self.items_per_page = 12  # 3 riviä, 4 saraketta
        self.max_pages = 0
        super().__init__(parent)
        
    def init_ui(self):
        # Aseta musta tausta 
        self.setStyleSheet("background-color: black;")

        # Päälayout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)
        
        # Yläpalkki (takaisin-nappi ja otsikko)
        top_bar = QHBoxLayout()
        
        # Takaisin-nappi
        self.back_button = QPushButton("← TAKAISIN", self)
        self.back_button.setFixedSize(150, 80)
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
        title.setStyleSheet("color: white;")
        title.setAlignment(Qt.AlignCenter)
        top_bar.addWidget(title, 1)  # Lisää stretch factor jotta otsikko keskittyy
        
        # Lisää tyhjä widget oikealle puolelle tasapainottamaan
        spacer = QWidget()
        spacer.setFixedSize(150, 60)
        top_bar.addWidget(spacer)
        
        self.main_layout.addLayout(top_bar)
        
        # Ohjelmapainikkeiden container
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(15)
        
        # Lisää grid container päälayoutiin
        self.main_layout.addWidget(self.grid_container, 1)  # 1 = stretch factor
        
        # Navigaatiopalkki alareunaan
        nav_bar = QHBoxLayout()
        nav_bar.setAlignment(Qt.AlignCenter)
        
        # Edellinen sivu -nappi
        self.prev_button = QPushButton("◄ EDELLINEN", self)
        self.prev_button.setFixedSize(180, 80)
        self.prev_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #333333;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
                border: 1px solid #dddddd;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }
        """)
        self.prev_button.clicked.connect(self.show_prev_page)
        nav_bar.addWidget(self.prev_button)
        
        # Sivunumerolabel
        self.page_label = QLabel("Sivu 1/1", self)
        self.page_label.setFixedSize(100, 60)
        self.page_label.setAlignment(Qt.AlignCenter)
        self.page_label.setFont(QFont("Arial", 18))
        self.page_label.setStyleSheet("color: white;")
        nav_bar.addWidget(self.page_label)
        
        # Seuraava sivu -nappi
        self.next_button = QPushButton("SEURAAVA ►", self)
        self.next_button.setFixedSize(180, 80)
        self.next_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #333333;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
                border: 1px solid #dddddd;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #888888;
            }
        """)
        self.next_button.clicked.connect(self.show_next_page)
        nav_bar.addWidget(self.next_button)
        
        self.main_layout.addLayout(nav_bar)
        
        # Päivitä näkymä
        self.update_program_list()
        
    def update_program_list(self, program_list=None):
        """Päivitä ohjelmalista dynaamisesti"""
        # Käytä parametrina annettua listaa tai hae ohjelmamanagerilta
        if program_list is None and self.program_manager:
            program_list = self.program_manager.get_program_list()
        elif program_list is None:
            program_list = [f"Ohjelma {i}" for i in range(1, 51)]
        
        # Tyhjennä vanhat napit
        self.clear_grid()
        self.program_buttons = []
        
        # Laske maksimisivumäärä
        self.max_pages = (len(program_list) + self.items_per_page - 1) // self.items_per_page
        
        # Varmista että nykyinen sivu on sallituissa rajoissa
        if self.current_page >= self.max_pages:
            self.current_page = max(0, self.max_pages - 1)
        
        # Hae näytettävät ohjelmat nykyiselle sivulle
        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(program_list))
        displayed_programs = program_list[start_idx:end_idx]
        
        # Luo ohjelmapainikkeet
        for i, program_name in enumerate(displayed_programs):
            # Hae ohjelman oikea ID
            program_id = start_idx + i + 1
            
            # Luo painike, jossa on sekä ID että nimi
            button = QPushButton(self.grid_container)
            button.setFixedSize(300, 120)
            
            # Luo selkeä layout painikkeelle
            button_layout = QVBoxLayout(button)
            button_layout.setContentsMargins(15, 5, 15, 5)
            button_layout.setSpacing(5)
            
            # ID-label (ylärivinä)
            id_label = QLabel(f"{program_id}", button)
            id_label.setAlignment(Qt.AlignCenter)
            id_label.setStyleSheet("color: #1976D2; font-size: 26px; font-weight: bold; background-color: transparent;")
            button_layout.addWidget(id_label)
            
            # Nimi-label (alarivinä)
            name_label = QLabel(program_name, button)
            name_label.setAlignment(Qt.AlignCenter)
            name_label.setStyleSheet("color: #333333; font-size: 22px; font-weight: bold; background-color: transparent;")
            name_label.setWordWrap(True)
            button_layout.addWidget(name_label)
            
            # Tyylittele painike
            button.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border-radius: 10px;
                    border: 1px solid #dddddd;
                    text-align: center;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #f0f0f0;
                    border: 1px solid #bbbbbb;
                }
                QPushButton:pressed {
                    background-color: #2196F3;
                    color: white;
                    border: 1px solid #1976D2;
                }
            """)
                        
            # Paikkaindeksi: 3 riviä, 4 nappia per rivi
            row = i // 4
            col = i % 4
            
            # Yhdistä painallus signaaliin (käytä ID:tä ja nimeä)
            button.clicked.connect(lambda checked, prog_id=program_id, prog_name=program_name: 
                                 self.select_program(prog_id, prog_name))
            
            self.grid_layout.addWidget(button, row, col)
            self.program_buttons.append(button)
        
        # Päivitä sivunumero ja navigointinapit
        self.page_label.setText(f"Sivu {self.current_page + 1}/{self.max_pages}")
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < self.max_pages - 1)
    
    def clear_grid(self):
        """Tyhjennä grid-layout kaikista widgeteistä"""
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
    
    def show_prev_page(self):
        """Näytä edellinen sivu"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_program_list()
    
    def show_next_page(self):
        """Näytä seuraava sivu"""
        if self.current_page < self.max_pages - 1:
            self.current_page += 1
            self.update_program_list()
    
    def select_program(self, program_id, program_name):
        """Valitse ohjelma ja lähetä signaali"""
        # Käytetään ForTest-laitteen ohjelman valinnassa suoraan program_id:tä (1-50)
        self.program_selected.emit(f"{program_id}. {program_name}")
        self.go_back()
    
    def go_back(self):
        """Palaa testaussivulle"""
        if hasattr(self.parent(), 'show_testing'):
            self.parent().show_testing()