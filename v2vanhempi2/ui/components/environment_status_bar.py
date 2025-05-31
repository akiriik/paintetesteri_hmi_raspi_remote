# ui/components/environment_status_bar.py
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

class EnvironmentStatusBar(QWidget):
    """Ympäristötilojen statusrivi (lämpötila ja kosteus)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
        self.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                border-top: 1px solid #34495e;
            }
        """)
        
        self.init_ui()
        
        # Tietojen päivitysajastin
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.request_sensor_update)
        self.update_timer.start(500)  # 500ms välein
        
    def init_ui(self):
        # Horisontaalinen layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(20)
        
        # Lämpötila-alue
        self.temp_icon = QLabel("🌡️", self)
        self.temp_icon.setFont(QFont("Arial", 12))
        self.temp_icon.setStyleSheet("color: #ecf0f1; background-color: transparent;")
        
        self.temp_label = QLabel("--.-°C", self)
        self.temp_label.setFont(QFont("Consolas", 12, QFont.Bold))
        self.temp_label.setStyleSheet("color: #3498db; background-color: transparent;")
        self.temp_label.setMinimumWidth(60)
        
        # Kosteus-alue
        self.humidity_icon = QLabel("💧", self)
        self.humidity_icon.setFont(QFont("Arial", 12))
        self.humidity_icon.setStyleSheet("color: #ecf0f1; background-color: transparent;")
        
        self.humidity_label = QLabel("--.-%", self)
        self.humidity_label.setFont(QFont("Consolas", 12, QFont.Bold))
        self.humidity_label.setStyleSheet("color: #2ecc71; background-color: transparent;")
        self.humidity_label.setMinimumWidth(60)
        
        # Tila-alue (virheviestit)
        self.status_label = QLabel("Alustetaan anturia...", self)
        self.status_label.setFont(QFont("Arial", 10))
        self.status_label.setStyleSheet("color: #95a5a6; background-color: transparent;")
        
        # Lisää komponentit layoutiin
        layout.addWidget(self.temp_icon)
        layout.addWidget(self.temp_label)
        layout.addWidget(self.humidity_icon)
        layout.addWidget(self.humidity_label)
        layout.addStretch()  # Tyhjä tila keskelle
        layout.addWidget(self.status_label)
    
    def update_sensor_data(self, data):
        """Päivitä anturitiedot"""
        temperature = data.get('temperature')
        humidity = data.get('humidity')
        
        # Päivitä lämpötila
        if temperature is not None:
            # Värikoodaus lämpötilan mukaan
            if temperature < 10:
                color = "#3498db"  # Sininen (kylmä)
            elif temperature < 25:
                color = "#2ecc71"  # Vihreä (normaali)
            elif temperature < 35:
                color = "#f39c12"  # Oranssi (lämmin)
            else:
                color = "#e74c3c"  # Punainen (kuuma)
            
            self.temp_label.setText(f"{temperature:.1f}°C")
            self.temp_label.setStyleSheet(f"color: {color}; background-color: transparent;")
        else:
            self.temp_label.setText("--.-°C")
            self.temp_label.setStyleSheet("color: #e74c3c; background-color: transparent;")
        
        # Päivitä kosteus
        if humidity is not None:
            # Värikoodaus kosteuden mukaan
            if humidity < 30:
                color = "#f39c12"  # Oranssi (kuiva)
            elif humidity < 60:
                color = "#2ecc71"  # Vihreä (normaali)
            elif humidity < 80:
                color = "#3498db"  # Sininen (kostea)
            else:
                color = "#e74c3c"  # Punainen (liian kostea)
            
            self.humidity_label.setText(f"{humidity:.1f}%")
            self.humidity_label.setStyleSheet(f"color: {color}; background-color: transparent;")
        else:
            self.humidity_label.setText("--.-%")
            self.humidity_label.setStyleSheet("color: #e74c3c; background-color: transparent;")
        
        # Päivitä tilatieto onnistumisesta
        if temperature is not None and humidity is not None:
            self.status_label.setText("SHT20 OK")
            self.status_label.setStyleSheet("color: #2ecc71; background-color: transparent;")
        else:
            self.status_label.setText("Anturi virhe")
            self.status_label.setStyleSheet("color: #e74c3c; background-color: transparent;")
    
    def show_sensor_error(self, error_message):
        """Näytä anturivirhe"""
        self.temp_label.setText("ERR")
        self.temp_label.setStyleSheet("color: #e74c3c; background-color: transparent;")
        
        self.humidity_label.setText("ERR")
        self.humidity_label.setStyleSheet("color: #e74c3c; background-color: transparent;")
        
        # Näytä virheviesti, mutta rajoita pituutta
        if len(error_message) > 40:
            error_message = error_message[:37] + "..."
        
        self.status_label.setText(error_message)
        self.status_label.setStyleSheet("color: #e74c3c; background-color: transparent;")
    
    def request_sensor_update(self):
        """Pyydä anturipäivitystä pääikkunalta"""
        # Tämä metodi kutsutaan ajastimesta, ja pääikkuna yhdistää sen omaan metodiinsa
        if hasattr(self.parent(), 'update_environment_sensors'):
            self.parent().update_environment_sensors()
    
    def cleanup(self):
        """Siivoa resurssit"""
        if hasattr(self, 'update_timer') and self.update_timer:
            self.update_timer.stop()