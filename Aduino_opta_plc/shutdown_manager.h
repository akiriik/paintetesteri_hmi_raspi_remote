#pragma once

#include "opta_config.h"
#include "opta_state.h"
#include "io_manager.h"

// -----------------------------
// Sammutuksen käynnistys
// -----------------------------

void startShutdownTimer() {
  if (shutdownTimerRunning || shutdownRelayActivated) {
    return;
  }

  shutdownTimerRunning = true;
  shutdownTimerStartedMs = millis();

  Serial.println("Shutdown request received");
  Serial.print("Shutdown delay ms: ");
  Serial.println(SHUTDOWN_DELAY_MS);
}

// -----------------------------
// Sammutuksen peruutus
// -----------------------------

void cancelShutdownTimer() {
  if (shutdownRelayActivated) {
    return;
  }

  shutdownRequest = false;
  shutdownTimerRunning = false;
  shutdownTimerStartedMs = 0;

  ModbusRTUServer.holdingRegisterWrite(SHUTDOWN_REQUEST_REGISTER, 0);

  Serial.println("Shutdown request cancelled");
}

// -----------------------------
// Sammutusreleen aktivointi
// -----------------------------

void activateShutdownPowerRelay() {
  if (shutdownRelayActivated) {
    return;
  }

  shutdownRelayActivated = true;
  shutdownTimerRunning = false;

  setOptaOutput(SHUTDOWN_POWER_OPTA_OUTPUT_NUMBER, true);

  Serial.println("Shutdown Opta output activated");
}

// -----------------------------
// Sammutuksen loop
// -----------------------------

void updateShutdownManager() {
  if (shutdownRequest && !shutdownTimerRunning && !shutdownRelayActivated) {
    startShutdownTimer();
  }

  if (!shutdownTimerRunning) {
    return;
  }

  if (millis() - shutdownTimerStartedMs >= SHUTDOWN_DELAY_MS) {
    activateShutdownPowerRelay();
  }
}