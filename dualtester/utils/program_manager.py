# utils/program_manager.py
import json
import os

from PyQt5.QtCore import QObject, pyqtSignal


class ProgramManager(QObject):
    """Lataa ainoastaan todelliset, tarkastettavissa olevat testiohjelmat."""

    program_list_updated = pyqtSignal(list)

    def __init__(self, config_path=None):
        super().__init__()

        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..")
        )

        if config_path is None:
            config_path = "config/programs.json"

        self.config_path = (
            config_path if os.path.isabs(config_path)
            else os.path.join(project_root, config_path)
        )
        print(f"Ohjelmalista ladataan tiedostosta: {self.config_path}")

        self.programs = []
        self.program_data = {"programs": []}
        self.load_programs()

    def load_programs(self):
        """Älä koskaan keksi oletusohjelmia, jos tuotantodata puuttuu."""
        self.programs = []
        self.program_data = {"programs": []}

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            entries = data.get("programs") if isinstance(data, dict) else None
            if not isinstance(entries, list):
                raise ValueError("programs-taulukko puuttuu")

            program_ids = set()
            for program in entries:
                if not isinstance(program, dict):
                    raise ValueError("Ohjelmarivi ei ole JSON-objekti")

                program_id = program.get("id")
                if not isinstance(program_id, int) or isinstance(program_id, bool) or program_id <= 0:
                    raise ValueError(f"Virheellinen ohjelma-ID: {program_id}")

                if program_id in program_ids:
                    raise ValueError(f"Duplikaatti ohjelma-ID: {program_id}")

                name = program.get("name")
                if not isinstance(name, str) or not name.strip():
                    raise ValueError(f"Ohjelman {program_id} nimi puuttuu")

                program_ids.add(program_id)

            self.program_data = data
            self.programs = [
                program["name"]
                for program in entries
            ]
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            print(
                f"VAKAVA: testiohjelmia ei ladattu tiedostosta "
                f"{self.config_path}: {exc}"
            )

        self.program_list_updated.emit(self.programs)

    def get_program_list(self):
        return self.programs

    def get_program_name(self, index):
        if 0 <= index < len(self.programs):
            return self.programs[index]
        return "Ei ohjelmaa"

    def get_program_description(self, index):
        programs = self.program_data.get("programs", [])
        if 0 <= index < len(programs):
            return programs[index].get("description", "")
        return ""

    def get_program_id(self, index):
        programs = self.program_data.get("programs", [])
        if 0 <= index < len(programs):
            return programs[index]["id"]
        return None

    def get_program_by_index(self, index):
        programs = self.program_data.get("programs", [])
        if 0 <= index < len(programs):
            return programs[index]
        return None
