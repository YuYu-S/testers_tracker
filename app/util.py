""" Module for creating a graphical user interface (GUI) components with PyQt5.

Copyright (C) Seagate Technology LLC, 2025. All rights reserved.
"""
from PyQt5.QtWidgets import QPushButton, QLabel, QTableWidget, QLineEdit, QFileDialog
from PyQt5.QtGui import QFont
from PyQt5.QtCore import QTimer
from typing import Callable, Optional, List

# Function to enable/disable a button
def enableButton(button: QPushButton, enable: bool = True) -> QPushButton:
    if enable:
        button.setEnabled(True)
    else:
        button.setEnabled(False)
    return button

# Function to create a label with optional font size
def createLabel(text: str, font: int = 10) -> QLabel:
    label = QLabel(text)
    label.setFont(setFontSize(font))

    return label

# Function to create a push button with a name, connected function, and optional font size
def createPushButton(name: str, func: Callable, font: int = 10) -> QPushButton:
    button = QPushButton(name)
    button.setFont(setFontSize(font))
    button.clicked.connect(func)
    button.adjustSize()

    return button

# Function to create a table with optional font size, row labels, and column labels
def createTable(
        font:          int = 10,
        labels_row:    Optional[List[str]] = None,
        labels_column: Optional[List[str]] = None,
        height:        int = 110
) -> QTableWidget:

    if labels_row is None:    labels_row = []
    if labels_column is None: labels_column = []

    table = QTableWidget(len(labels_row), len(labels_column))

    table.setHorizontalHeaderLabels(labels_column)
    table.setVerticalHeaderLabels(labels_row)
    table.setFixedHeight(height)
    table.setFont(setFontSize(font))

    return table

# Function to create a text field with optional font size
def createTextField(font: int = 10) -> QLineEdit:
    text_field = QLineEdit()
    text_field.setPlaceholderText("default: 120.0 hours")
    text_field.setFont(setFontSize(font))

    return text_field

# Function to get a folder path (data path)
def getDataPath() -> str:
    data_path = QFileDialog.getExistingDirectory(None, "Select Folder", r'c:\tracking')

    return data_path

# Function to create a timer to refresh the window
def getTimer(func: Callable) -> QTimer:
    timer = QTimer()
    timer.timeout.connect(func)

    return timer

# Function to set the font size
def setFontSize(size: int) -> QFont:
    font = QFont()
    font.setPointSize(size)

    return font
