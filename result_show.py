from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtCore import QAbstractTableModel, Qt #,QLocale
from PyQt5.QtGui import QIcon, QDoubleValidator
from PyQt5.uic import loadUi
import sys, time, pathlib, os
import pandas as pd
import numpy as np
import math

class PandasTableModel(QAbstractTableModel):
    def __init__(self, data, hheaders, vheaders):
        super().__init__()
        self.data = data
        self.hheaders = hheaders
        self.vheaders = vheaders

    def rowCount(self, parent=None):
        return len(self.data)

    def columnCount(self, parent=None):
        return len(self.data.columns)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            value = self.data.iloc[index.row(), index.column()]

            if pd.isnull(value):
                return '-'

            if isinstance(value, float):
                return f'{value:.3g}'

        return None

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.hheaders[section]

            if orientation == Qt.Vertical:
                return self.vheaders[section]

class MainUI(QMainWindow):
    def __init__(self):
        super(MainUI, self).__init__()
        loadUi("harm_ui.ui", self)
        self.setWindowIcon(QIcon("logo.png"))
        self.tabWidget.setTabEnabled(1, True)

        df = pd.read_csv("result.csv", index_col=0)
        
        print(df)

        # df['mean'] = df.mean(axis=1)
        # df['stdev'] = df.drop(['mean'], axis=1).std(axis=1)
        # df["percent"] = (100*df["stdev"]/df["mean"]).round(decimals=1).abs()

        df_header_v = df.index
        df_header_h = df.columns

        model = PandasTableModel(df, df_header_h, df_header_v)
        self.tblView_Result_1.setModel(model)
   
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # app = QApplication([])
    harm = MainUI()
    harm.show()
    
    # app.exec_()
    sys.exit(app.exec_())