# config/gpio_config.py

"""
GPIO- ja I/O-määritykset dualtester-versiolle.

Tämä tiedosto kokoaa fyysiset napit ja nappivalot yhteen paikkaan.
Varsinainen logiikka on controllereissa.

Huom:
- Nämä ovat vielä oletusmäärityksiä.
- DEV_MODE_GPIO = True, joten fyysisiä GPIO-inputteja ei vielä käytetä.
- Hätäseis ei korvaa oikeaa turvapiiriä.
"""


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


STATION_BUTTON_MAP = {
    "STATION1_START": 1,
    "STATION2_START": 2,

    # Vanhojen nimien yhteensopivuus
    "START": 1,
    "STOP": 1,
}


SPARE_BUTTONS = {
    "SPARE1",
    "SPARE2",
    "SPARE3",
    "SPARE4",
}


STATION_LIGHT_OUTPUTS = {
    1: 4,
    2: 5,
}