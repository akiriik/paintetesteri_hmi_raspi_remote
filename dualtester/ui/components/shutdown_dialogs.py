from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
import os
import sys


class ConfirmShutdownDialog(QDialog):
    """Ensimmäinen sammutuksen vahvistusdialogi"""

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

        layout.addSpacing(30)

        options_layout = QHBoxLayout()
        options_layout.addStretch()

        self.options_button = QPushButton("VAIHTOEHDOT")
        self.options_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 10px;
                padding: 10px;
                min-width: 200px;
                min-height: 40px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)

        options_layout.addWidget(self.options_button)
        options_layout.addStretch()
        layout.addLayout(options_layout)

        self.cancel_button.clicked.connect(self.on_cancel)
        self.shutdown_button.clicked.connect(self.on_shutdown)
        self.options_button.clicked.connect(self.on_options)

    def on_cancel(self):
        self.result_value = "cancel"
        self.accept()

    def on_shutdown(self):
        self.result_value = "shutdown"
        self.accept()

    def on_options(self):
        self.result_value = "options"
        self.accept()


class ShutdownOptionsDialog(QDialog):
    """Vaihtoehtoinen sammutusvalikko"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.result_value = None

        self.setWindowTitle("Sammutusvalikko")
        self.setModal(True)
        self.setFixedSize(800, 400)

        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                color: black;
                background-color: white;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(30)
        layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel("Valitse toiminto:", self)
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 20))
        layout.addWidget(title)

        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(15)

        self.raspberry_button = QPushButton("Sammuta Raspberry Pi")
        self.restart_button = QPushButton("Käynnistä ohjelma uudelleen")
        self.close_button = QPushButton("Sammuta ohjelma")
        self.cancel_button = QPushButton("Peruuta")

        buttons = [
            self.raspberry_button,
            self.restart_button,
            self.close_button,
            self.cancel_button,
        ]

        for button in buttons:
            button.setFixedHeight(60)
            button.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    color: black;
                    border-radius: 5px;
                    padding: 10px;
                    font-size: 18px;
                    border: 1px solid #ccc;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """)
            buttons_layout.addWidget(button)

        layout.addLayout(buttons_layout)

        self.raspberry_button.clicked.connect(lambda: self.set_result("raspberry"))
        self.restart_button.clicked.connect(lambda: self.set_result("restart"))
        self.close_button.clicked.connect(lambda: self.set_result("close"))
        self.cancel_button.clicked.connect(lambda: self.set_result("cancel"))

    def set_result(self, value):
        self.result_value = value
        self.accept()


class ShutdownController:
    """Sammutustoimintojen ohjain"""

    @staticmethod
    def show_confirm_dialog(parent):
        dialog = ConfirmShutdownDialog(parent)

        dialog.move(
            parent.width() // 2 - dialog.width() // 2,
            parent.height() // 2 - dialog.height() // 2,
        )

        dialog.exec_()

        if dialog.result_value == "shutdown":
            ShutdownController.shutdown_system(parent)
        elif dialog.result_value == "options":
            ShutdownController.show_options_dialog(parent)

    @staticmethod
    def show_options_dialog(parent):
        dialog = ShutdownOptionsDialog(parent)

        dialog.move(
            parent.width() // 2 - dialog.width() // 2,
            parent.height() // 2 - dialog.height() // 2,
        )

        dialog.exec_()

        if dialog.result_value == "raspberry":
            ShutdownController.shutdown_system(parent)
        elif dialog.result_value == "restart":
            ShutdownController.restart_application(parent)
        elif dialog.result_value == "close":
            ShutdownController.close_application(parent)

    @staticmethod
    def shutdown_system(parent):
        main_window = ShutdownController._get_main_window(parent)
        ShutdownController._write_shutdown_register(main_window)

        QTimer.singleShot(2000, ShutdownController._shutdown_raspberry)

    @staticmethod
    def _get_main_window(parent):
        if parent is None:
            return None

        if hasattr(parent, "hardware_service"):
            return parent

        return parent.parent()

    @staticmethod
    def _write_shutdown_register(main_window):
        if not main_window or not hasattr(main_window, "hardware_service"):
            return

        try:
            main_window.hardware_service.write_register(17999, 1)
        except Exception as e:
            print(f"Varoitus: sammutusrekisterin kirjoitus epäonnistui: {e}")

    @staticmethod
    def _shutdown_raspberry():
        os.system("sudo shutdown -h now")

    @staticmethod
    def restart_application(parent):
        main_window = ShutdownController._get_main_window(parent)

        if main_window:
            main_window.close()

        os.execv(sys.executable, [sys.executable] + sys.argv)

    @staticmethod
    def close_application(parent):
        main_window = ShutdownController._get_main_window(parent)

        if main_window:
            main_window.close()