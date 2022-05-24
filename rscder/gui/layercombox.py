from PyQt5.QtWidgets import QComboBox, QWidget, QLabel, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QIcon
from rscder.utils.project import Project, RasterLayer, ResultPointLayer
class LayerCombox(QComboBox):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.addItem('---', None)
        
        for layer in Project().layers.values(): 
            self.addItem(layer.name, layer.id)
        
        for i in range(self.count() - 1):
            self.setItemIcon(i + 1, QIcon(':/icons/layer.png'))


        self.currentIndexChanged.connect(self.on_changed)

        self.current_layer = None
    
    def on_changed(self, index):
        if index == 0:
            self.current_layer = None
        else:
            self.current_layer = Project().layers[self.itemData(index)]

class PairLayerCombox(QWidget):

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.layer1 = None
        self.layer2 = None
        self.initUI()
    
    def initUI(self):
        self.layer_combox = LayerCombox(self)
        layer_label = QLabel('图层组:')

        hbox = QHBoxLayout()
        hbox.addWidget(layer_label)
        hbox.addWidget(self.layer_combox)

        self.raster_layer1 = QComboBox(self)
        self.raster_layer1.addItem('---', None)

        self.raster_layer2 = QComboBox(self)
        self.raster_layer2.addItem('---', None)

        self.raster_layer1.currentIndexChanged.connect(self.on_raster_layer1_changed)
        self.raster_layer2.currentIndexChanged.connect(self.on_raster_layer2_changed)
        
        self.layer_combox.currentIndexChanged.connect(self.on_group_changed)

        self.setLayout(hbox)

    def on_raster_layer1_changed(self, index):
        if index == 0:
            self.layer1 = None
        else:
            self.layer1 = self.raster_layer1.itemData(index)
        
    def on_raster_layer2_changed(self, index):
        if index == 0:
            self.layer2 = None
        else:
            self.layer2 = self.raster_layer2.itemData(index)
    
    def on_group_changed(self, index):
        if index == 0:
            self.raster_layer1.clear()
            self.raster_layer2.clear()
            self.raster_layer1.addItem('---', None)
            self.raster_layer2.addItem('---', None)
        else:
            self.raster_layer1.clear()
            self.raster_layer2.clear()
            self.raster_layer1.addItem('---', None)
            self.raster_layer2.addItem('---', None)
            for sub in self.layer_combox.current_layer.layers:
                if isinstance(sub, RasterLayer):
                    self.raster_layer1.addItem(QIcon(':/icons/layer.png'), sub.name, sub)
                    self.raster_layer2.addItem(QIcon(':/icons/layer.png'), sub.name, sub)


class RasterLayerCombox(QComboBox):

    def __init__(self, parent=None, layer=None):
        super().__init__(parent)
        self.addItem('---', None)
        if layer is not None:
            for sub in layer.layers:
                if isinstance(sub, RasterLayer):
                    self.addItem(sub.name, sub)
        else:
            for layer in Project().layers.values(): 
                for sub in layer.layers:
                    if isinstance(sub, RasterLayer):
                        self.addItem(sub.name, sub)
            # self.addItem(layer.name, layer.id)
        
        for i in range(self.count() - 1):
            self.setItemIcon(i + 1, QIcon(':/icons/layer.png'))


        self.currentIndexChanged.connect(self.on_changed)

        self.current_layer = None
    
    def on_changed(self, index):
        if index == 0:
            self.current_layer = None
        else:
            self.current_layer = self.itemData(index)
    
class ResultPointLayerCombox(QComboBox):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.addItem('---', None)
        
        for layer in Project().layers.values(): 
            for sub in layer.layers:
                if isinstance(sub, ResultPointLayer):
                    self.addItem(sub.name, sub)
        
        for i in range(self.count() - 1):
            self.setItemIcon(i + 1, QIcon(':/icons/layer.png'))


        self.currentIndexChanged.connect(self.on_changed)

        self.current_layer = None
    
    def on_changed(self, index):
        if index == 0:
            self.current_layer = None
        else:
            self.current_layer = self.itemData(index)
    
