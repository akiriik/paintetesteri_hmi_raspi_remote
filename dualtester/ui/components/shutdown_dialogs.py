from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
import os


class ConfirmShutdownDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.result_value = None
        self.setWindowTitle("Sammutuksen vahvistus")
        self.setModal(True)
        self.setFixedSize(620, 360)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                background-color: white;
                color: black;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 35, 40, 35)
        layout.setSpacing(25)

        question_label = QLabel("Haluatko sammuttaa järjestelmän?")
        question_label.setAlignment(Qt.AlignCenter)
        question_label.setFont(QFont("Arial", 24, QFont.Bold))
        layout.addWidget(question_label)

        layout.addStretch()

        button_layout = QHBoxLayout()
        button_layout.setSpacing(25)

        self.cancel_button = QPushButton("PERUUTA")
        self.shutdown_button = QPushButton("SAMMUTA")

        for btn in (self.cancel_button, self.shutdown_button):
            btn.setFixedHeight(90)
            btn.setFont(QFont("Arial", 22, QFont.Bold))

        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #E0E0E0;
                color: #222222;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover {
                background-color: #D0D0D0;
            }
        """)

        self.shutdown_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)

        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.shutdown_button)
        layout.addLayout(button_layout)

        self.cancel_button.clicked.connect(self.cancel)
        self.shutdown_button.clicked.connect(self.shutdown)

    def cancel(self):
        self.result_value = "cancel"
        self.accept()

    def shutdown(self):
        self.result_value = "shutdown"
        self.accept()