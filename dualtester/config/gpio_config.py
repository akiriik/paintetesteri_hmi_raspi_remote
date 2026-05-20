# config/gpio_config.py

"""
GPIO- ja I/O-määritykset dualtester-versiolle.

Tämä tiedosto kokoaa fyysiset napit ja nappivalot yhteen paikkaan.
Varsinainen logiikka on controllereissa ja handler-luokissa.

Huom:
- Nämä ovat vielä oletusmäärityksiä.
- DEV_MODE_GPIO = True, joten fyysisiä GPIO-inputteja ei vielä käytetä.
- Hätäseis ei korvaa oikeaa turvapiiriä.
"""


# GPIO-inputtien yleinen toimintamalli:
#
# Raspberry Pi input:
# - käytetään BCM-numerointia
# - inputit ovat PUD_UP-tilassa
# - nappi oletetaan aktiiviseksi, kun input menee GND:hen
#
# Eli:
# - ei painettu = HIGH
# - painettu = LOW
GPIO_INPUT_PULL_UP = True
GPIO_INPUT_ACTIVE_LOW = True
GPIO_DEBOUNCE_TIME_MS = 200
GPIO_EVENT_BOUNCETIME_MS = 100


PHYSICAL_BUTTONS = {
    "STATION1_START": {
        "gpio": 5,
        "description": "ForTest 1 start/stop -nappi",
    },
    "STATION2_START": {
        "gpio": 6,
        "description": "ForTest 2 start/stop -nappi",
    },
    "EMERGENCY_STOP": {
        "gpio": 12,
        "description": "Ohjelmallinen hätäseisinput / tilatieto",
    },
    "SPARE1": {
        "gpio": 13,
        "description": "Varanappi 1",
    },
    "SPARE2": {
        "gpio": 16,
        "description": "Varanappi 2",
    },
    "SPARE3": {
        "gpio": 20,
        "description": "Varanappi 3",
    },
    "SPARE4": {
        "gpio": 21,
        "description": "Varanappi 4",
    },
}


# Pelkkä nimi -> GPIO -kartta GPIOInputHandlerille.
PHYSICAL_BUTTON_PINS = {
    button_name: button_data["gpio"]
    for button_name, button_data in PHYSICAL_BUTTONS.items()
}


STATION_BUTTON_MAP = {
    "STATION1_START": 1,
    "STATION2_START": 2,

}


SPARE_BUTTONS = {
    "SPARE1",
    "SPARE2",
    "SPARE3",
    "SPARE4",
}


# HardwareService output -numerot.
# Nämä eivät ole Raspberryn GPIO-numeroita, vaan ohjelman käyttämät output-kanavat.
STATION_LIGHT_OUTPUTS = {
    1: 4,
    2: 5,
}