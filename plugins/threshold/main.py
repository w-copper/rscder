import os
import pdb
from threading import Thread
import numpy as np
from rscder.gui.actions import ActionManager
from rscder.plugins.basic import BasicPlugin
from PyQt5.QtWidgets import QAction, QDialog, QHBoxLayout, QVBoxLayout, QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from rscder.gui.layercombox import RasterLayerCombox
from rscder.utils.icons import IconInstance
from rscder.utils.project import Project, RasterLayer, SingleBandRasterLayer
from threshold.otsu import OTSU
from osgeo import gdal
class OTSUDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('OTSU阈值')
        self.setWindowIcon(IconInstance().LOGO)

        self.setFixedWidth(500)

        self.layercombox = RasterLayerCombox(self)



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
        self.main_layout.addWidget(self.layercombox)
        self.main_layout.addLayout(self.button_layout)
        self.setLayout(self.main_layout)

    def on_ok(self):
        self.accept()

    def on_cancel(self):
        self.reject()


class OTSUPlugin(BasicPlugin):

    @staticmethod
    def info():
        return {
            "name": "OTSU",
            "description": "OTSU阈值",
            "author": "rscder",
            "version": "1.0.0"
        }
    
    def set_action(self):
        self.action = QAction('OTSU阈值', self.mainwindow)
        self.action.triggered.connect(self.run)
        ActionManager().postop_menu.addAction(self.action)

    def run(self):
        dialog = OTSUDialog(self.mainwindow)
        if dialog.exec_() == QDialog.Accepted:
            t = Thread(target=self.run_alg, args=(dialog.layercombox.current_layer,))
            t.start()
    
    def run_alg(self, layer:RasterLayer):
        if layer is None or layer.path is None:
            return
        ds = gdal.Open(layer.path)
        band = ds.GetRasterBand(1)
        band_count = ds.RasterCount
        if band_count > 1:
            self.message_box.error('请选择符合要求的图层')
            return
        hist = np.zeros(256, dtype=np.int)
        xsize = ds.RasterXSize
        ysize = ds.RasterYSize

        max_pixels = 1e7
        max_rows = max_pixels // xsize
        if max_rows < 1:
            max_rows = 1
        if max_rows > ysize:
            max_rows = ysize
        block_count = ysize // max_rows + 1
        for i in range(block_count):
            start_row = i * max_rows
            end_row = min((i + 1) * max_rows, ysize)
            block = band.ReadAsArray(0, start_row, xsize, end_row - start_row)
            hist += np.histogram(block.flatten(), bins=256, range=(0, 255))[0]
        hist = hist.astype(np.float32)
        gap = OTSU(hist)
        self.send_message.emit('阈值为：{}'.format(gap))

        out_th = os.path.join(Project().bcdm_path, '{}_otsu_bcdm.tif'.format(layer.name))
        out_ds = gdal.GetDriverByName('GTiff').Create(out_th, xsize, ysize, 1, gdal.GDT_Byte)
        out_ds.SetGeoTransform(ds.GetGeoTransform())
        out_ds.SetProjection(ds.GetProjection())
        out_band = out_ds.GetRasterBand(1)

        for i in range(block_count):
            start_row = i * max_rows
            end_row = min((i + 1) * max_rows, ysize)
            block = band.ReadAsArray(0, start_row, xsize, end_row - start_row)
            out_band.WriteArray(block > gap, 0, start_row)
        out_band.FlushCache()
        out_ds = None
        ds = None
        self.send_message.emit('OTSU阈值完成')

        otsu_layer = SingleBandRasterLayer(path = out_th, style_info={})
        layer.layer_parent.add_result_layer(otsu_layer)


# otsu_method = QAction('OTSU阈值分割')
#         postop_menu = self.ctx['postop_menu']
#         postop_menu.addAction(otsu_method)
#         otsu_method.setEnabled(False)
# point_result_lalyer = ResultPointLayer(out_csv, enable=False, proj  = layer1.proj, geo = layer1.geo)
# self.gap = OTSU(hist)

#         self.message_send.emit('OTSU：' + str(self.gap))

#         out_normal_ds.FlushCache()
#         del out_normal_ds
#         self.message_send.emit('完成归一化概率')   

#         self.message_send.emit('计算变化表格中...')
#         out_csv = os.path.join(Project().bcdm_path, '{}-{}.csv'.format(layer1.layer_parent.name, int(np.random.rand() * 100000)))
#         xblocks = xsize // cell_size[0]
        
#         normal_in_ds = gdal.Open(out_normal_tif)

#         with open(out_csv, 'w') as f:
#             f.write('x,y,diff,status\n')
#             for j in range(yblocks):
#                 block_xy = (0, j * cell_size[1])
#                 block_size = (xsize, cell_size[1])
#                 if block_xy[1] + block_size[1] > ysize:
#                     block_size = (xsize, ysize - block_xy[1])
#                 block_data = normal_in_ds.ReadAsArray(*block_xy, *block_size)
#                 for i in range(xblocks):
#                     start_x = i * cell_size[0]
#                     end_x = start_x + cell_size[0]
#                     if end_x > xsize:
#                         end_x = xsize
#                     block_data_xy = block_data[:, start_x:end_x]
#                     if block_data_xy.mean() > self.gap:
#                         center_x = start_x + cell_size[0] // 2
#                         center_y = j * cell_size[1] + cell_size[1] // 2
#                         center_x = center_x * geo[1] + geo [0]
#                         center_y = center_y * geo[5] + geo [3]
#                         f.write(f'{center_x},{center_y},{block_data_xy.mean() / 255 * 100},1\n')
        