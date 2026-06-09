# services/result_storage_service.py
import json
import os
import sqlite3
from datetime import datetime


DEFAULT_DATABASE_PATH = "/home/akiriik/painetesteri_hmi/data/test_results.db"


class ResultStorageService:
    """
    Testitulosten pysyvä SQLite-tallennus.

    Tietokanta on yksi paikallinen tiedosto Raspberryllä.
    Jokainen hyväksytty uusi ForTest-tulos tallennetaan omaksi rivikseen.
    """

    def __init__(self, parent=None, database_path=DEFAULT_DATABASE_PATH):
        self.parent = parent
        self.database_path = database_path
        self._ensure_database()

    def _connect(self):
        os.makedirs(os.path.dirname(self.database_path), exist_ok=True)
        connection = sqlite3.connect(self.database_path, timeout=5)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA synchronous=NORMAL")
        return connection

    def _ensure_database(self):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS test_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    timestamp TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,

                    station_id INTEGER NOT NULL,
                    tester_name TEXT NOT NULL,

                    program_number INTEGER,
                    program_name TEXT,
                    product_name TEXT,

                    result_code INTEGER,
                    result_text TEXT,
                    result_ok INTEGER,

                    pressure_mbar REAL,
                    decay_value REAL,
                    decay_unit TEXT,
                    leak_value REAL,
                    leak_unit TEXT,

                    room_temperature_c REAL,
                    room_humidity_percent REAL,
                    tank_temperature_c REAL,
                    tank_humidity_percent REAL,
                    tank_pressure_bar REAL,
                    part_temperature_c REAL,

                    raw_result_json TEXT,

                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_test_results_timestamp
                ON test_results(timestamp)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_test_results_date
                ON test_results(date)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_test_results_station
                ON test_results(station_id)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_test_results_program
                ON test_results(program_number, program_name)
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_test_results_result_ok
                ON test_results(result_ok)
                """
            )

    def save_test_result(self, data):
        if not isinstance(data, dict):
            return False

        timestamp = data.get("timestamp") or datetime.now().isoformat(timespec="seconds")
        date = data.get("date") or timestamp[:10]
        time = data.get("time") or timestamp[11:19]

        raw_result = data.get("raw_result")

        try:
            raw_result_json = json.dumps(raw_result, ensure_ascii=False)
        except Exception:
            raw_result_json = None

        values = {
            "timestamp": timestamp,
            "date": date,
            "time": time,
            "station_id": data.get("station_id"),
            "tester_name": data.get("tester_name"),
            "program_number": data.get("program_number"),
            "program_name": data.get("program_name"),
            "product_name": data.get("product_name"),
            "result_code": data.get("result_code"),
            "result_text": data.get("result_text"),
            "result_ok": data.get("result_ok"),
            "pressure_mbar": data.get("pressure_mbar"),
            "decay_value": data.get("decay_value"),
            "decay_unit": data.get("decay_unit"),
            "leak_value": data.get("leak_value"),
            "leak_unit": data.get("leak_unit"),
            "room_temperature_c": data.get("room_temperature_c"),
            "room_humidity_percent": data.get("room_humidity_percent"),
            "tank_temperature_c": data.get("tank_temperature_c"),
            "tank_humidity_percent": data.get("tank_humidity_percent"),
            "tank_pressure_bar": data.get("tank_pressure_bar"),
            "part_temperature_c": data.get("part_temperature_c"),
            "raw_result_json": raw_result_json,
        }

        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO test_results (
                        timestamp,
                        date,
                        time,
                        station_id,
                        tester_name,
                        program_number,
                        program_name,
                        product_name,
                        result_code,
                        result_text,
                        result_ok,
                        pressure_mbar,
                        decay_value,
                        decay_unit,
                        leak_value,
                        leak_unit,
                        room_temperature_c,
                        room_humidity_percent,
                        tank_temperature_c,
                        tank_humidity_percent,
                        tank_pressure_bar,
                        part_temperature_c,
                        raw_result_json
                    ) VALUES (
                        :timestamp,
                        :date,
                        :time,
                        :station_id,
                        :tester_name,
                        :program_number,
                        :program_name,
                        :product_name,
                        :result_code,
                        :result_text,
                        :result_ok,
                        :pressure_mbar,
                        :decay_value,
                        :decay_unit,
                        :leak_value,
                        :leak_unit,
                        :room_temperature_c,
                        :room_humidity_percent,
                        :tank_temperature_c,
                        :tank_humidity_percent,
                        :tank_pressure_bar,
                        :part_temperature_c,
                        :raw_result_json
                    )
                    """,
                    values,
                )

            return True

        except Exception as e:
            print(f"Tuloksen tallennus epäonnistui SQLiteen: {e}")
            return False

    def cleanup(self):
        pass
