from threading import Thread

import numpy as np
from rscder.gui.actions import ActionManager
from rscder.plugins.basic import BasicPlugin
from rscder.gui.layercombox import RasterLayerCombox
from PyQt5.QtWidgets import QAction, QFileDialog, QDialog, QLabel, QHBoxLayout, QVBoxLayout, QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from osgeo import gdal 
from rscder.utils.project import SingleBandRasterLayer

class EvalutationDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('精度评估')
        self.setWindowIcon(QIcon(":/icons/logo.png"))

        self.layer_select = RasterLayerCombox(self)
        self.gt_file = None

        gt_file_select_label = QLabel('真值文件:')
        self.gt_file_select = QPushButton('选择...', self)
        self.gt_file_select.clicked.connect(self.on_gt_file_select)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(gt_file_select_label)
        hbox1.addWidget(self.gt_file_select)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(QLabel('二值化结果图层：'))
        hbox2.addWidget(self.layer_select)

        self.ok_button = QPushButton('确定', self)
        self.ok_button.setIcon(QIcon(":/icons/ok.svg"))
        self.ok_button.clicked.connect(self.on_ok)

        self.cancel_button = QPushButton('取消', self)
        self.cancel_button.setIcon(QIcon(":/icons/cancel.svg"))
        self.cancel_button.clicked.connect(self.on_cancel)

        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.ok_button)
        self.button_layout.addWidget(self.cancel_button)

        self.main_layout = QVBoxLayout()
        self.main_layout.addLayout(hbox1)
        self.main_layout.addLayout(hbox2)
        self.main_layout.addLayout(self.button_layout)
        self.setLayout(self.main_layout)

    def on_gt_file_select(self):
        file_name, _ = QFileDialog.getOpenFileName(self, '选择真值文件', '', '*.tif')
        if file_name:
            self.gt_file = file_name
            self.gt_file_select.setText(file_name)

    def on_ok(self):
        self.accept()

    def on_cancel(self):
        self.reject()


class EvaluationPlugin(BasicPlugin):

    @staticmethod
    def info():
        return {
            'name': '精度评估',
            'author': 'RSC',
            'version': '1.0.0',
            'description': '精度评估',
            'category': 'Evaluation'
        }
    
    def set_action(self):
        self.action = QAction(QIcon(":/icons/evaluation.svg"), '精度评估', self.mainwindow)
        self.action.triggered.connect(self.show_dialog)
        ActionManager().evaluation_menu.addAction(self.action)
    
    def run_alg(self, layer:SingleBandRasterLayer, gt):
        if layer is None or gt is None:
            return
        self.send_message.emit('正在进行精度评估...')

        pred_ds = gdal.Open(layer.path)
        pred_band = pred_ds.GetRasterBand(1)
        gt_ds = gdal.Open(gt)
        gt_band = gt_ds.GetRasterBand(1)

        if pred_band is None or gt_band is None:
            return
        
        if pred_ds.RasterXSize != gt_ds.RasterXSize or pred_ds.RasterYSize != gt_ds.RasterYSize:
            self.send_message.emit('真值与预测结果大小不匹配')
            return
        
        
        xsize = pred_ds.RasterXSize
        ysize = pred_ds.RasterYSize

        max_pixels = 1e6
        y_block_size = int(max_pixels / xsize) + 1
        block_count = int(ysize / y_block_size) + 1

        cfm = np.zeros((2,2))

        for i in range(block_count):
            block_size = (xsize, y_block_size)
            block_offset = (0, i * y_block_size)

            if i == block_count - 1:
                block_size = (xsize, ysize - i * y_block_size)
            
            pred_block = pred_band.ReadAsArray(*block_offset, *block_size)
            gt_block = gt_band.ReadAsArray(*block_offset, *block_size)
            pred_block = pred_block.astype(np.uint8)
            gt_block = gt_block.astype(np.uint8)
            valid_mask = ((pred_block == 1) | (pred_block == 0)) & ((gt_block == 1) | (gt_block == 0))
            pred_block = pred_block[valid_mask]
            gt_block = gt_block[valid_mask]

            for k in range(2):
                for l in range(2):
                    cfm[k,l] += np.sum((pred_block == k) & (gt_block == l))
        

        self.send_message.emit('精度评估完成')
    
    def show_dialog(self):
        dialog = EvalutationDialog(self.mainwindow)
        dialog.exec_()
        if dialog.result() == QDialog.Accepted:
            layer = dialog.layer_select.current_layer()
            if not isinstance(layer, SingleBandRasterLayer):
                self.send_message.emit('请选择一个单波段栅格图层')
                return
            t = Thread(target=self.run_alg, args=(layer, dialog.gt_file))
            t.start()
        