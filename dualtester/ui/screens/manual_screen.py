# ui/screens/manual_screen.py
from PyQt5.QtWidgets import QPushButton, QLabel, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.screens.base_screen import BaseScreen


class ManualScreen(BaseScreen):
    """
    Käsikäyttösivu.

    Tämä näkymä ei käytä enää suoraan parent().modbus_manageria.
    Releohjaukset menevät HardwareService-luokan kautta.
    """

    def __init__(self, parent=None, modbus=None):
        self.relay_buttons = []
        self.relay_states = [False] * 8
        super().__init__(parent)

    def init_ui(self):
        self.setStyleSheet("background-color: black;")

        screen_w = self.parent().screen_width if self.parent() else 1920
        screen_h = self.parent().screen_height if self.parent() else 1080

        # Koordinaatit
        back_x = 20
        back_y = 20
        back_w = 180
        back_h = 65

        title_x = 230
        title_y = 20
        title_w = screen_w - 460
        title_h = 65

        status_x = 20
        status_y = 100
        status_w = screen_w - 40
        status_h = 55

        panel_x = 50
        panel_y = 185
        panel_w = screen_w - 100
        panel_h = 560

        button_w = 320
        button_h = 130
        button_gap_x = 45
        button_gap_y = 55
        button_start_x = 55
        button_start_y = 55

        bottom_status_x = 20
        bottom_status_y = screen_h - 110
        bottom_status_w = screen_w - 40
        bottom_status_h = 70

        self.back_button = QPushButton("← TAKAISIN", self)
        self.back_button.setGeometry(back_x, back_y, back_w, back_h)
        self.back_button.setFont(QFont("Arial", 16, QFont.Bold))
        self.back_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.back_button.clicked.connect(self.go_back)

        self.title_label = QLabel("KÄSIKÄYTTÖ", self)
        self.title_label.setGeometry(title_x, title_y, title_w, title_h)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Arial", 32, QFont.Bold))
        self.title_label.setStyleSheet("color: white; background: transparent; border: none;")

        self.connection_label = QLabel("", self)
        self.connection_label.setGeometry(status_x, status_y, status_w, status_h)
        self.connection_label.setAlignment(Qt.AlignCenter)
        self.connection_label.setFont(QFont("Consolas", 17))
        self.connection_label.setStyleSheet("""
            QLabel {
                color: #33FF33;
                background-color: #101010;
                border: 2px solid #333333;
                border-radius: 10px;
            }
        """)

        self.relay_panel = QFrame(self)
        self.relay_panel.setGeometry(panel_x, panel_y, panel_w, panel_h)
        self.relay_panel.setStyleSheet("""
            QFrame {
                background-color: #050505;
                border: 2px solid #333333;
                border-radius: 10px;
            }
        """)

        self.relay_buttons = []

        for i in range(8):
            row = i // 4
            col = i % 4

            x = button_start_x + col * (button_w + button_gap_x)
            y = button_start_y + row * (button_h + button_gap_y)

            btn = QPushButton(f"RELE {i + 1}\nPOIS", self.relay_panel)
            btn.setGeometry(x, y, button_w, button_h)
            btn.setFont(QFont("Arial", 22, QFont.Bold))
            btn.clicked.connect(lambda checked, idx=i: self.toggle_relay_button(idx))

            self.relay_buttons.append(btn)
            self._update_relay_button_style(i)

        self.relay_status_label = QLabel("Valitse rele käsikäyttöä varten", self)
        self.relay_status_label.setGeometry(
            bottom_status_x,
            bottom_status_y,
            bottom_status_w,
            bottom_status_h
        )
        self.relay_status_label.setAlignment(Qt.AlignCenter)
        self.relay_status_label.setFont(QFont("Consolas", 18))
        self.relay_status_label.setStyleSheet("""
            QLabel {
                color: white;
                background-color: #101010;
                border: 2px solid #333333;
                border-radius: 10px;
            }
        """)

        self.update_connection_status()

    def get_hardware_service(self):
        if self.parent() and hasattr(self.parent(), "hardware_service"):
            return self.parent().hardware_service
        return None

    def update_connection_status(self):
        hardware_service = self.get_hardware_service()

        if hardware_service and hasattr(hardware_service, "get_connection_status_text"):
            self.connection_label.setText(hardware_service.get_connection_status_text())
        else:
            self.connection_label.setText("MODBUS: --    GPIO: --    ANTURI: --")

    def toggle_relay_button(self, index):
        relay_num = index + 1
        old_state = self.relay_states[index]
        new_state = not old_state

        hardware_service = self.get_hardware_service()

        if not hardware_service:
            self.relay_status_label.setText("VIRHE: HardwareService ei ole käytössä")
            self.relay_status_label.setStyleSheet("""
                QLabel {
                    color: red;
                    background-color: #101010;
                    border: 2px solid #333333;
                    border-radius: 10px;
                }
            """)
            return

        success, message = hardware_service.control_relay(relay_num, new_state)

        if success:
            self.relay_states[index] = new_state
            self._update_relay_button_style(index)
            self.relay_status_label.setText(message)
            self.relay_status_label.setStyleSheet("""
                QLabel {
                    color: #33FF33;
                    background-color: #101010;
                    border: 2px solid #333333;
                    border-radius: 10px;
                }
            """)
        else:
            self.relay_states[index] = old_state
            self._update_relay_button_style(index)
            self.relay_status_label.setText(message)
            self.relay_status_label.setStyleSheet("""
                QLabel {
                    color: red;
                    background-color: #101010;
                    border: 2px solid #333333;
                    border-radius: 10px;
                }
            """)

        self.update_connection_status()

    def _update_relay_button_style(self, index):
        if index < 0 or index >= len(self.relay_buttons):
            return

        state = self.relay_states[index]
        btn = self.relay_buttons[index]

        if state:
            btn.setText(f"RELE {index + 1}\nPÄÄLLÄ")
            bg_color = "#0B7A28"
        else:
            btn.setText(f"RELE {index + 1}\nPOIS")
            bg_color = "#555555"

        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border-radius: 10px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #1976D2;
            }}
        """)

    def go_back(self):
        if hasattr(self.parent(), "show_testing"):
            self.parent().show_testing()

    def cleanup(self):
        pass