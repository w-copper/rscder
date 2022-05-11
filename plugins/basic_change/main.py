import math
import os
import pdb
from rscder.plugins.basic import BasicPlugin
from PyQt5.QtWidgets import QAction
from PyQt5.QtCore import pyqtSignal
from rscder.utils.project import PairLayer, ResultLayer
from osgeo import gdal, gdal_array
from threading import Thread
import numpy as np
class BasicMethod(BasicPlugin):

    message_send  = pyqtSignal(str)
    table_result_ok = pyqtSignal(str)

    @staticmethod
    def info():
        return {
            'name': 'BasicMethod',
            'description': 'BasicMethod',
            'author': 'RSCDER',
            'version': '1.0.0',
        }

    def set_action(self):
        basic_change_detection_menu = self.ctx['change_detection_menu']

        basic_diff_method = QAction('差分法')
        basic_change_detection_menu.addAction(basic_diff_method)

        basic_diff_method.setEnabled(False)
        self.basic_diff_method = basic_diff_method
        basic_diff_method.triggered.connect(self.basic_diff_alg)

        self.message_send.connect(self.send_message)
        self.table_result_ok.connect(self.on_table_result_ok)

        self.gap = 128

    def on_data_load(self, layer_id):
        self.basic_diff_method.setEnabled(True)

    def send_message(self, s):
        self.message_box.info(s)
    
    def on_table_result_ok(self, s):
        with open(s, 'r') as f:
            lines = f.readlines()
            data_lines = lines[1:]
        
        if len(data_lines) > 0:
            data_table = []
            for l in data_lines:
                l = l.strip()
                ls = l.split(',')
                ls = [float(i) for i in ls]
                data_table.append(ls)
            result = ResultLayer(ResultLayer.POINT)
            result.data = data_table
            self.result_table.set_data(result)


    def run_basic_diff_alg(self, pth1, pth2, cell_size, out):
        self.message_send.emit('开始计算差分法')

        ds1 = gdal.Open(pth1)
        ds2 = gdal.Open(pth2)
        xsize = ds1.RasterXSize
        ysize = ds1.RasterYSize
        band = ds1.RasterCount
        yblocks = ysize // cell_size[1]

        geo = ds1.GetGeoTransform()

        driver = gdal.GetDriverByName('GTiff')
        out_tif = os.path.join(out, 'temp.tif')
        out_ds = driver.Create(out_tif, xsize, ysize, 1, gdal.GDT_Float32)
        out_ds.SetGeoTransform(ds1.GetGeoTransform())
        out_ds.SetProjection(ds1.GetProjection())
        max_diff = 0
        min_diff = math.inf
        for j in range(yblocks):
            self.message_send.emit(f'计算{j}/{yblocks}')
            block_xy = (0, j * cell_size[1])
            block_size = (xsize, cell_size[1])
            if block_xy[1] + block_size[1] > ysize:
                block_size = (xsize, ysize - block_xy[1])
            block_data1 = ds1.ReadAsArray(*block_xy, *block_size)
            block_data2 = ds2.ReadAsArray(*block_xy, *block_size)

            if band == 1:
                block_data1 =  block_data1[None, ...]
                block_data2 =  block_data2[None, ...]
            # pdb.set_trace()
            block_diff = block_data1 - block_data2
            block_diff = block_diff.astype(np.float32)
            block_diff = np.abs(block_diff).sum(0)
            
            min_diff = min(min_diff, block_diff.min())
            max_diff = max(max_diff, block_diff.max())
            out_ds.GetRasterBand(1).WriteArray(block_diff, *block_xy)

            self.message_send.emit(f'完成{j}/{yblocks}')

        out_ds.FlushCache()
        del out_ds
        self.message_send.emit('归一化概率中...')
        temp_in_ds = gdal.Open(out_tif) 

        out_normal_tif = os.path.join(out, 'diff_0_255.tif')
        out_normal_ds = driver.Create(out_normal_tif, xsize, ysize, 1, gdal.GDT_Byte)

        for j in range(yblocks):
            block_xy = (0, j * cell_size[1])
            block_size = (xsize, cell_size[1])
            if block_xy[1] + block_size[1] > ysize:
                block_size = (xsize, ysize - block_xy[1])
            block_data = temp_in_ds.ReadAsArray(*block_xy, *block_size)
            block_data = (block_data - min_diff) / (max_diff - min_diff) * 255
            block_data = block_data.astype(np.uint8)
            out_normal_ds.GetRasterBand(1).WriteArray(block_data, *block_xy)
        
        out_normal_ds.FlushCache()
        del out_normal_ds
        self.message_send.emit('完成归一化概率')   

        self.message_send.emit('计算变化表格中...')
        out_csv = os.path.join(out, 'diff_table.csv')
        xblocks = xsize // cell_size[0]
        
        normal_in_ds = gdal.Open(out_normal_tif)

        with open(out_csv, 'w') as f:
            f.write('x,y,diff,status\n')
            for j in range(yblocks):
                block_xy = (0, j * cell_size[1])
                block_size = (xsize, cell_size[1])
                if block_xy[1] + block_size[1] > ysize:
                    block_size = (xsize, ysize - block_xy[1])
                block_data = normal_in_ds.ReadAsArray(*block_xy, *block_size)
                for i in range(xblocks):
                    start_x = i * cell_size[0]
                    end_x = start_x + cell_size[0]
                    if end_x > xsize:
                        end_x = xsize
                    block_data_xy = block_data[:, start_x:end_x]
                    if block_data_xy.mean() > self.gap:
                        center_x = start_x + cell_size[0] // 2
                        center_y = j * cell_size[1] + cell_size[1] // 2
                        center_x = center_x * geo[1] + geo [0]
                        center_y = center_y * geo[5] + geo [3]
                        f.write(f'{center_x},{center_y},{block_data_xy.mean()},1\n')
        
        self.table_result_ok.emit(out_csv)

        self.message_send.emit('完成计算变化表格')
                    
        self.message_send.emit('差分法计算完成')

    def basic_diff_alg(self):
        # layer_select = 
        layer:PairLayer = list(self.project.layers.values())[0]

        img1 = layer.pth1
        img2 = layer.pth2

        if not layer.check():
            return
        out_dir =os.path.join(self.project.root, 'basic_diff_result')
        if not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)

        t = Thread(target=self.run_basic_diff_alg, args=(img1, img2, layer.cell_size, out_dir))
        t.start()


        