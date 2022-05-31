import math
import os
import pdb
from rscder.gui.actions import ActionManager
from rscder.plugins.basic import BasicPlugin
from PyQt5.QtWidgets import QAction, QDialog, QHBoxLayout, QVBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from rscder.utils.icons import IconInstance
from rscder.utils.project import BasicLayer, Project, RasterLayer, SingleBandRasterLayer
from rscder.gui.layercombox import PairLayerCombox
from osgeo import gdal
from threading import Thread
import numpy as np

class MyDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('差分法')
        self.setWindowIcon(IconInstance().LOGO)

        # self.setFixedWidth(500)

        self.layer_select = PairLayerCombox(self)
    
        # self.number_input = QLineEdit(self)

        self.ok_button = QPushButton('确定', self)
        self.ok_button.setIcon(IconInstance().OK)
        self.ok_button.clicked.connect(self.on_ok)

        self.cancel_button = QPushButton('取消', self)
        self.cancel_button.setIcon(IconInstance().CANCEL)
        self.cancel_button.clicked.connect(self.on_cancel)
    
        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.ok_button)
        self.button_layout.addWidget(self.cancel_button)

        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.layer_select)

        self.main_layout.addLayout(self.button_layout)
        self.setLayout(self.main_layout)
    
    def on_ok(self):
        if self.layer_select.layer1 is None or self.layer_select.layer2 is None:
            self.reject()
            return
        self.accept()
    
    def on_cancel(self):
        self.reject()



class BasicMethod(BasicPlugin):

    result_ok = pyqtSignal(dict)

    @staticmethod
    def info():
        return {
            'name': 'BasicMethod',
            'description': 'BasicMethod',
            'author': 'RSCDER',
            'version': '1.0.0',
        }

    def set_action(self):

        basic_diff_method = QAction('差分法')
        ActionManager().unsupervised_menu.addAction(basic_diff_method)
        basic_diff_method.setEnabled(False)
        self.basic_diff_method = basic_diff_method
        basic_diff_method.triggered.connect(self.basic_diff_alg)

    def setup(self):
        self.basic_diff_method.setEnabled(True)

    def run_basic_diff_alg(self, layer1:RasterLayer, layer2:RasterLayer):
        
        pth1 = layer1.path
        pth2 = layer2.path

        

        cell_size = layer1.layer_parent.cell_size

        self.send_message.emit('开始计算差分法')

        ds1 = gdal.Open(pth1)
        ds2 = gdal.Open(pth2)
        if not layer1.compare(layer2):
            self.send_message.emit('两个图层的尺寸不同')
            return
        xsize = ds1.RasterXSize
        ysize = ds1.RasterYSize
        band = ds1.RasterCount
        yblocks = ysize // cell_size[1]

        driver = gdal.GetDriverByName('GTiff')
        out_tif = os.path.join(Project().cmi_path, 'temp.tif')
        out_ds = driver.Create(out_tif, xsize, ysize, 1, gdal.GDT_Float32)
        out_ds.SetGeoTransform(ds1.GetGeoTransform())
        out_ds.SetProjection(ds1.GetProjection())
        max_diff = 0
        min_diff = math.inf
        for j in range(yblocks + 1):
            
            self.send_message.emit(f'计算{j}/{yblocks}')
            block_xy = (0, j * cell_size[1])
            if block_xy[1] > ysize:
                break
            block_size = (xsize, cell_size[1])
            if block_xy[1] + block_size[1] > ysize:
                block_size = (xsize, ysize - block_xy[1])
            block_data1 = ds1.ReadAsArray(*block_xy, *block_size)
            block_data2 = ds2.ReadAsArray(*block_xy, *block_size)

            if band == 1:
                block_data1 =  block_data1[None, ...]
                block_data2 =  block_data2[None, ...]
            # pdb.set_trace()
            block_diff = block_data1.sum(0) - block_data2.sum(0)
            block_diff = block_diff.astype(np.float32)
            block_diff = np.abs(block_diff)
            
            min_diff = min(min_diff, block_diff[block_diff > 0].min())
            max_diff = max(max_diff, block_diff.max())
            out_ds.GetRasterBand(1).WriteArray(block_diff, *block_xy)

            self.send_message.emit(f'完成{j}/{yblocks}')

        out_ds.FlushCache()
        del out_ds
        self.send_message.emit('归一化概率中...')
        temp_in_ds = gdal.Open(out_tif) 

        out_normal_tif = os.path.join(Project().cmi_path, '{}_{}_cmi.tif'.format(layer1.layer_parent.name, int(np.random.rand() * 100000)))
        out_normal_ds = driver.Create(out_normal_tif, xsize, ysize, 1, gdal.GDT_Byte)
        out_normal_ds.SetGeoTransform(ds1.GetGeoTransform())
        out_normal_ds.SetProjection(ds1.GetProjection())
        # hist = np.zeros(256, dtype=np.int32)
        for j in range(yblocks+1):
            block_xy = (0, j * cell_size[1])
            if block_xy[1] > ysize:
                break
            block_size = (xsize, cell_size[1])
            if block_xy[1] + block_size[1] > ysize:
                block_size = (xsize, ysize - block_xy[1])
            block_data = temp_in_ds.ReadAsArray(*block_xy, *block_size)
            block_data = (block_data - min_diff) / (max_diff - min_diff) * 255
            block_data = block_data.astype(np.uint8)
            out_normal_ds.GetRasterBand(1).WriteArray(block_data, *block_xy)
            # hist_t, _ = np.histogram(block_data, bins=256, range=(0, 256))
            # hist += hist_t
        # print(hist)
        del temp_in_ds
        del out_normal_ds
        try:
            os.remove(out_tif)
        except:
            pass

        raster_result_layer = SingleBandRasterLayer(None, True, out_normal_tif, BasicLayer.BOATH_VIEW)

        # layer1.layer_parent.add_result_layer(point_result_lalyer)
        layer1.layer_parent.add_result_layer(raster_result_layer)

        # self.send_message.emit('完成计算变化表格')
                    
        self.send_message.emit('差分法计算完成')

    def basic_diff_alg(self):
        # layer_select = 

        layer_select = MyDialog(self.mainwindow)
        if layer_select.exec_():
            layer1 = layer_select.layer_select.layer1
            layer2 = layer_select.layer_select.layer2
        else:
            return
        # layer:PairLayer = list(self.project.layers.values())[0]

        t = Thread(target=self.run_basic_diff_alg, args=(layer1, layer2))
        t.start()


        