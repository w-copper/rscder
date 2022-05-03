import os
from pathlib import Path
from osgeo import gdal, gdal_array
from utils.setting import Settings
from qgis.core import QgsRasterLayer 
from PyQt5.QtCore import QObject, pyqtSignal

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

    def __init__(self, 
                    parent=None):
        super().__init__(parent)
        self.is_init = False
        self.cell_size = Settings.Project().cell_size
        self.max_memory = Settings.Project().max_memory
        self.max_threads = Settings.Project().max_threads
        self.root = Settings.General().root

    def connect(self, pair_canvas,
             layer_tree,
             message_box,
             result_table):
        self.pair_canvas = pair_canvas
        self.layer_tree = layer_tree
        self.message_box = message_box
        self.result_table = result_table
    
    def setup(self, file=None):
        self.is_init = True
        
        if file is None:
            self.file = Path(self.root)/'project'/'untitled.cdp'
        dir_name = os.path.dirname(self.file)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name, exist_ok=True)
        if not self.file.exists():
            f = self.file.open('w')
            f.close()
        else:
            self.load()
        # self.project_created.emit()
        self.project_init.emit(True)

    def save(self):
        pass 
    
    def clear(self):
        '''
        clear all layers
        '''
        self.layer_tree.clear()
        self.pair_canvas.clear()
        self.message_box.clear()
        self.result_table.clear()

    def load(self):
        pass

    def add_layer(self, pth1, pth2):
        player = PairLayer(pth1, pth2)
        if player.check():
            self.layer_tree.add_layer(player)
        else:
            self.message_box.show_message(player.msg)

class VectorLayer:
    pass

class GridLayer:
    pass

class PairLayer:
    
    def __init__(self, pth1, pth2) -> None:
        self.pth1 = pth1
        self.pth2 = pth2

        self.l1_name = os.path.basename(pth1)
        self.l2_name = os.path.basename(pth2)

        self.grid_layer = GridLayer()

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

        del ds1
        del ds2

        self.l1 = QgsRasterLayer(self.pth1, self.l1_name)
        self.l2 = QgsRasterLayer(self.pth2, self.l2_name)

        return True