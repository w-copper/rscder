
import logging
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt,QModelIndex, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import (QTableWidgetItem, QTableWidget, QMessageBox,  QAbstractItemView, QHeaderView, QStyleFactory)

from rscder.utils.project import PairLayer, Project, ResultLayer

class ResultTable(QtWidgets.QWidget):

    on_item_click = pyqtSignal(dict)
    on_item_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super(ResultTable, self).__init__(parent)
        # self.tableview = QTableView(self)
        self.tablewidget = QTableWidget(self)
        self.tablewidget.setColumnCount(4)
        self.tablewidget.setRowCount(0)
        self.tablewidget.setHorizontalHeaderLabels(['X', 'Y', '概率', '变化'])
        self.tablewidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.tablewidget.cellDoubleClicked.connect(self.onDoubleClicked)
        # self.tablewidget.cellClicked.connect(self.onClicked)
        self.tablewidget.cellChanged.connect(self.onChanged)

        # self.tablewidget.setModel(self.tableview)
        # self.tableview
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.tablewidget)
        self.setLayout(layout)
        self.result = None
        self.is_in_set_data = False
        self.no_change = False

    def clear(self):
        self.tablewidget.clear()
    
    def onChanged(self, row, col):
        if self.is_in_set_data or self.no_change:
            return
        if col == 3:
            self.no_change = True
            item_idx = row
            item_status = self.tablewidget.item(row, col).checkState() == Qt.Checked
            if item_status:
                self.tablewidget.item(row, col).setBackground(Qt.yellow)
            else:
                self.tablewidget.item(row, col).setBackground(Qt.green)
            # logging
            # logging.info()
            self.result.update({'row':item_idx, 'value':item_status})
            self.no_change = False

    def onDoubleClicked(self, row, col):
        x = self.tablewidget.item(row, 0).text()
        y = self.tablewidget.item(row, 1).text()
        self.on_item_click.emit({'x':float(x), 'y':float(y)})

    def save(self):
        if self.result is None:
            return
        self.result.save()

    def on_result(self, layer_id, result_id):
        self.is_in_set_data = True
        result = Project().layers[layer_id].results[result_id]
        if result != self.result:
            self.save() 
        self.result = result
        self.clear()
        self.set_data(result)
    def set_data(self, data:ResultLayer):
        self.is_in_set_data = True
        if data.layer_type != ResultLayer.POINT:
            return
        self.tablewidget.setRowCount(len(data.data))
        # print(len(data.data))
        self.tablewidget.setVerticalHeaderLabels([ str(i+1) for i in range(len(data.data))])
        for i, d in enumerate(data.data):
            self.tablewidget.setItem(i, 0, QTableWidgetItem(str(d[0]))) # X
            self.tablewidget.setItem(i, 1, QTableWidgetItem(str(d[1]))) # Y
            self.tablewidget.setItem(i, 2, QTableWidgetItem(str(d[2]))) # 概率
            status_item = QTableWidgetItem('变化')
            if d[3] == 0:
                status_item.setBackground(Qt.green)
                status_item.setCheckState(Qt.Unchecked)
            elif d[3] == 1:
                status_item.setBackground(Qt.yellow)
                status_item.setCheckState(Qt.Checked)
            self.tablewidget.setItem(i, 3, status_item) # 变化
        self.tablewidget.resizeColumnsToContents()
        self.tablewidget.resizeRowsToContents()
        self.tablewidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablewidget.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
    
        self.is_in_set_data = False