from cgitb import enable
from collections import OrderedDict
from email.message import Message
import imp
import inspect
import os
from pathlib import Path
from pydoc import render_doc
import shutil
from statistics import stdev
from tabnanny import check
from threading import Thread
from time import sleep, time
from typing import Dict, List
import uuid
import numpy as np
from osgeo import gdal, gdal_array,osr
from rscder.utils.icons import IconInstance
from rscder.gui.info import InfoBox
from rscder.utils.setting import Settings
from qgis.core import (\
    QgsRasterLayer, QgsMarkerSymbol, QgsUnitTypes, 
    QgsCategorizedSymbolRenderer, QgsRendererCategory, 
    QgsPalLayerSettings, QgsRuleBasedLabeling, QgsTextFormat, 
    QgsLineSymbol, QgsSingleSymbolRenderer, QgsSimpleLineSymbolLayer, 
    QgsVectorLayer, QgsCoordinateReferenceSystem, QgsFeature, 
    QgsGeometry, QgsPointXY, QgsMultiBandColorRenderer)
from PyQt5.QtCore import QObject, pyqtSignal, Qt, QThread,QSize
from PyQt5.QtWidgets import QTreeWidgetItem, QAction,QMessageBox
from PyQt5.QtGui import QColor, QIcon, QFont,QPixmap
import yaml
from rscder.utils.geomath import geo2imageRC,imageRC2geo
from .misc import singleton
def relative_path(path: str, root:str) -> str:
    return os.path.relpath(path, root)

@singleton
class Project(QObject):

    instance:'Project'

    project_init = pyqtSignal(bool)
    # layer_load = pyqtSignal()
    layer_tree_update = pyqtSignal()
    layer_show_update = pyqtSignal()

    ABSOLUTE_MODE = 'absolute'
    RELATIVE_MODE = 'relative'

    def run_auto_save(self):
        # t = QThread(self)
        if self.in_save:
            return
        if not self.is_init:
            return
        if not Settings.General().auto_save:
            return
        t = Thread(target=self.auto_save)
        t.start()
        
    def auto_save(self):
        # pre = time()
        self.in_save = True
        self.save()
        self.in_save = False
        
    def __init__(self, 
                    parent=None):
        super().__init__(parent)
        self.is_init = False
        self.cell_size = Settings.Project().cell_size
        self.max_memory = Settings.Project().max_memory
        self.max_threads = Settings.Project().max_threads
        self.root = str(Path(Settings.General().root)/'default')
        self.file_mode = Project.ABSOLUTE_MODE
        self.layers:Dict[str, PairLayer] = OrderedDict()
        self.current_layer = None
        self.is_closed = False
        self.in_save = False

        def set_close():
            self.is_closed = True
        
        parent.closed.connect(set_close)

        self.run_auto_save()

    def connect(self, 
             pair_canvas,
             layer_tree,
             message_box,
             result_table,
             eye):
        self.pair_canvas = pair_canvas
        self.layer_tree = layer_tree
        self.message_box = message_box
        self.result_table = result_table
        self.eye=eye
        IconInstance(self)
        self.layer_tree_update.connect(layer_tree.update_layer)
        self.layer_show_update.connect(pair_canvas.update_layer)
        self.layer_show_update.connect(eye.update_layer)
        eye.extent.connect(pair_canvas.zoom_to_extent)
        self.layer_tree_update.connect(self.run_auto_save)
        self.layer_show_update.connect(self.run_auto_save)

    def setup(self, path = None, name = None):
        '''
        create: path is not None and name is not None
        open:   path is file and name is None
        '''
        if path is not None and name is not None:
            self.root = str(Path(path)/name)
            self.file = str(Path(self.root)/(name + '.prj'))
        elif name is None:
            self.file = path
            self.root = os.path.split(path)[0]
        else:
            self.message_box.error('打开或创建工程失败')
        try:
            if not os.path.exists(self.root):
                os.makedirs(self.root, exist_ok=True)
            if not os.path.exists(self.file):
                with open(self.file, 'w') as f:
                    pass
            else:
                self.load()

            self.is_init = True
            self.project_init.emit(True)
        except:
            self.message_box.error('打开或创建工程失败')

    def save(self):
        data_dict = {
            'cell_size': self.cell_size,
            'max_memory': self.max_memory,
            'max_threads': self.max_threads,
            'root': self.root,
            'layers': [ layer.to_dict() for layer in self.layers.values() ],
        }
        # for layer in self.layers.values():
        #     layer.save()
        with open(self.file, 'w') as f:
            yaml.safe_dump(data_dict, f)

    def clear(self):
        '''
        clear all layers
        '''
        self.layers:Dict[str, PairLayer] = dict()
        self.layer_tree.clear()
        self.pair_canvas.clear()
        self.message_box.clear()
        self.result_table.clear()

    def load(self):
        try:
            with open(self.file, 'r') as f:
                data = yaml.safe_load(f)
            if data is None:
                return  
            # data = yaml.safe_load(open(self.file, 'r'))
            self.cell_size = data['cell_size']
            self.max_memory = data['max_memory']
            self.max_threads = data['max_threads']
            self.root = data['root']
            self.layers = dict()
            for layer in data['layers']:
                player = PairLayer.from_dict(layer)
                if player.check():
                    self.layers[player.id] = player
            
            self.layer_show_update.emit()
            self.layer_tree_update.emit()
            if len(list(self.layers.values())) > 0:
                self.current_layer = list(self.layers.values())[0]
                self.pair_canvas.zoom_to_layer(list(self.layers.values())[0].main_l1.layer)

        except Exception as e:
            self.message_box.error(str(e))
            self.clear()

    def zoom_to_layer(self, data):
        self.pair_canvas.zoom_to_layer(data['layer'])
        self.eye.zoom(data['layer'])

    @property
    def cmi_path(self):
        pth = os.path.join(self.root, 'cmi')
        if not os.path.exists(pth):
            os.makedirs(pth)
        return pth
    
    @property
    def bcdm_path(self):
        pth = os.path.join(self.root, 'bcdm')
        if not os.path.exists(pth):
            os.makedirs(pth)
        return pth
    @property
    def evalution_path(self):
        pth = os.path.join(self.root, 'evalution')
        if not os.path.exists(pth):
            os.makedirs(pth)
        return pth
    
    @property
    def other_path(self):
        pth = os.path.join(self.root, 'other')
        if not os.path.exists(pth):
            os.makedirs(pth)
        return pth

    def add_layer(self, pth1, pth2,style_info1,style_info2):
        player = PairLayer(pth1, pth2,style_info1,style_info2)
        if player.check():
            self.layers[player.id] = player
            self.layer_show_update.emit()
            self.layer_tree_update.emit()
            self.pair_canvas.zoom_to_layer(player.main_l1.layer)
        else:
            self.message_box.error(f'{player.name} and {player.name} are not same size')

def to_dict(obj:'BasicLayer'):
    init_args = inspect.getfullargspec(obj.__class__.__init__)[0][1:]
    data = {}
    for args in init_args:
        if hasattr(obj, args):
            data[args] = getattr(obj, args)
    data['type']=obj.__class__.__name__
    return data

def from_dict(data:dict):
    cls_type = data.pop('type')
    if cls_type is not None and cls_type in globals():
        return globals()[cls_type](**data)


class BasicLayer(QObject):

    LEFT_VIEW=1
    RIGHT_VIEW=2
    BOATH_VIEW=3

    IN_MEMORY=1
    IN_FILE=2

    layer_tree_update = pyqtSignal()
    layer_show_update = pyqtSignal()
    zoom_to_layer = pyqtSignal(dict)
    
    def __init__(self,
                name='未命名',
                enable = False,
                icon = None,
                path = None,
                path_mode = IN_MEMORY,
                view_mode = BOATH_VIEW,):
        super().__init__(Project())
        self.enable = enable
        self.name = name
        self.icon = icon
        self._path = path
        self._expand = True
        self.path_mode = path_mode
        self.view_mode = view_mode
        self.layer = None
        self.layer_parent = None
        self.layer_tree_update.connect(Project().layer_tree_update)
        self.layer_show_update.connect(Project().layer_show_update)
        self.zoom_to_layer.connect(Project().zoom_to_layer)

    @property
    def path(self):
        if self.path_mode == BasicLayer.IN_FILE and Project().file_mode == Project.RELATIVE_MODE:
            return os.path.relpath(self._path, Project().root)
        return self._path

    def get_item(self, root):
        
        item = QTreeWidgetItem(root)
        if self.icon is not None:
            item.setIcon(0, self.icon)
        item.setText(0, self.name)
        item.setCheckState(0, Qt.Checked if self.enable else Qt.Unchecked)
        item.item_update = self.item_update
        item.get_actions = self.get_actions
        item.setExpanded(self._expand)

        return item

    def item_update(self, item:QTreeWidgetItem):
        # item = self._item
        # print('start update')
        self.name = item.text(0)
        self._expand = item.isExpanded()
        pre = self.enable
        cur = item.checkState(0) == Qt.Checked
        if pre != cur:
            self.enable = cur
            self.layer_show_update.emit()
        # print('end update')

    def set_layer_parent(self, layer):
        self.layer_parent = layer

    def get_actions(self):
        actions = []
        zoom_to_action = QAction(IconInstance().GRID_ON, '缩放至所在图层', self)
        actions.append(zoom_to_action)
        def zoom_to():
            self.zoom_to_layer.emit(dict(layer=self.layer))
        zoom_to_action.triggered.connect(zoom_to)

        del_action = QAction(IconInstance().DELETE, '删除图层', self)

        def del_layer():
            if self.layer_parent is None:
                Project().layers.pop(self.id)
            else:
                self.layer_parent.remove_layer(self)
            self.layer_tree_update.emit()
            self.layer_show_update.emit()
        del_action.triggered.connect(del_layer)
        actions.append(del_action)

        if self.info:
            show_info=QAction(IconInstance().HELP,'属性信息')
            actions.append(show_info)
            def showIofn(info):
                #print(info)
                a=InfoBox(info)
                a.exec_()

            show_info.triggered.connect(lambda :showIofn(self.info))
        return actions

        return actions
    @property
    def info(self):
        return None

class GridLayer(BasicLayer):
    
    def set_render(self):
        symbol_layer = QgsSimpleLineSymbolLayer()
        width = 1
        if self.geo is not None:
            width = self.geo[1]
        symbol_layer.setWidth(width)
        symbol_layer.setColor(QColor.fromRgb(255,255,255, 255))

        symbol = QgsLineSymbol()
        symbol.changeSymbolLayer(0, symbol_layer)
        symbol.setWidthUnit(QgsUnitTypes.RenderMapUnits)
        render = QgsSingleSymbolRenderer(symbol)
        self.layer.setRenderer(render)
        

    def __init__(self, proj, geo, x_size, y_size, enable=True, name='格网', cell_size=(100,100), style_opts={}):

        super().__init__(name, enable, icon=IconInstance().GRID_ON)

        self.cell_size = cell_size
        self.proj = proj
        self.geo = geo
        self.x_size = x_size
        self.y_size = y_size

        self.x_min = geo[0]
        self.y_min = geo[3]
        self.x_res = geo[1]
        self.y_res = geo[5]
        self.x_max = self.x_min + self.x_res * self.x_size
        self.y_max = self.y_min + self.y_res * self.y_size
        self.x_lines = []
        for xi in range(self.x_size // self.cell_size[0] +1):
            self.x_lines.append(self.x_min + self.x_res * xi * self.cell_size[0])
        if self.x_lines[-1] > self.x_max:
            self.x_lines.pop()
        self.x_lines.append(self.x_max)
        self.y_lines = []
        for yi in range(self.y_size // self.cell_size[1]+1):
            self.y_lines.append(self.y_min + self.y_res * yi * self.cell_size[1])
        if self.y_lines[-1] < self.y_max:
            self.y_lines.pop()
        self.y_lines.append(self.y_max)
        crs = QgsCoordinateReferenceSystem()
        crs.createFromString('WKT:{}'.format(proj))
        # print(crs)
        lines_layer = QgsVectorLayer('LineString?crs={}'.format(crs.toProj()), 'temp-grid-outline', "memory")
        if not lines_layer.isValid():
            Project().message_box.error('Failed to create grid outline layer')
            return
        lines_layer.setLabelsEnabled(False)
        lines_layer.startEditing()
        features = []
        for x in self.x_lines:
            line = QgsFeature()
            line.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(x, self.y_min), QgsPointXY(x, self.y_max)]))
            features.append(line)
        for y in self.y_lines:
            line = QgsFeature()
            line.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(self.x_min, y), QgsPointXY(self.x_max, y)]))
            features.append(line)
        lines_layer.addFeatures(features)
        lines_layer.commitChanges()
        self.layer = lines_layer

        self.set_render()   

class Mask(object):
    def __init__(self,geoxy) -> None:
        super().__init__()
        self.xy=geoxy
class RasterLayer(BasicLayer):
    
    def __init__(self, name=None, enable=False, path=None, view_mode=BasicLayer.BOATH_VIEW,style_info={'r':1,'g':2,'b':3,'NIR':0}):
        if name is None:
            name = os.path.splitext(os.path.basename(path))[0]
        super().__init__(name, enable, IconInstance().RASTER, path, BasicLayer.IN_FILE, view_mode)
        self.layer = QgsRasterLayer(self.path, self.name)
        self.style_info=style_info
        self.apply_style()
    def compare(self, other:'RasterLayer'):
        '''
        与其他图像比较，看是否处于同一投影,有无重叠区域,能否进行变化检测
        other:其它同类图层
        return:-1,无法进行比较;0,有重叠区域;1,完全重叠。
        '''
        ds1:gdal.Dataset = gdal.Open(self.path)
        ds2 :gdal.Dataset = gdal.Open(other.path)
        geo1=ds1.GetGeoTransform()
        geo2=ds2.GetGeoTransform()
        map1xy=[imageRC2geo(geo1,0,0),imageRC2geo(geo1,ds1.RasterXSize,ds1.RasterYSize)]
        map2xy=[imageRC2geo(geo2,0,0),imageRC2geo(geo2,ds2.RasterXSize,ds2.RasterYSize)]
        map1xx=[map1xy[0][0],map1xy[1][0]]
        map1yy=[map1xy[0][1],map1xy[1][1]]
        map2xx=[map2xy[0][0],map2xy[1][0]]
        map2yy=[map2xy[0][1],map2xy[1][1]]
        map1xx.sort()
        map1yy.sort()
        map2yy.sort()
        map2xx.sort()
        if ds1 is None or ds2 is None:
            Project().message_box.error('图层打开失败')
            return -1
        if not ds1.GetProjection()==ds2.GetProjection():
            Project().message_box.error('投影不一致')
            return -1
        elif (map1xx[0]>map2xx[1] or map1xx[1]<map2xx[0])or(map1yy[0]>map2yy[1] or map1yy[1]<map2yy[0] ):
            Project().message_box.error('图层无重叠区域')
            return -1
        elif ds1.RasterXSize == ds2.RasterXSize and ds1.RasterYSize == ds2.RasterYSize and geo1==geo2:
            # Project().message_box.error('两图一致')
            return 1
        #图层尺寸相同
        Project().message_box.warning('图层不完全重叠')
        del ds1
        del ds2
        return 0
    def overlap(self,other:'RasterLayer'):
        '''
        与其他图像比较，看是否处于同一投影,有无重叠区域,能否进行变化检测
        other:其它同类图层
        return:[重叠区域左上点xy,重叠区域右下点xy]
        '''
        ds1:gdal.Dataset = gdal.Open(self.path)
        ds2 :gdal.Dataset = gdal.Open(other.path)
        geo1=ds1.GetGeoTransform()
        geo2=ds2.GetGeoTransform()
        #地理（投影）坐标，y向下变小
        map1xy=[imageRC2geo(geo1,0,0),imageRC2geo(geo1,ds1.RasterXSize,ds1.RasterYSize)]
        map2xy=[imageRC2geo(geo2,0,0),imageRC2geo(geo2,ds2.RasterXSize,ds2.RasterYSize)]
        xx=[map1xy[0][0],map1xy[1][0],map2xy[0][0],map2xy[1][0]]
        yy=[map1xy[0][1],map1xy[1][1],map2xy[0][1],map2xy[1][1]]
        xx.sort()
        yy.sort()
        return [xx[1],yy[2],xx[2],yy[1]]
    @property
    def band(self):
        ds:gdal.Dataset =  gdal.Open(self.path)
        if ds is None:
            return None
        band = ds.RasterCount
        del ds
        return band
    @property
    def geo(self):
        ds =  gdal.Open(self.path)
        if ds is None:
            return None
        geo = ds.GetGeoTransform()
        del ds
        return geo

    @property
    def proj(self):
        ds =  gdal.Open(self.path)
        if ds is None:
            return None
        proj = ds.GetProjection()
        del ds
        return proj
    
    @property
    def size(self):
        ds =  gdal.Open(self.path)
        if ds is None:
            return None
        s = (ds.RasterXSize, ds.RasterYSize)
        del ds
        return s
    def apply_style(self):
        pass
    
    @property
    def bandinfo(self):
        ds :gdal.Dataset=  gdal.Open(self.path)
        bands=ds.RasterCount
        bandinfo_={}
        for i in range(1,bands+1) :
            min,max,mean,stdev=ds.GetRasterBand(i).ComputeStatistics(True)
            bandinfo_['波段{}'.format(i)]=['最小值：{}'.format(min),'最大值：{}'.format(max),'均值：{}'.format(mean),'方差：{}'.format(stdev)]
        ds=None
        return bandinfo_

    def set_stlye(self,style_info):
        self.style_info=style_info
        self.apply_style()

    @property
    def info(self):
        #基础属性
        basic={}
        basic['文件名']=self.path

        basic['文件大小']="{} Mb".format(os.path.getsize(self.path)//(1024*1024))
        basic['波段信息']=self.bandinfo
        #渲染属性
        render=self.style_info

        mapinfo={
            '基础属性':basic,
            '渲染属性':render,
            'prewmap':self.preview
        }
        return mapinfo

    def previewAsPixmapo(self,width,height=None):
        w=self.layer.width()
        h=self.layer.height()
        if height:
            return QPixmap.fromImage(self.layer.previewAsImage(QSize(width,height)))
        return QPixmap.fromImage(self.layer.previewAsImage(QSize(width,int(width*h/w))))
    @property
    def preview(self,width=400):
        w=self.layer.width()
        h=self.layer.height()
        return self.layer.previewAsImage(QSize(width,int(width*h/w)))

class MultiBandRasterLayer(RasterLayer):

    def apply_style(self):
        renderer=QgsMultiBandColorRenderer(self.layer.dataProvider(),self.style_info['r'],self.style_info['g'],self.style_info['b'])
        self.layer.setRenderer(renderer)
        self.layer.triggerRepaint()
    def toArray(self,mask=None,band:list=None):
        ds:gdal.Dataset=gdal.Open(self.path)
        res=None
        startx=0
        starty=0
        xsize=ds.RasterXSize
        ysize=ds.RasterYSize
        if mask:
            #转为图像坐标
            startx,starty=geo2imageRC(self.geo,mask[0],mask[1])
            x2,y2=geo2imageRC(self.geo,mask[2],mask[3])
            xsize=x2-startx
            ysize=y2-starty
        res=ds.ReadAsArray(startx,starty,xsize,ysize,band_list=band)
        del ds
        return res
    def readAsArray(self,xoff: int = 0, yoff: int = 0, xsize= None, ysize = None, buf_obj= None, buf_xsize= None, buf_ysize = None, buf_type= None, callback = None, callback_data = None, interleave = 'band', band_list = None):
        ds:gdal.Dataset = gdal.Open(self.path)
        array=ds.ReadAsArray(xoff= 0, yoff= 0, xsize= None, ysize = None, buf_obj= None, buf_xsize= None, buf_ysize = None, buf_type= None, callback = None, callback_data = None, interleave= 'band', band_list = None)
        return array
class SingleBandRasterLayer(RasterLayer):
    
    def apply_style(self):
        pass
class VectorLayer(BasicLayer):
    pass


class ResultPointLayer(BasicLayer):

    def __init__(self, path, name=None, enable = False, proj = None, geo = None,result_path={},dsort=False):
        if name is None:
            name = os.path.splitext(os.path.basename(path))[0]
        super().__init__(name, enable, icon=IconInstance().VECTOR, path=path, path_mode = BasicLayer.IN_FILE, view_mode=BasicLayer.BOATH_VIEW )
        self.data = None
        self.wkt = proj
        self.geo = geo
        self.dsort=dsort
        self.result_path:dict=result_path
        # self.methods=
        self.load_point_file()
    
    def save(self):
       
        with open(self.path, 'w') as f:
            f.write('x,y,diff,status\n')
            for i in range(len(self.data)):
                f.write('{},{},{},{}\n'.format(self.data[i][0], self.data[i][1], self.data[i][2], int(self.data[i][3])))


    def update(self, data):
        row = data['row']
        value = data['value']
        self.data[row][-1] = int(value)
        self.update_point_layer(row)
    
    def format_point_layer(self, layer):
        layer.setLabelsEnabled(True)
        lyr = QgsPalLayerSettings()
        lyr.enabled = True
        lyr.fieldName = 'prob'
        lyr.placement = QgsPalLayerSettings.OverPoint
        
        lyr.textFont = QFont('Times New Roman', 100)
        text_format =  QgsTextFormat()
        text_format.setFont(lyr.textFont)
        if self.geo is None:
            res = 1
        else:
            res = self.geo[1]
        # lyr.xOffset = 25 * res
        # lyr.yOffset = -2 * res
        text_format.setSize(50 * res)
        text_format.setSizeUnit(QgsUnitTypes.RenderMapUnits)
        text_format.setColor(QColor('#FF0000'))
        # text_format.background().color = QColor('#000000')
        text_format.buffer().setEnabled(True)
        text_format.buffer().setSize(1)
        text_format.buffer().setOpacity(1)
        lyr.setFormat(text_format)
        root = QgsRuleBasedLabeling.Rule(QgsPalLayerSettings())
        rule = QgsRuleBasedLabeling.Rule(lyr)
        rule.setDescription('label')
        root.appendChild(rule)
        #Apply label configuration
        rules = QgsRuleBasedLabeling(root)
        layer.setLabeling(rules)

    def set_render(self, layer):
        # xres = self.geo[1]
        symbol_change = QgsMarkerSymbol.createSimple({'color': '#ffff00', 'size':  2 })
        symbol_change.setSizeUnit(QgsUnitTypes.RenderUnit.RenderMillimeters)
        category_change = QgsRendererCategory(1, symbol_change,'change')

        symbol_unchange = QgsMarkerSymbol.createSimple({'color': '#00000000', 'size': 0})
        
        category_unchange = QgsRendererCategory(0, symbol_unchange, 'unchange')
        render = QgsCategorizedSymbolRenderer('status', [category_change, category_unchange])
        layer.setRenderer(render)

    def load_point_file(self):
        data = np.loadtxt(self.path, delimiter=',', skiprows=1)
        if data is None:
            return
        if self.dsort:
            data=data[data[:,-2].argsort()]
        else:
            data=data[(-data[:,-2]).argsort()]
        self.data = data
        self.make_point_layer()
    
    def make_point_layer(self):
        if self.wkt is not None:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromString('WKT:{}'.format(self.wkt))
        else:
            crs = QgsCoordinateReferenceSystem()
        
        uri = 'Point?crs={}&field=status:integer&field=prob:string'.format(crs.toProj())
        layer = QgsVectorLayer(uri, self.name, "memory")
        if not layer.isValid():
            Project().message_box.error('Failed to create layer')
            return
        self.format_point_layer(layer)
        layer.startEditing()
        features = []
        # status_index = 
        for i, d in enumerate(self.data):
            point = QgsFeature(layer.fields())
            point.setId(i)
            point.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(d[0], d[1])))
            point.setAttribute('status', int(d[-1]))
            if d[-1] == 0:
                point.setAttribute('prob', '')
            else:
                point.setAttribute('prob', '%.2f%%'%(d[2]))
            # point.setAttribute('id', i)
            features.append(point)
        layer.addFeatures(features)
        self.set_render(layer)
        layer.commitChanges()
  
        self.layer = layer

    def update_point_layer(self, row = 0):
        if self.layer is None:
            return
        self.layer.startEditing()
        if row < 0:
            for i, d in enumerate(self.data):
                feature = self.layer.getFeature(i+1)
                if feature is None:
                    continue
                feature.setAttribute('status', int(d[-1]))  
                if d[-1] == 0:
                    feature.setAttribute('prob', '')
                else:
                    feature.setAttribute('prob', '%.2f%%'%(d[2]))
                self.layer.updateFeature(feature)
        else:
            feature = self.layer.getFeature(row+1)
            # print(feature)
            if feature is None:
                return
            feature.setAttribute('status', int(self.data[row][-1]))
            if self.data[row][-1] == 0:
                feature.setAttribute('prob', '')
            else:
                feature.setAttribute('prob', '%.2f%%'%(self.data[row][2]))
            self.layer.updateFeature(feature)
        self.layer.commitChanges()
        Project().result_table.show_result(self)


    def get_actions(self):
        actions = super().get_actions()
        show_in_table = QAction(IconInstance().TABLE, '显示在表格中')
        actions.insert(0, show_in_table)

        def show_to_table():
            Project().result_table.show_result(self)
        
        show_in_table.triggered.connect(show_to_table)

        return actions
    # def load_file(self, path):
    
    @property
    def info(self):
        #基础属性
        basic={}
        basic['文件路径']=self.path

        #中间算法信息：
        methods={ k:v[0]  for k ,v in self.result_path.items()}
        basic['变化检测算法']=methods
        #渲染信息
        render={}
        render['标注字体大小']=2
        render['标注颜色']='#ffff00'
        render['阈值']=self.result_path['后处理'][1]

        return {'基础属性':basic,'渲染属性':render}
class PairLayer(BasicLayer):
    
    def __init__(self, pth1, pth2,style_info1,style_info2,mask=None) -> None:
        
        self.layers:List[BasicLayer] = []
        self.id = str(uuid.uuid1())
        self.checked = False
        self.main_l1 = MultiBandRasterLayer(path = pth1, enable=True, view_mode=BasicLayer.LEFT_VIEW,style_info=style_info1)
        self.main_l2 = MultiBandRasterLayer(path = pth2, enable=True, view_mode=BasicLayer.RIGHT_VIEW,style_info=style_info2)
        self.main_l1.set_layer_parent(self)
        self.main_l2.set_layer_parent(self)
        self.grid = None
        self.cell_size = Project().cell_size
        name = os.path.basename(pth1)[:4] + '-' + os.path.basename(pth2)[:4]
        self.mask=mask
        # self.layer_update.connect(Project().layer_updated)

        super().__init__(name, True, IconInstance().DOCUMENT)
        self.layer = self.main_l1.layer
        if self.check():
            self.layers.append(self.main_l1)
            self.layers.append(self.main_l2)
            
            # self.layers.append(self.grid)
    @property
    def l1_geo(self):
        return self.main_l1.geo
    @property
    def l2_geo(self):
        return self.main_l2.geo
    
    def check(self):
        if self.checked:
            return self.checked
        self.checked = self.main_l1.compare(self.main_l2)
        if not self.checked==-1:#重叠
            self.mask=Mask(self.main_l1.overlap(self.main_l2))
            x1,y1=geo2imageRC(self.l1_geo,*self.mask.xy[0:2])
            x2,y2=geo2imageRC(self.l1_geo,*self.mask.xy[2:])
            self.size=[x2-x1,y2-y1]
            self.geo = self.main_l1.geo
            self.proj = self.main_l1.proj
            gridgeo=[self.mask.xy[0],self.l1_geo[1],self.l1_geo[2],self.mask.xy[1],self.l1_geo[4],self.l1_geo[5]]
            self.grid = GridLayer(self.proj, gridgeo , self.size[0], self.size[1], cell_size=Project().cell_size)
            self.grid.set_layer_parent(self)
        return self.checked!=-1

    def add_result_layer(self, result):
        result.set_layer_parent(self)
        self.layers.insert(0, result)
        self.layer_show_update.emit()
        self.layer_tree_update.emit()

    def has_layer(self, layer):
        for ilayer in self.layers:
            if ilayer is layer:
                return True
        return False
    
    def remove_layer(self, layer):
        idx = -1
        for ilayer in self.layers:
            idx += 1
            if ilayer is layer:
                break
        if idx >=  len(self.layers):
            return
        
        if layer is self.grid or layer is self.main_l1 or layer is self.main_l2:
            return
        
        self.layers.pop(idx)
        del layer

    def to_dict(self):
        data=dict(
            name=self.name,
            enable=self.enable,
            pth1=self.main_l1.path,
            pth2=self.main_l2.path,
            style_info1=self.main_l1.style_info,
            style_info2=self.main_l2.style_info,
            layers=[to_dict(l)  for l in self.layers if not (l is self.grid or l is self.main_l1 or l is self.main_l2) ],
            
        )
        return data


    @property
    def info(self):

        ds= gdal.Open(self.main_l1.path)
        srs= osr.SpatialReference(ds.GetProjectionRef())
        metadata={}
        # 空间参考系统
        metadata['proj4'] = srs.ExportToProj4()
        metadata['wkt'] = srs.ExportToWkt()
		# 地理坐标系
        metadata['geocs'] = srs.GetAttrValue('GEOGCS')
        metadata['uom'] = srs.GetAttrValue('UNIT')
		# 投影坐标系
        metadata['projcs'] = srs.GetAttrValue('PROJCS')  # if projected
        metadata['epsg'] = srs.GetAuthorityCode(None)
        ds=None

        #格网信息
        gridData={}
        gridData['格网大小']='{}像素'.format(self.grid.cell_size)
        gridData['格网线']=['宽度：1像素', '颜色：白色']

        #公共掩模
        maskData={}
        if self.mask:
            maskData['左上角坐标']=self.mask.xy[0:2]
            maskData['右下角坐标']=self.mask.xy[2:]

        mapinfo={
        '坐标系':metadata,
        '格网':gridData,
        '公共掩膜':maskData
        }
        
        return mapinfo


    @staticmethod
    def from_dict(data):
        player = PairLayer(data['pth1'], data['pth2'], data['style_info1'], data['style_info2'])
        player.name = data['name']
        for layer in data['layers']:
            l = from_dict(layer)
            l.set_layer_parent(player)
            player.layers.insert(0,l)
        return player