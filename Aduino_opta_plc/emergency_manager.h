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
// Hätäseisin pakkoalasajo
// -----------------------------

void forceEmergencyControlledOutputsOff() {
  // Hätäseis ei katkaise Optan releitä 1 ja 2:
  // rele 1 = järjestelmän sammutus
  // rele 2 = hätäseisvalo / shutdown-valo
  // Hätäseis katkaisee testiventtiilit ja D1608E-releet.

  setOptaOutput(FORTEST1_TEST_VALVE_OPTA_OUTPUT_NUMBER, false);
  setOptaOutput(FORTEST2_TEST_VALVE_OPTA_OUTPUT_NUMBER, false);

  ModbusRTUServer.holdingRegisterWrite(FORTEST1_TEST_VALVE_REGISTER, 0);
  ModbusRTUServer.holdingRegisterWrite(FORTEST2_TEST_VALVE_REGISTER, 0);

  setAllD1608ERelaysOff();

  for (uint8_t i = 0; i < D1608E_RELAY_COUNT; i++) {
    ModbusRTUServer.holdingRegisterWrite(D1608E_RELAY_REGISTER_START + i, 0);
    d1608eLastRelayRegisterValues[i] = 0;
  }

  jigSequenceRunning = false;
  jigSequenceCommand = JIG_SEQUENCE_NONE;
  jigSequenceStep = 0;
  jigSequenceError = JIG_SEQUENCE_ERROR_EMERGENCY_STOP;
  jigSequenceStatus = JIG_SEQUENCE_STATUS_ERROR;

  ModbusRTUServer.holdingRegisterWrite(JIG_SEQUENCE_COMMAND_REGISTER, 0);
  ModbusRTUServer.holdingRegisterWrite(JIG_SEQUENCE_START_REGISTER, 0);
  ModbusRTUServer.holdingRegisterWrite(JIG_SEQUENCE_STOP_REGISTER, 0);
  ModbusRTUServer.holdingRegisterWrite(JIG_SEQUENCE_STATUS_REGISTER, JIG_SEQUENCE_STATUS_ERROR);
  ModbusRTUServer.holdingRegisterWrite(JIG_SEQUENCE_STEP_REGISTER, 0);
  ModbusRTUServer.holdingRegisterWrite(JIG_SEQUENCE_ERROR_REGISTER, JIG_SEQUENCE_ERROR_EMERGENCY_STOP);

  emergencySafetyOutputsForcedOff = true;
}

// -----------------------------
// Hätäseisvalo / shutdown-valo
// -----------------------------

void setEmergencyLight(bool state) {
  emergencyLightState = state;
  setOptaOutput(EMERGENCY_LIGHT_OPTA_OUTPUT_NUMBER, state);
}

void updateEmergencyLightBlink() {
  // Hätäseis on tärkein tila:
  // jos hätäseis on aktiivinen, rele 2 vilkkuu.
  if (emergencyStopActive) {
    if (millis() - lastEmergencyLightBlinkMs >= EMERGENCY_LIGHT_BLINK_INTERVAL_MS) {
      lastEmergencyLightBlinkMs = millis();
      setEmergencyLight(!emergencyLightState);
    }

    return;
  }

  // Jos shutdown on käynnissä, rele 2 palaa jatkuvasti.
  // Tämä näyttää käyttäjälle 10 s viiveen aikana, että sammutus on aloitettu.
  if (shutdownTimerRunning || shutdownRelayActivated) {
    if (!emergencyLightState) {
      setEmergencyLight(true);
    }

    return;
  }

  // Normaali tila: rele 2 pois.
  if (emergencyLightState) {
    setEmergencyLight(false);
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
    emergencySafetyOutputsForcedOff = false;
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

  // Kun hätäseis on aktiivinen, pakotetaan ohjattavat lähdöt alas.
  // Tätä ei palauteta automaattisesti kuittauksessa.
  if (emergencyStopActive && !emergencySafetyOutputsForcedOff) {
    forceEmergencyControlledOutputsOff();
  }

  // Hätäseis poistuu vain dualtesteristä tulevalla kuittauksella,
  // eikä silloinkaan jos fyysinen hätäseis on edelleen aktiivinen.
  handleEmergencyResetRequest(emergencyButtonPhysicalActive);

  updateEmergencyStatusRegister();
  updateEmergencyLightBlink();
}
