
import pdb
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt,QModelIndex
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QCursor
from PyQt5.QtWidgets import (QTreeView, QTreeWidgetItem, QAbstractItemView, QHeaderView, QStyleFactory)
from rscder.gui.actions import get_action_manager

from rscder.utils.project import PairLayer, Project

class LayerTree(QtWidgets.QWidget):

    LAYER_TOOT = 0
    SUB_RASTER = 1
    RESULT = 2
    LEFT_RASTER = 0
    RIGHT_RASTER = 1
    GRID = 3

    tree_changed = QtCore.pyqtSignal(str)
    result_clicked = QtCore.pyqtSignal(str, int)
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.tree_view = QTreeView(self)
        self.tree = QtWidgets.QTreeWidget(self)
        
        self.tree.setColumnCount(1)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.right_menu_show)
        self.root=QTreeWidgetItem(self.tree)
        self.tree.setHeaderHidden(True)
        # self.tree.setHeaderLabels(['图层'])
        self.root.setText(0,'图层')
        self.root.setIcon(0,QtGui.QIcon(':/icons/layer.png'))

        # child1=QTreeWidgetItem()
        # child1.setText(0,'child1')
        # child1.setCheckState(0,Qt.Checked)

        # self.root.addChild(child1)
        self.tree.expandAll()

        self.tree.addTopLevelItem(self.root)

        # self.tree.clicked.connect(self.onClicked)
        self.tree.itemClicked.connect(self.onItemClicked)
        self.tree.itemChanged.connect(self.onItemChanged)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.tree)
        self.setLayout(layout)
        self.setLayoutDirection(Qt.LeftToRight)
        self.is_in_add_layer = False

    def onItemClicked(self, item:QtWidgets.QTreeWidgetItem, column):
        if item == self.root:
            return
        root = item
        if item.data(0, Qt.UserRole) != LayerTree.LAYER_TOOT:
            root = item.parent()
        if item.data(0, Qt.UserRole) == LayerTree.LAYER_TOOT:
            return
        layer = Project().layers[root.data(0, Qt.UserRole + 1)]
        Project().current_layer = layer
        if item.data(0, Qt.UserRole) == LayerTree.RESULT:
            # result = layer.results[item.data(0, Qt.UserRole + 1)]
            self.result_clicked.emit(layer.id, item.data(0, Qt.UserRole + 1))
        
        
    def onItemChanged(self, item:QtWidgets.QTreeWidgetItem, column):
        if self.is_in_add_layer:
            return
        if item == self.root:
            return
        root = item
        if item.data(0, Qt.UserRole) != LayerTree.LAYER_TOOT:
            root = item.parent()
        
        layer = Project().layers[root.data(0, Qt.UserRole + 1)]
        if item.data(0, Qt.UserRole) == LayerTree.LAYER_TOOT:
            layer.enable  = item.checkState(0) == Qt.Checked        
        if item.data(0, Qt.UserRole) == LayerTree.SUB_RASTER:
            if item.data(0, Qt.UserRole + 1) == LayerTree.LEFT_RASTER:
                layer.l1_enable = item.checkState(0) == Qt.Checked
            elif item.data(0, Qt.UserRole + 1) == LayerTree.RIGHT_RASTER:
                layer.l2_enable = item.checkState(0) == Qt.Checked
        if item.data(0, Qt.UserRole) == LayerTree.RESULT:   
            layer.results[item.data(0, Qt.UserRole + 1)].enable = item.checkState(0) == Qt.Checked
        
        if item.data(0, Qt.UserRole) == LayerTree.GRID:
            layer.grid_enable = item.checkState(0) == Qt.Checked

        self.tree_changed.emit(layer.id)

    def add_layer(self, layer:str):
        # self.tree.it
        self.is_in_add_layer = True
        layer:PairLayer = Project().layers[layer]
        item_root = QtWidgets.QTreeWidgetItem(self.root)
        item_root.setText(0,layer.name)
        item_root.setIcon(0, QtGui.QIcon(':/icons/document.png'))
        item_root.setData(0, Qt.UserRole, LayerTree.LAYER_TOOT)
        item_root.setData(0, Qt.UserRole + 1, layer.id)
        item_root.setCheckState(0, Qt.Checked if layer.enable else Qt.Unchecked)

        self.add_sub_layer(item_root, layer)
        self.is_in_add_layer = False

    def add_sub_layer(self, item_root, layer:PairLayer):
        # print(item_root.text(0))
        # print(layer.results.__len__())
        grid_item = QtWidgets.QTreeWidgetItem(item_root)
        grid_item.setText(0,'格网')
        grid_item.setData(0, Qt.UserRole, LayerTree.GRID)
        grid_item.setCheckState(0, Qt.Checked if layer.grid_enable else Qt.Unchecked)
        grid_item.setIcon(0, QtGui.QIcon(':/icons/grid.png'))

        item1 = QtWidgets.QTreeWidgetItem(item_root)
        item1.setText(0, layer.l1_name)
        item1.setCheckState(0, Qt.Checked if layer.l1_enable else Qt.Unchecked)
        item1.setData(0, Qt.UserRole, LayerTree.SUB_RASTER)
        item1.setData(0, Qt.UserRole + 1, LayerTree.LEFT_RASTER)
        item1.setIcon(0, QtGui.QIcon(':/icons/layer.png'))

        item2 = QtWidgets.QTreeWidgetItem(item_root)
        item2.setText(0, layer.l2_name)
        item2.setCheckState(0, Qt.Checked if layer.l2_enable else Qt.Unchecked)
        item2.setData(0, Qt.UserRole, LayerTree.SUB_RASTER)
        item2.setData(0, Qt.UserRole + 1, LayerTree.RIGHT_RASTER)
        item2.setIcon(0, QtGui.QIcon(':/icons/layer.png'))
 
        for ri, item in enumerate(layer.results):
            item_result = QtWidgets.QTreeWidgetItem(item_root)
            item_result.setText(0, item.name)
            item_result.setCheckState(0, Qt.Checked if item.enable else Qt.Unchecked)
            item_result.setData(0, Qt.UserRole, LayerTree.RESULT)
            item_result.setData(0, Qt.UserRole + 1, ri)

            item_result.setIcon(0, QtGui.QIcon(':/icons/vector.svg'))
        
        self.tree.expandAll()
    
    def update_layer(self, layer:str):
        self.is_in_add_layer = True
        layer:PairLayer = Project().layers[layer]
        
        layer_root = None
        # pdb.set_trace()
        for idx in range(self.root.childCount()):
            item_root = self.root.child(idx)
            if item_root.data(0, Qt.UserRole) == LayerTree.LAYER_TOOT:
                if item_root.data(0, Qt.UserRole + 1) == layer.id:
                    layer_root = item_root
                    break
        print(layer_root.text(0))
        if layer_root is None:
            self.add_layer(layer.id)
            return
        
        layer_root.setText(0,layer.name)

        while layer_root.childCount() > 0:
            layer_root.removeChild(layer_root.child(0))
        
        self.add_sub_layer(layer_root, layer)
        self.is_in_add_layer = False

    def clear(self):
        self.tree.clear()
        self.root = QTreeWidgetItem(self.tree)
        self.root.setText(0,'图层')
        self.tree.addTopLevelItem(self.root)

    def right_menu_show(self, position):
        rightMenu = QtWidgets.QMenu(self)
        # QAction = QtWidgets.QAction(self.menuBar1)
        item = self.tree.itemAt(position)

        action_manager = get_action_manager()
        actions = []
        data_load_action = action_manager.get_action('&数据加载', 'File')
        actions.append(data_load_action)
        if item is None:
            print('nothing')
        else:
            if item == self.root:
                pass
            elif item.data(0, Qt.UserRole) == LayerTree.LAYER_TOOT:
                actions.append(QtWidgets.QAction('&缩放至该图层', self))
                
                actions.append(QtWidgets.QAction('&重命名', self))
                actions.append(QtWidgets.QAction('&删除', self))
            elif item.data(0, Qt.UserRole) == LayerTree.SUB_RASTER:
                actions.append(QtWidgets.QAction('&缩放至该图层', self))
                
                actions.append(QtWidgets.QAction('&重命名', self))
                actions.append(QtWidgets.QAction('&删除', self))
            elif item.data(0, Qt.UserRole) == LayerTree.RESULT:
                actions.append(QtWidgets.QAction('&缩放至该图层', self))
                
                actions.append(QtWidgets.QAction('&重命名', self))
                actions.append(QtWidgets.QAction('&导出', self))
                actions.append(QtWidgets.QAction('&删除', self))
    

                
        for action in actions:
            rightMenu.addAction(action)
        
        rightMenu.exec_(QCursor.pos())