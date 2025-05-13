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
        self.program_data = {}  # Tallennetaan koko ohjelmatiedot
        self.load_programs()
    
    def load_programs(self):
        """Lataa ohjelmat konfiguraatiotiedostosta"""
        try:
            # Varmista että config-kansio on olemassa
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'programs' in data and isinstance(data['programs'], list):
                        self.program_data = data
                        # Muodosta ohjelmalista näyttöä varten
                        self.programs = []
                        for prog in data['programs']:
                            program_name = prog.get('name', f"Ohjelma {prog.get('id', 0)}")
                            self.programs.append(program_name)
            else:
                # Jos tiedostoa ei ole, luodaan oletuslista
                self.programs = [f"Ohjelma {i}" for i in range(1, 51)]
                self._create_default_config()
            
            self.program_list_updated.emit(self.programs)
        except Exception as e:
            print(f"Virhe ohjelmien latauksessa: {e}")
            self.programs = [f"Ohjelma {i}" for i in range(1, 51)]
            self.program_list_updated.emit(self.programs)
    
    def _create_default_config(self):
        """Luo oletuskonfiguraatio jos tiedostoa ei ole"""
        default_programs = {
            "programs": [
                {"id": i, "name": f"Ohjelma {i}", "description": ""} 
                for i in range(1, 51)
            ],
            "last_updated": "2025-05-13",
            "version": "1.0.0"
        }
        
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_programs, f, ensure_ascii=False, indent=2)
            self.program_data = default_programs
        except Exception as e:
            print(f"Virhe oletuskonfiguraation luonnissa: {e}")
    
    def get_program_list(self):
        """Palauta ohjelmien lista"""
        return self.programs
    
    def get_program_name(self, index):
        """Palauta ohjelman nimi indeksin perusteella"""
        if 0 <= index < len(self.programs):
            return self.programs[index]
        return f"Ohjelma {index + 1}"
    
    def get_program_description(self, index):
        """Palauta ohjelman kuvaus indeksin perusteella"""
        if 'programs' in self.program_data and index < len(self.program_data['programs']):
            return self.program_data['programs'][index].get('description', '')
        return ""
        
    def get_program_id(self, index):
        """Palauta ohjelman ID indeksin perusteella"""
        if 'programs' in self.program_data and index < len(self.program_data['programs']):
            return self.program_data['programs'][index].get('id', index + 1)
        return index + 1