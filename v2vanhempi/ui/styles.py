"""
styles.py - Modernit tyylit painetestausjärjestelmän käyttöliittymälle
"""

class Styles:
    """
    Sisältää tyylimäärittelyt sovelluksen eri osille.
    Käyttö: importtaa tämä luokka ja käytä sen vakioita.
    """
    
    # Värit
    PRIMARY_COLOR = "#2196F3"       # Sininen pääväri
    ACCENT_COLOR = "#FF5722"        # Oranssi korostusväri
    SUCCESS_COLOR = "#4CAF50"       # Vihreä onnistumisväri
    WARNING_COLOR = "#FFC107"       # Keltainen varoitusväri
    ERROR_COLOR = "#F44336"         # Punainen virheväri
    
    # Tumma teema
    DARK_BG_COLOR = "#2D2D30"       # Tumma tausta
    DARK_PANEL_COLOR = "#252526"    # Tumma paneelin tausta
    DARK_TEXT_COLOR = "#FFFFFF"     # Vaalea teksti
    DARK_SECONDARY_TEXT = "#BBBBBB" # Harmaa toissijainen teksti
    
    # Vaalea teema
    LIGHT_BG_COLOR = "#F5F5F5"      # Vaalea tausta
    LIGHT_PANEL_COLOR = "#FFFFFF"   # Valkoinen paneelin tausta
    LIGHT_TEXT_COLOR = "#212121"    # Tumma teksti
    LIGHT_SECONDARY_TEXT = "#757575" # Harmaa toissijainen teksti
    
    # Tyylitiedot
    
    # Pääikkuna (tumma teema)
    MAIN_WINDOW_DARK = f"""
        QWidget {{
            background-color: {DARK_BG_COLOR};
            color: {DARK_TEXT_COLOR};
        }}
        QPushButton#closeButton {{
            background-color: {ERROR_COLOR};
            color: white;
            border-radius: 15px;
            font-weight: bold;
        }}
        QPushButton#closeButton:hover {{
            background-color: #D32F2F;
        }}
    """
    
    # Pääikkuna (vaalea teema)
    MAIN_WINDOW_LIGHT = f"""
        QWidget {{
            background-color: {LIGHT_BG_COLOR};
            color: {LIGHT_TEXT_COLOR};
        }}
        QPushButton#closeButton {{
            background-color: {ERROR_COLOR};
            color: white;
            border-radius: 15px;
            font-weight: bold;
        }}
        QPushButton#closeButton:hover {{
            background-color: #D32F2F;
        }}
    """
    
    # Navigointipalkki (tumma teema)
    NAVBAR_DARK = f"""
        QFrame {{
            background-color: {DARK_PANEL_COLOR};
            border-top: 1px solid #3F3F46;
        }}
        QPushButton {{
            background-color: {DARK_PANEL_COLOR};
            color: {DARK_SECONDARY_TEXT};
            border: none;
            font-weight: bold;
            font-size: 18px;
            border-bottom: 3px solid transparent;
        }}
        QPushButton:hover {{
            background-color: #333337;
            color: {DARK_TEXT_COLOR};
        }}
        QPushButton[active="true"] {{
            background-color: {DARK_PANEL_COLOR};
            color: {PRIMARY_COLOR};
            border-bottom: 3px solid {PRIMARY_COLOR};
        }}
    """
    
    # Navigointipalkki (vaalea teema)
    NAVBAR_LIGHT = f"""
        QFrame {{
            background-color: {LIGHT_PANEL_COLOR};
            border-top: 1px solid #E0E0E0;
        }}
        QPushButton {{
            background-color: {LIGHT_PANEL_COLOR};
            color: {LIGHT_SECONDARY_TEXT};
            border: none;
            font-weight: bold;
            font-size: 18px;
            border-bottom: 3px solid transparent;
        }}
        QPushButton:hover {{
            background-color: #F5F5F5;
            color: {LIGHT_TEXT_COLOR};
        }}
        QPushButton[active="true"] {{
            background-color: {LIGHT_PANEL_COLOR};
            color: {PRIMARY_COLOR};
            border-bottom: 3px solid {PRIMARY_COLOR};
        }}
    """
    
    # Otsikot (tumma teema)
    TITLE_DARK = f"""
        QLabel {{
            color: {DARK_TEXT_COLOR};
            font-size: 38px;
            font-weight: bold;
        }}
    """
    
    # Otsikot (vaalea teema)
    TITLE_LIGHT = f"""
        QLabel {{
            color: {LIGHT_TEXT_COLOR};
            font-size: 38px;
            font-weight: bold;
        }}
    """
    
    # Painikkeet (tumma teema)
    BUTTON_DARK = f"""
        QPushButton {{
            background-color: {PRIMARY_COLOR};
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px 20px;
            font-size: 16px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: #1976D2;
        }}
        QPushButton:pressed {{
            background-color: #0D47A1;
        }}
        QPushButton:disabled {{
            background-color: #757575;
            color: #AAAAAA;
        }}
    """
    
    # Painikkeet (vaalea teema)
    BUTTON_LIGHT = f"""
        QPushButton {{
            background-color: {PRIMARY_COLOR};
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px 20px;
            font-size: 16px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: #1976D2;
        }}
        QPushButton:pressed {{
            background-color: #0D47A1;
        }}
        QPushButton:disabled {{
            background-color: #E0E0E0;
            color: #9E9E9E;
        }}
    """
    
    # Paneelityyli (tumma teema)
    PANEL_DARK = f"""
        QFrame#panel {{
            background-color: {DARK_PANEL_COLOR};
            border-radius: 10px;
            border: 1px solid #3F3F46;
        }}
        QLabel#panelTitle {{
            color: {DARK_TEXT_COLOR};
            font-size: 16px;
            font-weight: bold;
            padding: 10px;
        }}
    """
    
    # Paneelityyli (vaalea teema)
    PANEL_LIGHT = f"""
        QFrame#panel {{
            background-color: {LIGHT_PANEL_COLOR};
            border-radius: 10px;
            border: 1px solid #E0E0E0;
            box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.1);
        }}
        QLabel#panelTitle {{
            color: {LIGHT_TEXT_COLOR};
            font-size: 16px;
            font-weight: bold;
            padding: 10px;
        }}
    """
    
    # Erityinen tyyli käsikäytön relenappeille (tumma teema)
    RELAY_BUTTON_DARK = f"""
        QPushButton {{
            background-color: #424242;
            color: white;
            border-radius: 10px;
            font-size: 18px;
            font-weight: bold;
            border: 1px solid #555555;
        }}
        QPushButton:pressed {{
            background-color: {SUCCESS_COLOR};
        }}
        QPushButton[active="true"] {{
            background-color: {SUCCESS_COLOR};
            border: 1px solid #388E3C;
        }}
    """
    
    # Erityinen tyyli käsikäytön relenappeille (vaalea teema)
    RELAY_BUTTON_LIGHT = f"""
        QPushButton {{
            background-color: #9E9E9E;
            color: white;
            border-radius: 10px;
            font-size: 18px;
            font-weight: bold;
            border: 1px solid #757575;
        }}
        QPushButton:pressed {{
            background-color: {SUCCESS_COLOR};
        }}
        QPushButton[active="true"] {{
            background-color: {SUCCESS_COLOR};
            border: 1px solid #388E3C;
        }}
    """
    
    # Tilapalkin tyyli (tumma teema)
    STATUS_BAR_DARK = f"""
        QFrame {{
            background-color: #1E1E1E;
            border-top: 1px solid #3F3F46;
        }}
        QLabel {{
            color: {DARK_TEXT_COLOR};
        }}
    """
    
    # Tilapalkin tyyli (vaalea teema)
    STATUS_BAR_LIGHT = f"""
        QFrame {{
            background-color: #E0E0E0;
            border-top: 1px solid #BDBDBD;
        }}
        QLabel {{
            color: {LIGHT_TEXT_COLOR};
        }}
    """
    
    # Digitaalinen näyttötyyli
    DIGITAL_DISPLAY = f"""
        QLabel {{
            background-color: black;
            color: #33FF33;
            font-family: 'Digital-7', 'Consolas', monospace;
            font-size: 72px;
            border: 2px solid #444444;
            border-radius: 10px;
        }}
    """
    
    # Animaatiotyyli
    FADE_ANIMATION = """
        QWidget {
            animation: fadeIn 0.3s ease-in-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
    """