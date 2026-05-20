from PyQt5.QtWidgets import QWidget, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

from ui.components.environment_bar import EnvironmentBar
from ui.components.fortest_station import ForTestStation


class MainScreen(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("background-color: black;")

        screen_w = self.parent().screen_width if self.parent() else 1920
        screen_h = self.parent().screen_height if self.parent() else 1080

        top_h = 90
        margin = 10
        gap = 10

        station_y = top_h + margin
        station_h = screen_h - station_y - margin
        station_w = (screen_w - (margin * 2) - gap) // 2

        # Yhteinen yläpalkki
        self.environment_bar = EnvironmentBar(self)
        self.environment_bar.setGeometry(
            margin,
            margin,
            screen_w - margin * 2,
            top_h - margin
        )

        # Vasen ForTest
        self.fortest1 = ForTestStation(
            station_id=1,
            title="FORTEST 1",
            parent=self
        )
        self.fortest1.setGeometry(
            margin,
            station_y,
            station_w,
            station_h
        )

        # Oikea ForTest
        self.fortest2 = ForTestStation(
            station_id=2,
            title="FORTEST 2",
            parent=self
        )
        self.fortest2.setGeometry(
            margin + station_w + gap,
            station_y,
            station_w,
            station_h
        )

        # Yläpalkin napit
        self.environment_bar.manual_button.clicked.connect(self.open_manual_screen)
        self.environment_bar.shutdown_button.clicked.connect(self.show_confirm_shutdown_dialog)

    def open_manual_screen(self):
        """Avaa käsikäyttösivu MainWindowin kautta"""
        if hasattr(self.parent(), "show_manual"):
            self.parent().show_manual()

    def show_confirm_shutdown_dialog(self):
        """Sammutuksen vahvistus uuden yläpalkin kautta"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Sammutuksen vahvistus")
        dialog.setModal(True)
        dialog.setFixedSize(600, 400)

        dialog.move(
            self.width() // 2 - dialog.width() // 2,
            self.height() // 2 - dialog.height() // 2
        )

        dialog.setStyleSheet("""
            QDialog {
                background-color: white;
            }
            QLabel {
                background-color: white;
                color: black;
            }
        """)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)

        question_label = QLabel("Haluatko sammuttaa järjestelmän?")
        question_label.setAlignment(Qt.AlignCenter)
        question_label.setFont(QFont("Arial", 24))
        layout.addWidget(question_label)

        layout.addStretch()

        main_buttons_layout = QHBoxLayout()
        main_buttons_layout.setSpacing(20)

        cancel_button = QPushButton("PERUUTA")
        cancel_button.setStyleSheet("""
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

        shutdown_button = QPushButton("SAMMUTA")
        shutdown_button.setStyleSheet("""
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

        main_buttons_layout.addWidget(cancel_button)
        main_buttons_layout.addWidget(shutdown_button)
        layout.addLayout(main_buttons_layout)

        result_value = None

        def on_cancel():
            nonlocal result_value
            result_value = "cancel"
            dialog.accept()

        def on_shutdown():
            nonlocal result_value
            result_value = "shutdown"
            dialog.accept()

        cancel_button.clicked.connect(on_cancel)
        shutdown_button.clicked.connect(on_shutdown)

        dialog.exec_()

        if result_value == "shutdown":
            self.shutdown_system()

    def shutdown_system(self):
        """Kirjoita sammutusrekisteri ja sammuta Raspberry"""
        parent = self.parent()

        if hasattr(parent, "modbus_manager") and parent.modbus_manager:
            try:
                parent.modbus_manager.write_register(17999, 1)
            except Exception as e:
                print(f"Varoitus: sammutusrekisterin kirjoitus epäonnistui: {e}")

        QTimer.singleShot(2000, self._shutdown_raspberry)

    def _shutdown_raspberry(self):
        import os
        os.system("sudo shutdown -h now")

    def cleanup(self):
        """MainScreen cleanup"""
        pass