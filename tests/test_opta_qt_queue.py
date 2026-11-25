"""Reaalinen PyQt5/Qt QThread -integraatiotesti Optan kirjoitusjonolle."""
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "dualtester"))

from PyQt5.QtCore import QCoreApplication, QEventLoop, QTimer
from utils import modbus_manager


class FakeWriteResponse:
    def isError(self):
        return False


class FakeOptaModbus:
    def __init__(self, port=None, baudrate=None, **kwargs):
        self.connected = True
        self.calls = []

    def write_register(self, address, value):
        self.calls.append((address, value))
        return FakeWriteResponse()

    def close(self):
        self.connected = False


class OptaQtQueueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def test_queue_return_and_real_worker_ack(self):
        with patch.object(modbus_manager, "ModbusHandler", FakeOptaModbus):
            manager = modbus_manager.ModbusManager(port="/dev/fake-opta")
            seen = []
            loop = QEventLoop()

            def on_ack(address, value, success, message):
                seen.append((address, value, success, message))
                loop.quit()

            manager.writeAcknowledged.connect(on_ack)
            try:
                queued = manager.write_register(18092, 0)
                print(f"PYQT5_QUEUE_RETURN={queued!r}")
                QTimer.singleShot(1500, loop.quit)
                loop.exec_()
                self.assertEqual(
                    seen, [(18092, 0, True, "")],
                    "Worker ei lähettänyt Optan kirjoituskuittausta",
                )
                self.assertTrue(
                    queued,
                    "Worker suoritti kirjoituksen, mutta jonotuksen paluuarvo ilmoitti virheen",
                )
            finally:
                manager.cleanup()


if __name__ == "__main__":
    unittest.main()
