# ui/components/log_panel.py
from PyQt5.QtWidgets import QWidget, QTextEdit, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QFont

class LogPanel(QWidget):
    """Komponentti testilokien näyttämiseen"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Otsikko
        self.title = QLabel("VIESTIT / VIRHEET :", self)
        self.title.setFont(QFont("Arial", 14, QFont.Bold))
        self.title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title)
        
        # Lokialue
        self.log_area = QTextEdit(self)
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("""
            QTextEdit {
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                font-family: Consolas, Courier, monospace;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.log_area)
        
        # Muotoilu
        self.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #ddd;
            }
        """)
    
    def add_log_entry(self, message, level="INFO"):
        """Lisää lokiviesti"""
        timestamp = QDateTime.currentDateTime().toString("hh:mm:ss")
        
        if level == "ERROR":
            color = "red"
        elif level == "WARNING":
            color = "orange"
        elif level == "SUCCESS":
            color = "green"
        else:  # INFO
            color = "black"
        
        html = f'<span style="color: #888;">[{timestamp}]</span> <span style="color: {color};">{message}</span><br>'
        self.log_area.insertHtml(html)
        
        # Vieritä alas
        scrollbar = self.log_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_log(self):
        """Tyhjennä loki"""
        self.log_area.clear()