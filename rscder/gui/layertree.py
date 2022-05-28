
import logging
import pdb
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt,QModelIndex
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QCursor, QIcon
from PyQt5.QtWidgets import (QTreeView, QTreeWidgetItem, QAbstractItemView, QHeaderView, QStyleFactory)
from rscder.gui.actions import get_action_manager
from rscder.utils.icons import IconInstance

from rscder.utils.project import PairLayer, Project

class LayerTree(QtWidgets.QWidget):

    LAYER_TOOT = 0
    SUB_LAYERS = 1
    RESULT = 2
    LEFT_RASTER = 0
    RIGHT_RASTER = 1
    GRID = 3

    tree_changed = QtCore.pyqtSignal()
    zoom_to_layer_signal = QtCore.pyqtSignal(str)

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
        self.root.setIcon(0,IconInstance().LAYER)
        
        self.tree.expandAll()

        self.tree.addTopLevelItem(self.root)

        self.tree.itemChanged.connect(self.onItemChanged)
        self.tree.itemExpanded.connect(self.onItemExpanded)

        self._expand = True
        self.root.setExpanded(self._expand)

        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.tree)
        self.setLayout(layout)
        self.setLayoutDirection(Qt.LeftToRight)
        self.is_update_layer = False
        self.current_item = None     
    
    def onItemExpanded(self, item:QtWidgets.QTreeWidgetItem):
        if item == self.root:
            self._expand = item.isExpanded()
            return
        
        if hasattr(item, 'item_update'):
            item.item_update(item)

    def onItemChanged(self, item:QtWidgets.QTreeWidgetItem, column):
        if self.is_update_layer:
            return
        if item == self.root:
            self._expand = item.isExpanded()
            return
        
        if hasattr(item, 'item_update'):
            item.item_update(item)

    def update_layer(self):
        self.is_update_layer = True
        self.clear()
        for layer_group in Project().layers.values():
            item_root = layer_group.get_item(self.root)
            # self.root.addChild(item_root)
            layer_group.grid.get_item(item_root)
            for _, sub in enumerate(layer_group.layers):
                sub.get_item(item_root)
                # item_root.addChild(item)
        self.is_update_layer = False

    def clear(self):
        self.tree.clear()
        self.root = QTreeWidgetItem(self.tree)
        self.tree.addTopLevelItem(self.root)
        self.tree.expandAll()
        self.root.setText(0,'图层')
        self.root.setIcon(0,IconInstance().LAYER)
        self.root.setExpanded(self._expand)

    def right_menu_show(self, position):
        rightMenu = QtWidgets.QMenu(self)

        item = self.tree.itemAt(position)
        self.current_item = item
        action_manager = get_action_manager()
        actions = []
        data_load_action = action_manager.get_action('&数据加载', 'File')
        actions.append(data_load_action)
        
        if item is None:
            logging.info('nothing')
        else:
            if item == self.root:
                pass
            else:
                actions.extend(item.get_actions())
                    
        for action in actions:
            rightMenu.addAction(action)
        
        rightMenu.exec_(QCursor.pos())