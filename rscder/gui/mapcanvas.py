
# from alg.utils import random_color
# from mul.mulgrubcut import GrabCut
import multiprocessing
# from alg.grubcut import grubcut
# from gui.layerselect import LayerSelect
# from gui.default import get_default_category_colors, get_default_category_keys
# from os import truncate
from pathlib import Path
from PyQt5.QtCore import QSettings, QUrl, pyqtSignal, Qt, QVariant
from PyQt5.QtWidgets import QMessageBox, QWidget, QHBoxLayout
from PyQt5.QtGui import QColor, QDragEnterEvent, QDropEvent

from qgis.core import QgsPointXY, QgsRasterLayer, QgsVectorLayer, QgsFeature, QgsGeometry, QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsFillSymbol, QgsPalLayerSettings, QgsRuleBasedLabeling, QgsTextFormat
from qgis.gui import QgsMapCanvas, QgsMapToolPan, QgsMapToolZoom
from qgis.core import QgsRectangle, QgsVectorFileWriter, QgsProject, QgsField, QgsRasterFileWriter, QgsRasterPipe
import threading
import tempfile
import cv2
import os

from rscder.utils.project import PairLayer, Project

class DoubleCanvas(QWidget):
    corr_changed = pyqtSignal(str)
    scale_changed = pyqtSignal(str)

    def __init__(self, parent = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(False)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.mapcanva1 = CanvasWidget(self)
        self.mapcanva2 = CanvasWidget(self)
        self.mapcanva1.setCanvasColor(QColor(255, 255, 255))
        self.mapcanva2.setCanvasColor(QColor(255, 255, 255))
        
        self.mapcanva1.update_coordinates_text.connect(self.corr_changed)
        self.mapcanva2.update_coordinates_text.connect(self.corr_changed)

        def set_map1_extent():
            if self.mapcanva2.is_main:
                self.mapcanva1.set_extent(self.mapcanva2.extent())
        def set_map2_extent():
            if self.mapcanva1.is_main:
                self.mapcanva2.set_extent(self.mapcanva1.extent())

        self.mapcanva1.extentsChanged.connect(set_map2_extent)
        self.mapcanva2.extentsChanged.connect(set_map1_extent)

        self.set_pan_tool(True)

        self.mapcanva1.update_scale_text.connect(self.scale_changed)
        self.mapcanva2.update_scale_text.connect(self.scale_changed)
        
        layout = QHBoxLayout(self)
        layout.addWidget(self.mapcanva1)
        layout.addWidget(self.mapcanva2)
        
        self.setLayout(layout)
        self.grid_show = True

    def connect_grid_show(self, action):
        def show_grid(_):
            
            self.grid_show = not self.grid_show
            action.setChecked(self.grid_show)
            if self.grid_show:
                for layer in Project().layers.values():
                    self.mapcanva1.add_grid_layer(layer.grid_layer.grid_layer)
                    self.mapcanva2.add_grid_layer(layer.grid_layer.grid_layer)
            else:
                self.mapcanva1.remove_grid_layer()
                self.mapcanva2.remove_grid_layer()

        action.triggered.connect(show_grid)


    def connect_map_tool(self, pan, zoom_in, zoom_out):
        pan.triggered.connect(self.set_pan_tool)
        zoom_in.triggered.connect(self.set_zoom_in)
        zoom_out.triggered.connect( self.set_zoom_out)

    def set_pan_tool(self, s):
        print('set pan tool')
        if s:
            self.mapcanva1.setMapTool(QgsMapToolPan(self.mapcanva1))
            self.mapcanva2.setMapTool(QgsMapToolPan(self.mapcanva2))

    def set_zoom_in(self, s):
        print('set zoom in')
        if s:
            self.mapcanva1.setMapTool(QgsMapToolZoom(self.mapcanva1, False))
            self.mapcanva2.setMapTool(QgsMapToolZoom(self.mapcanva2, False))

    def set_zoom_out(self, s):
        print('set zoom out')
        if s:
            self.mapcanva1.setMapTool(QgsMapToolZoom(self.mapcanva1, True))
            self.mapcanva2.setMapTool(QgsMapToolZoom(self.mapcanva2, True))

    def add_layer(self, layer:str):
        layer = Project().layers[layer]
        if  not self.mapcanva1.is_main and not self.mapcanva2.is_main:
            self.mapcanva1.is_main = True
        self.mapcanva1.add_layer(layer.l1)
        self.mapcanva2.add_layer(layer.l2)
        if self.grid_show:
            self.mapcanva1.add_grid_layer(layer.grid_layer.grid_layer)
            self.mapcanva2.add_grid_layer(layer.grid_layer.grid_layer)
        
    
    def clear(self):
        self.mapcanva1.clear()
        self.mapcanva2.clear()

class CanvasWidget(QgsMapCanvas):
    update_coordinates_text = pyqtSignal(str)
    update_scale_text = pyqtSignal(str)

    def add_layer(self, layer) -> None:
        self.layers.insert(0, layer)
        self.setLayers(self.layers)
        self.zoomToFeatureExtent(layer.extent())

    def add_grid_layer(self, layer):
        self.grid_layers.append(layer)
        self.layers.insert(0, layer)
        self.setLayers(self.layers)

    def remove_grid_layer(self):
        layers = []
        for layer in self.layers:
            if layer in self.grid_layers:
                continue
            layers.append(layer)
        self.layers = layers
        self.setLayers(self.layers)

    def enterEvent(self,e):
        self.is_main = True
        # print(e)
        pass

    def leaveEvent(self, e):
        self.is_main = False
        pass

    def set_extent(self, extent:QgsRectangle):
        '''
        Zoom to extent
        '''
        # print(extent)
        if self.is_main:
            return
        else:
            self.zoomToFeatureExtent(extent)

    def clear(self) -> None:
        self.setTheme('')
        self.layers = []
        self.is_main = False
        self.setLayers([])
        self.clearCache()
        self.refresh()

    def __init__(self, parent):
        super().__init__(parent)        
        self.layers = []
        self.grid_layers = []
        self.is_main = False
        self.setCanvasColor(Qt.white)
        self.enableAntiAliasing(True)
        self.setAcceptDrops(False)

        # coordinates updated
        def coordinates2text(pt:QgsPointXY):
            return self.update_coordinates_text.emit("X: {:.5f}, Y: {:.5f}".format(pt.x(), pt.y()))
        self.xyCoordinates.connect(coordinates2text)
        self.scaleChanged.connect(lambda _ : self.update_scale_text.emit("1 : {:.3f}".format(self.scale())))

        self.total_f = 0
        self.start_extract = False
        self.label_pal = None
        # self.result_layers = []

    def dragEnterEvent(self, e:QDragEnterEvent) -> None:
        '''
        Can drag
        '''
        candidates = [".tif", ".tiff", ".jpg", ".jpeg", ".bmp", ".png"]
        
        if e.mimeData().hasUrls():
            if Path(e.mimeData().urls()[0].toLocalFile()).suffix in candidates:
                e.accept()
                return

        e.ignore()

    def dropEvent(self, e:QDropEvent) -> None:
        '''
        Drop image to the canvas
        '''
        url_path = e.mimeData().urls()[0]
        image_path = QUrl(url_path).toLocalFile()
        self.load_image(image_path)

    def load_image(self, path) -> None:
        if not Path(path).exists():
            return

        raster_layer = QgsRasterLayer(path, Path(path).name)
        if not raster_layer.isValid():
            print("栅格图层加载失败！")
        raster_layer.file_path = path
        
        # self.layers.insert(0, raster_layer)
        # self.layers.insert(0, vector_layer)
        # if self.current_raster_layer:
        #     del self.current_raster_layer
        # if self.current_vector_layer:
        #     del self.current_vector_layer
        
        QgsProject.instance().addMapLayer(raster_layer)
        self.current_raster_layer = raster_layer
        # self.current_vector_layer = vector_layer
        self.setExtent(raster_layer.extent())
        # self.setLayers([vector_layer, raster_layer])
        self.zoomToFeatureExtent(raster_layer.extent())
        self.have_current_image.emit(True)

    def load_result_from_txt(self, path) -> None:
        if not Path(path).exists():
            return    
        # vector_layer = QgsVectorLayer("Polygon?field=category:string(20)&field=confidence:double", Path(path).name, "memory")
        vector_layer = QgsVectorLayer("Polygon?field=category:string(20)&field=confidence:double&field=renderkey:string(32)&field=isman:boolean&field=isauto:boolean&field=label:string(64)", Path(path).name + ' outline', "memory")
        
        if not vector_layer.isValid():
            print("矢量图层加载失败！")        
        vector_layer.setLabelsEnabled(True)
        lyr = QgsPalLayerSettings()
        lyr.enabled = True
        lyr.fieldName = 'label'  # default in data sources
        # lyr.textFont = self._TestFont
        lyr.textNamedStyle = 'Medium'
        text_format =  QgsTextFormat()
        text_format.color = QColor('#ffffff')
        text_format.background().color = QColor('#000000')
        text_format.buffer().setEnabled(True)
        text_format.buffer().setSize(1)
        text_format.buffer().setOpacity(0.5)
        lyr.setFormat(text_format)
        self.label_pal = lyr
        root = QgsRuleBasedLabeling.Rule(QgsPalLayerSettings())
        rule = QgsRuleBasedLabeling.Rule(lyr)
        rule.setDescription('label')
        root.appendChild(rule)
        #Apply label configuration
        rules = QgsRuleBasedLabeling(root)
        vector_layer.setLabeling(rules)
        vector_layer.triggerRepaint()
        # lyr.writeToLayer(vector_layer)
        vector_layer.setRenderer(self.__get_categorical_renderer("renderkey"))
        QgsProject.instance().addMapLayer(vector_layer)
        self.current_vector_layer = vector_layer
        # provider = self.current_vector_layer.dataProvider()
        # provider.truncate()
        self.current_vector_layer.startEditing()
        # objects = []
        features = []
        with open(path) as f:
            for line in f.readlines():                
                item_data = line.split("\n")[0].split(" ")
                if len(item_data) == 1 + 4 * 2:
                    cls_name = item_data[0]
                    item_data[2] = -1.0 * float(item_data[2])
                    item_data[4] = -1.0 * float(item_data[4])
                    item_data[6] = -1.0 * float(item_data[6])
                    item_data[8] = -1.0 * float(item_data[8])
                    wkt = "POLYGON (({} {}, {} {}, {} {}, {} {}))".format(*item_data[1:])
                    conf = 1.0
                else:
                    cls_name = item_data[8]
                    # print(cls_name)
                    # print(cls_name[0])
                    # print(cls_name[0].isalpha())
                    if cls_name[0].isalpha():
                        item_data[1] = -1.0 * float(item_data[1])
                        item_data[3] = -1.0 * float(item_data[3])
                        item_data[5] = -1.0 * float(item_data[5])
                        item_data[7] = -1.0 * float(item_data[7])
                        conf = 1.0
                        wkt = "POLYGON (({} {}, {} {}, {} {}, {} {}))".format(*item_data[:8])
                    else:
                        cls_name = item_data[0]
                        conf = float(item_data[1])
                        item_data[3] = -1.0 * float(item_data[3])
                        item_data[5] = -1.0 * float(item_data[5])
                        item_data[7] = -1.0 * float(item_data[7])
                        item_data[9] = -1.0 * float(item_data[9])
                        wkt = "POLYGON (({} {}, {} {}, {} {}, {} {}))".format(*item_data[2:])
                    
                feat = QgsFeature(self.current_vector_layer.fields())
                feat.setGeometry(QgsGeometry.fromWkt(wkt))
                feat.setAttribute('category', cls_name)
                feat.setAttribute('confidence', conf)
                feat.setAttribute('renderkey', cls_name)
                feat.setAttribute('isman', False)
                feat.setAttribute('isauto', True)
                feat.setAttribute('label', f'{ cls_name},{conf:.3f}')
                features.append(feat)
                # objects.append({
                #     "category": item_data[0],
                #     "confidence": item_data[1],
                #     "fid": feat.id()
                # })
        self.current_vector_layer.addFeatures(features)
        self.current_vector_layer.commitChanges()
        self.have_current_vector.emit(True)
        self.layer_update()

    def clear_vector(self):
        if self.current_vector_layer is not None:
            provider = self.current_vector_layer.dataProvider()
            provider.truncate()
            self.layer_update()

    def change_current_vector_layer(self, vector_layer):
        if self.current_vector_layer is not None:
            self.current_vector_layer.removeSelection()
        self.current_vector_layer = vector_layer
        
        self.layer_update()

    def layer_update(self):
        if self.current_vector_layer is None:
            self.object_updated.emit([])
            return
        self.current_vector_layer.updateExtents()      
        self.refresh()
        objects = []
        for feature in self.current_vector_layer.getFeatures():
            objects.append({
                    "category": feature['category'],
                    "confidence": feature['confidence'],
                    "renderkey": feature['renderkey'],
                    'isman': feature['isman'],
                    'isauto': feature['isauto'],
                    "fid": feature.id()
                })
        self.object_updated.emit(objects)
    
    def selectd_changed(self, items:list):
        if len(items) == 0:
            self.current_vector_layer.removeSelection()
        else:
            self.current_vector_layer.selectByIds(list(item['fid'] for item in items))

    def item_change(self, items:list):
        self.current_vector_layer.startEditing()
        features = list(self.current_vector_layer.getFeatures())
        for f in features:
            has_f = False
            for item in items:
                if f.id() == item['fid']:
                    # f = QgsFeature(f)
                    has_f = True
                    f.setAttribute('category', item['category'])
                    f.setAttribute('confidence', item['confidence'])
                    f.setAttribute('renderkey', item['renderkey'])
                    f.setAttribute('isman',  item['isman'])
                    f.setAttribute('isauto',  item['isauto'])
                    self.current_vector_layer.updateFeature(f)
                    break
            if has_f:
                continue
            
            self.current_vector_layer.deleteFeature(f.id())

        self.current_vector_layer.commitChanges()
        self.current_vector_layer.updateExtents()  
        # print(self.current_vector_layer.fields())

        self.refresh()
    
    def zoom_to_full_extent(self) -> None:
        if self.current_raster_layer:
            self.zoomToFeatureExtent(self.current_raster_layer.extent())

    def __get_categorical_renderer(self, fieldname:str) -> QgsCategorizedSymbolRenderer:
        settings = QSettings(self)
        
        category_keys = settings.value("keys", get_default_category_keys())
        category_colors = settings.value("colors", get_default_category_colors())
        
        settings.beginGroup("Category")
        if len(category_colors) < len(category_keys):
            for _ in range(len(category_keys) -  len(category_colors)):
                category_colors.append(random_color())
            settings.setValue('colors', category_colors)
        settings.endGroup()
        categorized_renderer = QgsCategorizedSymbolRenderer()
        for key, color in zip(category_keys, category_colors):
            fill_color = QColor(color)
            fill_color.setAlphaF(0.3)
            categorized_renderer.addCategory(\
                QgsRendererCategory(
                        key, 
                        QgsFillSymbol.createSimple(
                            {"color":fill_color.name(QColor.HexArgb),"outline_color":color, "outline_width":"1"}), ''))
        categorized_renderer.setClassAttribute(fieldname)
        return categorized_renderer

    def export_to_raster(self, path) -> None:
        if self.current_vector_layer is None:
            return
    
    def load_extract_result(self, res):
        r = self.current_raster_layer
        vector_layer = QgsVectorLayer("Polygon?field=category:string(20)&field=confidence:double&field=renderkey:string(32)&field=isman:boolean&field=isauto:boolean", Path(r.file_path).name + ' outline', "memory")
        # vector_layer = QgsVectorLayer(tempfile)
        if not vector_layer.isValid():
            print("矢量图层加载失败！")        

        vector_layer.setRenderer(self.__get_categorical_renderer("renderkey"))
        lyr = QgsPalLayerSettings()
        lyr.enabled = True
        lyr.fieldName = 'label'  # default in data sources
        # lyr.textFont = self._TestFont
        lyr.textNamedStyle = 'Medium'
        text_format =  QgsTextFormat()
        text_format.color = QColor('#ffffff')
        text_format.background().color = QColor('#000000')
        text_format.buffer().setEnabled(True)
        text_format.buffer().setSize(1)
        text_format.buffer().setOpacity(0.5)
        lyr.setFormat(text_format)
        self.label_pal = lyr
        root = QgsRuleBasedLabeling.Rule(QgsPalLayerSettings())
        rule = QgsRuleBasedLabeling.Rule(lyr)
        rule.setDescription('label')
        root.appendChild(rule)
        #Apply label configuration
        rules = QgsRuleBasedLabeling(root)
        vector_layer.setLabeling(rules)
        vector_layer.triggerRepaint()
        vector_layer.startEditing()
        features = []
        for f in res:
            pts = f[0]
            prop = f[1]
            # pts = grubcut(img_path, pts, False, True, False )
            pts = list(  f'{p[0]} {p[1]}' for p in pts )
            wkt = f'POLYGON (( {",".join(pts)} ))'
            # geometry = QgsGeometry.fromWkt(wkt)
            feat = QgsFeature(vector_layer.fields())
            feat.setGeometry(QgsGeometry.fromWkt(wkt))
            feat.setAttribute('category', prop['category'])
            feat.setAttribute('confidence', prop['confidence'])
            feat.setAttribute('renderkey',  prop['category'])
            feat.setAttribute('isman',  False)
            feat.setAttribute('isauto',  True)
            features.append(feat)
        
        vector_layer.addFeatures(features)
        vector_layer.commitChanges()
        QgsProject.instance().addMapLayer(vector_layer)
        self.process_end.emit()
        r.has_extract = True
        self.start_extract = False
        r.extract_layer = vector_layer
        self.layer_update()
        
    def run_thread(self, conn, pp):
        all_ok = False
        # print(pp.is_alive)
        while pp.is_alive:
            r = conn.recv()
            # print(r)
            if all_ok:
                self.extract_end.emit(r)
                break
            if int(r) == self.total_f - 1:
                all_ok = True
            self.process_update.emit(r)
            # print(conn.recv())
    def grubcut(self, v, r):
        # for f in v.getFeatures():
        if self.start_extract:
            return
        self.current_raster_layer = r
        img_path = r.file_path
        if getattr(r, 'has_extract', False):
            vector_layer = r.extract_layer
            try:
                QgsProject.instance().removeMapLayer(vector_layer)
            except:
                pass

        # self.current_vector_layer = vector_layer
        features = []
        points = []
        for f in v.getFeatures():
            pts =  f.geometry().vertices()
            pts = list([ vr.x(), vr.y() ] for vr in pts)
            points.append(pts)
            features.append({
                'category': f['category'],
                'confidence': f['confidence']
            })
        self.total_f = len(points)
        self.start_extract = True
        self.process_start.emit([0, self.total_f])
        parent_conn, child_conn = multiprocessing.Pipe()
        t = GrabCut(child_conn, img_path, points, features)
        p = threading.Thread(target=self.run_thread, args=(parent_conn,t))
        t.start()
        p.start()
    
    def export_to(self, path, filter_name) -> None:
        if filter_name == 'Shp (*.shp)':
            if self.current_vector_layer is None:
                return
            ls = LayerSelect(self)
            ls.show()
            ls.exec()
            if ls.result() == LayerSelect.OK:
                save_options = QgsVectorFileWriter.SaveVectorOptions()
                save_options.driverName = "ESRI Shapefile"
                save_options.fileEncoding = "UTF-8"
                transform_context = QgsProject.instance().transformContext()
                error = QgsVectorFileWriter.writeAsVectorFormatV2(ls.value,
                                                                path,
                                                                transform_context,
                                                                save_options)
                if error[0] == QgsVectorFileWriter.NoError:
                    print("又成功了！")
                else:
                    print(error)

        if filter_name == 'JPEG Images(*.jpg)':
            file_name = path + '.tif'
            extent = self.current_raster_layer.extent()
            width, height = self.current_raster_layer.width(), self.current_raster_layer.height()
     
            pipe = QgsRasterPipe()
            provider = self.current_raster_layer.dataProvider()
            pipe.set(provider.clone())
            
            file_writer = QgsRasterFileWriter(file_name)
            error = file_writer.writeRaster(pipe,
                                    width,
                                    height,
                                    extent,
                                    self.current_raster_layer.crs())
        
            target_img = cv2.imread(file_name)
            jpg_file_name = path + '.jpg'
            cv2.imwrite(jpg_file_name, target_img)
            os.remove(file_name)
            if error == QgsRasterFileWriter.NoError:
                QMessageBox.about(self, 'Export Files', '导出JPEG图像成功！')
            else:
                QMessageBox.about(self, 'Export Files', '导出JPEG图像失败！')

        if filter_name == 'TIFF Images(*.tif)':
            file_name = path + '.tif'
            extent = self.current_raster_layer.extent()
            width, height = self.current_raster_layer.width(), self.current_raster_layer.height()
     
            pipe = QgsRasterPipe()
            provider = self.current_raster_layer.dataProvider()
            pipe.set(provider.clone())
            
            file_writer = QgsRasterFileWriter(file_name)
            error = file_writer.writeRaster(pipe,
                                    width,
                                    height,
                                    extent,
                                    self.current_raster_layer.crs())
            if error == QgsRasterFileWriter.NoError:
                QMessageBox.about(self, 'Export Files', '导出TIFF图像成功！')
            else:
                QMessageBox.about(self, 'Export Files', '导出TIFF图像失败！')
        if filter_name == 'PNG Images(*.png)':
            file_name = path + '.tif'
            extent = self.current_raster_layer.extent()
            width, height = self.current_raster_layer.width(), self.current_raster_layer.height()
     
            pipe = QgsRasterPipe()
            provider = self.current_raster_layer.dataProvider()
            pipe.set(provider.clone())
            
            file_writer = QgsRasterFileWriter(file_name)
            error = file_writer.writeRaster(pipe,
                                    width,
                                    height,
                                    extent,
                                    self.current_raster_layer.crs())
            target_img = cv2.imread(file_name)
            jpg_file_name = path + '.png'
            cv2.imwrite(jpg_file_name, target_img)
            os.remove(file_name)
            if error == QgsRasterFileWriter.NoError:
                QMessageBox.about(self, 'Export Files', '导出PNG图像成功！')
            else:
                QMessageBox.about(self, 'Export Files', '导出PNG图像失败！')