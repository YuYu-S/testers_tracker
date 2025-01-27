"""
This application allows users to:

1. View data by entering the number of hours from the current time.
2. View a yield table which has tester numbers, tester types, and yield percentages, with color
   coding to indicate healthy yields.
3. View pack information in a table, including pack numbers, HSA SN, disk bins, head bins, RCC, and
   RCC messages.
4. Access the MET file at the pack level by clicking on the pack number in the pack information
   table.
5. See an RCC summary table showing testers, date and time, RCC, and RCC messages.
6. Export data to an Excel file by clicking the 'Export Data File' button, with the option to choose
   the preferred directory.

The application retrieves data from ``C:\\Tracking``. If no CSV files are found in this directory,
the app will display a message indicating that it is unable to retrieve files to run the
application."

author  : Yu Yu Soe
version : 1.0

Copyright (C) Seagate Technology LLC, 2025. All rights reserved.
"""
from   app.data import Data
import app.util as util
import os
from   PyQt5.QtGui import QIcon
from   PyQt5.QtWidgets import (QApplication, QWidget, QTableWidgetItem, QVBoxLayout, QMessageBox,
                               QHBoxLayout, QPushButton, QTableWidget, QLineEdit)
import sys

import pandas as pd
from   typing import Optional, Tuple

class TestersTracker(QWidget):

    def __init__(self):
        super().__init__()

        self.button_submit = None
        self.data          = Data()
        self.data_path     = util.getDataPath()
        self.error         = None
        self.export_path   = None
        self.n_hours       = 120
        self.timer         = util.getTimer(self.refresh)

        # Set the window title, position and size, and assign a custom icon
        self.setWindowTitle('Testers Tracker')
        self.setGeometry(300, 200, 1200, 800)
        self.setWindowIcon(QIcon(r'../images/seagate.ico'))

        try:
            packs, yield_data, rcc = self.data.getData(
                data_path   = self.data_path,
                export_path = self.export_path,
                n_hours     = self.n_hours
            )

        except Exception as err:

            self.error = str(err)

            QMessageBox.information(self, "Warning from Testers Tracker", self.error)

            QApplication.exit()

        else:
            self.table_yield, self.table_packs, self.table_rcc, self.button_export = \
                self.createWindow(yield_data, packs, rcc)

            self.updatePackData(data=packs, tester=2)
            self.updateYieldTable(yield_data, packs)
            self.updateRccTable(rcc)

    def createInputHourLayout(self) -> QHBoxLayout:
        """
        Creates and returns a horizontal layout for entering hours. Includes a label, a text field
        for input, and a submit button.
        """
        layout_hours = QHBoxLayout()
        # Label for user instruction
        label = util.createLabel('Enter the number of hours (e.g., 2 or 2.5): ')

        # Create text field for user input
        text_field = util.createTextField(font=10)

        # Create ``Submit`` button to confirm the input
        self.button_submit = util.createPushButton('Submit', lambda: self.updateData(text_field))

        layout_hours.addWidget(label)
        layout_hours.addWidget(text_field)
        layout_hours.addWidget(self.button_submit)

        return layout_hours

    def createWindow(
        self,
        yield_data: pd.DataFrame,
        packs:      pd.DataFrame,
        rcc:        pd.DataFrame
    ) -> Tuple[QTableWidget, QTableWidget, QTableWidget, QPushButton]:

        layout_main = QVBoxLayout()

        self.setLayout(layout_main)

        layout_hour_input = self.createInputHourLayout()

        # create yield table
        #yield_columns      = [f'T{t}' for t in yield_data.index.tolist()]
        yield_columns      = yield_data.index.tolist()
        yield_rows         = ['type', 'yield %']
        widget_table_yield = util.createTable(labels_column=yield_columns, labels_row=yield_rows)

        # create packs table
        pack_columns      = packs.columns.tolist()
        widget_table_pack = util.createTable(labels_column=pack_columns, height=300)

        # create rcc table
        rcc_columns      = rcc.columns.tolist()
        widget_table_rcc = util.createTable(labels_column=rcc_columns, height=300)

        # create button to export data file to selected directory.
        widget_button_export_data = util.createPushButton(
            name = 'Export Data File',
            func = self.getDataExportPath
        )

        for table in [widget_table_yield, widget_table_pack, widget_table_rcc]:
            table.setStyleSheet("""
                QTableWidget {
                    border: 2px solid black;  /* Border around the table */
                    border-radius: 5px;       /* Rounded corners */
                    gridline-color: gray;     /* Color of grid lines */
                }
                QHeaderView::section {
                    background-color: lightgray;  /* Header background color */
                    font-weight: bold;            /* Header font style */
                }
            """)

        layout_main.addLayout(layout_hour_input)
        layout_main.addWidget(widget_table_yield)
        layout_main.addWidget(widget_table_pack)
        layout_main.addWidget(widget_table_rcc)
        layout_main.addWidget(widget_button_export_data)

        return widget_table_yield, widget_table_pack, widget_table_rcc, widget_button_export_data

    def getDataExportPath(self) -> str:

        self.export_path = util.getDataPath()

        if self.export_path:
            util.enableButton(self.button_export, enable=False)

        return self.export_path

    def openFile(self, file: str) -> None:
        """Open a file with the `.met` extension"""
        try:
            os.startfile(os.path.join(self.data_path, f'{file}.met'))
        except IOError as e:
            QMessageBox.critical(self, "Error", f"Could not open file: {e}")

    def refresh(self) -> None:

        try:
            util.enableButton(self.button_export, enable=True)

            packs, yield_data, rcc = self.data.getData(
                data_path=self.data_path,
                export_path=self.export_path,
                n_hours=self.n_hours
            )
    
            self.updateYieldTable(yield_data, packs)
            self.updateRccTable(rcc)
    
            self.export_path = None
    
            util.enableButton(self.button_submit, enable=True)

        except Exception as err:

            self.error = str(err)

            QMessageBox.information(self, "Warning from Testers Tracker", self.error)

            QApplication.exit()

    def runWindow(self) -> str:

        if self.error is None:
            #update data in every defined interval
            self.timer.start(30000)

        return self.error

    def updateData(self, hours_text_field: QLineEdit) -> None:
        """Retrieve and update data from now to the hours entered in the text field"""
        self.n_hours = float(hours_text_field.text())

        packs, yield_data,  rcc = self.data.getData(
            data_path   = self.data_path,
            export_path = self.export_path,
            n_hours     = self.n_hours
        )

        self.updateYieldTable(yield_data, packs)
        self.updatePackData(packs)
        self.updateRccTable(rcc)

        util.enableButton(self.button_submit, enable=False)

    def updatePackData(self, data: pd.DataFrame, tester: Optional[int] = None) -> None:
        """Update the content of the second table based on which tester number is clicked."""
        # Clear the second table's content first
        self.table_packs.clearContents()

        # Populate the second table with new items based on the clicked button
        if tester:
            data = data[data['tester'] == tester]

        data = data.sort_values('date_time', ascending=False)

        n_rows, n_cols = data.shape
        self.table_packs.setRowCount(n_rows)
        self.table_packs.setColumnCount(n_cols)

        for row in range(n_rows):
            for col in range(n_cols):
                item = str(data.iat[row, col])
                self.table_packs.setItem(row, col, QTableWidgetItem(item))
                self.table_packs.resizeColumnToContents(col)

                if col == 0:
                    button = util.createPushButton(
                        name=item,
                        func=lambda checked, filename=item: self.openFile(file=filename), font=10
                    )
                    self.table_packs.setCellWidget(row, col, button)

    def updateRccTable(self, data: pd.DataFrame) -> None:

        self.table_rcc.clearContents()

        n_rows, n_cols = data.shape

        self.table_rcc.setRowCount(n_rows)
        self.table_rcc.setColumnCount(n_cols)

        for row in range(n_rows):
            for col in range(n_cols):
                item_text = str(data.iat[row, col])
                self.table_rcc.setItem(row, col, QTableWidgetItem(item_text))
                self.table_rcc.resizeColumnToContents(col)

    def updateYieldTable(self, data: pd.DataFrame, pack_data:pd.DataFrame) -> QTableWidget:

        self.table_yield.clearContents()

        testers     = data.index.tolist()
        types_yield = data.columns.tolist()

        # The tester columns vary depending on the selected time frame.
        self.table_yield.setColumnCount(len(testers))
        self.table_yield.setHorizontalHeaderLabels(testers)

        for row, label in enumerate(types_yield):
            for col, tester in enumerate(testers):

                name = data.loc[tester, label]
                name_label = str(name)

                self.table_yield.setItem(row, col, QTableWidgetItem(name_label))
                self.table_yield.resizeColumnToContents(col)

                if not isinstance(name, str):

                    cell_num     = int(tester[1:])
                    tester_packs = pack_data[pack_data['tester'] == cell_num]

                    button = util.createPushButton(
                        name=name_label,
                        func=lambda checked, cell=cell_num, packs=tester_packs:
                        self.updatePackData(data=packs, tester=cell),
                        font=10
                    )

                    if name >= 80.0:          button.setStyleSheet("background-color: #32CD32")
                    elif 50.0 <= name < 80.0: button.setStyleSheet("background-color: yellow")
                    else:                     button.setStyleSheet("background-color: red")

                    self.table_yield.setCellWidget(row, col, button)

        return self.table_yield

if __name__ == "__main__":

    app = QApplication(sys.argv)

    testers_tracker = TestersTracker()
    error = testers_tracker.runWindow()

    if error is None:
        testers_tracker.show()
        sys.exit(app.exec_())
