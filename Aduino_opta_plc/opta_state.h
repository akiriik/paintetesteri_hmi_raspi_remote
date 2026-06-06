#pragma once

#include "opta_config.h"

// -----------------------------
// Opta onboard IO tilat
// -----------------------------

bool optaInputStates[OPTA_INPUT_COUNT] = {
  false, false, false, false, false, false, false, false
};

bool optaOutputStates[OPTA_OUTPUT_COUNT] = {
  false, false, false, false
};

// -----------------------------
// D1608E IO tilat
// -----------------------------

bool d1608eInputStates[D1608E_INPUT_COUNT] = {
  false, false, false, false, false, false
};

bool d1608eRelayStates[D1608E_RELAY_COUNT] = {
  false, false, false, false, false, false, false, false
};

int d1608eLastRelayRegisterValues[D1608E_RELAY_COUNT] = {
  -1, -1, -1, -1, -1, -1, -1, -1
};

// -----------------------------
// Järjestelmätilat
// -----------------------------

bool shutdownRequest = false;
bool shutdownTimerRunning = false;
bool shutdownRelayActivated = false;
unsigned long shutdownTimerStartedMs = 0;
int lastShutdownRegisterValue = -1;

bool emergencyStopActive = false;
bool emergencyResetRequest = false;
bool emergencyLightState = false;
unsigned long lastEmergencyLightBlinkMs = 0;
int lastEmergencyResetRegisterValue = -1;

// -----------------------------
// Ajoitus
// -----------------------------

unsigned long lastOptaUpdateMs = 0;

// -----------------------------
// Sekvenssimoottorin tila
// -----------------------------

bool sequenceRunning = false;
uint8_t sequenceCurrentStep = 0;
unsigned long sequenceStepStartedMs = 0;

unsigned long sequenceStepTimeMs[SEQUENCE_MAX_STEPS] = {
  SEQUENCE_DEFAULT_STEP_TIME_MS[0],
  SEQUENCE_DEFAULT_STEP_TIME_MS[1],
  SEQUENCE_DEFAULT_STEP_TIME_MS[2],
  SEQUENCE_DEFAULT_STEP_TIME_MS[3],
  SEQUENCE_DEFAULT_STEP_TIME_MS[4],
  SEQUENCE_DEFAULT_STEP_TIME_MS[5],
  SEQUENCE_DEFAULT_STEP_TIME_MS[6],
  SEQUENCE_DEFAULT_STEP_TIME_MS[7],
  SEQUENCE_DEFAULT_STEP_TIME_MS[8],
  SEQUENCE_DEFAULT_STEP_TIME_MS[9]
};

// -----------------------------
// Jigin sekvenssin tila
// -----------------------------

bool jigSequenceRunning = false;
uint16_t jigSequenceCommand = JIG_SEQUENCE_NONE;
uint16_t jigSequenceStatus = JIG_SEQUENCE_STATUS_IDLE;
uint16_t jigSequenceStep = 0;
uint16_t jigSequenceError = JIG_SEQUENCE_ERROR_NONE;

unsigned long jigSequenceStepStartedMs = 0;