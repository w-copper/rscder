import os
from pathlib import Path
from typing import Dict, List
import uuid
from osgeo import gdal, gdal_array
from rscder.utils.setting import Settings
from qgis.core import QgsRasterLayer, QgsLineSymbol, QgsSingleSymbolRenderer, QgsSimpleLineSymbolLayer, QgsVectorLayer, QgsCoordinateReferenceSystem, QgsFeature, QgsGeometry, QgsPointXY
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QColor
import yaml
def singleton(cls):
    _instance = {}

    def inner(*args, **kargs):
        if cls not in _instance:
            _instance[cls] = cls(*args, **kargs)
        return _instance[cls]
    return inner

@singleton
class Project(QObject):

    project_init = pyqtSignal(bool)

    layer_load = pyqtSignal(str)

    def __init__(self, 
                    parent=None):
        super().__init__(parent)
        self.is_init = False
        self.cell_size = Settings.Project().cell_size
        self.max_memory = Settings.Project().max_memory
        self.max_threads = Settings.Project().max_threads
        self.root = Settings.General().root
        self.layers:Dict = dict()
        # self.layers:List[PairLayer] = []

    def connect(self, pair_canvas,
             layer_tree,
             message_box,
             result_table):
        self.pair_canvas = pair_canvas
        self.layer_tree = layer_tree
        self.message_box = message_box
        self.result_table = result_table

        self.layer_load.connect(layer_tree.add_layer)
        self.layer_load.connect(pair_canvas.add_layer)
        # self.layer_load.connect(message_box.add_layer)

    
    def setup(self, file=None):
        self.is_init = True
        self.file = file
        if file is None:
            self.file = Path(self.root)/'project'/'untitled.prj'
        self.root = str(Path(self.file).parent)
        dir_name = os.path.dirname(self.file)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
        if not os.path.exists(self.file):
            with open(self.file, 'w') as f:
                pass
        else:
            self.load()
        # self.project_created.emit()
        self.project_init.emit(True)

    def save(self):
        data_dict = {
            'cell_size': self.cell_size,
            'max_memory': self.max_memory,
            'max_threads': self.max_threads,
            'root': self.root,
            'layers': [ layer.to_dict() for layer in self.layers.values() ],
            'results': []
        }
        with open(self.file, 'w') as f:
            yaml.safe_dump(data_dict, f)
        # yaml.safe_dump(data_dict, open(self.file, 'w'))

    
    def clear(self):
        '''
        clear all layers
        '''
        self.layers = dict()
        self.layer_tree.clear()
        self.pair_canvas.clear()
        self.message_box.clear()
        self.result_table.clear()

    def load(self):
        with open(self.file, 'r') as f:
            data = yaml.safe_load(f)
        if data is None:
            return
        # data = yaml.safe_load(open(self.file, 'r'))
        self.cell_size = data['cell_size']
        self.max_memory = data['max_memory']
        self.max_threads = data['max_threads']
        self.root = data['root']
        self.layers = dict()
        for layer in data['layers']:
            player = PairLayer.from_dict(layer)
            if player.check():
                self.layers[player.id] = player
                self.layer_load.emit(player.id)

    def add_layer(self, pth1, pth2):
        self.root = str(Path(pth1).parent)
        player = PairLayer(pth1, pth2, self.cell_size)
        if player.check():
            # self.layers.append(player)
            self.layers[player.id] = player
            self.layer_load.emit(player.id)
        else:
            self.message_box.error(player.msg)

class VectorLayer:
    pass

class GridLayer:
    
    def set_render(self):
        symbol_layer = QgsSimpleLineSymbolLayer()
        symbol_layer.setWidth(1)
        symbol_layer.setColor(QColor.fromRgb(255,255,255, 100))

        symbol = QgsLineSymbol()
        symbol.changeSymbolLayer(0, symbol_layer)

        render = QgsSingleSymbolRenderer(symbol)
        self.lines_layer.setRenderer(render)
        

    def __init__(self, cell_size, ds):
        self.cell_size = cell_size
        self.ds = ds

        proj = ds.GetProjection()
        geo = ds.GetGeoTransform()
        self.proj = proj
        self.geo = geo
        self.x_size = ds.RasterXSize
        self.y_size = ds.RasterYSize

        self.x_min = geo[0]
        self.y_min = geo[3]
        self.x_res = geo[1]
        self.y_res = geo[5]
        self.x_max = self.x_min + self.x_res * self.x_size
        self.y_max = self.y_min + self.y_res * self.y_size
        self.x_lines = []
        for xi in range(self.x_size // self.cell_size[0]):
            self.x_lines.append(self.x_min + self.x_res * xi * self.cell_size[0])
        if self.x_lines[-1] == self.x_max:
            self.x_lines.pop()
        self.x_lines.append(self.x_max)
        self.y_lines = []
        for yi in range(self.y_size // self.cell_size[1]):
            self.y_lines.append(self.y_min + self.y_res * yi * self.cell_size[1])
        if self.y_lines[-1] == self.y_max:
            self.y_lines.pop()
        self.y_lines.append(self.y_max)
        crs = QgsCoordinateReferenceSystem()
        crs.createFromString('WKT:{}'.format(ds.GetProjection()))
        # print(crs)
        lines_layer = QgsVectorLayer('LineString?crs={}'.format(crs.toProj()), 'temp-grid-outline', "memory")
        if not lines_layer.isValid():
            Project().message_box.error('Failed to create grid outline layer')
            return
        lines_layer.setLabelsEnabled(False)
        lines_layer.startEditing()
        features = []
        for x in self.x_lines:
            line = QgsFeature()
            line.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(x, self.y_min), QgsPointXY(x, self.y_max)]))
            features.append(line)
        for y in self.y_lines:
            line = QgsFeature()
            line.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(self.x_min, y), QgsPointXY(self.x_max, y)]))
            features.append(line)
        lines_layer.addFeatures(features)
        lines_layer.commitChanges()
        self.lines_layer = lines_layer

        self.set_render()
        # self.x_lines = [ self.x_min + i * self.x_res for i in range(self.x_size) ]

    @property
    def grid_layer(self):
        return self.lines_layer

    def to_dict(self):
        return {
            'cell_size': self.cell_size
        }
    
    @staticmethod
    def from_dict(data):
        return GridLayer()

class PairLayer:
    
    def to_dict(self):
        return {
            'pth1': self.pth1,
            'pth2': self.pth2,
            'l1_name': self.l1_name,
            'l2_name': self.l2_name,
            'cell_size': self.cell_size,
        }

    @staticmethod
    def from_dict(data):
        layer = PairLayer(data['pth1'], data['pth2'], data['cell_size'])
        layer.l1_name = data['l1_name']
        layer.l2_name = data['l2_name']
        # layer.grid_layer = GridLayer.from_dict(data['grid_layer'])
        return layer
    def __init__(self, pth1, pth2, cell_size) -> None:
        self.pth1 = pth1
        self.pth2 = pth2
        self.id = str(uuid.uuid1())

        self.l1_name = os.path.basename(pth1)
        self.l2_name = os.path.basename(pth2)

        self.cell_size = cell_size

        # self.grid_layer = GridLayer(cell_size)

        self.msg = ''
    
    def check(self):
        if not os.path.exists(self.pth1):
            self.msg = '图层1不存在'
            return False
        if not os.path.exists(self.pth2):
            self.msg = '图层2不存在'
            return False
        
        ds1 = gdal.Open(self.pth1)
        ds2 = gdal.Open(self.pth2)
        if ds1 is None or ds2 is None:
            self.msg = '图层打开失败'
            return False
        
        if ds1.RasterXSize != ds2.RasterXSize or ds1.RasterYSize != ds2.RasterYSize:
            self.msg = '图层尺寸不一致'
            return False

        self.grid_layer = GridLayer(self.cell_size, ds1)

        del ds1
        del ds2

        self.l1 = QgsRasterLayer(self.pth1, self.l1_name)
        self.l2 = QgsRasterLayer(self.pth2, self.l2_name)

        return True