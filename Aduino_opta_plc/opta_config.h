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
// Jigin sekvenssin ajat
// Muuta näitä tarvittaessa.
// Ajat ovat millisekunteina.
// -----------------------------

const unsigned long DELAY_SYL1_ON = 800;
const unsigned long DELAY_SYL1_OFF = 150;

const unsigned long DELAY_SYL2_ON = 1000;
const unsigned long DELAY_SYL2_OFF = 300;

const unsigned long DELAY_SYL3_ON = 1000;
const unsigned long DELAY_SYL3_OFF = 500;

const unsigned long SIGNAL_WAIT_TIME = 5000;
const unsigned long SEQUENCE_COMPLETION_DELAY = 5000;

// Anturi lisätään myöhemmin.
// const unsigned long SENSOR_CHECK_TIMEOUT = 1000;

// -----------------------------
// Jigin D1608E releet
// D1608E rele 1 = sylinteri 1
// D1608E rele 2 = sylinteri 2
// D1608E rele 3 = sylinteri 3
// -----------------------------

const uint8_t JIG_CYL1_RELAY_NUMBER = 1;
const uint8_t JIG_CYL2_RELAY_NUMBER = 2;
const uint8_t JIG_CYL3_RELAY_NUMBER = 3;

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

// D1608E-lisäosan releet
const uint16_t D1608E_RELAY_REGISTER_START = 18099;
const uint8_t D1608E_RELAY_COUNT = 8;

const uint16_t EMERGENCY_RESET_REGISTER = 19099;
const uint16_t EMERGENCY_STATUS_REGISTER = 19100;

// -----------------------------
// Jigin sekvenssi Modbus
// -----------------------------

const uint16_t JIG_SEQUENCE_COMMAND_REGISTER = 19200;
const uint16_t JIG_SEQUENCE_START_REGISTER = 19201;
const uint16_t JIG_SEQUENCE_STOP_REGISTER = 19202;

const uint16_t JIG_SEQUENCE_STATUS_REGISTER = 19210;
const uint16_t JIG_SEQUENCE_STEP_REGISTER = 19211;
const uint16_t JIG_SEQUENCE_ERROR_REGISTER = 19212;

// Komennot
const uint16_t JIG_SEQUENCE_NONE = 0;
const uint16_t JIG_SEQUENCE_COMMAND_PART_CLAMP = 1;

// Myöhemmäksi varattu:
// 2 = kappaleen vaihto
// 3 = NOK / kappale irti
// 4 = kappaleen poisto

// Statukset
const uint16_t JIG_SEQUENCE_STATUS_IDLE = 0;
const uint16_t JIG_SEQUENCE_STATUS_RUNNING = 1;
const uint16_t JIG_SEQUENCE_STATUS_DONE = 2;
const uint16_t JIG_SEQUENCE_STATUS_ERROR = 3;

// Virhekoodit
const uint16_t JIG_SEQUENCE_ERROR_NONE = 0;
const uint16_t JIG_SEQUENCE_ERROR_ABORTED = 1;
const uint16_t JIG_SEQUENCE_ERROR_EMERGENCY_STOP = 2;
const uint16_t JIG_SEQUENCE_ERROR_UNKNOWN_COMMAND = 3;
const uint16_t JIG_SEQUENCE_ERROR_INVALID_STEP = 4;

// Käytössä yksi holding register -alue:
// 17999 = shutdown request
// 18092...18093 = Optan omat releet 3 ja 4 testiventtiileille
// 18099...18106 = D1608E releet 1...8
// 19099 = emergency reset
// 19100 = emergency status
// 19200 = jig sequence command
// 19201 = jig sequence start
// 19202 = jig sequence stop
// 19210 = jig sequence status
// 19211 = jig sequence step
// 19212 = jig sequence error

const uint16_t MODBUS_HOLDING_REGISTER_START = SHUTDOWN_REQUEST_REGISTER;
const uint16_t MODBUS_HOLDING_REGISTER_COUNT =
  (JIG_SEQUENCE_ERROR_REGISTER + 1) - MODBUS_HOLDING_REGISTER_START;

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