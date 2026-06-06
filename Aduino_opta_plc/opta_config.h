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
// Ajat ovat millisekunteina.
// -----------------------------

// PART_CLAMP = kappale kiinni
const unsigned long PART_CLAMP_SYL2_CLOSE_WAIT_MS = 1000;
const unsigned long PART_CLAMP_SYL1_CLOSE_WAIT_MS = 150;
const unsigned long PART_CLAMP_SYL1_OPEN_WAIT_MS = 800;
const unsigned long PART_CLAMP_SYL3_CLOSE_1_WAIT_MS = 1500;
const unsigned long PART_CLAMP_SYL3_OPEN_WAIT_MS = 500;
const unsigned long PART_CLAMP_SYL1_CLOSE_2_WAIT_MS = 500;

// PART_RELEASE = kappale irti
const unsigned long PART_RELEASE_SYL3_OPEN_WAIT_MS = 500;
const unsigned long PART_RELEASE_SYL1_OPEN_WAIT_MS = 500;

// PART_REMOVE = kappaleen poisto
const unsigned long PART_REMOVE_SYL3_OPEN_1_WAIT_MS = 500;
const unsigned long PART_REMOVE_SYL1_OPEN_WAIT_MS = 500;
const unsigned long PART_REMOVE_SYL2_OPEN_WAIT_MS = 1000;
const unsigned long PART_REMOVE_SYL3_CLOSE_WAIT_MS = 1000;

// -----------------------------
// Jigin D1608E inputit
// -----------------------------

const uint8_t JIG_PART_PRESENT_INPUT_NUMBER = 1;

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

const uint16_t SHUTDOWN_REQUEST_REGISTER = 17999;

// Optan omat releet 3 ja 4 testiventtiileille
const uint16_t OPTA_TEST_VALVE_RELAY_REGISTER_START = 18092;
const uint8_t OPTA_TEST_VALVE_RELAY_COUNT = 2;

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
const uint16_t JIG_SEQUENCE_COMMAND_PART_CHANGE = 2;
const uint16_t JIG_SEQUENCE_COMMAND_PART_RELEASE = 3;
const uint16_t JIG_SEQUENCE_COMMAND_PART_REMOVE = 4;

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
const uint16_t JIG_SEQUENCE_ERROR_PART_MISSING = 5;

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

const uint16_t EMERGENCY_STATUS_OK = 1;
const uint16_t EMERGENCY_STATUS_ACTIVE = 0;

// -----------------------------
// Opta onboard inputit
// -----------------------------

const uint8_t OPTA_INPUT_COUNT = 8;

const uint8_t OPTA_INPUT_PINS[OPTA_INPUT_COUNT] = {
  A0,
  A1,
  A2,
  A3,
  A4,
  A5,
  A6,
  A7
};

// -----------------------------
// Opta onboard outputit
// -----------------------------

const uint8_t OPTA_OUTPUT_COUNT = 4;

const uint8_t OPTA_OUTPUT_PINS[OPTA_OUTPUT_COUNT] = {
  RELAY1,
  RELAY2,
  RELAY3,
  RELAY4
};

// -----------------------------
// D1608E expansion IO
// -----------------------------

const uint8_t D1608E_INPUT_COUNT = 6;
const uint8_t D1608E_OUTPUT_COUNT = 8;

const uint8_t D1608E_RELAY_INDEX[D1608E_OUTPUT_COUNT] = {
  0,
  1,
  2,
  3,
  4,
  5,
  6,
  7
};

const uint8_t D1608E_INPUT_INDEX[D1608E_INPUT_COUNT] = {
  0,
  1,
  2,
  3,
  4,
  5
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