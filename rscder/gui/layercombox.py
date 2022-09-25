from PyQt5.QtWidgets import QComboBox, QWidget, QLabel, QHBoxLayout, QVBoxLayout
from PyQt5.QtGui import QIcon
from rscder.utils.icons import IconInstance
from rscder.utils.project import PairLayer, Project, RasterLayer, ResultPointLayer,SingleBandRasterLayer
class LayerCombox(QComboBox):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.addItem('---', None)
        self.setMinimumWidth(200)
        
        for layer in Project().layers.values(): 
            self.addItem(IconInstance().LAYER, layer.name, layer.id)
        
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

        hbox1 = QHBoxLayout()
        
        hbox1.addWidget(QLabel('时相1:'))
        hbox1.addWidget(self.raster_layer1)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(QLabel('时相2:'))
        hbox2.addWidget(self.raster_layer2)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)

        self.setLayout(vbox)

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
                if issubclass(sub.__class__, RasterLayer):
                    self.raster_layer1.addItem(IconInstance().RASTER, sub.name, sub)
                    self.raster_layer2.addItem(IconInstance().RASTER, sub.name, sub)


class RasterLayerCombox(QComboBox):

    def __init__(self, parent=None, layer:PairLayer=None):
        super().__init__(parent)
        self.addItem('---', None)
        if layer is not None:
            for sub in layer.layers:
                if issubclass(sub.__class__, RasterLayer):
                    self.addItem(IconInstance().RASTER, sub.name, sub)
        else:
            for layer in Project().layers.values(): 
                for sub in layer.layers:
                    if issubclass(sub.__class__, RasterLayer):
                        self.addItem(IconInstance().RASTER, sub.name, sub)


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
                    self.addItem(IconInstance().VECTOR, sub.name, sub)
        
        self.currentIndexChanged.connect(self.on_changed)

        self.current_layer = None
    
    def on_changed(self, index):
        if index == 0:
            self.current_layer = None
        else:
            self.current_layer = self.itemData(index)
    
class ResultLayercombox(QWidget):
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.current_layer = None
        
        self.initUI()
    
    def initUI(self):
        self.layer_combox = LayerCombox(self)
        layer_label = QLabel('图层组:')

        hbox = QHBoxLayout()
        hbox.addWidget(layer_label)
        hbox.addWidget(self.layer_combox)

        self.raster_layer1 = QComboBox(self)
        self.raster_layer1.addItem('---', None)

        self.raster_layer1.currentIndexChanged.connect(self.on_raster_layer1_changed)
        self.layer_combox.currentIndexChanged.connect(self.on_group_changed)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(QLabel('二值化结果:'))
        hbox1.addWidget(self.raster_layer1)


        vbox = QVBoxLayout()
        vbox.addLayout(hbox)
        vbox.addLayout(hbox1)


        self.setLayout(vbox)

    def on_raster_layer1_changed(self, index):
        if index == 0:
            self.current_layer = None
        else:
            self.current_layer = self.raster_layer1.itemData(index)
        
    
    def on_group_changed(self, index):
        if index == 0:
            self.raster_layer1.clear()
            self.raster_layer1.addItem('---', None)
        else:
            self.raster_layer1.clear()
            self.raster_layer1.addItem('---', None)
            for l in self.layer_combox.current_layer.layers:
                if isinstance(l,ResultPointLayer):
                    for k,v in l.result_path.items():
                        self.raster_layer1.addItem(IconInstance().RASTER,k,SingleBandRasterLayer(path = v, style_info={}))
