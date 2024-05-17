import pandas as pd
from PyQt5.QtWidgets import *


# Подготовка данных
records = [
    (1, 'Vasya', 16),
    (2, 'Vasya2', 18),
    (3, 'Vasya3', 34),
    (4, 'Vasya4', 10),
    (5, 'Vasya5', 19),
]
df = pd.DataFrame(data=records, columns=['ID', 'NAME', 'AGE'])
headers = df.columns.values.tolist()

# Отображение данных на виджете
app = QApplication([])

table = QTableWidget()
table.setColumnCount(len(headers))
table.setHorizontalHeaderLabels(headers)

for i, row in df.iterrows():
    # Добавление строки
    table.setRowCount(table.rowCount() + 1)

    for j in range(table.columnCount()):
        table.setItem(i, j, QTableWidgetItem(str(row[j])))

table.show()

app.exec()