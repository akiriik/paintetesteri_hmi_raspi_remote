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
# Opta / onboard testiventtiilireleet
# ------------------------------------------------------------

# Nämä ovat Optan omia releitä, eivät D1608E-lisäosan releitä.
#
# 18092 = Optan oma rele 3 = ForTest 1 testiventtiili
# 18093 = Optan oma rele 4 = ForTest 2 testiventtiili
#
# Rele ON  = testiventtiili kiinni
# Rele OFF = testiventtiili auki / purku

FORTEST1_TEST_VALVE_REGISTER = 18092
FORTEST2_TEST_VALVE_REGISTER = 18093


# ------------------------------------------------------------
# Opta / D1608E-lisäosan releohjaus
# ------------------------------------------------------------

# Tämä alue ohjaa D1608E-lisäosan releitä.
# Rele 1 = 18099, rele 2 = 18100 jne.
# Kaava: OPTA_RELAY_REGISTER_BASE + relay_num
#
# Tätä käytetään myöhemmin jakotukkijigin venttiileille.
# Älä käytä tätä ForTest-testiventtiileille.

OPTA_RELAY_REGISTER_BASE = 18098

# ------------------------------------------------------------
# Opta / jig-sekvenssit
# ------------------------------------------------------------

JIG_SEQUENCE_COMMAND_REGISTER = 19200
JIG_SEQUENCE_START_REGISTER = 19201
JIG_SEQUENCE_STOP_REGISTER = 19202

JIG_SEQUENCE_STATUS_REGISTER = 19210
JIG_SEQUENCE_STEP_REGISTER = 19211
JIG_SEQUENCE_ERROR_REGISTER = 19212

JIG_SEQUENCE_NONE = 0
JIG_SEQUENCE_COMMAND_PART_CLAMP = 1

JIG_SEQUENCE_STATUS_IDLE = 0
JIG_SEQUENCE_STATUS_RUNNING = 1
JIG_SEQUENCE_STATUS_DONE = 2
JIG_SEQUENCE_STATUS_ERROR = 3