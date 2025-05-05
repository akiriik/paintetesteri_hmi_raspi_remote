#!/usr/bin/env python3
# This Python file uses the following encoding: utf-8
import sys
import os

# Import the main window
from ui.main_window import MainWindow
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())