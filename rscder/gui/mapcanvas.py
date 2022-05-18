
# from alg.utils import random_color
# from mul.mulgrubcut import GrabCut
import logging
import multiprocessing
# from alg.grubcut import grubcut
# from gui.layerselect import LayerSelect
# from gui.default import get_default_category_colors, get_default_category_keys
# from os import truncate
from pathlib import Path
from PyQt5.QtCore import QSettings, QUrl, pyqtSignal, Qt, QVariant
from PyQt5.QtWidgets import QMessageBox, QWidget, QHBoxLayout
from PyQt5.QtGui import QColor, QDragEnterEvent, QDropEvent

from qgis.core import QgsPointXY, QgsRasterLayer, QgsVectorLayer, QgsFeature, QgsGeometry, QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsFillSymbol, QgsPalLayerSettings, QgsRuleBasedLabeling, QgsTextFormat
from qgis.gui import QgsMapCanvas, QgsMapToolPan, QgsMapToolZoom
from qgis.core import QgsRectangle, QgsVectorFileWriter, QgsProject, QgsField, QgsRasterFileWriter, QgsRasterPipe
import threading
import tempfile
import cv2
import os

from rscder.utils.project import PairLayer, Project

class DoubleCanvas(QWidget):
    corr_changed = pyqtSignal(str)
    scale_changed = pyqtSignal(str)

    def __init__(self, parent = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(False)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.mapcanva1 = CanvasWidget(self)
        self.mapcanva2 = CanvasWidget(self)
        self.mapcanva1.setCanvasColor(QColor(0, 0, 0))
        self.mapcanva2.setCanvasColor(QColor(0, 0, 0))
        
        self.mapcanva1.update_coordinates_text.connect(self.corr_changed)
        self.mapcanva2.update_coordinates_text.connect(self.corr_changed)

        def set_map1_extent():
            if self.mapcanva2.is_main:
                self.mapcanva1.set_extent(self.mapcanva2.extent())
        def set_map2_extent():
            if self.mapcanva1.is_main:
                self.mapcanva2.set_extent(self.mapcanva1.extent())

        self.mapcanva1.extentsChanged.connect(set_map2_extent)
        self.mapcanva2.extentsChanged.connect(set_map1_extent)

        self.set_pan_tool(True)

        self.mapcanva1.update_scale_text.connect(self.scale_changed)
        self.mapcanva2.update_scale_text.connect(self.scale_changed)
        
        layout = QHBoxLayout(self)
        layout.addWidget(self.mapcanva1)
        layout.addWidget(self.mapcanva2)
        
        self.setLayout(layout)
        self.grid_show = True

    def connect_grid_show(self, action):
        def show_grid(_):
            
            self.grid_show = not self.grid_show
            action.setChecked(self.grid_show)
            if self.grid_show:
                for layer in Project().layers.values():
                    if layer.grid_enable:
                        self.mapcanva1.add_grid_layer(layer.grid_layer.grid_layer)
                        self.mapcanva2.add_grid_layer(layer.grid_layer.grid_layer)
            else:
                self.mapcanva1.remove_grid_layer()
                self.mapcanva2.remove_grid_layer()

        action.triggered.connect(show_grid)


    def connect_map_tool(self, pan, zoom_in, zoom_out):
        pan.triggered.connect(self.set_pan_tool)
        zoom_in.triggered.connect(self.set_zoom_in)
        zoom_out.triggered.connect( self.set_zoom_out)

    def set_pan_tool(self, s):
        # print('set pan tool')
        if s:
            self.mapcanva1.setMapTool(QgsMapToolPan(self.mapcanva1))
            self.mapcanva2.setMapTool(QgsMapToolPan(self.mapcanva2))

    def set_zoom_in(self, s):
        # print('set zoom in')
        if s:
            self.mapcanva1.setMapTool(QgsMapToolZoom(self.mapcanva1, False))
            self.mapcanva2.setMapTool(QgsMapToolZoom(self.mapcanva2, False))

    def set_zoom_out(self, s):
        # print('set zoom out')
        if s:
            self.mapcanva1.setMapTool(QgsMapToolZoom(self.mapcanva1, True))
            self.mapcanva2.setMapTool(QgsMapToolZoom(self.mapcanva2, True))

    def update_layer(self):
        layers = Project().layers
        layer_list_1 = []
        layer_list_2 = []
        for layer in layers.values():
            if layer.enable:
                if layer.grid_enable and self.grid_show:
                    layer_list_1.append(layer.grid_layer.grid_layer)
                    layer_list_2.append(layer.grid_layer.grid_layer)
                if layer.l1_enable:
                    layer_list_1.append(layer.l1)
                if layer.l2_enable:
                    layer_list_2.append(layer.l2)
                    
                for result in layer.results:
                    if result.enable:
                        layer_list_1.append(result.layer)
                        layer_list_2.append(result.layer)
        
        self.mapcanva1.setLayers(layer_list_1)
        self.mapcanva2.setLayers(layer_list_2)

    def add_layer(self, layer:str):
        if not layer in Project().layers:
            self.clear()
            return
        layer:PairLayer = Project().layers[layer]
        if not layer.enable:
            return
        # self.clear()

        if not self.mapcanva1.is_main and not self.mapcanva2.is_main:
            self.mapcanva1.is_main = True
        
        if layer.l1_enable:
            self.mapcanva1.add_layer(layer.l1)
        if layer.l2_enable:
            self.mapcanva2.add_layer(layer.l2)
        if layer.grid_enable and self.grid_show:
            self.mapcanva1.add_grid_layer(layer.grid_layer.grid_layer)
            self.mapcanva2.add_grid_layer(layer.grid_layer.grid_layer)
        for r in layer.results:
            if r.enable:
                self.mapcanva1.add_layer(r.layer)
                self.mapcanva2.add_layer(r.layer)
        # self.mapcanva1.set_extent(layer.l1.extent())
        self.mapcanva1.refresh()
        self.mapcanva2.refresh()

    def zoom_to_result(self, xydict:dict):
        x = xydict['x']
        y = xydict['y']
        if Project().current_layer is not None:
            layer = Project().current_layer
        else:
            layer = Project().layers[list(Project().layers.keys())[0]]

        extent = QgsRectangle(x - layer.cell_size[0] * layer.xres, y - layer.cell_size[1] * layer.yres, x + layer.cell_size[0] * layer.xres, y + layer.cell_size[1] * layer.yres)
        self.mapcanva1.set_extent(extent)
        self.mapcanva2.set_extent(extent)

    def zoom_to_layer(self, layer:str):
        layer:PairLayer = Project().layers[layer]
        self.mapcanva1.set_extent(layer.l1.extent())
        self.mapcanva2.set_extent(layer.l2.extent())
    def layer_changed(self, layer:str):
        self.add_layer(layer)

    def clear(self):
        self.mapcanva1.clear()
        self.mapcanva2.clear()

class CanvasWidget(QgsMapCanvas):
    update_coordinates_text = pyqtSignal(str)
    update_scale_text = pyqtSignal(str)

    def add_layer(self, layer) -> None:
        self.layers.insert(0, layer)
        self.setLayers(self.layers)
        self.zoomToFeatureExtent(layer.extent())

    def add_grid_layer(self, layer):
        self.grid_layers.append(layer)
        self.layers.insert(0, layer)
        self.setLayers(self.layers)

    def remove_grid_layer(self):
        layers = []
        for layer in self.layers:
            if layer in self.grid_layers:
                continue
            layers.append(layer)
        self.layers = layers
        self.setLayers(self.layers)

    def enterEvent(self,e):
        self.is_main = True
        # print(e)
        pass

    def leaveEvent(self, e):
        self.is_main = False
        pass

    def set_extent(self, extent:QgsRectangle):
        '''
        Zoom to extent
        '''
        # print(extent)
        if self.is_main:
            return
        else:
            self.zoomToFeatureExtent(extent)

    def clear(self) -> None:
        self.setTheme('')
        self.layers = []
        self.is_main = False
        self.setLayers([])
        self.clearCache()
        self.refresh()

    def __init__(self, parent):
        super().__init__(parent)        
        self.layers = []
        self.grid_layers = []
        self.is_main = False
        self.setCanvasColor(Qt.white)
        self.enableAntiAliasing(True)
        self.setAcceptDrops(False)

        # coordinates updated
        def coordinates2text(pt:QgsPointXY):
            return self.update_coordinates_text.emit("X: {:.5f}, Y: {:.5f}".format(pt.x(), pt.y()))
        self.xyCoordinates.connect(coordinates2text)
        self.scaleChanged.connect(lambda _ : self.update_scale_text.emit("1 : {:.3f}".format(self.scale())))  