# ui/components/fortest_station.py
from PyQt5.QtWidgets import QFrame, QLabel, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


PROGRAM_BOX_X = 20
PROGRAM_BOX_Y = 15
PROGRAM_BOX_W = 880
PROGRAM_BOX_H = 200

STATION_TITLE_X = 15
STATION_TITLE_Y = 10
STATION_TITLE_W = 650
STATION_TITLE_H = 35

TEMP_BUTTON_X = PROGRAM_BOX_W - 125
TEMP_BUTTON_Y = 10
TEMP_BUTTON_W = 100
TEMP_BUTTON_H = 36

PROGRAM_TITLE_X = 15
PROGRAM_TITLE_Y = 50
PROGRAM_TITLE_W = 850
PROGRAM_TITLE_H = 35

PROGRAM_DESC_X = 15
PROGRAM_DESC_Y = 85
PROGRAM_DESC_W = 850
PROGRAM_DESC_H = 28

PROGRAM_INFO_X = 15
PROGRAM_INFO_Y = 120
PROGRAM_INFO_W = 850
PROGRAM_INFO_H = 65

STATUS_BOX_X = 20
STATUS_BOX_Y = 230
STATUS_BOX_W = 880
STATUS_BOX_H = 65

STATUS_VALUE_X = 15
STATUS_VALUE_Y = 12
STATUS_VALUE_W = 850
STATUS_VALUE_H = 40

RESULTS_BOX_X = 20
RESULTS_BOX_Y = 310
RESULTS_BOX_W = 880
RESULTS_BOX_H = 490

CLEAR_RESULTS_X = RESULTS_BOX_X + RESULTS_BOX_W - 150
CLEAR_RESULTS_Y = RESULTS_BOX_Y + RESULTS_BOX_H - 52
CLEAR_RESULTS_W = 125
CLEAR_RESULTS_H = 38

JIG_PART_RELEASE_X = 245
JIG_PART_RELEASE_Y = 815
JIG_PART_RELEASE_W = 205
JIG_PART_RELEASE_H = 65

JIG_PART_CLAMP_X = 20
JIG_PART_CLAMP_Y = 815
JIG_PART_CLAMP_W = 205
JIG_PART_CLAMP_H = 65

JIG_PART_REMOVE_X = 470
JIG_PART_REMOVE_Y = 815
JIG_PART_REMOVE_W = 205
JIG_PART_REMOVE_H = 65

AUTO_PART_CHANGE_X = 695
AUTO_PART_CHANGE_Y = 815
AUTO_PART_CHANGE_W = 205
AUTO_PART_CHANGE_H = 65

SELECT_PROGRAM_X = 20
SELECT_PROGRAM_Y = 900
SELECT_PROGRAM_W = 280
SELECT_PROGRAM_H = 75

START_X = 330
START_Y = 900
START_W = 250
START_H = 75

STOP_X = 610
STOP_Y = 900
STOP_W = 290
STOP_H = 75

DEV_RESULT_X = 375
DEV_RESULT_Y = 720
DEV_RESULT_W = 160
DEV_RESULT_H = 60

FONT_STATION_TITLE = ("Consolas", 18)
FONT_STATUS = ("Consolas", 18)
FONT_PROGRAM_TITLE = ("Consolas", 18)
FONT_PROGRAM_DESC = ("Consolas", 13)
FONT_PROGRAM_INFO = ("Consolas", 14)
FONT_RESULTS = ("Consolas", 15)
FONT_BUTTON = ("Arial", 18)
FONT_START_STOP = ("Arial", 22)
FONT_JIG_BUTTON = ("Arial", 15)
FONT_DEV_BUTTON = ("Arial", 15)
FONT_CLEAR_BUTTON = ("Arial", 11)
FONT_TEMP_BUTTON = ("Arial", 12)


class ForTestStation(QFrame):
    def __init__(self, station_id, parent=None):
        super().__init__(parent)

        self.station_id = station_id
        self.results_history = []
        self.part_temperature_enabled = False

        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #050505;
                border: 0px solid #bfbfbf;
                border-radius: 0px;
            }
        """)

        self.program_box = QFrame(self)
        self.program_box.setGeometry(PROGRAM_BOX_X, PROGRAM_BOX_Y, PROGRAM_BOX_W, PROGRAM_BOX_H)
        self.program_box.setStyleSheet("""
            QFrame {
                background-color: black;
                border: 1px solid #333333;
                border-radius: 10px;
            }
        """)

        self.station_title_label = QLabel(f"FORTEST {self.station_id}", self.program_box)
        self.station_title_label.setGeometry(
            STATION_TITLE_X,
            STATION_TITLE_Y,
            STATION_TITLE_W,
            STATION_TITLE_H,
        )
        self.station_title_label.setFont(
            QFont(FONT_STATION_TITLE[0], FONT_STATION_TITLE[1], QFont.Bold)
        )
        self.station_title_label.setStyleSheet(
            "color: white; background: transparent; border: none;"
        )
        self.station_title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.part_temperature_button = QPushButton("LÄMPÖ", self.program_box)
        self.part_temperature_button.setGeometry(
            TEMP_BUTTON_X,
            TEMP_BUTTON_Y,
            TEMP_BUTTON_W,
            TEMP_BUTTON_H,
        )
        self.part_temperature_button.setFont(
            QFont(FONT_TEMP_BUTTON[0], FONT_TEMP_BUTTON[1], QFont.Bold)
        )
        self.part_temperature_button.clicked.connect(self.toggle_part_temperature_enabled)
        self.set_part_temperature_enabled(False)

        self.program_label = QLabel("OHJELMA: --", self.program_box)
        self.program_label.setGeometry(
            PROGRAM_TITLE_X,
            PROGRAM_TITLE_Y,
            PROGRAM_TITLE_W,
            PROGRAM_TITLE_H,
        )
        self.program_label.setFont(
            QFont(FONT_PROGRAM_TITLE[0], FONT_PROGRAM_TITLE[1], QFont.Bold)
        )
        self.program_label.setStyleSheet(
            "color: #ffffff; background: transparent; border: none;"
        )

        self.program_desc_label = QLabel("", self.program_box)
        self.program_desc_label.setGeometry(
            PROGRAM_DESC_X,
            PROGRAM_DESC_Y,
            PROGRAM_DESC_W,
            PROGRAM_DESC_H,
        )
        self.program_desc_label.setFont(
            QFont(FONT_PROGRAM_DESC[0], FONT_PROGRAM_DESC[1])
        )
        self.program_desc_label.setStyleSheet(
            "color: #ffffff; background: transparent; border: none;"
        )

        self.program_info_label = QLabel(
            "PAINE: --     TILAVUUS: --     TÄYTTÖ: --     TASAUS: --     TESTI: --     RAJA: --",
            self.program_box,
        )
        self.program_info_label.setGeometry(
            PROGRAM_INFO_X,
            PROGRAM_INFO_Y,
            PROGRAM_INFO_W,
            PROGRAM_INFO_H,
        )
        self.program_info_label.setFont(
            QFont(FONT_PROGRAM_INFO[0], FONT_PROGRAM_INFO[1])
        )
        self.program_info_label.setWordWrap(True)
        self.program_info_label.setStyleSheet(
            "color: #ffffff; background: transparent; border: none;"
        )

        self.status_box = QFrame(self)
        self.status_box.setGeometry(STATUS_BOX_X, STATUS_BOX_Y, STATUS_BOX_W, STATUS_BOX_H)
        self.status_box.setStyleSheet("""
            QFrame {
                background-color: black;
                border: 1px solid #333333;
                border-radius: 10px;
            }
        """)

        self.status_label = QLabel("VALITSE OHJELMA", self.status_box)
        self.status_label.setGeometry(
            STATUS_VALUE_X,
            STATUS_VALUE_Y,
            STATUS_VALUE_W,
            STATUS_VALUE_H,
        )
        self.status_label.setFont(
            QFont(FONT_STATUS[0], FONT_STATUS[1], QFont.Bold)
        )
        self.status_label.setStyleSheet(
            "color: orange; background: transparent; border: none;"
        )
        self.status_label.setAlignment(Qt.AlignCenter)

        self.results_box = QLabel("", self)
        self.results_box.setGeometry(RESULTS_BOX_X, RESULTS_BOX_Y, RESULTS_BOX_W, RESULTS_BOX_H)
        self.results_box.setFont(QFont(FONT_RESULTS[0], FONT_RESULTS[1]))
        self.results_box.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.results_box.setTextFormat(Qt.RichText)
        self.results_box.setStyleSheet("""
            QLabel {
                background-color: black;
                color: white;
                border: 1px solid #444444;
                border-radius: 10px;
                padding: 12px;
            }
        """)
        self._refresh_results_table()

        self.clear_results_button = QPushButton("TYHJENNÄ", self)
        self.clear_results_button.setGeometry(
            CLEAR_RESULTS_X,
            CLEAR_RESULTS_Y,
            CLEAR_RESULTS_W,
            CLEAR_RESULTS_H,
        )
        self.clear_results_button.setFont(
            QFont(FONT_CLEAR_BUTTON[0], FONT_CLEAR_BUTTON[1], QFont.Bold)
        )
        self.clear_results_button.setStyleSheet("""
            QPushButton {
                background-color: #303030;
                color: #DDDDDD;
                border-radius: 8px;
                border: 1px solid #666666;
            }
            QPushButton:hover {
                background-color: #555555;
            }
            QPushButton:pressed {
                background-color: #777777;
            }
        """)
        self.clear_results_button.clicked.connect(self.clear_results)

        jig_button_style = """
            QPushButton {
                background-color: #6A3D9A;
                color: white;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #8E5CC2;
            }
            QPushButton:disabled {
                background-color: #333333;
                color: #777777;
            }
        """

        self.jig_part_release_button = QPushButton("KAPPALE\nIRTI", self)
        self.jig_part_release_button.setGeometry(
            JIG_PART_RELEASE_X,
            JIG_PART_RELEASE_Y,
            JIG_PART_RELEASE_W,
            JIG_PART_RELEASE_H,
        )
        self.jig_part_release_button.setFont(
            QFont(FONT_JIG_BUTTON[0], FONT_JIG_BUTTON[1], QFont.Bold)
        )
        self.jig_part_release_button.setStyleSheet(jig_button_style)
        self.jig_part_release_button.hide()

        self.jig_part_clamp_button = QPushButton("KAPPALE\nKIINNI", self)
        self.jig_part_clamp_button.setGeometry(
            JIG_PART_CLAMP_X,
            JIG_PART_CLAMP_Y,
            JIG_PART_CLAMP_W,
            JIG_PART_CLAMP_H,
        )
        self.jig_part_clamp_button.setFont(
            QFont(FONT_JIG_BUTTON[0], FONT_JIG_BUTTON[1], QFont.Bold)
        )
        self.jig_part_clamp_button.setStyleSheet(jig_button_style)
        self.jig_part_clamp_button.hide()

        self.jig_part_remove_button = QPushButton("KAPPALEEN\nPOISTO", self)
        self.jig_part_remove_button.setGeometry(
            JIG_PART_REMOVE_X,
            JIG_PART_REMOVE_Y,
            JIG_PART_REMOVE_W,
            JIG_PART_REMOVE_H,
        )
        self.jig_part_remove_button.setFont(
            QFont(FONT_JIG_BUTTON[0], FONT_JIG_BUTTON[1], QFont.Bold)
        )
        self.jig_part_remove_button.setStyleSheet(jig_button_style)
        self.jig_part_remove_button.hide()

        self.auto_part_change_button = QPushButton("AUTOMAATTI\nOFF", self)
        self.auto_part_change_button.setGeometry(
            AUTO_PART_CHANGE_X,
            AUTO_PART_CHANGE_Y,
            AUTO_PART_CHANGE_W,
            AUTO_PART_CHANGE_H,
        )
        self.auto_part_change_button.setFont(
            QFont(FONT_JIG_BUTTON[0], FONT_JIG_BUTTON[1], QFont.Bold)
        )
        self.auto_part_change_button.hide()
        self.set_auto_part_change_enabled_state(False)

        self.select_program_button = QPushButton("VALITSE OHJELMA", self)
        self.select_program_button.setGeometry(
            SELECT_PROGRAM_X,
            SELECT_PROGRAM_Y,
            SELECT_PROGRAM_W,
            SELECT_PROGRAM_H,
        )
        self.select_program_button.setFont(
            QFont(FONT_BUTTON[0], FONT_BUTTON[1], QFont.Bold)
        )
        self.select_program_button.setStyleSheet("""
            QPushButton {
                background-color: #074678;
                color: white;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)

        self.start_button = QPushButton("START", self)
        self.start_button.setGeometry(START_X, START_Y, START_W, START_H)
        self.start_button.setFont(
            QFont(FONT_START_STOP[0], FONT_START_STOP[1], QFont.Bold)
        )
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #0B7A28;
                color: white;
                border-radius: 10px;
                border: none;
            }
            QPushButton:disabled {
                background-color: #333333;
                color: #777777;
            }
        """)

        self.stop_button = QPushButton("STOP", self)
        self.stop_button.setGeometry(STOP_X, STOP_Y, STOP_W, STOP_H)
        self.stop_button.setFont(
            QFont(FONT_START_STOP[0], FONT_START_STOP[1], QFont.Bold)
        )
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #A00000;
                color: white;
                border-radius: 10px;
                border: none;
            }
            QPushButton:disabled {
                background-color: #333333;
                color: #777777;
            }
        """)

        self.dev_result_button = QPushButton("DEV TULOS", self)
        self.dev_result_button.setGeometry(
            DEV_RESULT_X,
            DEV_RESULT_Y,
            DEV_RESULT_W,
            DEV_RESULT_H,
        )
        self.dev_result_button.setFont(
            QFont(FONT_DEV_BUTTON[0], FONT_DEV_BUTTON[1], QFont.Bold)
        )
        self.dev_result_button.setStyleSheet("""
            QPushButton {
                background-color: #555555;
                color: white;
                border-radius: 10px;
                border: none;
            }
            QPushButton:hover {
                background-color: #777777;
            }
        """)
        self.dev_result_button.hide()

        self.update_running_state(False, False)

    def toggle_part_temperature_enabled(self):
        self.set_part_temperature_enabled(not self.part_temperature_enabled)

    def set_part_temperature_enabled(self, enabled):
        self.part_temperature_enabled = bool(enabled)

        if self.part_temperature_enabled:
            self.part_temperature_button.setStyleSheet("""
                QPushButton {
                    background-color: #0B7A28;
                    color: white;
                    border-radius: 8px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #10A838;
                }
            """)
        else:
            self.part_temperature_button.setStyleSheet("""
                QPushButton {
                    background-color: #555555;
                    color: #DDDDDD;
                    border-radius: 8px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #777777;
                }
            """)

    def is_part_temperature_enabled(self):
        return bool(self.part_temperature_enabled)

    def update_program_info(
        self,
        display_name,
        description,
        pressure,
        volume,
        fill_time,
        settle_time,
        test_time,
        decay_text,
    ):
        self.program_label.setText(f"OHJELMA: {display_name}")
        self.program_desc_label.setText(description)

        self.program_info_label.setText(
            f"PAINE: {pressure} mbar     "
            f"TILAVUUS: {volume} ml     "
            f"TÄYTTÖ: {fill_time}s     "
            f"TASAUS: {settle_time}s     "
            f"TESTI: {test_time}s     "
            f"RAJA: {decay_text}"
        )

    def update_status(self, message, level="INFO"):
        color = "#33FF33"

        if level == "ERROR":
            color = "red"
        elif level == "WARNING":
            color = "orange"
        elif level == "SUCCESS":
            color = "#00FF00"
        elif level == "INFO":
            color = "#33CCFF"

        self.status_label.setStyleSheet(
            f"color: {color}; background: transparent; border: none;"
        )
        self.status_label.setText(message)

    def update_running_state(self, is_running, ready):
        if is_running:
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        else:
            self.start_button.setEnabled(bool(ready))
            self.stop_button.setEnabled(False)

    def set_jig_controls_visible(self, visible):
        visible = bool(visible)

        self.jig_part_release_button.setVisible(visible)
        self.jig_part_clamp_button.setVisible(visible)
        self.jig_part_remove_button.setVisible(visible)

    def set_jig_controls_enabled(self, enabled):
        enabled = bool(enabled)

        self.jig_part_release_button.setEnabled(enabled)
        self.jig_part_clamp_button.setEnabled(enabled)
        self.jig_part_remove_button.setEnabled(enabled)

    def set_auto_part_change_visible(self, visible):
        self.auto_part_change_button.setVisible(bool(visible))

    def set_auto_part_change_enabled_state(self, enabled):
        enabled = bool(enabled)

        if enabled:
            self.auto_part_change_button.setText("AUTOMAATTI\nON")
            self.auto_part_change_button.setStyleSheet("""
                QPushButton {
                    background-color: #0B7A28;
                    color: white;
                    border-radius: 10px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #10A838;
                }
                QPushButton:disabled {
                    background-color: #333333;
                    color: #777777;
                }
            """)
        else:
            self.auto_part_change_button.setText("AUTOMAATTI\nOFF")
            self.auto_part_change_button.setStyleSheet("""
                QPushButton {
                    background-color: #555555;
                    color: white;
                    border-radius: 10px;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #777777;
                }
                QPushButton:disabled {
                    background-color: #333333;
                    color: #777777;
                }
            """)

    def set_jig_part_clamp_visible(self, visible):
        self.set_jig_controls_visible(visible)

    def set_jig_part_clamp_enabled(self, enabled):
        self.set_jig_controls_enabled(enabled)

    def add_result_row(
        self,
        display_time,
        program_text,
        decay_text,
        result_text,
        result_color,
        room_temp_text,
        part_temp_text,
    ):
        new_result = {
            "display_time": display_time,
            "program_text": program_text,
            "decay_text": decay_text,
            "result_text": result_text,
            "result_color": result_color,
            "room_temp_text": room_temp_text,
            "part_temp_text": part_temp_text,
        }

        self.results_history.insert(0, new_result)

        if len(self.results_history) > 12:
            self.results_history.pop()

        self._refresh_results_table()

    def clear_results(self):
        self.results_history.clear()
        self._refresh_results_table()

    def _build_result_row(self, result, is_latest):
        display_time = result["display_time"]
        program_text = result["program_text"]
        decay_text = result["decay_text"]
        result_text = result["result_text"]
        result_color = result["result_color"]
        room_temp_text = result["room_temp_text"]
        part_temp_text = result["part_temp_text"]

        if is_latest:
            cell_style = " bgcolor=\"#303030\""
            return f"""
            <tr>
                <td{cell_style}><b>- {display_time}</b></td>
                <td{cell_style}><b>{program_text}</b></td>
                <td{cell_style}><b><span style="color:{result_color};">{decay_text}</span></b></td>
                <td{cell_style}><b><span style="color:{result_color};">{result_text}</span></b></td>
                <td{cell_style}><b>{room_temp_text}</b></td>
                <td{cell_style}><b>{part_temp_text} -</b></td>
            </tr>
            """

        return f"""
        <tr>
            <td>{display_time}</td>
            <td>{program_text}</td>
            <td><span style="color:{result_color};">{decay_text}</span></td>
            <td><span style="color:{result_color};">{result_text}</span></td>
            <td>{room_temp_text}</td>
            <td>{part_temp_text}</td>
        </tr>
        """

    def _refresh_results_table(self):
        result_rows = []

        for index, result in enumerate(self.results_history):
            result_rows.append(self._build_result_row(result, index == 0))

        display_html = f"""
        <table width="100%" cellspacing="0" cellpadding="6">
            <tr style="color:#888888; font-size:18px;">
                <td>AIKA</td>
                <td>OHJELMA</td>
                <td>VUOTO</td>
                <td>TULOS</td>
                <td>HUONE</td>
                <td>KAPPALE</td>
            </tr>
            {''.join(result_rows)}
        </table>
        """

        self.results_box.setText(display_html)
