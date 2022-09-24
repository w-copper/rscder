from osgeo import gdal, gdalconst
from rscder.utils.project import Project
import os
from misc import AlgFrontend
from thres import THRES
from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout, QLineEdit
from PyQt5.QtGui import QIntValidator, QDoubleValidator

@THRES.register
class ManulGapAlg(AlgFrontend):

    @staticmethod
    def get_name():
        return '手动阈值'
    
    @staticmethod
    def get_params(widget:QWidget=None):
        if widget is None:
            return dict(gap=125)
        lineedit:QLineEdit =  widget.layout().findChild(QLineEdit, 'lineedit')
        if lineedit is None:
            return dict(gap=125)
        
        gap = int(lineedit.text())

        return dict(gap=gap)
    @staticmethod
    def get_widget(parent=None):
        
        widget = QWidget(parent)
        lineedit = QLineEdit(widget)
        lineedit.setObjectName('lineedit')
        lineedit.setValidator(QIntValidator(1, 254))
        # lineedit.
        label = QLabel('阈值：')

        layout = QHBoxLayout()
        layout.addWidget(label)
        layout.addWidget(lineedit)

        widget.setLayout(layout)
        return widget

    
    @staticmethod
    def run_alg(pth,name = '',gap = 125, send_message = None):

        ds = gdal.Open(pth)
        band = ds.GetRasterBand(1)

        xsize = ds.RasterXSize
        ysize = ds.RasterYSize

        max_pixels = 1e7
        max_rows = max_pixels // xsize
        if max_rows < 1:
            max_rows = 1
        if max_rows > ysize:
            max_rows = ysize
        block_count = ysize // max_rows + 1
        
        if send_message is not None:
            send_message.emit('阈值为：{}'.format(gap))

        out_th = os.path.join(Project().bcdm_path, '{}_thresh{}_bcdm.tif'.format(name,gap))
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
        if send_message is not None:
            send_message.emit('自定义阈值分割完成')
        return out_th


import numpy as np

def OTSU(hist):
   
    u1=0.0#背景像素的平均灰度值
    u2=0.0#前景像素的平均灰度值
    th=0.0

    #总的像素数目
    PixSum= np.sum(hist)
    #各灰度值所占总像素数的比例
    PixRate=hist / PixSum
    #统计各个灰度值的像素个数
    Max_var = 0
    #确定最大类间方差对应的阈值
    GrayScale = len(hist)
    for i in range(1,len(hist)):#从1开始是为了避免w1为0.
        u1_tem=0.0
        u2_tem=0.0
        #背景像素的比列
        w1=np.sum(PixRate[:i])
        #前景像素的比例
        w2=1.0-w1
        if w1==0 or w2==0:
            pass
        else:#背景像素的平均灰度值
            for m in range(i):
                u1_tem=u1_tem+PixRate[m]*m
            u1 = u1_tem * 1.0 / w1
             #前景像素的平均灰度值
            for n in range(i,GrayScale):
                u2_tem = u2_tem + PixRate[n]*n
            u2 = u2_tem / w2
            #print(u1)
            #类间方差公式：G=w1*w2*(u1-u2)**2
            tem_var=w1*w2*np.power((u1-u2),2)
            #print(tem_var)
            #判断当前类间方差是否为最大值。
            if Max_var<tem_var:
                Max_var=tem_var#深拷贝，Max_var与tem_var占用不同的内存空间。
                th=i
    return th 

@THRES.register
class OTSUAlg(AlgFrontend):

    @staticmethod
    def get_name():
        return 'OTSU阈值'
    
    @staticmethod
    def run_alg(pth,name='',send_message=None):

        ds = gdal.Open(pth)
        band = ds.GetRasterBand(1)
        # band_count = ds.RasterCount
        
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
        send_message.emit('阈值为：{}'.format(gap))

        out_th = os.path.join(Project().bcdm_path, '{}_otsu_bcdm.tif'.format(name))
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
        send_message.emit('OTSU阈值完成')
        
        return out_th
        # ManulGapAlg.run_alg