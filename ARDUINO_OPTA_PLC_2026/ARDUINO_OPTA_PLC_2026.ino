#include "OptaBlue.h"
#include <ArduinoRS485.h>
#include <ArduinoModbus.h>

using namespace Opta;

// -----------------------------
// Modbus-asetukset
// -----------------------------

const uint8_t MODBUS_SLAVE_ID = 1;
const unsigned long MODBUS_BAUDRATE = 19200;

// Dualtester:
// OPTA_RELAY_REGISTER_BASE = 18098
// Rele 1 = 18098 + 1 = 18099
// Rele 8 = 18098 + 8 = 18106
const uint16_t RELAY_REGISTER_START = 18099;
const uint8_t RELAY_COUNT = 8;

const uint16_t HOLDING_REGISTER_START = RELAY_REGISTER_START;
const uint16_t HOLDING_REGISTER_COUNT = RELAY_COUNT;

// -----------------------------
// D1608E-asetukset
// -----------------------------

// D1608E output indexit 0...7
// Rele 1 = output 0
// Rele 8 = output 7
bool relayStates[RELAY_COUNT] = {false, false, false, false, false, false, false, false};
int lastRegisterValues[RELAY_COUNT] = {-1, -1, -1, -1, -1, -1, -1, -1};

// OptaController.update throttlaus
unsigned long lastOptaUpdateMs = 0;
const unsigned long OPTA_UPDATE_INTERVAL_MS = 100;

void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println("Opta D1608E relay 1-8 Modbus test");

  OptaController.begin();

  // Annetaan D1608E-laajennukselle hetki löytyä
  unsigned long startMs = millis();
  while (millis() - startMs < 1000) {
    OptaController.update();
  }

  // Kaikki releet pois päältä alussa
  setAllD1608ERelaysOff();

  // Arduino Opta RS485 turnaround / Modbus RTU frame delay
  // 19200 baudilla noin 1750 us.
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
    HOLDING_REGISTER_START,
    HOLDING_REGISTER_COUNT
  );

  for (uint8_t i = 0; i < RELAY_COUNT; i++) {
    ModbusRTUServer.holdingRegisterWrite(RELAY_REGISTER_START + i, 0);
  }

  Serial.println("Modbus RTU Server started");
  Serial.print("Slave ID: ");
  Serial.println(MODBUS_SLAVE_ID);
  Serial.print("Baudrate: ");
  Serial.println(MODBUS_BAUDRATE);
  Serial.print("Relay register start: ");
  Serial.println(RELAY_REGISTER_START);
  Serial.print("Relay count: ");
  Serial.println(RELAY_COUNT);
  Serial.print("RS485 pre/post delay us: ");
  Serial.println(preDelayBR);
}

void loop() {
  // Vastaa Modbus-pyyntöihin mahdollisimman usein
  ModbusRTUServer.poll();

  handleRelayRegisters();

  // Älä aja expansion updatea joka kierroksella
  if (millis() - lastOptaUpdateMs >= OPTA_UPDATE_INTERVAL_MS) {
    lastOptaUpdateMs = millis();
    OptaController.update();
  }
}

void handleRelayRegisters() {
  for (uint8_t relayIndex = 0; relayIndex < RELAY_COUNT; relayIndex++) {
    uint16_t registerAddress = RELAY_REGISTER_START + relayIndex;

    int registerValue = ModbusRTUServer.holdingRegisterRead(registerAddress);

    if (registerValue == lastRegisterValues[relayIndex]) {
      continue;
    }

    lastRegisterValues[relayIndex] = registerValue;

    bool newState = (registerValue != 0);

    if (newState == relayStates[relayIndex]) {
      continue;
    }

    relayStates[relayIndex] = newState;
    setD1608ERelay(relayIndex, relayStates[relayIndex]);
  }
}

void setD1608ERelay(uint8_t relayIndex, bool state) {
  if (relayIndex >= RELAY_COUNT) {
    return;
  }

  for (int i = 0; i < OPTA_CONTROLLER_MAX_EXPANSION_NUM; i++) {
    DigitalMechExpansion mechExp = OptaController.getExpansion(i);

    if (mechExp) {
      // relayIndex 0 = D1608E rele 1
      // relayIndex 7 = D1608E rele 8
      mechExp.digitalWrite(relayIndex, state ? HIGH : LOW);
      mechExp.updateDigitalOutputs();
      return;
    }
  }

  Serial.println("D1608E expansion not found");
}

void setAllD1608ERelaysOff() {
  for (int i = 0; i < OPTA_CONTROLLER_MAX_EXPANSION_NUM; i++) {
    DigitalMechExpansion mechExp = OptaController.getExpansion(i);

    if (mechExp) {
      for (uint8_t relayIndex = 0; relayIndex < RELAY_COUNT; relayIndex++) {
        mechExp.digitalWrite(relayIndex, LOW);
        relayStates[relayIndex] = false;
      }

      mechExp.updateDigitalOutputs();
      return;
    }
  }

  Serial.println("D1608E expansion not found at startup");
}