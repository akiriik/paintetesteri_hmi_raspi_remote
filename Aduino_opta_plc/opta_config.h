#pragma once

#include "OptaBlue.h"
#include <ArduinoRS485.h>
#include <ArduinoModbus.h>

using namespace Opta;

// -----------------------------
// Serial
// -----------------------------

const unsigned long SERIAL_BAUDRATE = 115200;

// -----------------------------
// Modbus-asetukset
// -----------------------------

const uint8_t MODBUS_SLAVE_ID = 1;
const unsigned long MODBUS_BAUDRATE = 19200;

// -----------------------------
// Modbus-rekisterit
// -----------------------------

// Dualtester:
// SHUTDOWN_REQUEST_REGISTER = 17999
// EMERGENCY_RESET_REGISTER = 19099
// EMERGENCY_STATUS_REGISTER = 19100
// OPTA_RELAY_REGISTER_BASE = 18098
//
// HUOM:
// Raspberryn nykyinen yleinen releohjaus käyttää D1608E-relealuetta.
// Optan omille releille 3 ja 4 on tässä omat rekisterit testiventtiileille.

const uint16_t SHUTDOWN_REQUEST_REGISTER = 17999;

// Optan omat releet 3 ja 4 testiventtiileille
const uint16_t OPTA_TEST_VALVE_RELAY_REGISTER_START = 18092;
const uint8_t OPTA_TEST_VALVE_RELAY_COUNT = 2;

// 18092 = Optan oma rele 3 = ForTest 1 testiventtiili
// 18093 = Optan oma rele 4 = ForTest 2 testiventtiili

const uint16_t FORTEST1_TEST_VALVE_REGISTER = 18092;
const uint16_t FORTEST2_TEST_VALVE_REGISTER = 18093;

const uint8_t FORTEST1_TEST_VALVE_OPTA_OUTPUT_NUMBER = 3;
const uint8_t FORTEST2_TEST_VALVE_OPTA_OUTPUT_NUMBER = 4;

// D1608E-lisäosan releet jätetään jakotukkijigin myöhempään ohjaukseen
const uint16_t D1608E_RELAY_REGISTER_START = 18099;
const uint8_t D1608E_RELAY_COUNT = 8;

const uint16_t EMERGENCY_RESET_REGISTER = 19099;
const uint16_t EMERGENCY_STATUS_REGISTER = 19100;

// Käytössä yksi holding register -alue:
// 17999 = shutdown request
// 18092...18093 = Optan omat releet 3 ja 4 testiventtiileille
// 18099...18106 = D1608E releet 1...8
// 19099 = emergency reset
// 19100 = emergency status

const uint16_t MODBUS_HOLDING_REGISTER_START = SHUTDOWN_REQUEST_REGISTER;
const uint16_t MODBUS_HOLDING_REGISTER_COUNT =
  (EMERGENCY_STATUS_REGISTER + 1) - MODBUS_HOLDING_REGISTER_START;

// -----------------------------
// Sammutus
// -----------------------------

const unsigned long SHUTDOWN_DELAY_MS = 10000;
const uint8_t SHUTDOWN_POWER_OPTA_OUTPUT_NUMBER = 1;

// -----------------------------
// Hätäseis
// -----------------------------

const uint8_t EMERGENCY_BUTTON_OPTA_INPUT_NUMBER = 1;
const uint8_t EMERGENCY_LIGHT_OPTA_OUTPUT_NUMBER = 2;

const unsigned long EMERGENCY_LIGHT_BLINK_INTERVAL_MS = 500;

// Dualtester:
// 1 = hätäseis OK
// 0 = hätäseis aktiivinen
const uint16_t EMERGENCY_STATUS_OK = 1;
const uint16_t EMERGENCY_STATUS_ACTIVE = 0;

// -----------------------------
// Opta onboard inputit
// -----------------------------

const uint8_t OPTA_INPUT_COUNT = 8;

const uint8_t OPTA_INPUT_PINS[OPTA_INPUT_COUNT] = {
  A0,  // I1
  A1,  // I2
  A2,  // I3
  A3,  // I4
  A4,  // I5
  A5,  // I6
  A6,  // I7
  A7   // I8
};

// -----------------------------
// Opta onboard outputit
// -----------------------------

const uint8_t OPTA_OUTPUT_COUNT = 4;

const uint8_t OPTA_OUTPUT_PINS[OPTA_OUTPUT_COUNT] = {
  RELAY1,  // OUTPUT 1 = järjestelmän sammutus
  RELAY2,  // OUTPUT 2 = hätäseisvalo
  RELAY3,  // OUTPUT 3 = ForTest 1 testiventtiili
  RELAY4   // OUTPUT 4 = ForTest 2 testiventtiili
};

// -----------------------------
// D1608E expansion IO
// -----------------------------

const uint8_t D1608E_INPUT_COUNT = 6;
const uint8_t D1608E_OUTPUT_COUNT = 8;

// D1608E output indexit 0...7
// Rele 1 = output 0
// Rele 8 = output 7

const uint8_t D1608E_RELAY_INDEX[D1608E_OUTPUT_COUNT] = {
  0,  // rele 1
  1,  // rele 2
  2,  // rele 3
  3,  // rele 4
  4,  // rele 5
  5,  // rele 6
  6,  // rele 7
  7   // rele 8
};

// D1608E input indexit 0...5
// Input 1 = input 0
// Input 6 = input 5

const uint8_t D1608E_INPUT_INDEX[D1608E_INPUT_COUNT] = {
  0,  // input 1
  1,  // input 2
  2,  // input 3
  3,  // input 4
  4,  // input 5
  5   // input 6
};

// -----------------------------
// Päivitysajat
// -----------------------------

const unsigned long OPTA_UPDATE_INTERVAL_MS = 100;

// -----------------------------
// Sekvenssimoottorin oletusajat
// -----------------------------

const uint8_t SEQUENCE_MAX_STEPS = 10;

const unsigned long SEQUENCE_DEFAULT_STEP_TIME_MS[SEQUENCE_MAX_STEPS] = {
  500,
  500,
  500,
  500,
  500,
  500,
  500,
  500,
  500,
  500
};