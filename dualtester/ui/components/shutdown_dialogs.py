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
        self.setFixedSize(600, 400)

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
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        question_label = QLabel("Haluatko sammuttaa järjestelmän?")
        question_label.setAlignment(Qt.AlignCenter)
        question_label.setFont(QFont("Arial", 24))
        layout.addWidget(question_label)

        layout.addStretch()

        main_buttons_layout = QHBoxLayout()
        main_buttons_layout.setSpacing(20)

        self.cancel_button = QPushButton("PERUUTA")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #333333;
                border-radius: 10px;
                padding: 15px;
                min-width: 200px;
                min-height: 80px;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)

        self.shutdown_button = QPushButton("SAMMUTA")
        self.shutdown_button.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border-radius: 10px;
                padding: 15px;
                min-width: 200px;
                min-height: 80px;
                font-size: 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #D32F2F;
            }
        """)

        main_buttons_layout.addWidget(self.cancel_button)
        main_buttons_layout.addWidget(self.shutdown_button)
        layout.addLayout(main_buttons_layout)

        self.cancel_button.clicked.connect(self.on_cancel)
        self.shutdown_button.clicked.connect(self.on_shutdown)

    def on_cancel(self):
        self.result_value = "cancel"
        self.accept()

    def on_shutdown(self):
        self.result_value = "shutdown"
        self.accept()


class ShutdownController:
    @staticmethod
    def show_confirm_dialog(parent):
        dialog = ConfirmShutdownDialog(parent)

        dialog.move(
            parent.width() // 2 - dialog.width() // 2,
            parent.height() // 2 - dialog.height() // 2
        )

        dialog.exec_()

        if dialog.result_value == "shutdown":
            ShutdownController.shutdown_system(parent)

    @staticmethod
    def shutdown_system(parent):
        main_window = parent.parent() if parent else None

        if hasattr(main_window, "modbus_manager") and main_window.modbus_manager:
            try:
                main_window.modbus_manager.write_register(17999, 1)
            except Exception as e:
                print(f"Varoitus: sammutusrekisterin kirjoitus epäonnistui: {e}")

        QTimer.singleShot(2000, ShutdownController._shutdown_raspberry)

    @staticmethod
    def _shutdown_raspberry():
        os.system("sudo shutdown -h now")