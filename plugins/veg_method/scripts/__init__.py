from datetime import datetime
from osgeo import gdal
import math,os
import time
from PyQt5 import QtWidgets
from sklearn.cluster import k_means
from rscder.utils.geomath import geo2imageRC, imageRC2geo
from rscder.utils.project import Project, PairLayer
from misc import Register, AlgFrontend

VEG_CD = Register('植被变化检测方法')

import numpy as np
from .ACD import ACD
from .AHT import AHT
from .OCD import OCD
from .LHBA import LHBA
from .SH import SH

def warp(file,ds:gdal.Dataset,srcWin=[0,0,0,0]):
    driver = gdal.GetDriverByName('GTiff')
    xsize=ds.RasterXSize
    ysize=ds.RasterYSize
    geo=ds.GetGeoTransform()
    orj=ds.GetProjection()
    band=ds.RasterCount
    if os.path.exists(file):
        os.remove(file)
    out_ds:gdal.Dataset=driver.Create(file, xsize, ysize, band, gdal.GDT_Byte)
    out_ds.SetGeoTransform(geo)
    out_ds.SetProjection(orj)
    for b in range(1,band+1):
        out_ds.GetRasterBand(b).WriteArray(ds.ReadAsArray(*srcWin,band_list=[b]),*(0,0))
    del out_ds

@VEG_CD.register
class BasicCD(AlgFrontend):

    @staticmethod
    def get_name():
        return '差分法'
    
    @staticmethod
    def run_alg(pth1:str,pth2:str,layer_parent:PairLayer,send_message = None,*args, **kargs):
            
        ds1:gdal.Dataset=gdal.Open(pth1)
        ds2:gdal.Dataset=gdal.Open(pth2)
        
        cell_size = layer_parent.cell_size
        xsize = layer_parent.size[0]
        ysize = layer_parent.size[1]

        band = ds1.RasterCount
        yblocks = ysize // cell_size[1]

        driver = gdal.GetDriverByName('GTiff')
        out_tif = os.path.join(Project().other_path, 'temp.tif')
        out_ds = driver.Create(out_tif, xsize, ysize, 1, gdal.GDT_Float32)
        geo=layer_parent.grid.geo
        proj=layer_parent.grid.proj
        out_ds.SetGeoTransform(geo)
        out_ds.SetProjection(proj)

        max_diff = 0
        min_diff = math.inf
        
        start1x,start1y=geo2imageRC(ds1.GetGeoTransform(),layer_parent.mask.xy[0],layer_parent.mask.xy[1])
        end1x,end1y=geo2imageRC(ds1.GetGeoTransform(),layer_parent.mask.xy[2],layer_parent.mask.xy[3])

        start2x,start2y=geo2imageRC(ds2.GetGeoTransform(),layer_parent.mask.xy[0],layer_parent.mask.xy[1])
        end2x,end2y=geo2imageRC(ds2.GetGeoTransform(),layer_parent.mask.xy[2],layer_parent.mask.xy[3])

        for j in range(yblocks + 1):#该改这里了
            if send_message is not None:
                send_message.emit(f'计算{j}/{yblocks}')
            block_xy1 = (start1x, start1y+j * cell_size[1])
            block_xy2 = (start2x,start2y+j*cell_size[1])
            block_xy=(0,j * cell_size[1])
            if block_xy1[1] > end1y or block_xy2[1] > end2y:
                break
            block_size=(xsize, cell_size[1])
            block_size1 = (xsize, cell_size[1])  
            block_size2 = (xsize,cell_size[1])
            if block_xy[1] + block_size[1] > ysize:
                block_size = (xsize, ysize - block_xy[1])
            if block_xy1[1] + block_size1[1] > end1y:
                block_size1 = (xsize,end1y - block_xy1[1])
            if block_xy2[1] + block_size2[1] > end2y:
                block_size2 = (xsize, end2y - block_xy2[1]) 
            block_data1 = ds1.ReadAsArray(*block_xy1, *block_size1)
            block_data2 = ds2.ReadAsArray(*block_xy2, *block_size2)

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
            if send_message is not None:

                send_message.emit(f'完成{j}/{yblocks}')
        del ds2
        del ds1
        out_ds.FlushCache()
        del out_ds
        if send_message is not None:
            send_message.emit('归一化概率中...')
        temp_in_ds = gdal.Open(out_tif) 
        
        out_normal_tif = os.path.join(Project().cmi_path, '{}_{}_cmi.tif'.format(layer_parent.name, int(np.random.rand() * 100000)))
        out_normal_ds = driver.Create(out_normal_tif, xsize, ysize, 1, gdal.GDT_Byte)
        out_normal_ds.SetGeoTransform(geo)
        out_normal_ds.SetProjection(proj)
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
        if send_message is not None:
            send_message.emit('差分法计算完成')
        return out_normal_tif

@VEG_CD.register
class LSTS(AlgFrontend):

    @staticmethod
    def get_name():
        return 'LSTS'

    @staticmethod
    def get_widget(parent=None):

        widget = QtWidgets.QWidget(parent)

        return widget

    @staticmethod
    def get_params(widget=None):
        return dict(n=5, w_size=(3,3))
    
    @staticmethod
    def run_alg(pth1:str,pth2:str,layer_parent:PairLayer,send_message=None,n=5,w_size=(3,3), *args, **kws):
        ds1:gdal.Dataset=gdal.Open(pth1)
        ds2:gdal.Dataset=gdal.Open(pth2)
        
        cell_size = layer_parent.cell_size
        xsize = layer_parent.size[0]
        ysize = layer_parent.size[1]

        band = ds1.RasterCount
        yblocks = ysize // cell_size[1]

        driver = gdal.GetDriverByName('GTiff')
        out_tif = os.path.join(Project().other_path, '%d.tif'%(int(datetime.now().timestamp() * 1000)))
        out_ds = driver.Create(out_tif, xsize, ysize, 1, gdal.GDT_Float32)
        geo=layer_parent.grid.geo
        proj=layer_parent.grid.proj
        out_ds.SetGeoTransform(geo)
        out_ds.SetProjection(proj)
        pixnum=w_size[0]*w_size[1]
        # send_message.emit('pixnum:'pixnum)
        max_diff = 0
        min_diff = math.inf
        win_h=w_size[0]//2 #half hight of window 
        win_w=w_size[1]//2 #half width of window
        a=[[(i+1)**j for j in range(n+1)] for i in range(pixnum)]
        A=np.array(a).astype(np.float64)# 
        
        k_=np.array(range(1,n+1))
        df1=np.zeros(pixnum).astype(np.float64)
        df2=np.zeros(pixnum).astype(np.float64)

        start1x,start1y=geo2imageRC(ds1.GetGeoTransform(),layer_parent.mask.xy[0],layer_parent.mask.xy[1])
        end1x,end1y=geo2imageRC(ds1.GetGeoTransform(),layer_parent.mask.xy[2],layer_parent.mask.xy[3])

        start2x,start2y=geo2imageRC(ds2.GetGeoTransform(),layer_parent.mask.xy[0],layer_parent.mask.xy[1])
        end2x,end2y=geo2imageRC(ds2.GetGeoTransform(),layer_parent.mask.xy[2],layer_parent.mask.xy[3])

        for j in range(yblocks + 1):
            if send_message is not None:
                send_message.emit(f'计算{j}/{yblocks}')
            block_xy1 = (start1x, start1y+j * cell_size[1])
            block_xy2 = (start2x,start2y+j*cell_size[1])
            block_xy=(0,j * cell_size[1])
            if block_xy1[1] > end1y or block_xy2[1] > end2y:
                break
            block_size=(xsize, cell_size[1])
            block_size1 = (xsize, cell_size[1])  
            block_size2 = (xsize,cell_size[1])
            if block_xy[1] + block_size[1] > ysize:
                block_size = (xsize, ysize - block_xy[1])
            if block_xy1[1] + block_size1[1] > end1y:
                block_size1 = (xsize,end1y - block_xy1[1])
            if block_xy2[1] + block_size2[1] > end2y:
                block_size2 = (xsize, end2y - block_xy2[1]) 
            block_data1 = ds1.ReadAsArray(*block_xy1, *block_size1)
            block_data2 = ds2.ReadAsArray(*block_xy2, *block_size2)
            
            if band == 1:
                block_data1 =  block_data1[None, ...]
                block_data2 =  block_data2[None, ...]
            # pdb.set_trace()
            else:
                block_data1=np.mean(block_data1,0)
                block_data2=np.mean(block_data2,0)
            block_diff=np.zeros(block_data1.shape).astype(np.float64)

            for i in range(win_h,block_size1[1]-win_h):
                for j_ in range(win_w,block_size1[0]-win_w):
                    pix=0
                    
                    #get b
                    # b1=block_data[i+win_h:i+win_h] c in range(j_-win_w,j_+win_w+1)
                    b1=block_data1[i-win_h:i+win_h+1,j_-win_w:j_+win_w+1]
                    b2=block_data2[i-win_h:i+win_h+1,j_-win_w:j_+win_w+1]
                    b1=[b if (r+1)//2 else b[::-1] for r,b in enumerate(b1)]
                    b2=[b if (r+1)//2 else b[::-1] for r,b in enumerate(b2)]
                    b1=np.expand_dims(np.concatenate(b1,0),1)
                    b2=np.expand_dims(np.concatenate(b2,0),1)

                    x1=np.squeeze(np.linalg.pinv(A).dot(b1))
                    x2=np.squeeze(np.linalg.pinv(A).dot(b2))
                    #df
                    k_=range(1,n+1)
                    for pix in range(1,pixnum+1):
                        df1[pix-1]=x1[1:n+1].dot(np.array([k*(pix**(k-1)) for k in k_]))
                        df2[pix-1]=x2[1:n+1].dot(np.array([k*(pix**(k-1)) for k in k_]))
                    
                    #distance 欧式距离
                    block_diff[i][j_]=np.dot(df1-df2,df1-df2)**0.5
            
            min_diff = min(min_diff, block_diff[block_diff > 0].min())
            max_diff = max(max_diff, block_diff.max())
            out_ds.GetRasterBand(1).WriteArray(block_diff, *block_xy)

            send_message.emit(f'完成{j}/{yblocks}')
        del ds2
        del ds1
        out_ds.FlushCache()
        del out_ds
        if send_message is not None:
            send_message.emit('归一化概率中...')
        temp_in_ds = gdal.Open(out_tif) 
        
        out_normal_tif = os.path.join(Project().cmi_path, '{}_{}_cmi.tif'.format(layer_parent.name, int(np.random.rand() * 100000)))
        out_normal_ds = driver.Create(out_normal_tif, xsize, ysize, 1, gdal.GDT_Byte)
        out_normal_ds.SetGeoTransform(geo)
        out_normal_ds.SetProjection(proj)
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
        
        if send_message is not None:
            send_message.emit('LSTS法计算完成')
        return out_normal_tif


@VEG_CD.register
class CVAAlg(AlgFrontend):

    @staticmethod
    def get_name():
        return 'CVA'

    @staticmethod
    def run_alg(pth1:str,pth2:str,layer_parent:PairLayer,send_message = None, *args, **kargs):

        ds1:gdal.Dataset=gdal.Open(pth1)
        ds2:gdal.Dataset=gdal.Open(pth2)
        
        cell_size = layer_parent.cell_size
        xsize = layer_parent.size[0]
        ysize = layer_parent.size[1]

        band = ds1.RasterCount
        yblocks = ysize // cell_size[1]

        driver = gdal.GetDriverByName('GTiff')
        out_tif = os.path.join(Project().other_path, 'temp.tif')
        out_ds = driver.Create(out_tif, xsize, ysize, 1, gdal.GDT_Float32)
        geo=layer_parent.grid.geo
        proj=layer_parent.grid.proj
        out_ds.SetGeoTransform(geo)
        out_ds.SetProjection(proj)
        max_diff = 0
        min_diff = math.inf
        

        start1x,start1y=geo2imageRC(ds1.GetGeoTransform(),layer_parent.mask.xy[0],layer_parent.mask.xy[1])
        end1x,end1y=geo2imageRC(ds1.GetGeoTransform(),layer_parent.mask.xy[2],layer_parent.mask.xy[3])

        start2x,start2y=geo2imageRC(ds2.GetGeoTransform(),layer_parent.mask.xy[0],layer_parent.mask.xy[1])
        end2x,end2y=geo2imageRC(ds2.GetGeoTransform(),layer_parent.mask.xy[2],layer_parent.mask.xy[3])

        for j in range(yblocks + 1):
            if send_message is not None:
                send_message.emit(f'计算{j}/{yblocks}')
            block_xy1 = (start1x, start1y+j * cell_size[1])
            block_xy2 = (start2x,start2y+j*cell_size[1])
            block_xy=(0,j * cell_size[1])
            if block_xy1[1] > end1y or block_xy2[1] > end2y:
                break
            block_size=(xsize, cell_size[1])
            block_size1 = (xsize, cell_size[1])  
            block_size2 = (xsize,cell_size[1])
            if block_xy[1] + block_size[1] > ysize:
                block_size = (xsize, ysize - block_xy[1])
            if block_xy1[1] + block_size1[1] > end1y:
                block_size1 = (xsize,end1y - block_xy1[1])
            if block_xy2[1] + block_size2[1] > end2y:
                block_size2 = (xsize, end2y - block_xy2[1]) 
            block_data1 = ds1.ReadAsArray(*block_xy1, *block_size1)
            block_data2 = ds2.ReadAsArray(*block_xy2, *block_size2)
            
            if band == 1:
                block_data1 =  block_data1[None, ...]
                block_data2 =  block_data2[None, ...]
            # pdb.set_trace()
            block_diff=np.sum((block_data1-block_data2)**2,0)**0.5
            min_diff = min(min_diff, block_diff[block_diff > 0].min())
            max_diff = max(max_diff, block_diff.max())
            out_ds.GetRasterBand(1).WriteArray(block_diff, *block_xy)
            if send_message is not None:
                send_message.emit(f'完成{j}/{yblocks}')
        del ds2
        del ds1
        out_ds.FlushCache()
        del out_ds
        if send_message is not None:
            send_message.emit('归一化概率中...')
        temp_in_ds = gdal.Open(out_tif) 
        
        out_normal_tif = os.path.join(Project().cmi_path, '{}_{}_cmi.tif'.format(layer_parent.name, int(np.random.rand() * 100000)))
        out_normal_ds = driver.Create(out_normal_tif, xsize, ysize, 1, gdal.GDT_Byte)
        out_normal_ds.SetGeoTransform(geo)
        out_normal_ds.SetProjection(proj)
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
        if send_message is not None:
            send_message.emit('欧式距离计算完成')
        return out_normal_tif

@VEG_CD.register
class ACDAlg(AlgFrontend):

    @staticmethod
    def get_name():
        return 'ACD'
    
    @staticmethod
    def run_alg(pth1:str,pth2:str,layer_parent:PairLayer,send_message = None, *args, **kargs):
        
        if send_message is None:
            class Empty:
                
                def emit(self, *args, **kws):
                    print(args)
            send_message = Empty()
            # send_message.emit = print

        xsize = layer_parent.size[0]
        ysize = layer_parent.size[1]
        geo=layer_parent.grid.geo
        proj=layer_parent.grid.proj
        #提取公共部分
        send_message.emit('提取重叠区域数据.....')

        ds2:gdal.Dataset=gdal.Open(pth2)
        temp_tif2 = os.path.join(Project().other_path,'temp2.tif')
        start2x,start2y=geo2imageRC(ds2.GetGeoTransform(),layer_parent.mask.xy[0],layer_parent.mask.xy[1])
        end2x,end2y=geo2imageRC(ds2.GetGeoTransform(),layer_parent.mask.xy[2],layer_parent.mask.xy[3])
        warp(temp_tif2,ds2,srcWin=[start2x,start2y,xsize,ysize])
        del ds2
        send_message.emit('图像二提取完成')
        

        ds1:gdal.Dataset=gdal.Open(pth1)
        temp_tif1 = os.path.join(Project().other_path, 'temp1.tif')
        start1x,start1y=geo2imageRC(ds1.GetGeoTransform(),layer_parent.mask.xy[0],layer_parent.mask.xy[1])
        end1x,end1y=geo2imageRC(ds1.GetGeoTransform(),layer_parent.mask.xy[2],layer_parent.mask.xy[3])
        warp(temp_tif1,ds1,srcWin=[start1x,start1y,xsize,ysize])
        del ds1
        send_message.emit('图像一提取完成')
        
        
        
        #运算
        send_message.emit('开始ACD计算.....')
        time.sleep(0.1)
        out_normal_tif = os.path.join(Project().cmi_path, '{}_{}_cmi.tif'.format(layer_parent.name, int(np.random.rand() * 100000)))
        ACD(temp_tif1,temp_tif2,out_normal_tif)
        #添加投影
        send_message.emit('录入投影信息.....')
        time.sleep(0.1)
        ds=gdal.Open(out_normal_tif,1)
        ds.SetGeoTransform(geo)
        ds.SetProjection(proj)
        del ds
        
        return out_normal_tif


@VEG_CD.register
class AHTAlg(AlgFrontend):

    @staticmethod
    def get_name():
        return 'AHT'
    
    @staticmethod
    def run_alg(pth1:str,pth2:str,layer_parent:PairLayer,send_message = None, *args, **kargs):
        
        if send_message is None:
            class Empty:
                
                def emit(self, *args, **kws):
                    print(args)
            send_message = Empty()

        xsize = layer_parent.size[0]
        ysize = layer_parent.size[1]
        geo=layer_parent.grid.geo
        proj=layer_parent.grid.proj
        #提取公共部分
        send_message.emit('提取重叠区域数据.....')

        ds2:gdal.Dataset=gdal.Open(pth2)
        temp_tif2 = os.path.join(Project().other_path,'temp2.tif')
        start2x,start2y=geo2imageRC(ds2.GetGeoTransform(),layer_parent.mask.xy[0],layer_parent.mask.xy[1])
        end2x,end2y=geo2imageRC(ds2.GetGeoTransform(),layer_parent.mask.xy[2],layer_parent.mask.xy[3])
        warp(temp_tif2,ds2,srcWin=[start2x,start2y,xsize,ysize])
        del ds2
        send_message.emit('图像二提取完成')
        

        ds1:gdal.Dataset=gdal.Open(pth1)
        temp_tif1 = os.path.join(Project().other_path, 'temp1.tif')
        start1x,start1y=geo2imageRC(ds1.GetGeoTransform(),layer_parent.mask.xy[0],layer_parent.mask.xy[1])
        end1x,end1y=geo2imageRC(ds1.GetGeoTransform(),layer_parent.mask.xy[2],layer_parent.mask.xy[3])
        warp(temp_tif1,ds1,srcWin=[start1x,start1y,xsize,ysize])
        del ds1
        send_message.emit('图像一提取完成')
        
        
        
        #运算
        send_message.emit('开始AHT计算.....')
        time.sleep(0.1)
        out_normal_tif = os.path.join(Project().cmi_path, '{}_{}_cmi.tif'.format(layer_parent.name, int(np.random.rand() * 100000)))
        AHT(temp_tif1,temp_tif2,out_normal_tif)
        #添加投影
        send_message.emit('录入投影信息.....')
        time.sleep(0.1)
        ds=gdal.Open(out_normal_tif,1)
        ds.SetGeoTransform(geo)
        ds.SetProjection(proj)
        del ds
        
        return out_normal_tif


@VEG_CD.register
class OCDAlg(AlgFrontend):

    @staticmethod
    def get_name():
        return 'OCD'
    
    @staticmethod
    def run_alg(pth1:str,pth2:str,layer_parent:PairLayer,send_message = None, *args, **kargs):
        
        if send_message is None:
            class Empty:
                
                def emit(self, *args, **kws):
                    print(args)
            send_message = Empty()

        xsize = layer_parent.size[0]
        ysize = layer_parent.size[1]
        geo=layer_parent.grid.geo
        proj=layer_parent.grid.proj
        #提取公共部分
        send_message.emit('提取重叠区域数据.....')

        ds2:gdal.Dataset=gdal.Open(pth2)
        temp_tif2 = os.path.join(Project().other_path,'temp2.tif')
        start2x,start2y=geo2imageRC(ds2.GetGeoTransform(),layer_parent.mask.xy[0],layer_parent.mask.xy[1])
        end2x,end2y=geo2imageRC(ds2.GetGeoTransform(),layer_parent.mask.xy[2],layer_parent.mask.xy[3])
        warp(temp_tif2,ds2,srcWin=[start2x,start2y,xsize,ysize])
        del ds2
        send_message.emit('图像二提取完成')
        

        ds1:gdal.Dataset=gdal.Open(pth1)
        temp_tif1 = os.path.join(Project().other_path, 'temp1.tif')
        start1x,start1y=geo2imageRC(ds1.GetGeoTransform(),layer_parent.mask.xy[0],layer_parent.mask.xy[1])
        end1x,end1y=geo2imageRC(ds1.GetGeoTransform(),layer_parent.mask.xy[2],layer_parent.mask.xy[3])
        warp(temp_tif1,ds1,srcWin=[start1x,start1y,xsize,ysize])
        del ds1
        send_message.emit('图像一提取完成')
        
        
        
        #运算
        send_message.emit('开始OCD计算.....')
        time.sleep(0.1)
        out_normal_tif = os.path.join(Project().cmi_path, '{}_{}_cmi.tif'.format(layer_parent.name, int(np.random.rand() * 100000)))
        OCD(temp_tif1,temp_tif2,out_normal_tif,Project().other_path)
        #添加投影
        send_message.emit('录入投影信息.....')
        time.sleep(0.1)
        ds=gdal.Open(out_normal_tif,1)
        ds.SetGeoTransform(geo)
        ds.SetProjection(proj)
        del ds
        
        return out_normal_tif

@VEG_CD.register
class LHBAAlg(AlgFrontend):

    @staticmethod
    def get_name():
        return 'LHBA'
    
    @staticmethod
    def run_alg(pth1:str,pth2:str,layer_parent:PairLayer,send_message = None, *args, **kargs):
        
        if send_message is None:
            class Empty:
                
                def emit(self, *args, **kws):
                    print(args)
            send_message = Empty()


        xsize = layer_parent.size[0]
        ysize = layer_parent.size[1]
        geo=layer_parent.grid.geo
        proj=layer_parent.grid.proj
        #提取公共部分
        send_message.emit('提取重叠区域数据.....')

        ds2:gdal.Dataset=gdal.Open(pth2)
        temp_tif2 = os.path.join(Project().other_path,'temp2.tif')
        start2x,start2y=geo2imageRC(ds2.GetGeoTransform(),layer_parent.mask.xy[0],layer_parent.mask.xy[1])
        end2x,end2y=geo2imageRC(ds2.GetGeoTransform(),layer_parent.mask.xy[2],layer_parent.mask.xy[3])
        warp(temp_tif2,ds2,srcWin=[start2x,start2y,xsize,ysize])
        del ds2
        send_message.emit('图像二提取完成')


        ds1:gdal.Dataset=gdal.Open(pth1)
        temp_tif1 = os.path.join(Project().other_path, 'temp1.tif')
        start1x,start1y=geo2imageRC(ds1.GetGeoTransform(),layer_parent.mask.xy[0],layer_parent.mask.xy[1])
        end1x,end1y=geo2imageRC(ds1.GetGeoTransform(),layer_parent.mask.xy[2],layer_parent.mask.xy[3])
        warp(temp_tif1,ds1,srcWin=[start1x,start1y,xsize,ysize])
        del ds1
        send_message.emit('图像一提取完成')

        #运算
        send_message.emit('开始LHBA计算.....')
        time.sleep(0.1)
        out_normal_tif = os.path.join(Project().cmi_path, '{}_{}_cmi.tif'.format(layer_parent.name, int(np.random.rand() * 100000)))
        LHBA(temp_tif1,temp_tif2,out_normal_tif)
        #添加投影
        send_message.emit('录入投影信息.....')
        time.sleep(0.1)
        ds=gdal.Open(out_normal_tif,1)
        ds.SetGeoTransform(geo)
        ds.SetProjection(proj)
        del ds
        return out_normal_tif


@VEG_CD.register
class SHAlg(AlgFrontend):

    @staticmethod
    def get_name():
        return 'SH'
    
    @staticmethod
    def run_alg(pth1:str,pth2:str,layer_parent:PairLayer,send_message = None, *args, **kargs):
        
        if send_message is None:
            class Empty:
                
                def emit(self, *args, **kws):
                    print(args)
            send_message = Empty()



        xsize = layer_parent.size[0]
        ysize = layer_parent.size[1]
        geo=layer_parent.grid.geo
        proj=layer_parent.grid.proj
        #提取公共部分
        send_message.emit('提取重叠区域数据.....')

        ds2:gdal.Dataset=gdal.Open(pth2)
        temp_tif2 = os.path.join(Project().other_path,'temp2.tif')
        start2x,start2y=geo2imageRC(ds2.GetGeoTransform(),layer_parent.mask.xy[0],layer_parent.mask.xy[1])
        end2x,end2y=geo2imageRC(ds2.GetGeoTransform(),layer_parent.mask.xy[2],layer_parent.mask.xy[3])
        warp(temp_tif2,ds2,srcWin=[start2x,start2y,xsize,ysize])
        del ds2
        send_message.emit('图像二提取完成')


        ds1:gdal.Dataset=gdal.Open(pth1)
        temp_tif1 = os.path.join(Project().other_path, 'temp1.tif')
        start1x,start1y=geo2imageRC(ds1.GetGeoTransform(),layer_parent.mask.xy[0],layer_parent.mask.xy[1])
        end1x,end1y=geo2imageRC(ds1.GetGeoTransform(),layer_parent.mask.xy[2],layer_parent.mask.xy[3])
        warp(temp_tif1,ds1,srcWin=[start1x,start1y,xsize,ysize])
        del ds1
        send_message.emit('图像一提取完成')

        #运算
        send_message.emit('开始SH计算.....')
        time.sleep(0.1)
        out_normal_tif = os.path.join(Project().cmi_path, '{}_{}_cmi.tif'.format(layer_parent.name, int(np.random.rand() * 100000)))
        SH(temp_tif1,temp_tif2,out_normal_tif)
        #添加投影
        send_message.emit('录入投影信息.....')
        time.sleep(0.1)
        ds=gdal.Open(out_normal_tif,1)
        ds.SetGeoTransform(geo)
        ds.SetProjection(proj)
        del ds
        return out_normal_tif
