#include "opta_config.h"
#include "opta_state.h"
#include "io_manager.h"
#include "modbus_manager.h"
#include "sequence_engine.h"

void setup() {
  Serial.begin(SERIAL_BAUDRATE);
  delay(1000);

  Serial.println("Opta D1608E / onboard IO / Modbus");

  initOptaOnboardIO();
  initExpansionIO();

  setAllOptaOutputsOff();
  setAllD1608ERelaysOff();

  initModbusServer();

  Serial.println("Opta ready");
}

void loop() {
  pollModbus();

  readOptaInputs();
  readD1608EInputs();

  handleModbusRelayRegisters();
  handleModbusSystemRegisters();

  updateSequenceEngine();

  updateOptaControllerThrottled();
}