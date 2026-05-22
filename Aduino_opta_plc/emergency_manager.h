#pragma once

#include "opta_config.h"
#include "opta_state.h"
#include "io_manager.h"

// -----------------------------
// Hätäseis input
// -----------------------------

bool readEmergencyButtonActive() {
  // Hätäseisnappi on NC.
  // Normaali tila = input 1 HIGH.
  // Hätäseis painettuna / piiri auki = input 1 LOW.
  return !getOptaInput(EMERGENCY_BUTTON_OPTA_INPUT_NUMBER);
}

// -----------------------------
// Hätäseisvalo
// -----------------------------

void setEmergencyLight(bool state) {
  emergencyLightState = state;
  setOptaOutput(EMERGENCY_LIGHT_OPTA_OUTPUT_NUMBER, state);
}

void updateEmergencyLightBlink() {
  if (!emergencyStopActive) {
    if (emergencyLightState) {
      setEmergencyLight(false);
    }

    return;
  }

  if (millis() - lastEmergencyLightBlinkMs >= EMERGENCY_LIGHT_BLINK_INTERVAL_MS) {
    lastEmergencyLightBlinkMs = millis();
    setEmergencyLight(!emergencyLightState);
  }
}

// -----------------------------
// Hätäseis status
// -----------------------------

void updateEmergencyStatusRegister() {
  if (emergencyStopActive) {
    ModbusRTUServer.holdingRegisterWrite(
      EMERGENCY_STATUS_REGISTER,
      EMERGENCY_STATUS_ACTIVE
    );
  } else {
    ModbusRTUServer.holdingRegisterWrite(
      EMERGENCY_STATUS_REGISTER,
      EMERGENCY_STATUS_OK
    );
  }
}

void handleEmergencyResetRequest(bool emergencyButtonPhysicalActive) {
  if (!emergencyResetRequest) {
    return;
  }

  emergencyResetRequest = false;

  // Kuittaus hyväksytään vain jos fyysinen NC-hätäseis on palautunut.
  // Jos nappi on vielä painettuna / piiri auki, hätäseis jää aktiiviseksi.
  if (!emergencyButtonPhysicalActive) {
    emergencyStopActive = false;
  }

  updateEmergencyStatusRegister();
}

// -----------------------------
// Hätäseis loop
// -----------------------------

void updateEmergencyManager() {
  bool emergencyButtonPhysicalActive = readEmergencyButtonActive();

  // Hätäseis lukittuu päälle heti, kun NC-piiri aukeaa.
  if (emergencyButtonPhysicalActive) {
    emergencyStopActive = true;
  }

  // Hätäseis poistuu vain dualtesteristä tulevalla kuittauksella,
  // eikä silloinkaan jos fyysinen hätäseis on edelleen aktiivinen.
  handleEmergencyResetRequest(emergencyButtonPhysicalActive);

  updateEmergencyStatusRegister();
  updateEmergencyLightBlink();
}