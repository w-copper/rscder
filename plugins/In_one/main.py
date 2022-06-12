from asyncio.windows_events import NULL
import os
import pdb
from threading import Thread
import numpy as np
from rscder.gui.actions import ActionManager
from rscder.plugins.basic import BasicPlugin
from PyQt5.QtWidgets import QAction, QDialog, QHBoxLayout, QVBoxLayout, QPushButton,QWidget,QLabel,QLineEdit,QPushButton,QPixmap
from PyQt5.QtGui import QIcon,QPixmap
from PyQt5.QtCore import Qt
from rscder.gui.layercombox import RasterLayerCombox
from rscder.utils.icons import IconInstance
from rscder.utils.project import Project, RasterLayer, SingleBandRasterLayer
from threshold.otsu import OTSU
from osgeo import gdal
from plugins.In_one import pic
class LockerButton(QPushButton):
    def __init__(self,parent=NULL):
        super(LockerButton,self).__init__(parent)
        m_imageLabel =  QLabel
        m_imageLabel.setFixedWidth(20)
        m_imageLabel.setScaledContents(True)
        m_imageLabel.setStyleSheet("QLabel{background-color:transparent;}")
        m_textLabel =  QLabel
        m_textLabel.setStyleSheet("QLabel{background-color:transparent;}")
        self.m_imageLabel=m_imageLabel
        self.m_textLabel=m_textLabel
        self.hide_=1
        mainLayout =  QHBoxLayout()
        
        mainLayout.addWidget(self.m_imageLabel)
        mainLayout.addWidget(self.m_textLabel)
        mainLayout.setMargin(0)
        mainLayout.setSpacing(0)
        self.setLayout(mainLayout)
    def SetImageLabel(self, pixmap:QPixmap):
        self.m_imageLabel.setPixmap(pixmap)
    def SetTextLabel(self, text):
        self.m_textLabel.setText(text)

class AllInOne(QDialog):
    def __init__(self, parent=None):
        super(AllInOne, self).__init__(parent)
        self.setWindowTitle('变化检测')
        self.setWindowIcon(IconInstance().LOGO)
        self.initUI()

    def initUI(self):
        
        #预处理
        filterWeight=QWidget(self)
        self.filerButton =LockerButton(); 
        self.filerButton.setObjectName("LockerButton")
        self.filerButton.SetTextLabel("大小")
        self.filerButton.SetImageLabel(QPixmap('../pic/右箭头.png'))
        self.filerButton.setStyleSheet("#LockerButton{background-color:transparent}"
        "#LockerButton:hover{background-color:rgba(195,195,195,0.4)}")
        self.layer_combox = RasterLayerCombox(self)
        layer_label = QLabel('图层:')
        hbox = QHBoxLayout()
        hbox.addWidget(layer_label)
        hbox.addWidget(self.layer_combox)
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
        hlayout1 = QHBoxLayout(self)
        hlayout1.addWidget(size_label)
        hlayout1.addWidget(x_size_input)
        hlayout1.addWidget(time_label)
        hlayout1.addWidget(y_size_input)
        vlayout = QVBoxLayout(self)
        vlayout.addWidget(self.filerButton)
        vlayout.addLayout(hbox)
        vlayout.addLayout(hlayout1)
        filterWeight.setLayout(vlayout)

        #变化检测
        changeWeight=QWidget(self)


        totalvlayout=QVBoxLayout()
        totalvlayout.addWidget(filterWeight)
        self.setLayout(totalvlayout)


        self.filerButton.clicked.connect(lambda: self.hide(self.filerButton,filterWeight))

    def hide(self,button:LockerButton,weight:QWidget):
        if ((button.hide_)%2)==1:
            weight.setVisible(False)
            button.SetImageLabel(QPixmap('../pic/右箭头.png'))
        else:
            weight.setVisible(True)
            button.SetImageLabel(QPixmap('../pic/下箭头.png'))

class InOnePlugin(BasicPlugin):
    @staticmethod
    def info():
        return {
            'name': 'AllinOne',
            'description': 'AllinOne',
            'author': 'RSCDER',
            'version': '1.0.0',
        }

    def set_action(self):

        basic_diff_method_in_one = QAction('inone差分法')
        ActionManager().change_detection_menu.addAction(basic_diff_method_in_one)
        self.basic_diff_method_in_one = basic_diff_method_in_one
        basic_diff_method_in_one.triggered.connect(self.run) 


    def run(self):
        pass