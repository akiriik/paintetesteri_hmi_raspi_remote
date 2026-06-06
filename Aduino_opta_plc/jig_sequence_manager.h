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

void startJigSequence(uint16_t command) {
  if (jigSequenceRunning) {
    return;
  }

  if (emergencyStopActive) {
    abortJigSequence(JIG_SEQUENCE_ERROR_EMERGENCY_STOP);
    return;
  }

  if (command != JIG_SEQUENCE_COMMAND_PART_CLAMP) {
    abortJigSequence(JIG_SEQUENCE_ERROR_UNKNOWN_COMMAND);
    return;
  }

  setAllJigCylindersOff();

  jigSequenceCommand = command;
  jigSequenceRunning = true;
  jigSequenceStep = 1;
  jigSequenceStepStartedMs = millis();

  writeJigSequenceError(JIG_SEQUENCE_ERROR_NONE);
  writeJigSequenceStatus(JIG_SEQUENCE_STATUS_RUNNING);
  writeJigSequenceStep(jigSequenceStep);
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
// Kappale kiinni -sekvenssi
//
// Releet:
// D1608E R1 = sylinteri 1
// D1608E R2 = sylinteri 2
// D1608E R3 = sylinteri 3
// -----------------------------

void updatePartClampSequence() {
  unsigned long elapsedMs = millis() - jigSequenceStepStartedMs;

  switch (jigSequenceStep) {
    case 1:
      if (elapsedMs >= DELAY_SYL1_ON) {
        setJigCylinder1(true);
        jigSequenceStep = 2;
        jigSequenceStepStartedMs = millis();
        writeJigSequenceStep(jigSequenceStep);
      }
      break;

    case 2:
      if (elapsedMs >= DELAY_SYL1_OFF) {
        setJigCylinder1(false);
        jigSequenceStep = 3;
        jigSequenceStepStartedMs = millis();
        writeJigSequenceStep(jigSequenceStep);
      }
      break;

    case 3:
      if (elapsedMs >= DELAY_SYL3_ON) {
        setJigCylinder3(true);
        jigSequenceStep = 4;
        jigSequenceStepStartedMs = millis();
        writeJigSequenceStep(jigSequenceStep);
      }
      break;

    case 4:
      if (elapsedMs >= DELAY_SYL2_ON) {
        setJigCylinder2(true);
        jigSequenceStep = 5;
        jigSequenceStepStartedMs = millis();
        writeJigSequenceStep(jigSequenceStep);
      }
      break;

    case 5:
      if (elapsedMs >= DELAY_SYL1_ON) {
        setJigCylinder1(true);
        jigSequenceStep = 6;
        jigSequenceStepStartedMs = millis();
        writeJigSequenceStep(jigSequenceStep);
      }
      break;

    case 6:
      if (elapsedMs >= SEQUENCE_COMPLETION_DELAY) {
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

  abortJigSequence(JIG_SEQUENCE_ERROR_UNKNOWN_COMMAND);
}