# ui/components/environment_status_bar.py
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

class EnvironmentStatusBar(QWidget):
    """Ympäristötilojen statusrivi (lämpötila, kosteus ja paine)"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(40)
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
        
        # Paine-alue
        self.pressure_icon = QLabel("⚡", self)
        self.pressure_icon.setFont(QFont("Arial", 12))
        self.pressure_icon.setStyleSheet("color: #ecf0f1; background-color: transparent;")
        
        self.pressure_label = QLabel("---- BAR", self)
        self.pressure_label.setFont(QFont("Consolas", 12, QFont.Bold))
        self.pressure_label.setStyleSheet("color: #f39c12; background-color: transparent;")
        self.pressure_label.setMinimumWidth(80)
        
        # Lisää komponentit layoutiin
        layout.addWidget(self.temp_icon)
        layout.addWidget(self.temp_label)
        layout.addWidget(self.humidity_icon)
        layout.addWidget(self.humidity_label)
        layout.addWidget(self.pressure_icon)
        layout.addWidget(self.pressure_label)
        layout.addStretch()  # Tyhjä tila loppuun
    
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
    
    def update_pressure_data(self, pressure_value):
        """Päivitä painetiedot (UINT arvo rekisteristä 19500)"""
        if pressure_value is not None:
            # Skaalaa ADC-arvo bar-painiksi
            # Lineaarinen interpolaatio taulukon perusteella
            pressure_bar = self.convert_adc_to_bar(pressure_value)
            self.pressure_label.setText(f"{pressure_bar:.2f} BAR")
            self.pressure_label.setStyleSheet("color: #f39c12; background-color: transparent;")
        else:
            self.pressure_label.setText("---.- BAR")
            self.pressure_label.setStyleSheet("color: #e74c3c; background-color: transparent;")
    
    def convert_adc_to_bar(self, adc_value):
        """Muuntaa ADC-arvon bar-painiksi lineaarisella interpolaatiolla"""
        # Kalibrointitaulukko (ADC-arvo, bar-paine)
        calibration_table = [
            (3277, 0.0), (4544, 0.5), (5811, 1.0), (7079, 1.5), (8346, 2.0),
            (9613, 2.5), (10881, 3.0), (12148, 3.5), (13415, 4.0), (14682, 4.5),
            (15950, 5.0), (17217, 5.5), (18484, 6.0), (19752, 6.5), (21019, 7.0),
            (22286, 7.5), (23553, 8.0), (24821, 8.5), (26088, 9.0), (27355, 9.5),
            (28623, 10.0)
        ]
        
        # Jos arvo on alle pienimmän, palauta 0
        if adc_value <= calibration_table[0][0]:
            return 0.0
        
        # Jos arvo on yli suurimman, ekstrapoloi
        if adc_value >= calibration_table[-1][0]:
            return calibration_table[-1][1]
        
        # Etsi sopiva välialue ja interpoloi
        for i in range(len(calibration_table) - 1):
            adc1, bar1 = calibration_table[i]
            adc2, bar2 = calibration_table[i + 1]
            
            if adc1 <= adc_value <= adc2:
                # Lineaarinen interpolaatio
                ratio = (adc_value - adc1) / (adc2 - adc1)
                return bar1 + ratio * (bar2 - bar1)
        
        return 0.0
    
    def show_sensor_error(self, error_message):
        """Näytä anturivirhe (vain lämpötilalle ja kosteudelle)"""
        self.temp_label.setText("ERR")
        self.temp_label.setStyleSheet("color: #e74c3c; background-color: transparent;")
        
        self.humidity_label.setText("ERR")
        self.humidity_label.setStyleSheet("color: #e74c3c; background-color: transparent;")
    
    def show_pressure_error(self):
        """Näytä paineanturin virhe"""
        self.pressure_label.setText("ERR")
        self.pressure_label.setStyleSheet("color: #e74c3c; background-color: transparent;")
    
    def request_sensor_update(self):
        """Pyydä anturipäivitystä pääikkunalta"""
        if hasattr(self.parent(), 'update_environment_sensors'):
            self.parent().update_environment_sensors()
    
    def cleanup(self):
        """Siivoa resurssit"""
        if hasattr(self, 'update_timer') and self.update_timer:
            self.update_timer.stop()