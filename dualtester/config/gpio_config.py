# config/gpio_config.py

"""
GPIO- ja I/O-määritykset dualtester-versiolle.

Inputit:
- BCM-numerointi
- pull-up käytössä
- nappi maadoittaa GPIO:n
- ei painettu = HIGH
- painettu = LOW

Outputit:
- BCM-numerointi GPIOHandlerissa
- fyysiselle kaksiväriselle 24 V napille on kaksi lähtöä:
  - ON/OFF
  - COLOR / rele
"""

GPIO_INPUT_PULL_UP = True
GPIO_INPUT_ACTIVE_LOW = True
GPIO_DEBOUNCE_TIME_MS = 200
GPIO_EVENT_BOUNCETIME_MS = 100


PHYSICAL_BUTTONS = {
    "STATION1_START": {
        "gpio": 24,
        "description": "ForTest 1 start/stop -kytkin, valkoinen johto",
    },
    "STATION2_START": {
        "gpio": 25,
        "description": "ForTest 2 start/stop -kytkin, pinkki johto",
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


# GPIOHandlerin output-kanavat.
#
# Nämä ovat ohjelman sisäisiä output-numeroita.
# Varsinainen GPIO-pinni määritellään utils/gpio_handler.py:ssä.
GPIO_OUTPUT_CHANNELS = {
    "FORTEST1_LED_ON": 1,       # ruskea   -> GPIO17
    "FORTEST1_LED_COLOR": 2,    # punainen -> GPIO27
    "FORTEST2_LED_ON": 3,       # vihreä   -> GPIO22
    "FORTEST2_LED_COLOR": 4,    # harmaa   -> GPIO23
}


STATION_LIGHT_OUTPUTS = {
    1: {
        "on_off": GPIO_OUTPUT_CHANNELS["FORTEST1_LED_ON"],
        "color": GPIO_OUTPUT_CHANNELS["FORTEST1_LED_COLOR"],
    },
    2: {
        "on_off": GPIO_OUTPUT_CHANNELS["FORTEST2_LED_ON"],
        "color": GPIO_OUTPUT_CHANNELS["FORTEST2_LED_COLOR"],
    },
}