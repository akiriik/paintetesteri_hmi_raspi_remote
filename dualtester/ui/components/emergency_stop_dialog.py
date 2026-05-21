# ui/components/emergency_stop_dialog.py
from PyQt5.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QFrame
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont


class EmergencyStopDialog(QDialog):
    def __init__(self, parent=None, hardware_service=None):
        super().__init__(parent)

        self.hardware_service = hardware_service

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setStyleSheet("background-color: transparent;")
        self.setFixedSize(700, 500)

        if parent:
            self.move(
                parent.width() // 2 - self.width() // 2,
                parent.height() // 2 - self.height() // 2,
            )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.red_frame = QFrame(self)
        self.red_frame.setStyleSheet("""
            background-color: white;
            border-radius: 20px;
            border: 16px solid red;
        """)
        frame_layout = QVBoxLayout(self.red_frame)
        frame_layout.setContentsMargins(20, 20, 20, 20)
        frame_layout.setSpacing(40)

        frame_layout.addStretch()

        self.text_container = QFrame(self.red_frame)
        self.text_container.setFixedSize(400, 100)
        self.text_container.setStyleSheet("""
            background-color: white;
            border-radius: 20px;
            border: 4px solid red;
        """)

        self.title = QLabel("HÄTÄSEIS", self.text_container)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setGeometry(0, 0, 400, 100)
        self.title.setFont(QFont("Arial", 36, QFont.Bold))
        self.title.setStyleSheet("color: black; background-color: transparent;")

        frame_layout.addWidget(self.text_container, 0, Qt.AlignCenter)
        frame_layout.addStretch()

        self.reset_button = QPushButton("KUITTAUS", self.red_frame)
        self.reset_button.setFixedSize(300, 80)
        self.reset_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 20px;
                font-size: 24px;
                font-weight: bold;
                border: none;
            }
        """)
        self.reset_button.clicked.connect(self.reset_emergency_stop)
        frame_layout.addWidget(self.reset_button, 0, Qt.AlignCenter)

        layout.addWidget(self.red_frame)

        self.blink_timer = QTimer(self)
        self.blink_timer.timeout.connect(self.toggle_blink)
        self.blink_timer.start(500)
        self.is_visible = True

    def toggle_blink(self):
        self.is_visible = not self.is_visible

        if self.is_visible:
            self.text_container.setStyleSheet("""
                background-color: white;
                border-radius: 20px;
                border: 4px solid red;
            """)
        else:
            self.text_container.setStyleSheet("""
                background-color: red;
                border-radius: 20px;
                border: 4px solid red;
            """)

    def reset_emergency_stop(self):
        if not self.hardware_service:
            return

        self.hardware_service.reset_emergency_stop()
        QTimer.singleShot(500, self.check_status_after_reset)

    def check_status_after_reset(self):
        if not self.hardware_service:
            return

        status = self.hardware_service.read_emergency_stop_status()

        if status == 1:
            self.accept()
        else:
            self.reset_button.setText("KUITTAUS\nHÄTÄSEIS EDELLEEN AKTIIVINEN")
            self.reset_button.setStyleSheet("""
                QPushButton {
                    background-color: #FFC107;
                    color: black;
                    border-radius: 20px;
                    font-size: 18px;
                    font-weight: bold;
                    border: none;
                }
            """)

    def closeEvent(self, event):
        if self.blink_timer:
            self.blink_timer.stop()

        super().closeEvent(event)