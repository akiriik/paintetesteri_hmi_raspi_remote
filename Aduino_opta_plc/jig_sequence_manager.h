#pragma once

#include "opta_config.h"
#include "opta_state.h"
#include "io_manager.h"

// -----------------------------
// Jigin releiden apufunktiot
// -----------------------------

void setJigCylinder1(bool state) {
  setD1608ERelayByNumber(JIG_CYL1_RELAY_NUMBER, state);
}

void setJigCylinder2(bool state) {
  setD1608ERelayByNumber(JIG_CYL2_RELAY_NUMBER, state);
}

void setJigCylinder3(bool state) {
  setD1608ERelayByNumber(JIG_CYL3_RELAY_NUMBER, state);
}

void setAllJigCylindersOff() {
  setJigCylinder1(false);
  setJigCylinder2(false);
  setJigCylinder3(false);
}

// -----------------------------
// Modbus status
// -----------------------------

void writeJigSequenceStatus(uint16_t status) {
  jigSequenceStatus = status;
  ModbusRTUServer.holdingRegisterWrite(JIG_SEQUENCE_STATUS_REGISTER, status);
}

void writeJigSequenceStep(uint16_t step) {
  jigSequenceStep = step;
  ModbusRTUServer.holdingRegisterWrite(JIG_SEQUENCE_STEP_REGISTER, step);
}

void writeJigSequenceError(uint16_t errorCode) {
  jigSequenceError = errorCode;
  ModbusRTUServer.holdingRegisterWrite(JIG_SEQUENCE_ERROR_REGISTER, errorCode);
}

void setJigSequenceStep(uint16_t step) {
  jigSequenceStep = step;
  jigSequenceStepStartedMs = millis();
  writeJigSequenceStep(jigSequenceStep);
}

// -----------------------------
// Sekvenssin lopetus / keskeytys
// -----------------------------

void finishJigSequence() {
  jigSequenceRunning = false;
  jigSequenceCommand = JIG_SEQUENCE_NONE;
  jigSequenceStep = 0;

  writeJigSequenceStatus(JIG_SEQUENCE_STATUS_DONE);
  writeJigSequenceStep(0);

  ModbusRTUServer.holdingRegisterWrite(JIG_SEQUENCE_START_REGISTER, 0);
  ModbusRTUServer.holdingRegisterWrite(JIG_SEQUENCE_COMMAND_REGISTER, 0);
}

void abortJigSequence(uint16_t errorCode) {
  setAllJigCylindersOff();

  jigSequenceRunning = false;
  jigSequenceCommand = JIG_SEQUENCE_NONE;
  jigSequenceStep = 0;

  writeJigSequenceError(errorCode);
  writeJigSequenceStatus(JIG_SEQUENCE_STATUS_ERROR);
  writeJigSequenceStep(0);

  ModbusRTUServer.holdingRegisterWrite(JIG_SEQUENCE_START_REGISTER, 0);
  ModbusRTUServer.holdingRegisterWrite(JIG_SEQUENCE_STOP_REGISTER, 0);
  ModbusRTUServer.holdingRegisterWrite(JIG_SEQUENCE_COMMAND_REGISTER, 0);
}

// -----------------------------
// Sekvenssin käynnistys
// -----------------------------

bool isKnownJigSequenceCommand(uint16_t command) {
  return (
    command == JIG_SEQUENCE_COMMAND_PART_CLAMP ||
    command == JIG_SEQUENCE_COMMAND_PART_RELEASE ||
    command == JIG_SEQUENCE_COMMAND_PART_REMOVE
  );
}

void startJigSequence(uint16_t command) {
  if (jigSequenceRunning) {
    return;
  }

  if (emergencyStopActive) {
    abortJigSequence(JIG_SEQUENCE_ERROR_EMERGENCY_STOP);
    return;
  }

  if (!isKnownJigSequenceCommand(command)) {
    abortJigSequence(JIG_SEQUENCE_ERROR_UNKNOWN_COMMAND);
    return;
  }

  jigSequenceCommand = command;
  jigSequenceRunning = true;

  writeJigSequenceError(JIG_SEQUENCE_ERROR_NONE);
  writeJigSequenceStatus(JIG_SEQUENCE_STATUS_RUNNING);

  if (command == JIG_SEQUENCE_COMMAND_PART_CLAMP) {
    setJigCylinder2(true);
    setJigSequenceStep(1);
    return;
  }

  if (command == JIG_SEQUENCE_COMMAND_PART_RELEASE) {
    setJigCylinder3(false);
    setJigSequenceStep(1);
    return;
  }

  if (command == JIG_SEQUENCE_COMMAND_PART_REMOVE) {
    setJigCylinder3(false);
    setJigSequenceStep(1);
    return;
  }
}

// -----------------------------
// Modbus-komentojen käsittely
// -----------------------------

void handleModbusJigSequenceRegisters() {
  int commandValue = ModbusRTUServer.holdingRegisterRead(JIG_SEQUENCE_COMMAND_REGISTER);
  int startValue = ModbusRTUServer.holdingRegisterRead(JIG_SEQUENCE_START_REGISTER);
  int stopValue = ModbusRTUServer.holdingRegisterRead(JIG_SEQUENCE_STOP_REGISTER);

  if (stopValue != 0) {
    abortJigSequence(JIG_SEQUENCE_ERROR_ABORTED);
    return;
  }

  if (startValue != 0 && !jigSequenceRunning) {
    startJigSequence((uint16_t)commandValue);
  }
}

// -----------------------------
// PART_CLAMP = kappale kiinni
//
// Alkutapahtuma käynnistyksessä:
// SYL2 kiinni
//
// Vaiheet:
// 1 odota 1000 ms
// 2 SYL1 kiinni, odota 150 ms
// 3 SYL1 auki, odota 800 ms
// 4 SYL3 kiinni, odota 500 ms
// 5 SYL3 auki, odota 500 ms
// 6 SYL1 kiinni, odota 500 ms
// 7 SYL3 kiinni, valmis
// -----------------------------

void updatePartClampSequence() {
  unsigned long elapsedMs = millis() - jigSequenceStepStartedMs;

  switch (jigSequenceStep) {
    case 1:
      if (elapsedMs >= PART_CLAMP_SYL2_CLOSE_WAIT_MS) {
        setJigCylinder1(true);
        setJigSequenceStep(2);
      }
      break;

    case 2:
      if (elapsedMs >= PART_CLAMP_SYL1_CLOSE_WAIT_MS) {
        setJigCylinder1(false);
        setJigSequenceStep(3);
      }
      break;

    case 3:
      if (elapsedMs >= PART_CLAMP_SYL1_OPEN_WAIT_MS) {
        setJigCylinder3(true);
        setJigSequenceStep(4);
      }
      break;

    case 4:
      if (elapsedMs >= PART_CLAMP_SYL3_CLOSE_1_WAIT_MS) {
        setJigCylinder3(false);
        setJigSequenceStep(5);
      }
      break;

    case 5:
      if (elapsedMs >= PART_CLAMP_SYL3_OPEN_WAIT_MS) {
        setJigCylinder1(true);
        setJigSequenceStep(6);
      }
      break;

    case 6:
      if (elapsedMs >= PART_CLAMP_SYL1_CLOSE_2_WAIT_MS) {
        setJigCylinder3(true);
        finishJigSequence();
      }
      break;

    default:
      abortJigSequence(JIG_SEQUENCE_ERROR_INVALID_STEP);
      break;
  }
}

// -----------------------------
// PART_RELEASE = kappale irti
//
// Alkutapahtuma käynnistyksessä:
// SYL3 auki
//
// Vaiheet:
// 1 odota 500 ms
// 2 SYL1 auki, odota 500 ms
// 3 SYL2 auki, valmis
// -----------------------------

void updatePartReleaseSequence() {
  unsigned long elapsedMs = millis() - jigSequenceStepStartedMs;

  switch (jigSequenceStep) {
    case 1:
      if (elapsedMs >= PART_RELEASE_SYL3_OPEN_WAIT_MS) {
        setJigCylinder1(false);
        setJigSequenceStep(2);
      }
      break;

    case 2:
      if (elapsedMs >= PART_RELEASE_SYL1_OPEN_WAIT_MS) {
        setJigCylinder2(false);
        finishJigSequence();
      }
      break;

    default:
      abortJigSequence(JIG_SEQUENCE_ERROR_INVALID_STEP);
      break;
  }
}

// -----------------------------
// PART_REMOVE = kappaleen poisto
//
// Alkutapahtuma käynnistyksessä:
// SYL3 auki
//
// Vaiheet:
// 1 odota 500 ms
// 2 SYL1 auki, odota 500 ms
// 3 SYL2 auki, odota 1000 ms
// 4 SYL3 kiinni, odota 1000 ms
// 5 SYL3 auki, valmis
// -----------------------------

void updatePartRemoveSequence() {
  unsigned long elapsedMs = millis() - jigSequenceStepStartedMs;

  switch (jigSequenceStep) {
    case 1:
      if (elapsedMs >= PART_REMOVE_SYL3_OPEN_1_WAIT_MS) {
        setJigCylinder1(false);
        setJigSequenceStep(2);
      }
      break;

    case 2:
      if (elapsedMs >= PART_REMOVE_SYL1_OPEN_WAIT_MS) {
        setJigCylinder2(false);
        setJigSequenceStep(3);
      }
      break;

    case 3:
      if (elapsedMs >= PART_REMOVE_SYL2_OPEN_WAIT_MS) {
        setJigCylinder3(true);
        setJigSequenceStep(4);
      }
      break;

    case 4:
      if (elapsedMs >= PART_REMOVE_SYL3_CLOSE_WAIT_MS) {
        setJigCylinder3(false);
        finishJigSequence();
      }
      break;

    default:
      abortJigSequence(JIG_SEQUENCE_ERROR_INVALID_STEP);
      break;
  }
}

// -----------------------------
// Sekvenssi-loop
// -----------------------------

void updateJigSequenceManager() {
  if (!jigSequenceRunning) {
    return;
  }

  if (emergencyStopActive) {
    abortJigSequence(JIG_SEQUENCE_ERROR_EMERGENCY_STOP);
    return;
  }

  if (jigSequenceCommand == JIG_SEQUENCE_COMMAND_PART_CLAMP) {
    updatePartClampSequence();
    return;
  }

  if (jigSequenceCommand == JIG_SEQUENCE_COMMAND_PART_RELEASE) {
    updatePartReleaseSequence();
    return;
  }

  if (jigSequenceCommand == JIG_SEQUENCE_COMMAND_PART_REMOVE) {
    updatePartRemoveSequence();
    return;
  }

  abortJigSequence(JIG_SEQUENCE_ERROR_UNKNOWN_COMMAND);
}