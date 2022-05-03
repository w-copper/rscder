
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt,QModelIndex
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import (QTreeView, QTreeWidgetItem, QAbstractItemView, QHeaderView, QStyleFactory)

from utils.project import PairLayer

class LayerTree(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.tree_view = QTreeView(self)
        self.tree = QtWidgets.QTreeWidget(self)
        self.tree.setColumnCount(1)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.right_menu_show)
        self.root=QTreeWidgetItem(self.tree)
        self.tree.setHeaderHidden(True)
        # self.tree.setHeaderLabels(['图层'])
        self.root.setText(0,'Root')

        child1=QTreeWidgetItem()
        child1.setText(0,'child1')
        child1.setCheckState(0,Qt.Checked)

        self.root.addChild(child1)
        self.tree.expandAll()

        self.tree.addTopLevelItem(self.root)

        self.tree.clicked.connect(self.onClicked)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.tree)
        self.setLayout(layout)
        self.setLayoutDirection(Qt.LeftToRight)

    def onClicked(self,index):
        print(index.row())

    def add_layer(self, layer:PairLayer):
        pass
    
    def right_menu_show(self, position):
        rightMenu = QtWidgets.QMenu(self)
        # QAction = QtWidgets.QAction(self.menuBar1)
        self.actionreboot = QtWidgets.QAction('zhangji')
        self.actionreboot.setObjectName("actionreboot")
        self.actionreboot.setText('aaa')
        rightMenu.addAction(self.actionreboot)
        
        rightMenu.exec_(self.mapToGlobal(position))

