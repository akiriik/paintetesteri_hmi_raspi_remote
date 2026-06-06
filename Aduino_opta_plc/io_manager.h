#pragma once

#include "opta_config.h"
#include "opta_state.h"

// -----------------------------
// Expansion-haku
// -----------------------------

DigitalMechExpansion getD1608EExpansion() {
  for (int i = 0; i < OPTA_CONTROLLER_MAX_EXPANSION_NUM; i++) {
    DigitalMechExpansion mechExp = OptaController.getExpansion(i);

    if (mechExp) {
      return mechExp;
    }
  }

  return DigitalMechExpansion();
}

// -----------------------------
// Alustus
// -----------------------------

void initOptaOnboardIO() {
  for (uint8_t i = 0; i < OPTA_INPUT_COUNT; i++) {
    pinMode(OPTA_INPUT_PINS[i], INPUT);
    optaInputStates[i] = false;
  }

  for (uint8_t i = 0; i < OPTA_OUTPUT_COUNT; i++) {
    pinMode(OPTA_OUTPUT_PINS[i], OUTPUT);
    digitalWrite(OPTA_OUTPUT_PINS[i], LOW);
    optaOutputStates[i] = false;
  }
}

void initExpansionIO() {
  OptaController.begin();

  unsigned long startMs = millis();

  while (millis() - startMs < 1000) {
    OptaController.update();
  }

  DigitalMechExpansion mechExp = getD1608EExpansion();

  if (!mechExp) {
    Serial.println("D1608E expansion not found at startup");
    return;
  }

  for (uint8_t i = 0; i < D1608E_INPUT_COUNT; i++) {
    d1608eInputStates[i] = false;
  }

  for (uint8_t i = 0; i < D1608E_RELAY_COUNT; i++) {
    mechExp.digitalWrite(D1608E_RELAY_INDEX[i], LOW);
    d1608eRelayStates[i] = false;
  }

  mechExp.updateDigitalOutputs();
}

// -----------------------------
// Opta onboard inputit
// -----------------------------

void readOptaInputs() {
  for (uint8_t i = 0; i < OPTA_INPUT_COUNT; i++) {
    optaInputStates[i] = (digitalRead(OPTA_INPUT_PINS[i]) == HIGH);
  }
}

bool getOptaInput(uint8_t inputNumber) {
  if (inputNumber < 1 || inputNumber > OPTA_INPUT_COUNT) {
    return false;
  }

  return optaInputStates[inputNumber - 1];
}

// -----------------------------
// Opta onboard outputit
// -----------------------------

void setOptaOutput(uint8_t outputNumber, bool state) {
  if (outputNumber < 1 || outputNumber > OPTA_OUTPUT_COUNT) {
    return;
  }

  uint8_t index = outputNumber - 1;

  optaOutputStates[index] = state;
  digitalWrite(OPTA_OUTPUT_PINS[index], state ? HIGH : LOW);
}

bool getOptaOutput(uint8_t outputNumber) {
  if (outputNumber < 1 || outputNumber > OPTA_OUTPUT_COUNT) {
    return false;
  }

  return optaOutputStates[outputNumber - 1];
}

void setAllOptaOutputsOff() {
  for (uint8_t i = 0; i < OPTA_OUTPUT_COUNT; i++) {
    setOptaOutput(i + 1, false);
  }
}

// -----------------------------
// D1608E inputit
// -----------------------------

void readD1608EInputs() {
  DigitalMechExpansion mechExp = getD1608EExpansion();

  if (!mechExp) {
    for (uint8_t i = 0; i < D1608E_INPUT_COUNT; i++) {
      d1608eInputStates[i] = false;
    }
    return;
  }

  mechExp.updateDigitalInputs();

  for (uint8_t i = 0; i < D1608E_INPUT_COUNT; i++) {
    PinStatus value = mechExp.digitalRead(D1608E_INPUT_INDEX[i]);
    d1608eInputStates[i] = (value == HIGH);
  }
}

bool getD1608EInput(uint8_t inputNumber) {
  if (inputNumber < 1 || inputNumber > D1608E_INPUT_COUNT) {
    return false;
  }

  return d1608eInputStates[inputNumber - 1];
}

// -----------------------------
// D1608E releet
// -----------------------------

void setD1608ERelay(uint8_t relayIndex, bool state) {
  if (relayIndex >= D1608E_RELAY_COUNT) {
    return;
  }

  DigitalMechExpansion mechExp = getD1608EExpansion();

  if (!mechExp) {
    Serial.println("D1608E expansion not found");
    return;
  }

  mechExp.digitalWrite(D1608E_RELAY_INDEX[relayIndex], state ? HIGH : LOW);
  mechExp.updateDigitalOutputs();

  d1608eRelayStates[relayIndex] = state;
}

void setD1608ERelayByNumber(uint8_t relayNumber, bool state) {
  if (relayNumber < 1 || relayNumber > D1608E_RELAY_COUNT) {
    return;
  }

  setD1608ERelay(relayNumber - 1, state);
}

bool getD1608ERelay(uint8_t relayNumber) {
  if (relayNumber < 1 || relayNumber > D1608E_RELAY_COUNT) {
    return false;
  }

  return d1608eRelayStates[relayNumber - 1];
}

void setAllD1608ERelaysOff() {
  DigitalMechExpansion mechExp = getD1608EExpansion();

  if (!mechExp) {
    Serial.println("D1608E expansion not found");
    return;
  }

  for (uint8_t i = 0; i < D1608E_RELAY_COUNT; i++) {
    mechExp.digitalWrite(D1608E_RELAY_INDEX[i], LOW);
    d1608eRelayStates[i] = false;
  }

  mechExp.updateDigitalOutputs();
}

// -----------------------------
// OptaController update
// -----------------------------

void updateOptaControllerThrottled() {
  if (millis() - lastOptaUpdateMs >= OPTA_UPDATE_INTERVAL_MS) {
    lastOptaUpdateMs = millis();
    OptaController.update();
  }
}