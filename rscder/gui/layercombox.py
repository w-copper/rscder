from PyQt5.QtWidgets import QComboBox
from rscder.utils.project import Project
class LayerCombox(QComboBox):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.addItem('---', None)
        
        for layer in Project().layers.values(): 
            self.addItem(layer.name, layer.id)
        
        self.currentIndexChanged.connect(self.on_changed)

        self.current_layer = None
    
    def on_changed(self, index):
        if index == 0:
            self.current_layer = None
        else:
            self.current_layer = Project().layers[self.itemData(index)]
    
