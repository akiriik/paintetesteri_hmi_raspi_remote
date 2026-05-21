#pragma once

#include "opta_config.h"
#include "opta_state.h"
#include "io_manager.h"

// -----------------------------
// Sekvenssimoottorin ohjaus
// -----------------------------

void startSequence() {
  if (sequenceRunning) {
    return;
  }

  sequenceRunning = true;
  sequenceCurrentStep = 0;
  sequenceStepStartedMs = millis();

  setAllD1608ERelaysOff();
  setAllOptaOutputsOff();
}

void stopSequence() {
  sequenceRunning = false;
  sequenceCurrentStep = 0;
  sequenceStepStartedMs = 0;

  setAllD1608ERelaysOff();
  setAllOptaOutputsOff();
}

void nextSequenceStep() {
  sequenceCurrentStep++;
  sequenceStepStartedMs = millis();

  if (sequenceCurrentStep >= SEQUENCE_MAX_STEPS) {
    stopSequence();
  }
}

// -----------------------------
// Sekvenssiaskeleet
// -----------------------------

void applySequenceStep(uint8_t step) {
  switch (step) {
    case 0:
      // Varattu myöhemmälle rele-/venttiilisekvenssille
      break;

    case 1:
      // Varattu myöhemmälle rele-/venttiilisekvenssille
      break;

    case 2:
      // Varattu myöhemmälle rele-/venttiilisekvenssille
      break;

    case 3:
      // Varattu myöhemmälle rele-/venttiilisekvenssille
      break;

    case 4:
      // Varattu myöhemmälle rele-/venttiilisekvenssille
      break;

    case 5:
      // Varattu myöhemmälle rele-/venttiilisekvenssille
      break;

    case 6:
      // Varattu myöhemmälle rele-/venttiilisekvenssille
      break;

    case 7:
      // Varattu myöhemmälle rele-/venttiilisekvenssille
      break;

    case 8:
      // Varattu myöhemmälle rele-/venttiilisekvenssille
      break;

    case 9:
      // Varattu myöhemmälle rele-/venttiilisekvenssille
      break;

    default:
      stopSequence();
      break;
  }
}

// -----------------------------
// Sekvenssimoottorin loop
// -----------------------------

void updateSequenceEngine() {
  if (!sequenceRunning) {
    return;
  }

  applySequenceStep(sequenceCurrentStep);

  if (millis() - sequenceStepStartedMs >= sequenceStepTimeMs[sequenceCurrentStep]) {
    nextSequenceStep();
  }
}