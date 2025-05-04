from ui.screens.base_screen import BaseScreen

class HomeScreen(BaseScreen):
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def init_ui(self):
        # Create title
        self.main_title = self.create_title("-PAINETESTAUS-", 240)
        
        # Create subtitle
        self.subtitle = self.create_subtitle("VALMIUSTILASSA", 360)