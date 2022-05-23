
import logging
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt,QModelIndex, pyqtSignal
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import (QTableWidgetItem, QTableWidget, QMessageBox,  QAbstractItemView, QHeaderView, QStyleFactory)
from qgis.core import QgsRectangle
from rscder.utils.project import PairLayer, Project, ResultPointLayer

class ResultTable(QtWidgets.QWidget):

    on_item_click = pyqtSignal(QgsRectangle)
    on_item_changed = pyqtSignal(dict)

    def __init__(self, parent=None):
        super(ResultTable, self).__init__(parent)
        # self.tableview = QTableView(self)
        self.tablewidget = QTableWidget(self)
        self.tablewidget.setColumnCount(3)
        self.tablewidget.setRowCount(0)
        self.tablewidget.setHorizontalHeaderLabels(['变化位置(x,y)', '疑似变化概率', '目视判读'])
        self.tablewidget.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.tablewidget.cellClicked.connect(self.onClicked)
        # self.tablewidget.cellClicked.connect(self.onClicked)
        self.tablewidget.cellChanged.connect(self.onChanged)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.tablewidget)
        self.setLayout(layout)
        self.result = None
        self.is_in_set_data = False
        self.no_change = False

    def clear(self):
        self.tablewidget.clear()
        self.tablewidget.setColumnCount(3)
        self.tablewidget.setRowCount(0)
        self.tablewidget.setHorizontalHeaderLabels(['变化位置(x,y)', '疑似变化概率', '目视判读'])
    
    def onChanged(self, row, col):
        if self.is_in_set_data or self.no_change:
            return
        if col == 2:
            self.no_change = True
            item_idx = row
            item_status = self.tablewidget.item(row, col).checkState() == Qt.Checked
            if item_status:
                self.tablewidget.item(row, col).setBackground(Qt.yellow)
                self.tablewidget.item(row, col).setText('YES')
            else:
                self.tablewidget.item(row, col).setBackground(Qt.green)
                self.tablewidget.item(row, col).setText('NO')
            # logging
            # logging.info()
            self.result.update({'row':item_idx, 'value':item_status})
            self.no_change = False

    def onClicked(self, row, col):
        if col != 0:
            return
        data = self.result.data[row]
        x = data[0]
        y = data[1]
        xres = self.result.layer_parent.geo[1]
        yres = self.result.layer_parent.geo[5]
        cell_size = self.result.layer_parent.cell_size
        x_min = x - xres * cell_size[0]
        x_max = x + xres * cell_size[0]
        y_min = y - yres * cell_size[1]
        y_max = y + yres * cell_size[1]
        extent = QgsRectangle(x_min, y_min, x_max, y_max)

        self.on_item_click.emit(extent)

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
        self.show_result(result)
        
    def show_result(self, data:ResultPointLayer):
        self.is_in_set_data = True
        self.result = data
        self.tablewidget.setRowCount(len(data.data))
        # print(len(data.data))
        self.tablewidget.setVerticalHeaderLabels([ str(i+1) for i in range(len(data.data))])
        for i, d in enumerate(data.data):
            self.tablewidget.setItem(i, 0, QTableWidgetItem('%.3f,%.3f'%(d[0], d[1]))) # X
            self.tablewidget.setItem(i, 1, QTableWidgetItem('%.2f'%d[2])) # Y
            status_item = QTableWidgetItem('')
            if d[3] == 0:
                status_item.setBackground(Qt.green)
                status_item.setCheckState(Qt.Unchecked)
                status_item.setText('NO')
            elif d[3] == 1:
                status_item.setBackground(Qt.yellow)
                status_item.setCheckState(Qt.Checked)
                status_item.setText('YES')
            self.tablewidget.setItem(i, 2, status_item) # 变化
        self.tablewidget.resizeColumnsToContents()
        self.tablewidget.resizeRowsToContents()
        self.tablewidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tablewidget.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
    
        self.is_in_set_data = False