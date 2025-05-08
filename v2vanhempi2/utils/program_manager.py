# utils/program_manager.py
import os
import json
from PyQt5.QtCore import QObject, pyqtSignal

class ProgramManager(QObject):
    """Hallinnoi testiohjelmia"""
    program_list_updated = pyqtSignal(list)
    
    def __init__(self, config_path="config/programs.json"):
        super().__init__()
        self.config_path = config_path
        self.programs = []
        self.load_programs()
    
    def load_programs(self):
        """Lataa ohjelmat konfiguraatiotiedostosta"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'programs' in data and isinstance(data['programs'], list):
                        self.programs = data['programs']
            else:
                # Jos tiedostoa ei ole, käytä oletusnimiä
                self.programs = [f"Ohjelma {i}" for i in range(1, 31)]
            
            self.program_list_updated.emit(self.programs)
        except Exception as e:
            print(f"Virhe ohjelmien latauksessa: {e}")
            self.programs = [f"Ohjelma {i}" for i in range(1, 31)]
            self.program_list_updated.emit(self.programs)
    
    def get_program_list(self):
        """Palauta ohjelmien lista"""
        return self.programs
    
    def get_program_name(self, index):
        """Palauta ohjelman nimi indeksin perusteella"""
        if 0 <= index < len(self.programs):
            return self.programs[index]
        return f"Ohjelma {index + 1}"