from tkinter.ttk import Style
from PyQt5.QtWidgets import  QWidget, QApplication, QMainWindow, QToolBox
from PyQt5.QtWidgets import QDialog, QFileDialog, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox
from PyQt5.QtCore import Qt, QSize, QSettings
from PyQt5.QtGui import QIcon,QColor
from PyQt5 import QtGui
from rscder.utils.setting import Settings
from rscder.gui.mapcanvas import DoubleCanvas
from qgis.gui import QgsMapCanvas
from rscder.utils.project import RasterLayer
class loader(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle('载入数据')
        self.setWindowIcon(QIcon(":/icons/data_load.png"))
        self.path1=''
        self.path2=''
        self.bands=['red:','green:','blue:','NIR:']
        self.bandsorder=[3,2,1,4]
        self.mapcanva1 = QgsMapCanvas(self)
        self.mapcanva2 = QgsMapCanvas(self)
        self.mapcanva1.setCanvasColor(QColor(0, 0, 0))
        self.mapcanva2.setCanvasColor(QColor(0, 0, 0))
        self.mapcanva1.setFixedWidth(200)
        self.mapcanva1.setFixedHeight(200)
        self.mapcanva2.setFixedWidth(200)
        self.mapcanva2.setFixedHeight(200)
        maplayout=QHBoxLayout()
        maplayout.addWidget(self.mapcanva1)
        maplayout.addWidget(self.mapcanva2)

        path1_label = QLabel('Pic 1:')
        path1_label.setFixedWidth(60)
        path1_input = QLineEdit()
        path1_input.setPlaceholderText('Pic 1')
        path1_input.setToolTip('Pic 1')
        path1_input.setReadOnly(True)
        path1_input.setText(self.path1)
        self.path1_input = path1_input


        path1_open = QPushButton('...', self)
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

        style1_layout=QHBoxLayout()
        for i in range(4):
            style1_layout.addWidget(labels1[i])
            style1_layout.addWidget(style1_inputs[i])
        style1_layout.addWidget(style1_set)

        path2_label = QLabel('Pic 2:')
        path2_label.setFixedWidth(60)
        path2_input = QLineEdit()
        path2_input.setPlaceholderText('Pic 1')
        path2_input.setToolTip('Pic 1')
        path2_input.setReadOnly(True)
        path2_input.setText(self.path2)
        self.path2_input = path2_input

        path2_open = QPushButton('...', self)
        path2_open.setFixedWidth(30)
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

        style2_layout=QHBoxLayout()
        for i in range(4):
            style2_layout.addWidget(labels2[i])
            style2_layout.addWidget(style2_inputs[i])
        style2_layout.addWidget(style2_set)

        ok_button = QPushButton(self.tr('确定'))
        cancel_button = QPushButton(self.tr('取消'))

        ok_button.clicked.connect(self.ok)
        cancel_button.clicked.connect(self.cancel)
        
        button_layout = QHBoxLayout()
        button_layout.setDirection(QHBoxLayout.RightToLeft)
        button_layout.addWidget(ok_button, 0, Qt.AlignRight)
        button_layout.addWidget(cancel_button, 0, Qt.AlignRight)

        main_layout = QVBoxLayout()
        main_layout.addLayout(path1_layout)
        main_layout.addLayout(style1_layout)
        main_layout.addLayout(path2_layout)
        main_layout.addLayout(style2_layout)
        main_layout.addLayout(maplayout)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def open_file1(self):
        path1 = QFileDialog.getOpenFileNames(self, '打开数据1', Settings.General().last_path, '*.*')
        if path1:
            self.path1 = path1[0][0]
            self.path1_input.setText(self.path1)
        self.left_layer=RasterLayer(path=self.path1)
        self.mapcanva1.setLayers([self.left_layer.layer])
        self.mapcanva1.zoomToFeatureExtent(self.left_layer.layer.extent())

    def open_file2(self):
        path2 = QFileDialog.getOpenFileNames(self, '打开数据2', Settings.General().last_path, '*.*')
        if path2:
            self.path2 = path2[0][0]
            self.path2_input.setText(self.path2)
        self.right_layer=RasterLayer(path=self.path2)
        self.mapcanva2.setLayers([self.right_layer.layer])
        self.mapcanva2.zoomToFeatureExtent(self.right_layer.layer.extent())
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

    def set_style1(self):
        self.bandsorder1=[int(q.text()) for q in self.style1_inputs ]
        self.style1={'r':self.bandsorder1[0],'g':self.bandsorder1[1],'b':self.bandsorder1[2],'NIR':self.bandsorder1[3]}
        self.left_layer.set_stlye(self.style1)

    def set_style2(self):
        self.bandsorder2=[int(q.text()) for q in self.style2_inputs ]
        self.style2={'r':self.bandsorder2[0],'g':self.bandsorder2[1],'b':self.bandsorder2[2],'NIR':self.bandsorder2[3]}
        self.right_layer.set_stlye(self.style2)