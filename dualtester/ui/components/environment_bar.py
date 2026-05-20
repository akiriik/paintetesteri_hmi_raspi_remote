from PyQt5.QtWidgets import QFrame, QLabel, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class EnvironmentBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #101010;
                border: 2px solid #333333;
                border-radius: 10px;
            }
        """)

        self.title_label = QLabel("PAINETESTAUS  |  2x FORTEST", self)
        self.title_label.setGeometry(20, 10, 420, 60)
        self.title_label.setFont(QFont("Consolas", 22, QFont.Bold))
        self.title_label.setStyleSheet("color: white; background: transparent; border: none;")
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.environment_label = QLabel(
            "HUONE: --.-°C / --.- %    SÄILIÖ: --.-°C / -.-- BAR    IO: --    ANTURIT: --",
            self
        )
        self.environment_label.setGeometry(460, 10, 950, 60)
        self.environment_label.setFont(QFont("Consolas", 16))
        self.environment_label.setStyleSheet("color: #33FF33; background: transparent; border: none;")
        self.environment_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.manual_button = QPushButton("KÄSIKÄYTTÖ", self)
        self.manual_button.setGeometry(1450, 10, 190, 60)
        self.manual_button.setFont(QFont("Arial", 16, QFont.Bold))
        self.manual_button.setStyleSheet("""
            QPushButton {
                background-color: #303030;
                color: white;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)

        self.shutdown_button = QPushButton("SAMMUTA", self)
        self.shutdown_button.setGeometry(1660, 10, 210, 60)
        self.shutdown_button.setFont(QFont("Arial", 16, QFont.Bold))
        self.shutdown_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)