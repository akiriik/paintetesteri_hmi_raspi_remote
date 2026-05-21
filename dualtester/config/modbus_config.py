# config/modbus_config.py

"""
Opta / yhteisen Modbus-väylän rekisterit.

Nämä kuuluvat Arduino Optan RS485 Modbus RTU -väylään.
ForTest-laitteiden rekisterit ovat tiedostossa fortest_config.py.
"""

# ------------------------------------------------------------
# Opta / yhteinen ohjausväylä
# ------------------------------------------------------------

# Ulkoisen ohjauksen sammutuspyyntö
SHUTDOWN_REQUEST_REGISTER = 17999

# Ohjelmallisen hätäseis-tilan kuittaus
EMERGENCY_RESET_REGISTER = 19099