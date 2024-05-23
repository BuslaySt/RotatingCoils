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
            # if np.isnan(value):
            if pd.isnull(value):
                return '-'

            if isinstance(value, float):
                # Render float to 6 dp
                return f"{value:.6f}"

        return None

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.hheaders[section]

            if orientation == Qt.Vertical:
                return self.vheaders[section]

    # def headerData(self, section, orientation, role=Qt.DisplayRole):
    #     if role == Qt.DisplayRole and orientation == Qt.Horizontal:
    #         return self.hheaders[section]
    #     if role == Qt.DisplayRole and orientation == Qt.Vertical:
    #         return self.vheaders[section]
    #     return None

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
        df.drop(['name', '0', '1', '2', '3', '4'], axis=1, inplace=True)
        # print(df)
        df_header_h = ['Среднее', 'Абс. откл.', 'Откл. в %']
        df_header_v = ["harm01", "harm02", "harm03", "harm04", "harm05", "harm06", "harm07", "harm08", "harm09", "harm10",
                        "harm11", "harm12", "harm13", "harm14", "harm15", "harm16", "deltaX", "deltaY", "alpha", 'H_avg']
        model = PandasTableModel(df, df_header_h, df_header_v)
        self.tblView_Result_1.setModel(model)
   
if __name__ == '__main__':
    app = QApplication(sys.argv)
    # app = QApplication([])
    harm = MainUI()
    harm.show()
    
    # app.exec_()
    sys.exit(app.exec_())