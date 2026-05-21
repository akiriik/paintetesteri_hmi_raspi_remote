# config/port_config.py

"""
Fyysisten sarjaväylien porttikonfiguraatio.

Tämä tiedosto määrittää Raspberry Pi:n USB/RS485-portit.

Huom:
- Arduino Opta käyttää omaa RS485 Modbus RTU -väylää.
- ForTest 1 käyttää omaa väylää.
- ForTest 2 käyttää myöhemmin omaa väylää.
- Raspberry Pi:n suorat GPIO:t eivät käytä sarjaporttia.
- Porttinimet kannattaa myöhemmin muuttaa pysyviksi udev-nimiksi.
"""

# ------------------------------------------------------------
# Arduino Opta / yhteinen RS485 Modbus RTU
# ------------------------------------------------------------

OPTA_MODBUS_PORT = "/dev/opta"
OPTA_MODBUS_BAUDRATE = 19200


# ------------------------------------------------------------
# ForTest-laitteet
# ------------------------------------------------------------

FORTEST_1_PORT = "/dev/ttyUSB1"
FORTEST_2_PORT = "/dev/ttyUSB2"
FORTEST_BAUDRATE = 19200