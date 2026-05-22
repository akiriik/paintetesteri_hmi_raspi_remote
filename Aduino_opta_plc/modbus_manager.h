#pragma once

#include "opta_config.h"
#include "opta_state.h"
#include "io_manager.h"

// -----------------------------
// Modbus alustus
// -----------------------------

void initModbusServer() {
  constexpr float bitduration = 1.0f / MODBUS_BAUDRATE;

  constexpr unsigned long preDelayBR =
    static_cast<unsigned long>(bitduration * 9.6f * 3.5f * 1000000.0f);

  constexpr unsigned long postDelayBR =
    static_cast<unsigned long>(bitduration * 9.6f * 3.5f * 1000000.0f);

  RS485.setDelays(preDelayBR, postDelayBR);

  if (!ModbusRTUServer.begin(MODBUS_SLAVE_ID, MODBUS_BAUDRATE, SERIAL_8N1)) {
    Serial.println("Failed to start Modbus RTU Server!");

    while (1) {
      delay(1000);
    }
  }

  ModbusRTUServer.configureHoldingRegisters(
    MODBUS_HOLDING_REGISTER_START,
    MODBUS_HOLDING_REGISTER_COUNT
  );

  ModbusRTUServer.holdingRegisterWrite(SHUTDOWN_REQUEST_REGISTER, 0);
  ModbusRTUServer.holdingRegisterWrite(EMERGENCY_RESET_REGISTER, 0);
  ModbusRTUServer.holdingRegisterWrite(EMERGENCY_STATUS_REGISTER, EMERGENCY_STATUS_OK);

  for (uint8_t i = 0; i < D1608E_RELAY_COUNT; i++) {
    ModbusRTUServer.holdingRegisterWrite(D1608E_RELAY_REGISTER_START + i, 0);
  }

  Serial.println("Modbus RTU Server started");
  Serial.print("Slave ID: ");
  Serial.println(MODBUS_SLAVE_ID);
  Serial.print("Baudrate: ");
  Serial.println(MODBUS_BAUDRATE);
  Serial.print("Holding register start: ");
  Serial.println(MODBUS_HOLDING_REGISTER_START);
  Serial.print("Holding register count: ");
  Serial.println(MODBUS_HOLDING_REGISTER_COUNT);
  Serial.print("Shutdown register: ");
  Serial.println(SHUTDOWN_REQUEST_REGISTER);
  Serial.print("Relay register start: ");
  Serial.println(D1608E_RELAY_REGISTER_START);
  Serial.print("Relay count: ");
  Serial.println(D1608E_RELAY_COUNT);
  Serial.print("RS485 pre/post delay us: ");
  Serial.println(preDelayBR);
}

// -----------------------------
// Modbus loop
// -----------------------------

void pollModbus() {
  ModbusRTUServer.poll();
}

// -----------------------------
// Shutdown-rekisteri
// -----------------------------

void handleModbusShutdownRegister() {
  int registerValue = ModbusRTUServer.holdingRegisterRead(SHUTDOWN_REQUEST_REGISTER);

  if (registerValue == lastShutdownRegisterValue) {
    return;
  }

  lastShutdownRegisterValue = registerValue;

  if (registerValue != 0) {
    shutdownRequest = true;
  }
}

void handleModbusEmergencyResetRegister() {
  int registerValue = ModbusRTUServer.holdingRegisterRead(EMERGENCY_RESET_REGISTER);

  if (registerValue == lastEmergencyResetRegisterValue) {
    return;
  }

  lastEmergencyResetRegisterValue = registerValue;

  if (registerValue != 0) {
    emergencyResetRequest = true;
    ModbusRTUServer.holdingRegisterWrite(EMERGENCY_RESET_REGISTER, 0);
    lastEmergencyResetRegisterValue = 0;
  }
}

// -----------------------------
// Releiden Modbus-käsittely
// -----------------------------

void handleModbusRelayRegisters() {
  for (uint8_t relayIndex = 0; relayIndex < D1608E_RELAY_COUNT; relayIndex++) {
    uint16_t registerAddress = D1608E_RELAY_REGISTER_START + relayIndex;

    int registerValue = ModbusRTUServer.holdingRegisterRead(registerAddress);

    if (registerValue == d1608eLastRelayRegisterValues[relayIndex]) {
      continue;
    }

    d1608eLastRelayRegisterValues[relayIndex] = registerValue;

    bool newState = (registerValue != 0);

    if (newState == d1608eRelayStates[relayIndex]) {
      continue;
    }

    setD1608ERelay(relayIndex, newState);
  }
}

// -----------------------------
// Järjestelmärekisterit
// -----------------------------

void handleModbusSystemRegisters() {
  // Ei vielä käytössä.
  // EMERGENCY_RESET_REGISTER = 19099
  // EMERGENCY_STATUS_REGISTER = 19100
  //
  // Näitä ei lisätä tähän vielä, koska silloin rekisterialue kasvaisi
  // 17999...19100 asti.
}