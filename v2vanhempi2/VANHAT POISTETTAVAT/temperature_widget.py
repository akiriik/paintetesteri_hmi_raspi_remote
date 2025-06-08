# ui/components/temperature_widget.py
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class TemperatureWidget(QWidget):
    """Widget lämpötilojen näyttämiseen"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 150)
        self.init_ui()
        
    def init_ui(self):
        # Pääkehys
        self.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                border-radius: 10px;
                border: 2px solid #34495e;
            }
        """)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(5)
        
        # Otsikko
        title = QLabel("🌡️ LÄMPÖTILA", self)
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #ecf0f1; background-color: transparent;")
        layout.addWidget(title)
        
        # Lämpötila-alue
        self.temp_container = QWidget(self)
        self.temp_layout = QVBoxLayout(self.temp_container)
        self.temp_layout.setContentsMargins(5, 0, 5, 0)
        self.temp_layout.setSpacing(3)
        
        # Alkuteksti
        self.status_label = QLabel("Haetaan antureita...", self.temp_container)
        self.status_label.setFont(QFont("Arial", 12))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #bdc3c7; background-color: transparent;")
        self.temp_layout.addWidget(self.status_label)
        
        layout.addWidget(self.temp_container)
        
        # Säilytä viitteet lämpötila-labeleihin
        self.temp_labels = []
    
    def update_temperatures(self, temperatures):
        """Päivitä lämpötilat"""
        # Tyhjennä vanhat labelit
        self.clear_temperature_labels()
        
        if not temperatures:
            self.status_label.setText("Ei antureita")
            self.status_label.show()
            return
        
        # Piilota status label
        self.status_label.hide()
        
        # Luo uudet labelit jokaiselle anturille
        for i, (sensor_id, temp) in enumerate(temperatures.items()):
            # Lyhennä anturi-ID näyttöä varten
            short_id = sensor_id[-6:] if len(sensor_id) > 6 else sensor_id
            
            # Luo horisontaalinen layout lämpötilalle
            temp_row = QWidget(self.temp_container)
            temp_row_layout = QHBoxLayout(temp_row)
            temp_row_layout.setContentsMargins(0, 0, 0, 0)
            temp_row_layout.setSpacing(10)
            
            # Anturi-ID
            id_label = QLabel(f"#{i+1}:", temp_row)
            id_label.setFont(QFont("Arial", 10))
            id_label.setStyleSheet("color: #95a5a6; background-color: transparent;")
            id_label.setFixedWidth(30)
            temp_row_layout.addWidget(id_label)
            
            # Lämpötila-arvo
            if isinstance(temp, (int, float)):
                # Värikoodaus lämpötilan mukaan
                if temp < 10:
                    color = "#3498db"  # Sininen (kylmä)
                elif temp < 25:
                    color = "#2ecc71"  # Vihreä (normaali)
                elif temp < 35:
                    color = "#f39c12"  # Oranssi (lämmin)
                else:
                    color = "#e74c3c"  # Punainen (kuuma)
                
                temp_text = f"{temp:.1f}°C"
            else:
                color = "#e74c3c"  # Punainen virheille
                temp_text = str(temp)
            
            temp_label = QLabel(temp_text, temp_row)
            temp_label.setFont(QFont("Consolas", 12, QFont.Bold))
            temp_label.setStyleSheet(f"color: {color}; background-color: transparent;")
            temp_label.setAlignment(Qt.AlignLeft)
            temp_row_layout.addWidget(temp_label, 1)
            
            # Lisää rivi layoutiin
            self.temp_layout.addWidget(temp_row)
            self.temp_labels.append(temp_row)
            
            # Maksimissaan 3 anturia (tilan vuoksi)
            if i >= 2:
                break
    
    def clear_temperature_labels(self):
        """Tyhjennä vanhat lämpötila-labelit"""
        for label in self.temp_labels:
            label.deleteLater()
        self.temp_labels.clear()
    
    def show_error(self, message):
        """Näytä virheviesti"""
        self.clear_temperature_labels()
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: #e74c3c; background-color: transparent;")
        self.status_label.show()
    
    def show_no_sensors(self):
        """Näytä 'ei antureita' viesti"""
        self.clear_temperature_labels()
        self.status_label.setText("Ei DS18B20 antureita")
        self.status_label.setStyleSheet("color: #95a5a6; background-color: transparent;")
        self.status_label.show()