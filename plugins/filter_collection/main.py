from datetime import datetime
import os
from threading import Thread
from PyQt5.QtWidgets import QDialog, QAction
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QModelIndex, pyqtSignal
from rscder.gui.actions import ActionManager
from rscder.utils.icons import IconInstance
from rscder.utils.project import PairLayer, Project, RasterLayer, ResultPointLayer
from rscder.plugins.basic  import BasicPlugin
from rscder.gui.layercombox import RasterLayerCombox
from osgeo import gdal, gdal_array
from skimage.filters import rank
from skimage.morphology import  rectangle
from filter_collection import FILTER
from misc import AlgFrontend

@FILTER.register
class MainFilter(AlgFrontend):

    @staticmethod
    def get_name():
        return '均值滤波'
    
    @staticmethod
    def get_widget(parent=None):
        widget = QtWidgets.QWidget(parent)
        x_size_input = QtWidgets.QLineEdit(widget)
        x_size_input.setText('3')
        x_size_input.setValidator(QtGui.QIntValidator())
        x_size_input.setObjectName('xinput')
        y_size_input = QtWidgets.QLineEdit(widget)
        y_size_input.setValidator(QtGui.QIntValidator())
        y_size_input.setObjectName('yinput')
        y_size_input.setText('3')

        size_label = QtWidgets.QLabel(widget)
        size_label.setText('窗口大小:')

        time_label = QtWidgets.QLabel(widget)
        time_label.setText('X')

        hlayout1 = QtWidgets.QHBoxLayout()

        hlayout1.addWidget(size_label)
        hlayout1.addWidget(x_size_input)
        hlayout1.addWidget(time_label)
        hlayout1.addWidget(y_size_input)

        widget.setLayout(hlayout1)

        return widget

    @staticmethod
    def get_params(widget:QtWidgets.QWidget=None):
        if widget is None:
            return dict(x_size=3, y_size=3)
        
        x_input = widget.findChild(QtWidgets.QLineEdit, 'xinput')
        y_input = widget.findChild(QtWidgets.QLineEdit, 'yinput')

        if x_input is None or y_input is None:
            return dict(x_size=3, y_size=3)
        
        x_size = int(x_input.text())
        y_size = int(y_input.text())

        return dict(x_size=x_size, y_size=y_size)

    @staticmethod
    def run_alg(pth, x_size, y_size, *args, **kargs):
        x_size = int(x_size)
        y_size = int(y_size)
        # pth = layer.path
        if pth is None:
            return
        
        ds = gdal.Open(pth)
        band_count = ds.RasterCount

        out_path = os.path.join(Project().other_path, 'mean_filter_{}.tif'.format(int(datetime.now().timestamp() * 1000)))
        out_ds = gdal.GetDriverByName('GTiff').Create(out_path, ds.RasterXSize, ds.RasterYSize, band_count, ds.GetRasterBand(1).DataType)
        out_ds.SetProjection(ds.GetProjection())
        out_ds.SetGeoTransform(ds.GetGeoTransform())

        for i in range(band_count):
            band = ds.GetRasterBand(i+1)
            data = band.ReadAsArray()
            
            data = rank.mean(data, rectangle(y_size, x_size))

            out_band = out_ds.GetRasterBand(i+1)
            out_band.WriteArray(data)

        out_ds.FlushCache()
        del out_ds
        del ds
        return out_path

class FilterSetting(QDialog):
    def __init__(self, parent=None):
        super(FilterSetting, self).__init__(parent)
        self.setWindowTitle('滤波设置')
        self.setWindowIcon(IconInstance().FILTER)
        self.initUI()

    def initUI(self):
        self.layer_combox = RasterLayerCombox(self)
        layer_label = QtWidgets.QLabel('图层:')

        hbox = QtWidgets.QHBoxLayout()
        hbox.addWidget(layer_label)
        hbox.addWidget(self.layer_combox)

        x_size_input = QtWidgets.QLineEdit(self)
        x_size_input.setText('3')
        y_size_input = QtWidgets.QLineEdit(self)
        y_size_input.setText('3')

        size_label = QtWidgets.QLabel(self)
        size_label.setText('窗口大小:')

        time_label = QtWidgets.QLabel(self)
        time_label.setText('X')

        self.x_size_input = x_size_input
        self.y_size_input = y_size_input

        hlayout1 = QtWidgets.QHBoxLayout()
        hlayout1.addWidget(size_label)
        hlayout1.addWidget(x_size_input)
        hlayout1.addWidget(time_label)
        hlayout1.addWidget(y_size_input)

        ok_button = QtWidgets.QPushButton(self)
        ok_button.setText('确定')
        ok_button.clicked.connect(self.accept)

        cancel_button = QtWidgets.QPushButton(self)
        cancel_button.setText('取消')
        cancel_button.clicked.connect(self.reject)

        hlayout2 = QtWidgets.QHBoxLayout()
        hlayout2.addWidget(ok_button,0,alignment=Qt.AlignHCenter)
        hlayout2.addWidget(cancel_button,0,alignment=Qt.AlignHCenter)

        vlayout = QtWidgets.QVBoxLayout()
        vlayout.addLayout(hbox)
        vlayout.addLayout(hlayout1)
        vlayout.addLayout(hlayout2)
        self.setLayout(vlayout)


class MainPlugin(BasicPlugin):
    
    alg_ok = pyqtSignal(PairLayer, RasterLayer)

    @staticmethod
    def info():
        return {
            'name': 'FilterCollection',
            'author': 'rscder',
            'version': '0.0.1',
            'description': 'Filter Collections'
        }
    
    def set_action(self):
        self.action = QAction('均值滤波', self.mainwindow)
        # self.action.setCheckable)
        # self.action.setChecked(False)
        self.action.triggered.connect(self.run)
        ActionManager().filter_menu.addAction(self.action)
        self.alg_ok.connect(self.alg_oked)
        # basic
    
    def alg_oked(self, parent, layer:RasterLayer):
        parent.add_result_layer(layer)

    def run_alg(self, layer:RasterLayer, x_size, y_size, method='mean'):
        x_size = int(x_size)
        y_size = int(y_size)
        pth = layer.path
        if pth is None:
            return
        
        ds = gdal.Open(pth)
        band_count = ds.RasterCount
        out_path = os.path.join(Project().other_path, '{}_mean_filter.tif'.format(layer.name))
        out_ds = gdal.GetDriverByName('GTiff').Create(out_path, ds.RasterXSize, ds.RasterYSize, band_count, ds.GetRasterBand(1).DataType)
        out_ds.SetProjection(ds.GetProjection())
        out_ds.SetGeoTransform(ds.GetGeoTransform())

        for i in range(band_count):
            band = ds.GetRasterBand(i+1)
            data = band.ReadAsArray()
            
            data = rank.mean(data, rectangle(y_size, x_size))

            out_band = out_ds.GetRasterBand(i+1)
            out_band.WriteArray(data)

        out_ds.FlushCache()
        del out_ds
        del ds

        rlayer = RasterLayer(path = out_path, enable= True, view_mode = layer.view_mode )

        self.alg_ok.emit(layer.layer_parent, rlayer)

    def run(self):
        dialog = FilterSetting(self.mainwindow)
        dialog.show()
        if dialog.exec_():
            x_size = int(dialog.x_size_input.text())
            y_size = int(dialog.y_size_input.text())
            t = Thread(target=self.run_alg, args=(dialog.layer_combox.current_layer, x_size, y_size))
            t.start()