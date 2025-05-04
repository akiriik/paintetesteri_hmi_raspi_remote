from PyQt5.QtWidgets import QFrame, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QPropertyAnimation, QEasingCurve, QPoint

class NavigationBar(QFrame):
    # Signaali, joka lähetetään kun näyttöä vaihdetaan
    screen_changed = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setStyleSheet("""
            QFrame {
                background-color: white; 
                border-top: 1px solid #dddddd;
            }
        """)
        
        # Napin tyylimäärittelyt
        self.inactive_style = """
            QPushButton {
                background-color: white;
                color: #555555;
                border: none;
                font-weight: bold;
                font-size: 18px;
                border-bottom: 3px solid transparent;
                padding-bottom: 5px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                color: #333333;
            }
        """
        
        self.active_style = """
            QPushButton {
                background-color: white;
                color: #2196F3;
                border: none;
                font-weight: bold;
                font-size: 18px;
                border-bottom: 3px solid #2196F3;
                padding-bottom: 5px;
            }
        """
        
        # Alustetaan UI-elementit
        self.init_ui()
    
    def init_ui(self):
        # Luodaan layout navigointipalkille
        nav_layout = QHBoxLayout(self)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)
        
        # Luodaan navigointipainikkeet
        button_labels = ["ETUSIVU", "OHJELMA", "TESTAUS", "KÄSIKÄYTTÖ", "MODBUS"]
        
        self.nav_buttons = []
        
        for i, label in enumerate(button_labels):
            # Luodaan painike
            btn = QPushButton(label)
            btn.setStyleSheet(self.inactive_style)
            btn.setMinimumSize(QSize(256, 70))  # 1280/5 = 256 pikseliä per painike
            
            # Yhdistä nappi signaaliin, joka vaihtaa näyttöä
            btn.clicked.connect(lambda checked, index=i: self.change_screen(index))
            
            self.nav_buttons.append(btn)
            nav_layout.addWidget(btn)
        
        # Aseta ETUSIVU aktiiviseksi aluksi
        self.nav_buttons[0].setStyleSheet(self.active_style)
        self.current_index = 0
        
        # Luodaan indikaattori, joka animoidaan aktiivisen napin alle
        self.indicator = QFrame(self)
        self.indicator.setStyleSheet("background-color: #2196F3;")
        self.indicator.setFixedHeight(3)
        self.indicator.setFixedWidth(240)  # Hieman kapeampi kuin nappi
        self.indicator.move(8, 67)  # Aseta indikaattori ensimmäisen napin alle
        self.indicator.show()
    
    def change_screen(self, index):
        # Jos sama näyttö on jo valittu, älä tee mitään
        if index == self.current_index:
            return
        
        # Päivitä nappi-tyylit
        for i, btn in enumerate(self.nav_buttons):
            if i == index:
                btn.setStyleSheet(self.active_style)
            else:
                btn.setStyleSheet(self.inactive_style)
        
        # Animoi indikaattori uuden napin alle
        target_pos = QPoint(8 + index * 256, 67)
        animation = QPropertyAnimation(self.indicator, b"pos")
        animation.setDuration(300)  # millisekunteina
        animation.setStartValue(self.indicator.pos())
        animation.setEndValue(target_pos)
        animation.setEasingCurve(QEasingCurve.OutCubic)
        animation.start()
        
        self.current_index = index
        
        # Lähetä signaali näytön vaihtamiseksi
        self.screen_changed.emit(index)