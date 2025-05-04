#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Väliaikainen tyhjä ohjelmasivu
"""
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt
from ui.screens.base_screen import BaseScreen

class ProgramScreen(BaseScreen):
    def __init__(self, parent=None, modbus=None):
        super().__init__(parent)
    
    def init_ui(self):
        # Sivun otsikko
        self.title = self.create_title("OHJELMAT")