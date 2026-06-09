# ui/screens/settings_screen.py
from PyQt5.QtWidgets import QPushButton, QLabel, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from ui.screens.base_screen import BaseScreen


class SettingsScreen(BaseScreen):
    """
    Asetussivu.

    Tällä sivulla näytetään laiteyhteyksien tilat ja jätetään näkyviin vain
    ForTest-ohjelmien hallintaan liittyvät painikkeet.
    """

    STATUS_STYLE = """
        QLabel {{
            color: {color};
            background-color: #101010;
            border: 2px solid #333333;
            border-radius: 10px;
        }}
    """

    PANEL_STYLE = """
        QFrame {
            background-color: #050505;
            border: 2px solid #333333;
            border-radius: 10px;
        }
    """

    TITLE_STYLE = """
        color: white;
        background: transparent;
        border: none;
    """

    def __init__(self, parent=None):
        super().__init__(parent)

    def init_ui(self):
        self.setStyleSheet("background-color: black;")

        screen_w = self.parent().screen_width if self.parent() else 1920
        screen_h = self.parent().screen_height if self.parent() else 1080

        self.back_button = QPushButton("← TAKAISIN", self)
        self.back_button.setGeometry(20, 20, 180, 65)
        self.back_button.setFont(QFont("Arial", 16, QFont.Bold))
        self.back_button.setStyleSheet(self._button_style("#2196F3", "#1976D2"))
        self.back_button.clicked.connect(self.go_back)

        self.title_label = QLabel("ASETUKSET", self)
        self.title_label.setGeometry(230, 20, screen_w - 460, 65)
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setFont(QFont("Arial", 32, QFont.Bold))
        self.title_label.setStyleSheet(self.TITLE_STYLE)

        self.connection_status_label = QLabel("", self)
        self.connection_status_label.setGeometry(20, 100, screen_w - 40, 70)
        self.connection_status_label.setAlignment(Qt.AlignCenter)
        self.connection_status_label.setFont(QFont("Consolas", 17))
        self.connection_status_label.setStyleSheet(self.STATUS_STYLE.format(color="#33FF33"))

        left_panel_x = 50
        right_panel_x = 985
        panel_y = 195
        panel_w = 885
        panel_h = 610

        self.fortest1_connection_label = None
        self.fortest2_connection_label = None

        self.fortest1_panel = self._create_fortest_panel(
            station_id=1,
            title="FORTEST 1 OHJELMAT",
            x=left_panel_x,
            y=panel_y,
            w=panel_w,
            h=panel_h,
        )

        self.fortest2_panel = self._create_fortest_panel(
            station_id=2,
            title="FORTEST 2 OHJELMAT",
            x=right_panel_x,
            y=panel_y,
            w=panel_w,
            h=panel_h,
        )

        self.status_label = QLabel("Valitse asetustoiminto", self)
        self.status_label.setGeometry(20, screen_h - 110, screen_w - 40, 70)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Consolas", 18))
        self._set_status("Valitse asetustoiminto", "white")

        self.refresh()

    def _create_fortest_panel(self, station_id, title, x, y, w, h):
        panel = QFrame(self)
        panel.setGeometry(x, y, w, h)
        panel.setStyleSheet(self.PANEL_STYLE)

        title_label = QLabel(title, panel)
        title_label.setGeometry(20, 20, w - 40, 50)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 22, QFont.Bold))
        title_label.setStyleSheet(self.TITLE_STYLE)

        connection_label = QLabel("", panel)
        connection_label.setGeometry(30, 85, w - 60, 55)
        connection_label.setAlignment(Qt.AlignCenter)
        connection_label.setFont(QFont("Consolas", 14))
        connection_label.setStyleSheet(self.STATUS_STYLE.format(color="#CCCCCC"))

        if station_id == 1:
            self.fortest1_connection_label = connection_label
        elif station_id == 2:
            self.fortest2_connection_label = connection_label

        button_w = 380
        button_h = 95
        left_x = 55
        right_x = 450
        start_y = 190
        gap_y = 130

        self._create_button(
            parent=panel,
            text="HAE OHJELMAT\nTESTERILTÄ",
            x=left_x,
            y=start_y,
            w=button_w,
            h=button_h,
            callback=lambda checked=False, sid=station_id: self.fetch_programs_placeholder(sid),
        )

        self._create_button(
            parent=panel,
            text="AKTIIVISEN OHJELMAN\nTARKISTUS",
            x=right_x,
            y=start_y,
            w=button_w,
            h=button_h,
            callback=lambda checked=False, sid=station_id: self.read_active_program_placeholder(sid),
        )

        self._create_button(
            parent=panel,
            text="OHJELMAN LUONTI /\nMUOKKAUS",
            x=left_x,
            y=start_y + gap_y,
            w=button_w,
            h=button_h,
            callback=lambda checked=False, sid=station_id: self.program_edit_placeholder(sid),
        )

        return panel

    def _create_button(self, parent, text, x, y, w, h, callback):
        button = QPushButton(text, parent)
        button.setGeometry(x, y, w, h)
        button.setFont(QFont("Arial", 17, QFont.Bold))
        button.setStyleSheet(self._button_style("#555555", "#1976D2"))
        button.clicked.connect(callback)
        return button

    def _button_style(self, bg_color, hover_color):
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border-radius: 10px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:disabled {{
                background-color: #222222;
                color: #777777;
            }}
        """

    def _get_fortest_service(self):
        parent = self.parent()

        if parent and hasattr(parent, "fortest_service"):
            return parent.fortest_service

        return None

    def _get_hardware_service(self):
        parent = self.parent()

        if parent and hasattr(parent, "hardware_service"):
            return parent.hardware_service

        return None

    def _get_connection_text(self, station_id):
        parent = self.parent()

        if not parent or not hasattr(parent, "fortest_service"):
            return f"ForTest {station_id}: yhteystila ei käytettävissä"

        fortest_service = parent.fortest_service

        port = "--"
        if hasattr(fortest_service, "fortest_station_ports"):
            port = fortest_service.fortest_station_ports.get(station_id, "--")

        baudrate = "--"
        if hasattr(fortest_service, "fortest_baudrate"):
            baudrate = fortest_service.fortest_baudrate

        connected = False
        if hasattr(fortest_service, "is_connected"):
            connected = fortest_service.is_connected(station_id)

        state_text = "OK" if connected else "EI YHTEYTTÄ"

        return f"ForTest {station_id}: {state_text}    Portti: {port}    Baud: {baudrate}"

    def _get_main_connection_text(self):
        hardware_service = self._get_hardware_service()
        fortest_service = self._get_fortest_service()

        if hardware_service and hasattr(hardware_service, "get_connection_status_text"):
            hardware_text = hardware_service.get_connection_status_text()
        else:
            hardware_text = "OPTA: EI PALVELUA    GPIO: EI PALVELUA"

        if fortest_service and hasattr(fortest_service, "is_connected"):
            f1_ok = fortest_service.is_connected(1)
            f2_ok = fortest_service.is_connected(2)
            f1_text = "FORTEST 1: OK" if f1_ok else "FORTEST 1: EI YHTEYTTÄ"
            f2_text = "FORTEST 2: OK" if f2_ok else "FORTEST 2: EI YHTEYTTÄ"
            fortest_text = f"{f1_text}    {f2_text}"
        else:
            fortest_text = "FORTEST 1: EI PALVELUA    FORTEST 2: EI PALVELUA"

        return f"{hardware_text}    {fortest_text}"

    def refresh(self):
        self.connection_status_label.setText(self._get_main_connection_text())

        if self.fortest1_connection_label:
            self.fortest1_connection_label.setText(self._get_connection_text(1))

        if self.fortest2_connection_label:
            self.fortest2_connection_label.setText(self._get_connection_text(2))

    def fetch_programs_placeholder(self, station_id):
        self._set_status(
            f"ForTest {station_id}: ohjelmien haku lisätään seuraavassa vaiheessa",
            "orange",
        )

    def read_active_program_placeholder(self, station_id):
        fortest_service = self._get_fortest_service()

        if not fortest_service:
            self._set_status("VIRHE: ForTestService ei ole käytössä", "red")
            return

        if hasattr(fortest_service, "read_status"):
            fortest_service.read_status(station_id)
            self._set_status(
                f"ForTest {station_id}: aktiivisen ohjelman tarkistuspyyntö lähetetty",
                "#33FF33",
            )
        else:
            self._set_status("VIRHE: read_status puuttuu ForTestServicestä", "red")

    def program_edit_placeholder(self, station_id):
        self._set_status(
            f"ForTest {station_id}: ohjelman luonti/muokkaus lisätään lukutestin jälkeen",
            "orange",
        )

    def _set_status(self, message, color):
        self.status_label.setText(message)
        self.status_label.setStyleSheet(self.STATUS_STYLE.format(color=color))

    def go_back(self):
        if hasattr(self.parent(), "show_testing"):
            self.parent().show_testing()

    def cleanup(self):
        pass
