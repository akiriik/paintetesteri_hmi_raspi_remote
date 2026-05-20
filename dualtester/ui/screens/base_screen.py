from PyQt5.QtWidgets import QFrame, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

class BaseScreen(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Poistettu musta tausta täältä
        # self.setStyleSheet("background-color: black;")
        
        # Set up common fonts
        self.title_font = QFont()
        self.title_font.setPointSize(42)
        self.title_font.setBold(True)
        
        self.subtitle_font = QFont()
        self.subtitle_font.setPointSize(28)
        
        # Initialize UI elements
        self.init_ui()
    
    def init_ui(self):
        """
        Initialize the UI elements of the screen.
        This method should be overridden by child classes.
        """
        pass
    
    def create_title(self, text, y_pos=50):
        """
        Create a title label with the given text.
        """
        title = QLabel(text, self)
        title.setFont(self.title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setGeometry(0, y_pos, 1280, 100)
        return title
    
    def create_subtitle(self, text, y_pos=200):
        """
        Create a subtitle label with the given text.
        """
        subtitle = QLabel(text, self)
        subtitle.setFont(self.subtitle_font)
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setGeometry(0, y_pos, 1280, 60)
        return subtitle
    
    def update(self):
        """
        Update the screen contents.
        This method should be overridden by child classes if needed.
        """
        pass
    
    def cleanup(self):
        """
        Clean up resources used by the screen.
        This method should be overridden by child classes if needed.
        """
        pass