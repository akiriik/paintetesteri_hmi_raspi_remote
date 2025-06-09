from PyQt5.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFrame
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

class SystemStatusDialog(QDialog):
    def __init__(self, parent=None, modbus=None):
        super().__init__(parent)
        self.modbus = modbus
        self.current_pressure = 0.0
        self.current_temperature = None
        self.input_pressure_on = False
        self.pressure_raising = False

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setModal(True)
        self.setStyleSheet("background-color: #2e2e2e;")  # vaaleampi musta
        self.setFixedSize(800, 600)

        if parent:
            self.move(
                parent.width() // 2 - self.width() // 2,
                parent.height() // 2 - self.height() // 2
            )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.main_frame = QFrame(self)
        self.main_frame.setStyleSheet("""
            background-color: #2e2e2e;
            border-radius: 20px;
            border: 2px solid white;
        """)
        frame_layout = QVBoxLayout(self.main_frame)
        frame_layout.setContentsMargins(30, 30, 30, 30)
        frame_layout.setSpacing(20)

        # Otsikko
        self.title = QLabel("JÄRJESTELMÄN TILA", self.main_frame)
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFont(QFont("Arial", 24, QFont.Bold))
        self.title.setStyleSheet("""
            color: white;
            background-color: transparent;
            border: none;
        """)
        frame_layout.addWidget(self.title)

        # Paine
        self.pressure_label = QLabel("Järjestelmän paine: -.-- BAR", self.main_frame)
        self.pressure_label.setAlignment(Qt.AlignCenter)
        self.pressure_label.setFont(QFont("Arial", 18))
        self.pressure_label.setStyleSheet("""
            color: white;
            background-color: transparent;
            border: none;
        """)
        frame_layout.addWidget(self.pressure_label)

        # Lämpötila
        self.temperature_label = QLabel("Lämpötila: --.-°C", self.main_frame)
        self.temperature_label.setAlignment(Qt.AlignCenter)
        self.temperature_label.setFont(QFont("Arial", 18))
        self.temperature_label.setStyleSheet("""
            color: white;
            background-color: transparent;
            border: none;
        """)
        frame_layout.addWidget(self.temperature_label)

        # Tulopaine
        self.input_pressure_label = QLabel("Tulopaine: EI TIETOA", self.main_frame)
        self.input_pressure_label.setAlignment(Qt.AlignCenter)
        self.input_pressure_label.setFont(QFont("Arial", 18))
        self.input_pressure_label.setStyleSheet("""
            color: white;
            background-color: transparent;
            border: none;
        """)
        frame_layout.addWidget(self.input_pressure_label)

        frame_layout.addStretch()

        # Tilaviesti
        self.status_message = QLabel("Järjestelmän paine liian matala", self.main_frame)
        self.status_message.setAlignment(Qt.AlignCenter)
        self.status_message.setFont(QFont("Arial", 16, QFont.Bold))
        self.status_message.setStyleSheet("""
            color: #F44336;
            background-color: transparent;
            border: none;
        """)
        frame_layout.addWidget(self.status_message)

        frame_layout.addStretch()

        # Painikkeet
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(20)

        self.start_system_btn = QPushButton("KÄYNNISTÄ JÄRJESTELMÄ", self.main_frame)
        self.start_system_btn.setFixedSize(300, 80)
        self.start_system_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 10px;
                font-size: 18px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.start_system_btn.clicked.connect(self.start_system)
        buttons_layout.addWidget(self.start_system_btn)

        self.stop_system_btn = QPushButton("PYSÄYTÄ JÄRJESTELMÄ", self.main_frame)
        self.stop_system_btn.setFixedSize(300, 80)
        self.stop_system_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                border-radius: 10px;
                font-size: 18px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        self.stop_system_btn.clicked.connect(self.stop_system)
        buttons_layout.addWidget(self.stop_system_btn)

        frame_layout.addLayout(buttons_layout)

        self.close_btn = QPushButton("SULJE", self.main_frame)
        self.close_btn.setFixedSize(200, 60)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #888888;
                color: white;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #666666;
            }
        """)
        self.close_btn.clicked.connect(self.reject)
        frame_layout.addWidget(self.close_btn, 0, Qt.AlignCenter)

        layout.addWidget(self.main_frame)

        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(1000)

    def start_system(self):
        if self.modbus:
            self.modbus.toggle_relay(3, 1)
            self.pressure_raising = True
            self.status_message.setText("Nostetaan painetta...")
            self.status_message.setStyleSheet("""
                color: #FF9800;
                background-color: transparent;
                border: none;
                font-weight: bold;
            """)
            self.start_system_btn.setEnabled(False)

    def stop_system(self):
        if self.modbus:
            self.modbus.toggle_relay(3, 0)
            self.pressure_raising = False
            self.status_message.setText("Järjestelmä pysäytetty")
            self.status_message.setStyleSheet("""
                color: #F44336;
                background-color: transparent;
                border: none;
                font-weight: bold;
            """)
            self.start_system_btn.setEnabled(True)

    def update_status(self):
        if not self.modbus:
            return
        self.modbus.read_register(19500, 1)
        self.modbus.read_register(18101, 1)

    def update_pressure(self, pressure_bar):
        self.current_pressure = pressure_bar
        self.pressure_label.setText(f"Järjestelmän paine: {pressure_bar:.2f} BAR")
        if pressure_bar >= 6.0 and self.pressure_raising:
            self.status_message.setText("Paine riittävä!")
            self.status_message.setStyleSheet("""
                color: #4CAF50;
                background-color: transparent;
                border: none;
                font-weight: bold;
            """)
            QTimer.singleShot(2000, self.accept)

    def update_temperature(self, temperature):
        self.current_temperature = temperature
        if temperature is not None:
            self.temperature_label.setText(f"Lämpötila: {temperature:.1f}°C")
        else:
            self.temperature_label.setText("Lämpötila: --.-°C")

    def update_input_pressure_status(self, status):
        self.input_pressure_on = (status == 1)
        if self.input_pressure_on:
            self.input_pressure_label.setText("Tulopaine: PÄÄLLÄ")
            self.input_pressure_label.setStyleSheet("""
                color: #4CAF50;
                background-color: transparent;
                border: none;
            """)
            self.stop_system_btn.setEnabled(True)
        else:
            self.input_pressure_label.setText("Tulopaine: POIS")
            self.input_pressure_label.setStyleSheet("""
                color: #F44336;
                background-color: transparent;
                border: none;
            """)
            self.stop_system_btn.setEnabled(False)
            self.start_system_btn.setEnabled(True)
            self.pressure_raising = False

    def check_auto_close_conditions(self):
        return (self.current_pressure >= 6.0 and self.input_pressure_on and not self.pressure_raising)

    def closeEvent(self, event):
        self.update_timer.stop()
        super().closeEvent(event)
