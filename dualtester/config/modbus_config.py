# config/modbus_config.py

"""
Modbus-rekisterien keskitetty konfiguraatio.

Tähän tiedostoon kerätään dualtester-rakenteessa käytettävät
Modbus-rekisteriosoitteet.
"""

# ------------------------------------------------------------
# Opta / yhteinen ohjausväylä
# ------------------------------------------------------------

# Ulkoisen ohjauksen sammutuspyyntö
SHUTDOWN_REQUEST_REGISTER = 17999

# Ohjelmallisen hätäseis-tilan kuittaus
EMERGENCY_RESET_REGISTER = 19099


# ------------------------------------------------------------
# ForTest
# ------------------------------------------------------------

# ForTest-ohjelman valinta
FORTEST_PROGRAM_REGISTER = 0x0060