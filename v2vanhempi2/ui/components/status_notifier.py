# ui/components/status_notifier.py
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, QSize, QPoint, QPropertyAnimation, QEasingCurve

class StatusNotifier(QFrame):
    """Pieni pop-up ikkuna tilaviestejä varten"""
    
    INFO = 0
    SUCCESS = 1
    WARNING = 2
    ERROR = 3
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Tyyli
        self.setObjectName("statusNotifier")
        self.setStyleSheet("""
            QFrame#statusNotifier {
                background-color: #333333;
                border-radius: 8px;
                color: white;
            }
        """)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Viesti
        self.message_label = QLabel("", self)
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("color: white; font-size: 16px;")
        layout.addWidget(self.message_label)
        
        # Piilota aluksi
        self.hide()
        
        # Ajastin automaattista sulkemista varten
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide_animation)
        
        # Animaatiot
        self.show_anim = QPropertyAnimation(self, b"pos")
        self.show_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.show_anim.setDuration(300)
        
        self.hide_anim = QPropertyAnimation(self, b"pos")
        self.hide_anim.setEasingCurve(QEasingCurve.InCubic)
        self.hide_anim.setDuration(300)
        self.hide_anim.finished.connect(self.hide)
    
    def show_message(self, message, status_type=INFO, duration=3000):
        """Näytä tilaviesti"""
        # Aseta viesti
        self.message_label.setText(message)
        
        # Aseta tyyli tyypin mukaan
        if status_type == self.SUCCESS:
            self.setStyleSheet("""
                QFrame#statusNotifier {
                    background-color: #4CAF50;
                    border-radius: 8px;
                    color: white;
                }
            """)
        elif status_type == self.WARNING:
            self.setStyleSheet("""
                QFrame#statusNotifier {
                    background-color: #FFC107;
                    border-radius: 8px;
                    color: black;
                }
            """)
        elif status_type == self.ERROR:
            self.setStyleSheet("""
                QFrame#statusNotifier {
                    background-color: #F44336;
                    border-radius: 8px;
                    color: white;
                }
            """)
        else:  # INFO
            self.setStyleSheet("""
                QFrame#statusNotifier {
                    background-color: #2196F3;
                    border-radius: 8px;
                    color: white;
                }
            """)
        
        # Sovita koko viestiin
        self.adjustSize()
        self.setFixedWidth(400)
        
        # Aseta sijainti (alareunaan)
        parent_rect = self.parent().rect()
        start_pos = QPoint(
            parent_rect.width() // 2 - self.width() // 2,
            parent_rect.height() + 10
        )
        self.move(start_pos)
        
        end_pos = QPoint(
            parent_rect.width() // 2 - self.width() // 2,
            parent_rect.height() - self.height() - 20
        )
        
        # Näytä animaatio
        self.show()
        self.show_anim.setStartValue(start_pos)
        self.show_anim.setEndValue(end_pos)
        self.show_anim.start()
        
        # Aseta ajastin
        self.timer.start(duration)
    
    def hide_animation(self):
        """Aloita piilotusanimaatio"""
        start_pos = self.pos()
        end_pos = QPoint(
            start_pos.x(),
            self.parent().height() + 10
        )
        
        self.hide_anim.setStartValue(start_pos)
        self.hide_anim.setEndValue(end_pos)
        self.hide_anim.start()