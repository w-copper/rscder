from PyQt5.QtCore import QSettings, QUrl, pyqtSignal, Qt, QVariant
from PyQt5.QtWidgets import QMessageBox, QWidget, QHBoxLayout
from PyQt5.QtGui import QColor, QDragEnterEvent, QDropEvent
from qgis.core import  QgsGeometry, QgsRectangle
from qgis.gui import QgsMapCanvas,QgsRubberBand,QgsMapToolEmitPoint
from qgis.core import QgsRectangle,QgsPoint
from rscder.utils.project import BasicLayer, PairLayer, Project
class RectangleMapTool(QgsMapToolEmitPoint):
    def __init__(self, canvas,color,witdth):
        self.canvas = canvas
        QgsMapToolEmitPoint.__init__(self, self.canvas)
        self.rubberBand = QgsRubberBand(self.canvas, True)
        self.rubberBand.setColor(color)
        self.rubberBand.setWidth(witdth)
        self.reset()
        self.Extent=0
    def reset(self):
        self.startPoint = self.endPoint = None
        self.isEmittingPoint = False
        self.rubberBand.reset(True)
    def draw_extent(self,extent):
        point1 = QgsPoint(extent.xMinimum(), extent.yMinimum())
        point2 = QgsPoint(extent.xMaximum(), extent.yMinimum())
        point3 = QgsPoint(extent.xMaximum(), extent.yMaximum())
        point4 = QgsPoint(extent.xMinimum(), extent.yMaximum())
        points=[point1,point2,point3,point4,point1]
        self.rubberBand.setToGeometry(QgsGeometry.fromPolyline(points), None)
        self.rubberBand.show()

class eagleEye(QgsMapCanvas):
    extent=pyqtSignal(object)
    def __init__(self, parent):
        super().__init__(parent)        
        self.layers = []
        self.grid_layers = []
        self.is_main = False
        self.setCanvasColor(Qt.white)
        self.enableAntiAliasing(True)
        self.setAcceptDrops(False)
        self.Extent=0
        self.changing=False
        self.rubber=RectangleMapTool(self,Qt.yellow,1)

    

    def update_layer(self):
        layers = Project().layers
        layer_list_1 = []
        for layer in layers.values():
            if layer.enable:
                for sub_layer in layer.layers:
                    if sub_layer.enable:
                        if sub_layer.view_mode == BasicLayer.LEFT_VIEW:
                            layer_list_1.append(sub_layer.layer)
                        elif sub_layer.view_mode == BasicLayer.BOATH_VIEW:
                            layer_list_1.append(sub_layer.layer)
        self.setLayers(layer_list_1)
        if len(layer_list_1) > 0:
            self.zoomToFeatureExtent(layer_list_1[0].extent())
    def zoom(self,layer):
        self.zoomToFeatureExtent(layer.extent())
    def draw_extent(self,extent):
        self.Extent=extent
        self.rubber.draw_extent(self.Extent)
        

    def reset_extent(self,center):
        if not self.Extent:
            return
        center=self.rubber.toMapCoordinates(center)
        x=(self.Extent.xMaximum()-self.Extent.xMinimum())//2
        y=(self.Extent.yMaximum()-self.Extent.yMinimum())//2
        self.Extent=QgsRectangle(center.x()-x,center.y()-y,center.x()+x,center.y()+y)
        self.draw_extent(self.Extent)
        
    def mousePressEvent(self,e):
        if not self.Extent:
            return
        self.changing=True
        self.reset_extent(e.pos())
        self.extent.emit(self.Extent)
    def mouseMoveEvent(self,e):
        if self.changing:
            self.reset_extent(e.pos())
            self.extent.emit(self.Extent)

    def mouseReleaseEvent(self,e):
        self.changing=False

    def wheelEvent(self,e):
        pass