from PyQt5.QtWidgets import QFrame, QLabel, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class ForTestStation(QFrame):
    def __init__(self, station_id, title, parent=None):
        super().__init__(parent)
        self.station_id = station_id
        self.title = title
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #050505;
                border: 2px solid #333333;
                border-radius: 10px;
            }
        """)

        self.title_label = QLabel(self.title, self)
        self.title_label.setGeometry(20, 15, 300, 40)
        self.title_label.setFont(QFont("Consolas", 24, QFont.Bold))
        self.title_label.setStyleSheet("color: white; background: transparent; border: none;")
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.status_label = QLabel("TILA: --    FORTEST: --", self)
        self.status_label.setGeometry(330, 15, 560, 40)
        self.status_label.setFont(QFont("Consolas", 16))
        self.status_label.setStyleSheet("color: orange; background: transparent; border: none;")
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.program_box = QFrame(self)
        self.program_box.setGeometry(20, 70, 880, 170)
        self.program_box.setStyleSheet("""
            QFrame {
                background-color: black;
                border: 1px solid #333333;
                border-radius: 10px;
            }
        """)

        self.program_label = QLabel("OHJELMA: --", self.program_box)
        self.program_label.setGeometry(15, 10, 850, 35)
        self.program_label.setFont(QFont("Consolas", 18, QFont.Bold))
        self.program_label.setStyleSheet("color: #33FF33; background: transparent; border: none;")

        self.program_info_label = QLabel(
            "PAINE: --     TILAVUUS: --     TÄYTTÖ: --     TASAUS: --     TESTI: --     RAJA: --",
            self.program_box
        )
        self.program_info_label.setGeometry(15, 55, 850, 95)
        self.program_info_label.setFont(QFont("Consolas", 14))
        self.program_info_label.setWordWrap(True)
        self.program_info_label.setStyleSheet("color: #33FF33; background: transparent; border: none;")

        self.results_box = QLabel("", self)
        self.results_box.setGeometry(20, 255, 880, 580)
        self.results_box.setFont(QFont("Consolas", 15))
        self.results_box.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.results_box.setStyleSheet("""
            QLabel {
                background-color: black;
                color: white;
                border: 1px solid #444444;
                border-radius: 10px;
                padding: 12px;
            }
        """)
        self.results_box.setText("AIKA        OHJELMA        VUOTO        TULOS        HUONE        KAPPALE")

        self.select_program_button = QPushButton("VALITSE OHJELMA", self)
        self.select_program_button.setGeometry(20, 850, 280, 75)
        self.select_program_button.setFont(QFont("Arial", 18, QFont.Bold))
        self.select_program_button.setStyleSheet("""
            QPushButton {
                background-color: #074678;
                color: white;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)

        self.start_button = QPushButton("START", self)
        self.start_button.setGeometry(330, 850, 250, 75)
        self.start_button.setFont(QFont("Arial", 22, QFont.Bold))
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #0B7A28;
                color: white;
                border-radius: 10px;
                border: none;
            }
        """)

        self.stop_button = QPushButton("STOP", self)
        self.stop_button.setGeometry(610, 850, 290, 75)
        self.stop_button.setFont(QFont("Arial", 22, QFont.Bold))
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #A00000;
                color: white;
                border-radius: 10px;
                border: none;
            }
        """)