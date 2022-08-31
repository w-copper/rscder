from colorsys import hls_to_rgb
import os
from turtle import width
from osgeo import gdal
from PyQt5.QtWidgets import  QWidget, QApplication, QMainWindow, QToolBox
from PyQt5.QtWidgets import QDialog, QFileDialog, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox,QSpacerItem,QDialogButtonBox
from PyQt5.QtCore import Qt, QSize,QSettings,pyqtSignal,QThread
from PyQt5.QtGui import QIcon,QColor,QPalette,QPixmap
from PyQt5 import QtGui
from threading import Thread
from rscder.utils.icons import IconInstance
from rscder.utils.setting import Settings
from qgis.gui import QgsMapCanvas
from rscder.utils.project import MultiBandRasterLayer, Project, RasterLayer
from rscder.gui.progress_bar import MetroCircleProgress

class progressDialog(QDialog):
    def __init__(self, parent=None,name='default') -> None:
        super(progressDialog,self).__init__(parent)
        self.setWindowTitle(name)
        self.setWindowIcon(IconInstance().RASTER)
        self.setFixedSize(300,80)
        # self.setWindowIcon(IconInstance().RASTER)
        tlayout=QVBoxLayout()
        tlayout.setContentsMargins(10,0,0,0)
        hlayout=QHBoxLayout()
        h2layout=QHBoxLayout()
        self.label=QLabel('加载影像...')
        hlayout.addWidget(self.label)
        hlayout.addItem(QSpacerItem(30,0))
        tlayout.addLayout(hlayout)
        h2layout.addWidget(MetroCircleProgress(self, radius=7))
        tlayout.addLayout(h2layout)
        self.setLayout(tlayout)
    def setlabel(self,content:str):
        self.label.setText(content)

class loader(QDialog):
    signal1=pyqtSignal(str)
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.left_layer=None
        self.right_layer=None
        self.setWindowTitle('载入数据')
        self.setWindowIcon(IconInstance().DATA_LOAD)
        self.pyramid:bool=False
        self.temp1=''
        self.temp2=''
        self.path1=''
        self.path2=''
        self.bands=['red:','green:','blue:','NIR:']
        self.bandsorder=[1,2,3,4]
        
        self.left_map=QLabel()
        self.left_map.setFixedSize(200,200)
        self.left_map.setAutoFillBackground(True)
        self.left_map.setBackgroundRole(QPalette.Dark)

        self.right_map=QLabel()
        self.right_map.setFixedSize(200,200)
        self.right_map.setAutoFillBackground(True)
        self.right_map.setBackgroundRole(QPalette.Dark)
        maplayout=QHBoxLayout()
        maplayout.addWidget(self.left_map)
        maplayout.addWidget(self.right_map)

        path1_label = QLabel('时相1影像:')
        path1_label.setFixedWidth(60)
        path1_input = QLineEdit()
        path1_input.setPlaceholderText('时相1影像')
        path1_input.setToolTip('时相1影像')
        path1_input.setReadOnly(True)
        path1_input.setText(self.path1)
        self.path1_input = path1_input


        path1_open = QPushButton('...', self)
        # path1_open.setEnabled(False)
        path1_open.setFixedWidth(30)
        path1_open.clicked.connect(self.open_file1)


        path1_layout=QHBoxLayout()
        path1_layout.addWidget(path1_label)
        path1_layout.addWidget(path1_input)
        path1_layout.addWidget(path1_open)


        labels1=[QLabel() for i in range(4)]
        style1_inputs=[QLineEdit() for i in range(4)]
        for i in range(4):
            labels1[i].setText(self.bands[i])
            labels1[i].setFixedWidth(50)
            style1_inputs[i].setText(str(self.bandsorder[i]))
            style1_inputs[i].setFixedWidth(20)
        self.style1_inputs=style1_inputs
        style1_set = QPushButton(self.tr('确定'), self)
        style1_set.setFixedWidth(40)
        style1_set.clicked.connect(self.set_style1)
        style1_set.setEnabled(False)
        style1_layout=QHBoxLayout()
        for i in range(4):
            style1_layout.addWidget(labels1[i])
            style1_layout.addWidget(style1_inputs[i])
        style1_layout.addWidget(style1_set)

        path2_label = QLabel('时相2影像:')
        path2_label.setFixedWidth(60)
        path2_input = QLineEdit()
        path2_input.setPlaceholderText('时相2影像')
        path2_input.setToolTip('时相2影像')
        path2_input.setReadOnly(True)
        path2_input.setText(self.path2)
        self.path2_input = path2_input

        path2_open = QPushButton('...', self)
        path2_open.setFixedWidth(30)
        # path2_open.setEnabled(False)
        path2_open.clicked.connect(self.open_file2)

        path2_layout=QHBoxLayout()
        path2_layout.addWidget(path2_label)
        path2_layout.addWidget(path2_input)
        path2_layout.addWidget(path2_open)


        labels2=[QLabel() for i in range(4)]

        style2_inputs=[QLineEdit() for i in range(4)]
        for i in range(4):
            labels2[i].setText(self.bands[i])
            labels2[i].setFixedWidth(50)
            style2_inputs[i].setText(str(self.bandsorder[i]))
            style2_inputs[i].setFixedWidth(20)
        self.style2_inputs=style2_inputs
        style2_set = QPushButton(self.tr('确定'), self)
        style2_set.setFixedWidth(40)
        style2_set.clicked.connect(self.set_style2)
        style2_set.setEnabled(False)
        self.open1=style1_set
        self.open2=style2_set
        style2_layout=QHBoxLayout()
        for i in range(4):
            style2_layout.addWidget(labels2[i])
            style2_layout.addWidget(style2_inputs[i])
        style2_layout.addWidget(style2_set)

        ok_button = QPushButton(self.tr('确定'))
        cancel_button = QPushButton(self.tr('取消'))

        ok_button.clicked.connect(self.ok)
        cancel_button.clicked.connect(self.cancel)
        ok_button.setDefault(True)
        cancel_button.setDefault(False)
        buttonbox=QDialogButtonBox(self)
        buttonbox.addButton(ok_button,QDialogButtonBox.NoRole)
        buttonbox.addButton(cancel_button,QDialogButtonBox.NoRole)
        buttonbox.setCenterButtons(True)
        # button_layout = QHBoxLayout()
        # button_layout.setDirection(QHBoxLayout.RightToLeft)
        # button_layout.addWidget(cancel_button, 0, Qt.AlignCenter)
        # button_layout.addWidget(ok_button, 0, Qt.AlignCenter)

        main_layout = QVBoxLayout()
        main_layout.addLayout(path1_layout)
        main_layout.addLayout(style1_layout)
        main_layout.addLayout(path2_layout)
        main_layout.addLayout(style2_layout)
        main_layout.addLayout(maplayout)
        main_layout.addWidget(buttonbox)
        # main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def open_file1(self):
        path1 = QFileDialog.getOpenFileNames(self, '打开数据1', Settings.General().last_path, '*.*')
        if path1[0]!='':
            try:

                self.path1 = path1[0][0]
                self.path1_input.setText(self.path1)
                result=QMessageBox.question(self, '提示', '是否创建图像金字塔', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)  #默认关闭界面选择No
                if result==QMessageBox.Yes:
                    progress1:QDialog=progressDialog(self,'加载时相一')
                    progress1.setModal(False)
                    self.left_layer=MultiBandRasterLayer(path=self.path1)
                    t1=GdalPreviewImage(self.left_layer,self.left_map,width=200,parent=self.parent())
                    t1.finished.connect(lambda :self.setlabel(progress1))
                    t2=build_pyramids_overviews(self.path1,self.parent())
                    t2.finished.connect(progress1.hide)
                    t1.finished.connect(t2.start)
                    t1.finished.connect(lambda : self.open1.setEnabled(True))
                    t1.start()
                    # t2.start()
                    progress1.show()
                else:
                    progress1=progressDialog(self,'加载时相一')
                    progress1.setModal(False)
                    self.left_layer=MultiBandRasterLayer(path=self.path1)
                    t1=GdalPreviewImage(self.left_layer,self.left_map,width=200,parent=self.parent())
                    # t1.started.connect(progress1.show)
                    t1.finished.connect(lambda : self.open1.setEnabled(True))
                    t1.finished.connect(progress1.hide)
                    t1.start()
                    progress1.show()
                    

            except:
                return
    
    def open_file2(self):
        path2 = QFileDialog.getOpenFileNames(self, '打开数据2', Settings.General().last_path, '*.*')
        if  path2[0]!='':

            self.path2 = path2[0][0]
            self.path2_input.setText(self.path2)
            result=QMessageBox.question(self, '提示', '是否创建图像金字塔', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)  #默认关闭界面选择No

            if result==QMessageBox.Yes:
                progress2=progressDialog(self,'加载时相二')
                progress2.setModal(False)
                # progress1.show
                self.right_layer=MultiBandRasterLayer(path=self.path2)

                t1=GdalPreviewImage(self.right_layer,self.right_map,width=200,parent=self.parent())

                # t1.started.connect(progress1.show)
                t1.finished.connect(lambda :self.open2.setEnabled(True))
                t1.finished.connect(lambda :self.setlabel(progress2))
                
                t2=build_pyramids_overviews(self.path2,self.parent())
                t2.finished.connect(progress2.hide)
                t1.start()
                t1.finished.connect(t2.start)
                progress2.show()
            else:
                progress2=progressDialog(self,'加载时相二')
                progress2.setModal(False)
                self.right_layer=MultiBandRasterLayer(path=self.path2)
                t1=GdalPreviewImage(self.right_layer,self.right_map,width=200,parent=self.parent())

                # t1.started.connect(progress1.show)
                t1.finished.connect(lambda :self.open2.setEnabled(True))
                t1.finished.connect(progress2.hide)
                t1.start()
                progress2.show()

    def ok(self):
        self.bandsorder1=[int(q.text()) for q in self.style1_inputs ]
        self.style1={'r':self.bandsorder1[0],'g':self.bandsorder1[1],'b':self.bandsorder1[2],'NIR':self.bandsorder1[3]}

        self.bandsorder2=[int(q.text()) for q in self.style2_inputs ]
        self.style2={'r':self.bandsorder2[0],'g':self.bandsorder2[1],'b':self.bandsorder2[2],'NIR':self.bandsorder2[3]}

        if self.path1 == '':
            QMessageBox.warning(self, 'Warning', 'Please select pic 1!')
            return
        if self.path2 == '':
            QMessageBox.warning(self, 'Warning', 'Please select pic 2!')
            return
        self.accept()
    def cancel(self):
        self.reject()


    def setlabel(self,s):
        try:
            s.setlabel('创建影像金字塔..')
        except:
            pass
    def set_style1(self):
        self.bandsorder1=[int(q.text()) for q in self.style1_inputs ]
        self.style1={'r':self.bandsorder1[0],'g':self.bandsorder1[1],'b':self.bandsorder1[2],'NIR':self.bandsorder1[3]}
        self.left_layer.set_stlye(self.style1)
        self.left_map.setPixmap(self.left_layer.previewAsPixmapo(width=200))

    def set_style2(self):
        self.bandsorder2=[int(q.text()) for q in self.style2_inputs ]
        self.style2={'r':self.bandsorder2[0],'g':self.bandsorder2[1],'b':self.bandsorder2[2],'NIR':self.bandsorder2[3]}
        self.right_layer.set_stlye(self.style2)
        self.right_map.setPixmap(self.right_layer.previewAsPixmapo(width=200))

class GdalPreviewImage(QThread):
    def __init__(self,layer,map,width=200,parent=None) -> None:
        super(GdalPreviewImage,self).__init__(parent)
        self.layer=layer
        self.map=map
        self.width=width
    def run(self):
        self.map.setPixmap(self.layer.previewAsPixmapo(width=self.width))


class build_pyramids_overviews(QThread):
    def __init__(self,filename,parent=None) -> None:
        super(build_pyramids_overviews,self).__init__(parent)
        self.filename=filename
    def run(self):
        try:
            filename=self.filename
            image:gdal.Dataset = gdal.Open(filename, 0)
            gdal.SetConfigOption('COMPRESS_OVERVIEW', 'DEFLATE')
            ov_list = [2, 4,6, 8, 12,16,24, 32, 48,64,96,128]
            image.BuildOverviews("NEAREST",overviewlist=ov_list)
            del image
        except:
            pass

if __name__ == '__main__':
    import sys

    app = QApplication(sys.argv)
    w = progressDialog()
    w.show()
    sys.exit(app.exec_())