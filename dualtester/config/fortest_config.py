# config/fortest_config.py

"""
ForTest-laitteiden rekisterit ja komennot.

Nämä kuuluvat ForTest 1 / ForTest 2 -laitteiden omiin väyliin.
Nämä eivät ole Arduino Optan Modbus-rekistereitä.
"""

# ------------------------------------------------------------
# ForTest coil-komennot
# ------------------------------------------------------------

# Käynnistä testi
FORTEST_START_TEST_COIL = 0x0A

# Keskeytä / pysäytä testi
FORTEST_ABORT_TEST_COIL = 0x14


# -------------------------------------------------------------
# ForTest holding register -luennat
# -------------------------------------------------------------

# Laitteen statusalue
FORTEST_STATUS_REGISTER = 0x0030
FORTEST_STATUS_REGISTER_COUNT = 32

# Testitulosten alue
FORTEST_RESULTS_REGISTER = 0x0040
FORTEST_RESULTS_REGISTER_COUNT = 32


# ------------------------------------------------------------
# ForTest ohjelmanvalinta
# ------------------------------------------------------------

# ForTest-ohjelman valinta
FORTEST_PROGRAM_REGISTER = 0x0060