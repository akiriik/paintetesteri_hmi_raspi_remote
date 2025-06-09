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
       self.setStyleSheet("background-color: #2e2e2e;")
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

       # Sammutusnappi vasempaan yläkulmaan
       self.shutdown_system_btn = QPushButton("SAMMUTA JÄRJESTELMÄ", self.main_frame)
       self.shutdown_system_btn.setFixedSize(250, 50)
       self.shutdown_system_btn.setStyleSheet("""
           QPushButton {
               background-color: #F44336;
               color: white;
               border-radius: 10px;
               font-size: 16px;
               font-weight: bold;
               border: none;
           }
           QPushButton:hover {
               background-color: #D32F2F;
           }
       """)
       self.shutdown_system_btn.clicked.connect(self.show_shutdown_options)
       
       # Layout sammutusnapille
       shutdown_layout = QHBoxLayout()
       shutdown_layout.addWidget(self.shutdown_system_btn)
       shutdown_layout.addStretch()
       frame_layout.addLayout(shutdown_layout)

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
       self.start_system_btn.setEnabled(False)
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
       
       if pressure_bar >= 6.0:
           self.status_message.setText("Paine riittävä!")
           self.status_message.setStyleSheet("""
               color: #4CAF50;
               background-color: transparent;
               border: none;
               font-weight: bold;
           """)
       else:
           self.status_message.setText("Järjestelmän paine liian matala")
           self.status_message.setStyleSheet("""
               color: #F44336;
               background-color: transparent;
               border: none;
               font-weight: bold;
           """)

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
           self.start_system_btn.setEnabled(False)
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

   def show_shutdown_options(self):
       """Näytä sammutusvalinnat"""
       from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout
       
       dialog = QDialog(self)
       dialog.setWindowTitle("Sammutusvalinnat")
       dialog.setModal(True)
       dialog.setFixedSize(600, 400)
       
       dialog.move(
           self.width() // 2 - dialog.width() // 2,
           self.height() // 2 - dialog.height() // 2
       )
       
       layout = QVBoxLayout(dialog)
       layout.setSpacing(20)
       layout.setContentsMargins(40, 40, 40, 40)
       
       dialog.setStyleSheet("""
           QDialog { background-color: white; }
           QLabel { background-color: white; color: black; }
       """)

       question_label = QLabel("Haluatko sammuttaa järjestelmän?")
       question_label.setAlignment(Qt.AlignCenter)
       question_label.setFont(QFont("Arial", 24))
       layout.addWidget(question_label)
       
       layout.addStretch()
       
       main_buttons_layout = QHBoxLayout()
       main_buttons_layout.setSpacing(20)
       
       peruuta_btn = QPushButton("PERUUTA")
       peruuta_btn.setStyleSheet("""
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
       
       sammuta_btn = QPushButton("SAMMUTA")
       sammuta_btn.setStyleSheet("""
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
       
       main_buttons_layout.addWidget(peruuta_btn)
       main_buttons_layout.addWidget(sammuta_btn)
       layout.addLayout(main_buttons_layout)
       
       layout.addSpacing(30)
       
       vaihtoehdot_layout = QHBoxLayout()
       vaihtoehdot_layout.addStretch()
       
       vaihtoehdot_btn = QPushButton("VAIHTOEHDOT")
       vaihtoehdot_btn.setStyleSheet("""
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
       
       vaihtoehdot_layout.addWidget(vaihtoehdot_btn)
       vaihtoehdot_layout.addStretch()
       layout.addLayout(vaihtoehdot_layout)
       
       result_value = None
       
       def on_peruuta():
           nonlocal result_value
           result_value = "peruuta"
           dialog.accept()
       
       def on_sammuta():
           nonlocal result_value
           result_value = "sammuta"
           dialog.accept()
       
       def on_vaihtoehdot():
           nonlocal result_value
           result_value = "vaihtoehdot"
           dialog.accept()
       
       peruuta_btn.clicked.connect(on_peruuta)
       sammuta_btn.clicked.connect(on_sammuta)
       vaihtoehdot_btn.clicked.connect(on_vaihtoehdot)
       
       dialog.exec_()
       
       if result_value == "sammuta":
           if self.modbus:
               self.modbus.write_register(17999, 1)
               self.status_message.setText("Sammutetaan järjestelmä...")
               self.status_message.setStyleSheet("""
                   color: #FF9800;
                   background-color: transparent;
                   border: none;
                   font-weight: bold;
               """)
               QTimer.singleShot(2000, self.shutdown_raspberry)
       elif result_value == "vaihtoehdot":
           self.show_advanced_shutdown_options()

   def shutdown_raspberry(self):
       """Sammuta Raspberry Pi järjestelmä"""
       import os
       os.system("sudo shutdown -h now")

   def show_advanced_shutdown_options(self):
       """Näytä edistyneet sammutusvalinnat"""
       from PyQt5.QtWidgets import QDialog, QVBoxLayout
       
       dialog = QDialog(self)
       dialog.setWindowTitle("Sammutusvalinnat")
       dialog.setModal(True)
       dialog.setFixedSize(500, 350)
       
       dialog.move(
           self.width() // 2 - dialog.width() // 2,
           self.height() // 2 - dialog.height() // 2
       )
       
       layout = QVBoxLayout(dialog)
       layout.setSpacing(20)
       layout.setContentsMargins(40, 40, 40, 40)
       
       dialog.setStyleSheet("""
           QDialog { background-color: white; }
           QLabel { color: black; background-color: white; }
       """)

       title = QLabel("Valitse toiminto:", dialog)
       title.setAlignment(Qt.AlignCenter)
       title.setFont(QFont("Arial", 20))
       layout.addWidget(title)
       
       buttons_layout = QVBoxLayout()
       buttons_layout.setSpacing(15)
       
       raspberry_btn = QPushButton("Sammuta Raspberry Pi")
       restart_btn = QPushButton("Käynnistä ohjelma uudelleen")
       close_btn = QPushButton("Sammuta ohjelma")
       cancel_btn = QPushButton("Peruuta")
       
       buttons = [raspberry_btn, restart_btn, close_btn, cancel_btn]
       
       for btn in buttons:
           btn.setFixedHeight(50)
           btn.setStyleSheet("""
               QPushButton {
                   background-color: #f0f0f0;
                   color: black;
                   border-radius: 5px;
                   padding: 10px;
                   font-size: 16px;
                   border: 1px solid #ccc;
               }
               QPushButton:hover {
                   background-color: #e0e0e0;
               }
           """)
           buttons_layout.addWidget(btn)
       
       layout.addLayout(buttons_layout)
       
       result_value = None
       
       def set_result(value):
           nonlocal result_value
           result_value = value
           dialog.accept()
       
       raspberry_btn.clicked.connect(lambda: set_result("raspberry"))
       restart_btn.clicked.connect(lambda: set_result("restart"))
       close_btn.clicked.connect(lambda: set_result("close"))
       cancel_btn.clicked.connect(lambda: set_result("cancel"))
       
       dialog.exec_()
       
       if result_value == "raspberry":
           self.status_message.setText("Sammutetaan Raspberry Pi...")
           import os
           os.system("sudo shutdown -h now")
       elif result_value == "restart":
           self.status_message.setText("Käynnistetään ohjelma uudelleen...")
           self.parent().close()
           import os
           import sys
           os.execv(sys.executable, ['python'] + sys.argv)
       elif result_value == "close":
           self.status_message.setText("Sammutetaan ohjelma...")
           self.parent().close()

   def closeEvent(self, event):
       self.update_timer.stop()
       super().closeEvent(event)