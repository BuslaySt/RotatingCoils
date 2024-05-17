import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableView, QVBoxLayout, QWidget
from PyQt5.QtCore import QAbstractTableModel, Qt
import pandas as pd

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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Create a Pandas DataFrame
        data = {'Column1': [1, 2, 3],
                'Column2': [4, 5, 6],
                'Column3': [7, 8, 9]}
        df = pd.DataFrame(data)

        # Create a table view and set the model
        self.table_view = QTableView(self)
        model = PandasTableModel(df)
        self.table_view.setModel(model)

        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(self.table_view)

        # Set the layout to the main window
        central_widget = QWidget(self)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    mainWin.show()
    sys.exit(app.exec_())