from PyQt5.QtWidgets import QPushButton, QLabel, QGridLayout, QVBoxLayout, QHBoxLayout, QWidget
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from ui.screens.base_screen import BaseScreen


PROGRAM_COLUMNS = 2
PROGRAM_ROWS = 4
PROGRAMS_PER_PAGE = PROGRAM_COLUMNS * PROGRAM_ROWS

PROGRAM_CARD_W = 420
PROGRAM_CARD_H = 165


class ProgramSelectionScreen(BaseScreen):
    program_selected = pyqtSignal(dict)  # Signaali valitulle ohjelmalle

    def __init__(self, parent=None, program_manager=None):
        self.program_manager = program_manager
        self.current_page = 0
        self.items_per_page = PROGRAMS_PER_PAGE
        self.max_pages = 0
        super().__init__(parent)

    def init_ui(self):
        self.setStyleSheet("background-color: black;")

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(15)

        top_bar = QHBoxLayout()

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

        title = QLabel("VALITSE OHJELMA", self)
        title.setFont(QFont("Arial", 30, QFont.Bold))
        title.setStyleSheet("color: white;")
        title.setAlignment(Qt.AlignCenter)
        top_bar.addWidget(title, 1)

        spacer = QWidget()
        spacer.setFixedSize(150, 60)
        top_bar.addWidget(spacer)

        self.main_layout.addLayout(top_bar)

        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setHorizontalSpacing(15)
        self.grid_layout.setVerticalSpacing(12)
        self.grid_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        self.main_layout.addWidget(self.grid_container, 1)

        nav_bar = QHBoxLayout()
        nav_bar.setAlignment(Qt.AlignCenter)

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

        self.page_label = QLabel("Sivu 1/1", self)
        self.page_label.setFixedSize(130, 60)
        self.page_label.setAlignment(Qt.AlignCenter)
        self.page_label.setFont(QFont("Arial", 18))
        self.page_label.setStyleSheet("color: white;")
        nav_bar.addWidget(self.page_label)

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

        self.update_program_list()

    def _format_value(self, value, suffix=""):
        if value is None or value == "":
            return "--"

        if isinstance(value, float):
            if value.is_integer():
                value = int(value)

        text = str(value)

        if suffix and text != "--":
            return f"{text}{suffix}"

        return text

    def _format_decay_text(self, program_data):
        max_decay = program_data.get("max_decay", {})

        if not isinstance(max_decay, dict):
            return "--"

        value = max_decay.get("value", "--")
        unit = max_decay.get("unit", "")
        mode = max_decay.get("mode", "")

        if value is None or value == "":
            return "--"

        if isinstance(value, float) and value.is_integer():
            value = int(value)

        text = str(value)

        if unit:
            text += f" {unit}"

        if mode:
            text += f" ({mode})"

        return text

    def _create_program_card(self, program_data, fallback_name):
        program_id = program_data.get("id", "--")
        program_name = program_data.get("name", fallback_name)
        description = program_data.get("description", "")

        pressure = self._format_value(program_data.get("pressure_mbar", "--"), " mbar")
        volume = self._format_value(program_data.get("piece_volume_ml", "--"), " ml")
        fill_time = self._format_value(program_data.get("fill_time_s", "--"), "s")
        settle_time = self._format_value(program_data.get("settle_time_s", "--"), "s")
        test_time = self._format_value(program_data.get("test_time_s", "--"), "s")
        decay_text = self._format_decay_text(program_data)

        button = QPushButton(self.grid_container)
        button.setFixedSize(PROGRAM_CARD_W, PROGRAM_CARD_H)
        button.setStyleSheet("""
            QPushButton {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #dddddd;
                text-align: left;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border: 1px solid #bbbbbb;
            }
            QPushButton:pressed {
                background-color: #D8ECFF;
                border: 1px solid #1976D2;
            }
        """)

        button_layout = QVBoxLayout(button)
        button_layout.setContentsMargins(14, 10, 14, 10)
        button_layout.setSpacing(4)

        title_label = QLabel(f"{program_id}. {program_name}", button)
        title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title_label.setStyleSheet(
            "color: #1976D2; font-size: 21px; font-weight: bold; background-color: transparent;"
        )
        title_label.setWordWrap(True)
        button_layout.addWidget(title_label)

        if description:
            desc_label = QLabel(description, button)
            desc_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            desc_label.setStyleSheet(
                "color: #555555; font-size: 13px; background-color: transparent;"
            )
            desc_label.setWordWrap(True)
            button_layout.addWidget(desc_label)

        info_1 = QLabel(f"PAINE: {pressure}     TILAVUUS: {volume}", button)
        info_1.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        info_1.setStyleSheet(
            "color: #222222; font-size: 14px; background-color: transparent;"
        )
        button_layout.addWidget(info_1)

        info_2 = QLabel(
            f"TÄYTTÖ: {fill_time}     TASAUS: {settle_time}     TESTI: {test_time}",
            button,
        )
        info_2.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        info_2.setStyleSheet(
            "color: #222222; font-size: 14px; background-color: transparent;"
        )
        button_layout.addWidget(info_2)

        info_3 = QLabel(f"RAJA: {decay_text}", button)
        info_3.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        info_3.setStyleSheet(
            "color: #222222; font-size: 14px; background-color: transparent;"
        )
        info_3.setWordWrap(True)
        button_layout.addWidget(info_3)

        button.clicked.connect(lambda checked, prog=program_data: self.select_program(prog))

        return button

    def update_program_list(self, program_list=None):
        """Päivitä ohjelmalista dynaamisesti."""
        if program_list is None and self.program_manager:
            program_list = self.program_manager.get_program_list()
        elif program_list is None:
            program_list = [f"Ohjelma {i}" for i in range(1, 51)]

        self.clear_grid()
        self.program_buttons = []

        self.max_pages = max(
            1,
            (len(program_list) + self.items_per_page - 1) // self.items_per_page,
        )

        if self.current_page >= self.max_pages:
            self.current_page = max(0, self.max_pages - 1)

        start_idx = self.current_page * self.items_per_page
        end_idx = min(start_idx + self.items_per_page, len(program_list))
        displayed_programs = program_list[start_idx:end_idx]

        for i, program_name in enumerate(displayed_programs):
            program_index = start_idx + i
            program_data = None

            if self.program_manager:
                program_data = self.program_manager.get_program_by_index(program_index)

            if program_data is None:
                program_data = {
                    "id": start_idx + i + 1,
                    "name": program_name,
                    "description": "",
                }

            button = self._create_program_card(program_data, program_name)

            row = i // PROGRAM_COLUMNS
            col = i % PROGRAM_COLUMNS

            self.grid_layout.addWidget(button, row, col)
            self.program_buttons.append(button)

        self.page_label.setText(f"Sivu {self.current_page + 1}/{self.max_pages}")
        self.prev_button.setEnabled(self.current_page > 0)
        self.next_button.setEnabled(self.current_page < self.max_pages - 1)

    def clear_grid(self):
        """Tyhjennä grid-layout kaikista widgeteistä."""
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

    def show_prev_page(self):
        """Näytä edellinen sivu."""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_program_list()

    def show_next_page(self):
        """Näytä seuraava sivu."""
        if self.current_page < self.max_pages - 1:
            self.current_page += 1
            self.update_program_list()

    def select_program(self, program_data):
        """Valitse ohjelma ja lähetä koko ohjelmatiedot."""
        self.program_selected.emit(program_data)
        self.go_back()

    def go_back(self):
        """Palaa testaussivulle."""
        if hasattr(self.parent(), "show_testing"):
            self.parent().show_testing()
