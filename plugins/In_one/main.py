import os
from threading import Thread
import numpy as np
# from plugins.basic_change.main import MyDialog
from rscder.gui.actions import ActionManager
from rscder.plugins.basic import BasicPlugin
from PyQt5.QtWidgets import QAction, QDialog, QHBoxLayout, QVBoxLayout, QPushButton,QWidget,QLabel,QLineEdit,QPushButton,QComboBox,QDialogButtonBox
from PyQt5.QtGui import QPixmap

from rscder.gui.layercombox import PairLayerCombox
from rscder.utils.icons import IconInstance
from rscder.utils.geomath import geo2imageRC
from rscder.utils.project import Project,  PairLayer,ResultPointLayer,MultiBandRasterLayer
from In_one.otsu import OTSU
from osgeo import gdal
from In_one import pic
import math
from skimage.filters import rank
from skimage.morphology import disk, rectangle
from In_one.scripts.UnsupervisedCD import LSTS,CVA,ACD_
from In_one.scripts.USCD import ACD
def Meanfilter(x_size,y_size,layer:MultiBandRasterLayer):
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
    return out_path

def basic_cd(pth1:str,pth2:str,layer_parent:PairLayer,send_message):
    ds1:gdal.Dataset=gdal.Open(pth1)
    ds2:gdal.Dataset=gdal.Open(pth2)
    
    cell_size = layer_parent.cell_size
    xsize = layer_parent.size[0]
    ysize = layer_parent.size[1]

    band = ds1.RasterCount
    yblocks = ysize // cell_size[1]

    driver = gdal.GetDriverByName('GTiff')
    out_tif = os.path.join(Project().cmi_path, 'temp.tif')
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

        send_message.emit(f'完成{j}/{yblocks}')
    del ds2
    del ds1
    out_ds.FlushCache()
    del out_ds
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

    # raster_result_layer = SingleBandRasterLayer(None, True, out_normal_tif, BasicLayer.BOATH_VIEW)

    # layer1.layer_parent.add_result_layer(point_result_lalyer)
    # layer1.layer_parent.add_result_layer(raster_result_layer)

    # self.send_message.emit('完成计算变化表格')
                
    send_message.emit('差分法计算完成')
    return out_normal_tif

def otsu(pth,name,send_message):
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
    return out_th,gap
    #otsu_layer = SingleBandRasterLayer(path = out_th, style_info={})
    #layer.layer_parent.add_result_layer(otsu_layer)

def thresh(pth,gap,name,send_message):
    ds = gdal.Open(pth)
    band = ds.GetRasterBand(1)
    # band_count = ds.RasterCount
    
    
    xsize = ds.RasterXSize
    ysize = ds.RasterYSize

    max_pixels = 1e7
    max_rows = max_pixels // xsize
    if max_rows < 1:
        max_rows = 1
    if max_rows > ysize:
        max_rows = ysize
    block_count = ysize // max_rows + 1
    # for i in range(block_count):
    #     start_row = i * max_rows
    #     end_row = min((i + 1) * max_rows, ysize)
    #     block = band.ReadAsArray(0, start_row, xsize, end_row - start_row)
        # hist += np.histogram(block.flatten(), bins=256, range=(0, 255))[0]
    # hist = hist.astype(np.float32)
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
    send_message.emit('自定义阈值分割完成')
    return out_th
    #otsu_layer = SingleBandRasterLayer(path = out_th, style_info={})
    #layer.layer_parent.add_result_layer(otsu_layer)

def table_layer(pth,layer,name,send_message,dict):
    send_message.emit('正在计算表格结果...')
    cell_size = layer.layer_parent.cell_size
    ds = gdal.Open(pth)
    xsize = ds.RasterXSize
    ysize = ds.RasterYSize
    geo = ds.GetGeoTransform()

    out_csv = os.path.join(Project().other_path, f'{name}_table_result.csv')
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
                
                center_x = start_x + cell_size[0] // 2
                center_y = j * cell_size[1] + cell_size[1] // 2
                center_x = center_x * geo[1] + geo [0]
                center_y = center_y * geo[5] + geo [3]
                f.write(f'{center_x},{center_y},{block_data_xy.mean() * 100},{int(block_data_xy.mean() > 0.5)}\n')

    result_layer = ResultPointLayer(out_csv, enable=True, proj=layer.proj, geo=layer.geo,result_path=dict)
    # print(result_layer.result_path)
    layer.layer_parent.add_result_layer(result_layer)
    send_message.emit('计算完成')

class LockerButton(QPushButton):
    def __init__(self,parent=None):
        super(LockerButton,self).__init__(parent)
        m_imageLabel =  QLabel(self)
        m_imageLabel.setFixedWidth(20)
        m_imageLabel.setScaledContents(True)
        m_imageLabel.setStyleSheet("QLabel{background-color:transparent;}")
        m_textLabel =  QLabel(self)
        m_textLabel.setStyleSheet("QLabel{background-color:transparent;}")
        self.m_imageLabel=m_imageLabel
        self.m_textLabel=m_textLabel
        self.hide_=1
        mainLayout =  QHBoxLayout()
        
        mainLayout.addWidget(self.m_imageLabel)
        mainLayout.addWidget(self.m_textLabel)
        mainLayout.setContentsMargins(0,0,0,0)
        mainLayout.setSpacing(0)
        self.setLayout(mainLayout)
    def SetImageLabel(self, pixmap:QPixmap):
        self.m_imageLabel.setPixmap(pixmap)
    def SetTextLabel(self, text):
        self.m_textLabel.setText(text)


class selectCombox(QComboBox):
    def __init__(self, parent,list:list,default='--') :
        super(selectCombox,self).__init__(parent)
        self.choose=None
        self.list=list
        self.default=default
        self.addItem(default, None)
        self.addItems(list)
        self.currentIndexChanged.connect(self.on_change)
    
    def on_change(self,index):
        if index == 0:
            self.choose=self.default
        else:
            self.choose=self.list[index-1]
        # print(self.choose)

class AllInOne(QDialog):
    def __init__(self, pre,cd,threshold,parent=None):
        super(AllInOne, self).__init__(parent)
        self.setWindowTitle('变化检测')
        self.setWindowIcon(IconInstance().LOGO)
        self.pre=pre#['均值滤波','test滤波']
        self.cd=cd#['差分法','test法']
        self.threshold=threshold#['OTSU']
        self.initUI()

    def initUI(self):
        #图层
        self.layer_combox = PairLayerCombox(self)
        layerbox = QHBoxLayout()
        layerbox.addWidget(self.layer_combox)

        #预处理
        filterWeight=QWidget(self)
        filterlayout=QVBoxLayout()
        filerButton =LockerButton(filterWeight)
        filerButton.setObjectName("filerButton")
        filerButton.SetTextLabel("预处理")
        filerButton.SetImageLabel(QPixmap('plugins/In_one/pic/箭头_列表展开.png'))
        filerButton.setStyleSheet("#filerButton{background-color:transparent;border:none;}"
        "#filerButton:hover{background-color:rgba(195,195,195,0.4);border:none;}")
        self.pre_select=selectCombox(self,self.pre)
        
        x_size_input = QLineEdit(self)
        x_size_input.setText('3')
        y_size_input = QLineEdit(self)
        y_size_input.setText('3')
        size_label = QLabel(self)
        size_label.setText('窗口大小:')
        time_label = QLabel(self)
        time_label.setText('X')
        self.x_size_input = x_size_input
        self.y_size_input = y_size_input
        hlayout1 = QHBoxLayout()
        hlayout1.addWidget(size_label)
        hlayout1.addWidget(x_size_input)
        hlayout1.addWidget(time_label)
        hlayout1.addWidget(y_size_input)
        vlayout = QVBoxLayout()
        vlayout.addWidget(self.pre_select)
        vlayout.addLayout(hlayout1)
        filterWeight.setLayout(vlayout)
        filterlayout.addWidget(filerButton)
        filterlayout.addWidget(filterWeight)
        #变化检测
        changelayout=QVBoxLayout()
        changeWeight=QWidget(self)
        changeButton =LockerButton(changeWeight)
        changeButton.setObjectName("changeButton")
        changeButton.SetTextLabel("变化检测")
        changeButton.SetImageLabel(QPixmap('plugins/In_one/pic/箭头_列表展开.png'))
        changeButton.setStyleSheet("#changeButton{background-color:transparent;border:none;}"
        "#changeButton:hover{background-color:rgba(195,195,195,0.4);border:none;}")
        changeWeightlayout=QVBoxLayout()
        self.cd_select=selectCombox(self,self.cd)
        changeWeightlayout.addWidget(self.cd_select)
        changeWeight.setLayout(changeWeightlayout)
        changelayout.addWidget(changeButton)
        changelayout.addWidget(changeWeight)

        #阈值处理
        thresholdlayout=QVBoxLayout()
        thresholdWeight=QWidget(self)
        thresholdButton =LockerButton(thresholdWeight)
        thresholdButton.setObjectName("thresholdButton")
        thresholdButton.SetTextLabel("阈值处理")
        thresholdButton.SetImageLabel(QPixmap('plugins/In_one/pic/箭头_列表展开.png'))
        thresholdButton.setStyleSheet("#thresholdButton{background-color:transparent;border:none;}"
        "#thresholdButton:hover{background-color:rgba(195,195,195,0.4);border:none;}")
        self.threshold_select=selectCombox(self,self.threshold,default='手动阈值')
        self.threshold_input=QLineEdit(self)
        self.threshold_input.setText('0.5')
        self.threshold_select.currentIndexChanged.connect(lambda index:self.hide_(self.threshold_input,index==0))
        thresholdWeightlayout=QVBoxLayout()
        thresholdWeightlayout.addWidget(self.threshold_select)
        thresholdWeightlayout.addWidget(self.threshold_input)

        thresholdWeight.setLayout(thresholdWeightlayout)
        thresholdlayout.addWidget(thresholdButton)
        thresholdlayout.addWidget(thresholdWeight)

        #确认
        
        self.ok_button = QPushButton('确定', self)
        self.ok_button.setIcon(IconInstance().OK)
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setDefault(True)
        

        self.cancel_button = QPushButton('取消', self)
        self.cancel_button.setIcon(IconInstance().CANCEL)
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setDefault(False)
        buttonbox=QDialogButtonBox(self)
        buttonbox.addButton(self.ok_button,QDialogButtonBox.NoRole)
        buttonbox.addButton(self.cancel_button,QDialogButtonBox.NoRole)
        buttonbox.setCenterButtons(True)
        #buttonbox.setContentsMargins(,)
        

        totalvlayout=QVBoxLayout()
        totalvlayout.addLayout(layerbox)
        totalvlayout.addLayout(filterlayout)
        totalvlayout.addLayout(changelayout)
        totalvlayout.addLayout(thresholdlayout)
        totalvlayout.addWidget(buttonbox)
        totalvlayout.addStretch()
        
        self.setLayout(totalvlayout)


        filerButton.clicked.connect(lambda: self.hide(filerButton,filterWeight))
        changeButton.clicked.connect(lambda: self.hide(changeButton,changeWeight))
        thresholdButton.clicked.connect(lambda: self.hide(thresholdButton,thresholdWeight))



    def hide(self,button:LockerButton,weight:QWidget):
        if ((button.hide_)%2)==1:
            weight.setVisible(False)
            button.SetImageLabel(QPixmap('plugins/In_one/pic/箭头_列表向右.png'))
        else:
            weight.setVisible(True)
            button.SetImageLabel(QPixmap('plugins/In_one/pic/箭头_列表展开.png'))
        button.hide_=(button.hide_)%2+1
    def hide_(self,widget:QWidget,h:bool):
        if h:
            widget.setVisible(True)
        else:
            widget.setVisible(False)
    def hideWidget(self,widget:QWidget):
        if widget.isVisible:
            widget.setVisible(False)
        else:
            widget.setVisible(True)
    @property
    def param(self):
        class param(object):
            pass
        p=param()
        p.pre=self.pre
        p.cd=self.cd
        p.threshold=self.threshold
        p.layer_combox=self.layer_combox
        p.pre_select=self.pre_select
        p.x_size_input=self.x_size_input
        p.y_size_input=self.y_size_input
        p.threshold_select=self.threshold_select
        p.threshold_input=self.threshold_input
        p.cd_select=self.cd_select
        return p
class InOnePlugin(BasicPlugin):
    pre={"均值滤波":Meanfilter}#可添加其他方法
    cd={'差分法':basic_cd,'LSTS':LSTS,'CVA':CVA,'ACD':ACD_}#可添加其他方法
    threshold={'OTSU阈值':otsu}#可添加其他方法


    @staticmethod
    def info():
        return {
            'name': 'AllinOne',
            'description': 'AllinOne',
            'author': 'RSCDER',
            'version': '1.0.0',
        }

    def set_action(self):
        
        basic_diff_method_in_one = QAction(IconInstance().UNSUPERVISED, '&无监督变化检测')
        ActionManager().change_detection_menu.addAction(basic_diff_method_in_one)
        # ActionManager().menubar.addAction(basic_diff_method_in_one)
        self.basic_diff_method_in_one = basic_diff_method_in_one
        basic_diff_method_in_one.triggered.connect(self.run) 

    def run(self):
        myDialog=AllInOne(list(self.pre.keys()),list(self.cd.keys()),list(self.threshold.keys()),self.mainwindow)
        myDialog.show()
        if myDialog.exec_()==QDialog.Accepted:
            w=myDialog.param
            t=Thread(target=self.run_alg,args=(w,))
            t.start()

    def run_alg(self,w:AllInOne):
        dict={}
        layer1=w.layer_combox.layer1
        
        
        pth1 = w.layer_combox.layer1.path
        pth2 = w.layer_combox.layer2.path
        name=layer1.layer_parent.name
    # 预处理
        # 若添加的预处理函数接口相同，则无需判断是哪种方法
        # if w.pre_select.choose==self.pre.keys()[0]:
        #     pass
        # el
        preKey=w.pre_select.choose
        pth1=self.pre[preKey](w.x_size_input.text(),w.y_size_input.text(),w.layer_combox.layer1)
        self.send_message.emit('{}图像{}'.format(preKey,w.layer_combox.layer1.name))
        pth2=self.pre[preKey](w.x_size_input.text(),w.y_size_input.text(),w.layer_combox.layer2)
        self.send_message.emit('{}图像{}'.format(preKey,w.layer_combox.layer2.name))
        name=name+'_'+preKey
        dict['预处理']=[preKey,'|'.format(pth1,pth2)]


        cdpth=None
    #变化检测
        # if w.cd_select.choose==self.cd[0]:
        # if w.cd_select.choose=='ACD':
        #     cdKey='ACD'
        #     self.send_message.emit('ACD计算中...')
        #     cdpth=os.path.join(Project().cmi_path, '{}_{}_cmi.tif'.format(w.layer_combox.layer1.layer_parent.name, int(np.random.rand() * 100000)))
        #     print(pth1,pth2,cdpth)
        #     ACD(pth1,pth2,cdpth)
        # else:
        #     pass
        cdKey=w.cd_select.choose
        cdpth=self.cd[cdKey](pth1,pth2,w.layer_combox.layer1.layer_parent,self.send_message)
        name += '_'+cdKey
        dict['变化检测算法']=[cdKey,cdpth]
        
    #阈值处理
    #例如手动阈值和otsu参数不同，则要做区分
        thpth=None
        if w.threshold_select.choose=='手动阈值':
            thpth=thresh(cdpth,float(w.threshold_input.text()),w.layer_combox.layer1.layer_parent.name,self.send_message)
            dict['后处理']=['手动阈值',[float(w.threshold_input.text())],thpth]
        else:
            thpth,gap=otsu(cdpth,w.layer_combox.layer1.layer_parent.name,self.send_message)
            name+='_otsu'
            dict['后处理']=['OTSU阈值',gap,cdpth]

        table_layer(thpth,layer1,name,self.send_message,dict)

