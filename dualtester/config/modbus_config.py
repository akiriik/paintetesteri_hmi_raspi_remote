# config/modbus_config.py

"""
Modbus-rekisterien keskitetty konfiguraatio.

Tähän tiedostoon kerätään yhteiset Opta / Modbus-rekisteriosoitteet,
joita käytetään dualtester-rakenteessa.
"""

# Ulkoisen ohjauksen sammutuspyyntö
SHUTDOWN_REQUEST_REGISTER = 17999

# Ohjelmallisen hätäseis-tilan kuittaus
EMERGENCY_RESET_REGISTER = 19099