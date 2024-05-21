from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtCore import QLocale, QAbstractTableModel, Qt
from PyQt5.QtGui import QIcon, QDoubleValidator
from PyQt5.uic import loadUi
import sys, time, pathlib, os
import pandas as pd
import numpy as np
import math

class PandasTableModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self.data = data

    def rowCount(self, parent=None):
        return len(self.data)

    def columnCount(self, parent=None):
        return len(self.data.columns)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return str(self.data.iloc[index.row(), index.column()])
        return None

class MainUI(QMainWindow):
    def __init__(self):
        super(MainUI, self).__init__()
        loadUi("harm_ui.ui", self)
        self.setWindowIcon(QIcon("logo.png"))
        self.tabWidget.setTabEnabled(1, True)

        df = pd.read_csv("result.csv")
        df.rename(columns = {'Unnamed: 0':'name'}, inplace = True)
        df["mean"] = df.iloc[:, 1:5].mean(axis=1)
        df["stdev"] = df.iloc[:, 1:5].std(axis=1)
        df["percent"] = (100*df.iloc[:, 1:5].std(axis=1)/df.iloc[:, 1:5].mean(axis=1)).round()
        df1 = df.drop(['0', '1', '2', '3', '4'], axis=1)
        print(df1)

        model = PandasTableModel(df1)
        self.tblView_Result_1.setModel(model)
   
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # app = QApplication([])
    harm = MainUI()
    harm.show()
    
    app.exec_()
    # sys.exit(app.exec_())