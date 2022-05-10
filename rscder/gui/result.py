
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt,QModelIndex, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import (QTableWidgetItem, QTableWidget, QAbstractItemView, QHeaderView, QStyleFactory)

from rscder.utils.project import PairLayer, ResultLayer

class ResultTable(QtWidgets.QWidget):

    on_item_click = pyqtSignal(dict)
    on_item_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super(ResultTable, self).__init__(parent)
        # self.tableview = QTableView(self)
        self.tablewidget = QTableWidget(self)
        self.tablewidget.setColumnCount(5)
        self.tablewidget.setRowCount(0)
        self.tablewidget.setHorizontalHeaderLabels(['序号', 'X', 'Y', '概率', '变化'])
        self.tablewidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.tablewidget.cellDoubleClicked.connect(self.onDoubleClicked)
        self.tablewidget.cellClicked.connect(self.onClicked)
        self.tablewidget.cellChanged.connect(self.onChanged)

        # self.tablewidget.setModel(self.tableview)
        # self.tableview
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.tablewidget)
        self.setLayout(layout)

    def clear(self):
        pass
    
    def onChanged(self, row, col):
        if col == 4:
            item_idx = row
            item_status = self.tablewidget.item(row, col).checkState() == Qt.Checked
            self.on_item_changed.emit({'idx':item_idx, 'status':item_status})

    def onClicked(self, row, col):
        if col == 4:
            self.tablewidget.item(row, col).setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
    
    def onDoubleClicked(self, row, col):
        x = self.tablewidget.item(row, 1).text()
        y = self.tablewidget.item(row, 2).text()
        self.on_item_click.emit({'x':x, 'y':y})

    def set_data(self, data:ResultLayer):
        self.tablewidget.setRowCount(len(data.data))
        for i, d in enumerate(data.data):
            self.tablewidget.setItem(i, 0, QTableWidgetItem(str(i+1)))
            self.tablewidget.setItem(i, 1, QTableWidgetItem(str(d[0]))) # X
            self.tablewidget.setItem(i, 2, QTableWidgetItem(str(d[1]))) # Y
            self.tablewidget.setItem(i, 3, QTableWidgetItem(str(d[2]))) # 概率
            status_item = QTableWidgetItem('变化')
            if d[3] == 0:
                status_item.setBackground(Qt.green)
                status_item.setCheckState(Qt.Unchecked)
            elif d[3] == 1:
                status_item.setBackground(Qt.yellow)
                status_item.setCheckState(Qt.Checked)
            self.tablewidget.setItem(i, 4, status_item) # 变化
        self.tablewidget.resizeColumnsToContents()
        self.tablewidget.resizeRowsToContents()
        self.tablewidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablewidget.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
    


