
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt,QModelIndex
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import (QTreeView, QTreeWidgetItem, QAbstractItemView, QHeaderView, QStyleFactory)
from rscder.gui.actions import get_action_manager

from rscder.utils.project import PairLayer, Project

class LayerTree(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        # self.tree_view = QTreeView(self)
        self.tree = QtWidgets.QTreeWidget(self)
        
        self.tree.setColumnCount(1)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.right_menu_show)
        self.root=QTreeWidgetItem(self.tree)
        self.tree.setHeaderHidden(True)
        # self.tree.setHeaderLabels(['图层'])
        self.root.setText(0,'图层')

        # child1=QTreeWidgetItem()
        # child1.setText(0,'child1')
        # child1.setCheckState(0,Qt.Checked)

        # self.root.addChild(child1)
        self.tree.expandAll()

        self.tree.addTopLevelItem(self.root)

        self.tree.clicked.connect(self.onClicked)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.tree)
        self.setLayout(layout)
        self.setLayoutDirection(Qt.LeftToRight)

    def onClicked(self,index):
        print(index.row())
        item = self.tree.currentItem()
        if item == self.root:
            return
        layer_id = str(item.data(0, Qt.UserRole))
        layer = Project().layers[layer_id]
        print(layer.l1_name)
        print(layer.l2_name)

    def add_layer(self, layer:str):
        layer:PairLayer = Project().layers[layer]
        item1 = QtWidgets.QTreeWidgetItem(self.root)
        item1.setText(0, layer.l1_name)
        item1.setCheckState(0, Qt.Checked)
        item2 = QtWidgets.QTreeWidgetItem(self.root)
        item2.setText(0, layer.l2_name)
        item2.setCheckState(0, Qt.Checked)

        item1.setData(0, Qt.UserRole, layer.id)
        item2.setData(0, Qt.UserRole, layer.id)
        self.tree.expandAll()

    def clear(self):
        self.tree.clear()
        self.root = QTreeWidgetItem(self.tree)
        self.root.setText(0,'图层')
        self.tree.addTopLevelItem(self.root)

    def right_menu_show(self, position):
        rightMenu = QtWidgets.QMenu(self)
        # QAction = QtWidgets.QAction(self.menuBar1)
        item = self.tree.currentItem()
        action_manager = get_action_manager()
        actions = []
        if item == self.root:
            data_load_action = action_manager.get_action('&数据加载', 'File')
            actions.append(data_load_action)
        else:
            pass
            
        for action in actions:
            rightMenu.addAction(action)
        
        rightMenu.exec_(self.mapToGlobal(position))

