import os
from pathlib import Path
from typing import Dict, List
import uuid
import numpy as np
from osgeo import gdal, gdal_array
from rscder.utils.setting import Settings
from qgis.core import QgsRasterLayer, QgsMarkerSymbol,  QgsPalLayerSettings, QgsRuleBasedLabeling, QgsTextFormat, QgsLineSymbol, QgsSingleSymbolRenderer, QgsSimpleLineSymbolLayer, QgsVectorLayer, QgsCoordinateReferenceSystem, QgsFeature, QgsGeometry, QgsPointXY
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QColor
import yaml
from .misc import singleton

def relative_path(path: str, root:str) -> str:
    return os.path.relpath(path, root)

@singleton
class Project(QObject):

    project_init = pyqtSignal(bool)
    layer_load = pyqtSignal(str)

    ABSOLUTE_MODE = 'absolute'
    RELATIVE_MODE = 'relative'

    def __init__(self, 
                    parent=None):
        super().__init__(parent)
        self.is_init = False
        self.cell_size = Settings.Project().cell_size
        self.max_memory = Settings.Project().max_memory
        self.max_threads = Settings.Project().max_threads
        self.root = str(Path(Settings.General().root)/'default')
        self.file_mode = Project.ABSOLUTE_MODE
        self.layers:Dict[str, PairLayer] = dict()
        self.current_layer = None

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
        # 
    def change_result(self, layer_id, result_id, data):   
        if layer_id in self.layers:
            result = self.layers[layer_id].results[result_id]

            if result.layer_type == ResultLayer.POINT:
                result.update(data)
            elif result.layer_type == ResultLayer.RASTER:
                pass

    def setup(self, path = None, name = None):
        self.is_init = True
        if path is not None:
            self.root = path
        if name is None:
            self.file = str(Path(self.root)/'default.prj')
        else:
            self.file = str(Path(self.root)/name)
        if not os.path.exists(self.root):
            os.makedirs(self.root, exist_ok=True)
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
            'layers': [ layer.to_dict(None if self.file_mode == Project.ABSOLUTE_MODE else self.root) for layer in self.layers.values() ],
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
        try:
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
                player = PairLayer.from_dict(layer, None if self.file_mode == Project.ABSOLUTE_MODE else self.root)
                if player.check():
                    self.layers[player.id] = player
                    self.layer_load.emit(player.id)
        except Exception as e:
            self.message_box.error(str(e))
            self.clear()
    def add_layer(self, pth1, pth2):
        # self.root = str(Path(pth1).parent)
        
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

class ResultLayer:

    POINT = 0
    RASTER = 1

    def __init__(self, name, layer_type = POINT):
        self.layer_type = layer_type
        self.data = None
        self.layer = None
        self.name = name
        self.path = None
        self.wkt = None
        self.enable = False
    
    def update(self, data):
        if self.layer_type == ResultLayer.POINT:
            row = data['row']
            value = data['value']
            self.data[row][-1] = value
            self.update_point_layer()
        elif self.layer_type == ResultLayer.RASTER:
            pass

    def load_file(self, path):
        self.path = path
        if self.layer_type == ResultLayer.POINT:
            self.load_point_file()
        elif self.layer_type == ResultLayer.RASTER:
            self.load_raster_file()
        else:
            raise Exception('Unknown layer type')
    
    def format_point_layer(self, layer):
        layer.setLabelsEnabled(True)
        lyr = QgsPalLayerSettings()
        lyr.enabled = True
        lyr.fieldName = 'id'
        lyr.placement = QgsPalLayerSettings.OverPoint
        lyr.textNamedStyle = 'Medium'
        text_format =  QgsTextFormat()
        text_format.color = QColor('#ffffff')
        text_format.background().color = QColor('#000000')
        text_format.buffer().setEnabled(True)
        text_format.buffer().setSize(1)
        text_format.buffer().setOpacity(0.5)
        lyr.setFormat(text_format)
        root = QgsRuleBasedLabeling.Rule(QgsPalLayerSettings())
        rule = QgsRuleBasedLabeling.Rule(lyr)
        rule.setDescription('label')
        root.appendChild(rule)
        #Apply label configuration
        rules = QgsRuleBasedLabeling(root)
        layer.setLabeling(rules)

    def set_render(self, layer):
        symbol = QgsMarkerSymbol.createSimple({'color': '#ffffff', 'size': '5'})
        render = QgsSingleSymbolRenderer(symbol)
        layer.setRenderer(render)

    def load_point_file(self):
        data = np.loadtxt(self.path, delimiter=',', skiprows=1)
        if data is None:
            return
        self.data = data
        self.make_point_layer()
    
    def make_point_layer(self):
        if self.wkt is not None:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromString('WKT:{}'.format(self.wkt))
        else:
            crs = QgsCoordinateReferenceSystem()
        
        uri = 'Point?crs={}'.format(crs.toProj())
        layer = QgsVectorLayer(uri, self.name, "memory")
        if not layer.isValid():
            Project().message_box.error('Failed to create layer')
            return
        self.format_point_layer(layer)
        layer.startEditing()
        features = []
        for i, d in enumerate(self.data):
            point = QgsFeature(i)
            point.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(d[0], d[1])))
            # point.setAttribute('id', i)
            features.append(point)
        layer.addFeatures(features)
        layer.commitChanges()
        self.set_render(layer)
        self.layer = layer

    def update_point_layer(self):
        if self.layer is None:
            return
        self.layer.startEditing()
        add_features = []
        delete_features = []
        for i, d in enumerate(self.data):
            feature = self.layer.getFeature(i+1)
            if d[-1]:
                if feature is None:
                    feature = QgsFeature(i)
                    feature.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(d[0], d[1])))
                    # feature.setAttribute('id', i)
                    add_features.append(feature)
            else:
                if feature is not None:
                    delete_features.append(feature.id())
        if len(add_features) > 0:
            self.layer.addFeatures(add_features)
        if len(delete_features) > 0:            
            self.layer.deleteFeatures(delete_features)

        self.layer.commitChanges()


    def load_raster_file(self):
        ds = gdal.Open(self.path)
        if ds is None:
            return
        self.layer = QgsRasterLayer(self.path, self.name)

    @staticmethod
    def from_dict(data, root = None):
        result = ResultLayer(data['name'], data['layer_type'])
        result.wkt = data['wkt']
        if root is not None:
            result.load_file(str(Path(root) / data['path']))
        else:
            result.load_file(data['path'])
        return result

    def to_dict(self, root=None):
        return {
            'name': self.name,
            'layer_type': self.layer_type,
            'wkt': self.wkt,
            'path': self.path if root is None else str(Path(self.path).relative_to(root))
        }
    # def load_file(self, path):


class PairLayer:
    
    def to_dict(self, root = None):
        if root is None:
            return {
                'pth1': self.pth1,
                'pth2': self.pth2,
                'l1_name': self.l1_name,
                'l2_name': self.l2_name,
                'cell_size': self.cell_size,
                'results': [r.to_dict(root) for r in self.results],
                'name': self.name
                
            }
        else:
            return {
                'pth1': relative_path(self.pth1, root),
                'pth2': relative_path(self.pth2, root),
                'name': self.name,
                'l1_name': self.l1_name,
                'l2_name': self.l2_name,
                'cell_size': self.cell_size,
                'results': [r.to_dict(root) for r in self.results]
            }

    @staticmethod
    def from_dict(data, root = None):
        if root is None:
            layer = PairLayer(data['pth1'], data['pth2'], data['cell_size'])
        else:
            layer = PairLayer(os.path.join(root, data['pth1']), os.path.join(root, data['pth2']), data['cell_size'])
        layer.l1_name = data['l1_name']
        layer.l2_name = data['l2_name']
        layer.name = data['name']

        for r in data['results']:
            layer.results.append(ResultLayer.from_dict(r, root))
        # layer.grid_layer = GridLayer.from_dict(data['grid_layer'])
        return layer
    def __init__(self, pth1, pth2, cell_size) -> None:
        self.pth1 = pth1
        self.pth2 = pth2
        self.enable = True
        self.l1_enable = True
        self.l2_enable = True
        self.grid_enable = True
        self.id = str(uuid.uuid1())
        self.name = '{}-{}'.format(os.path.basename(pth1), os.path.basename(pth2))
        self.l1_name = os.path.basename(pth1)
        self.l2_name = os.path.basename(pth2)

        self.cell_size = cell_size
        self.msg = ''
        self.checked = False

        self.xsize = 0
        self.ysize = 0
        self.xres = 0
        self.yres = 0

        self.wkt = None

        self.results:List[ResultLayer] = []

    def check(self):
        if self.checked:
            return self.checked
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

        self.xsize = ds1.RasterXSize
        self.ysize = ds1.RasterYSize

        self.xres = ds1.GetGeoTransform()[1]
        self.yres = ds1.GetGeoTransform()[5]

        self.wkt = ds1.GetProjection()

        self.grid_layer = GridLayer(self.cell_size, ds1)

        del ds1
        del ds2

        self.l1 = QgsRasterLayer(self.pth1, self.l1_name)
        self.l2 = QgsRasterLayer(self.pth2, self.l2_name)
        self.checked = True
        return True