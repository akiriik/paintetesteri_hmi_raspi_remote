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

# Ohjelmallisen hätäseispiirin tilaluku
EMERGENCY_STATUS_REGISTER = 19100
EMERGENCY_STATUS_REGISTER_COUNT = 1


# ------------------------------------------------------------
# Opta / releohjaus
# ------------------------------------------------------------

# Rele 1 = 18099, rele 2 = 18100 jne.
# Kaava: OPTA_RELAY_REGISTER_BASE + relay_num
OPTA_RELAY_REGISTER_BASE = 18098