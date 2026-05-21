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

  for (uint8_t i = 0; i < D1608E_RELAY_COUNT; i++) {
    ModbusRTUServer.holdingRegisterWrite(D1608E_RELAY_REGISTER_START + i, 0);
  }

  Serial.println("Modbus RTU Server started");
  Serial.print("Slave ID: ");
  Serial.println(MODBUS_SLAVE_ID);
  Serial.print("Baudrate: ");
  Serial.println(MODBUS_BAUDRATE);
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
  // SHUTDOWN_REQUEST_REGISTER = 17999
  // EMERGENCY_RESET_REGISTER = 19099
  // EMERGENCY_STATUS_REGISTER = 19100
  //
  // Näitä ei lisätä tähän vielä, koska ArduinoModbusin erilliset
  // rekisterialueet / iso aukollinen rekisterialue pitää päättää ennen käyttöönottoa.
}