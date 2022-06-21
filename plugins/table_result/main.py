import os
from threading import Thread
from rscder.gui.actions import ActionManager
from rscder.gui.layercombox import RasterLayerCombox, ResultLayercombox
from rscder.plugins.basic import BasicPlugin
from PyQt5.QtWidgets import QAction, QDialog, QLabel, QHBoxLayout, QVBoxLayout, QPushButton
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from rscder.utils.icons import IconInstance

from rscder.utils.project import Project, ResultPointLayer, SingleBandRasterLayer
from osgeo import gdal
class TableResultDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('表格结果')
        self.setWindowIcon(IconInstance().LOGO)

        self.layer_select = ResultLayercombox(self)
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel('二值化结果图层：'))
        hbox.addWidget(self.layer_select)

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
        self.main_layout.addLayout(hbox)
        self.main_layout.addLayout(self.button_layout)
        self.setLayout(self.main_layout)

    def on_ok(self):
        self.accept()

    def on_cancel(self):
        self.reject()


class TableResultPlugin(BasicPlugin):

    @staticmethod
    def info():
        return {
            'name': 'TableResult',
            'author': 'RSC',
            'version': '1.0.0',
            'description': '表格结果'
        }
    
    def set_action(self):
        self.action = QAction(IconInstance().VECTOR, '表格结果', self.mainwindow)
        self.action.triggered.connect(self.show_dialog)
        ActionManager().position_menu.addAction(self.action)
    
    def run(self, layer:SingleBandRasterLayer):
        self.send_message.emit('正在计算表格结果...')
        if not isinstance(layer, SingleBandRasterLayer):
            self.send_message.emit('请选择一个单波段栅格图层')
            return
        
        cell_size = layer.layer_parent.cell_size
        ds = gdal.Open(layer.path)
        xsize = ds.RasterXSize
        ysize = ds.RasterYSize
        geo = ds.GetGeoTransform()

        out_csv = os.path.join(Project().other_path, f'{layer.name}_table_result.csv')
        yblocks = ysize // cell_size[1] + 1
        xblocks = xsize // cell_size[0] + 1
        with open(out_csv, 'w') as f:
            f.write('x,y,diff,status\n')
            for j in range(yblocks):
                block_xy = (0, j * cell_size[1])
                block_size = (xsize, cell_size[1])
                if block_xy[1] + block_size[1] > ysize:
                    block_size = (xsize, ysize - block_xy[1])
                block_data = ds.ReadAsArray(*block_xy, *block_size)
                for i in range(xblocks):
                    start_x = i * cell_size[0]
                    end_x = start_x + cell_size[0]
                    if end_x > xsize:
                        end_x = xsize
                    block_data_xy = block_data[:, start_x:end_x]
                    if block_data_xy.mean() > 0.5:
                        center_x = start_x + cell_size[0] // 2
                        center_y = j * cell_size[1] + cell_size[1] // 2
                        center_x = center_x * geo[1] + geo [0]
                        center_y = center_y * geo[5] + geo [3]
                        f.write(f'{center_x},{center_y},{block_data_xy.mean() * 100},1\n')

        result_layer = ResultPointLayer(out_csv, enable=True, proj=layer.proj, geo=layer.geo)
        layer.layer_parent.add_result_layer(result_layer)
        self.send_message.emit('计算完成')
        

    def show_dialog(self):
        dialog = TableResultDialog()
        if dialog.exec_() == QDialog.Accepted:
            if dialog.layer_select.current_layer is not None:
                t = Thread(target=self.run, args=(dialog.layer_select.current_layer,))
                t.start()
