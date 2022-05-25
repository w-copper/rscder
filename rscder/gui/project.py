from pathlib import Path
from PyQt5.QtWidgets import QDialog, QFileDialog, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox
from PyQt5.QtGui import QIcon, QIntValidator
from PyQt5.QtCore import Qt
from rscder.utils.project import Project
from rscder.utils.setting import Settings

class Create(QDialog):

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr('创建项目'))
        self.setWindowIcon(QIcon(":/icons/logo.png"))

        self.file = str(Path(Settings.General().last_path))
        self.name = '未命名'
        self.max_memory = Settings.Project().max_memory
        self.cell_size = Settings.Project().cell_size        

        file_label = QLabel('项目目录:')
        file_label.setFixedWidth(100)
        file_input = QLineEdit()
        file_input.setPlaceholderText('项目目录')
        file_input.setToolTip('项目目录')
        file_input.setReadOnly(True)
        file_input.setText(self.file)
        self.file_input = file_input

        file_open = QPushButton('...', self)
        file_open.setFixedWidth(30)
        file_open.clicked.connect(self.open_file)


        name_label = QLabel('项目名称:')
        name_label.setFixedWidth(100)
        name_input = QLineEdit()
        name_input.setPlaceholderText('项目名称')
        name_input.setToolTip('项目名称')
        name_input.setText(self.name)
        self.name_input = name_input


        name_input_layout = QHBoxLayout()
        name_input_layout.addWidget(name_label)
        name_input_layout.addWidget(name_input)

        file_input_layout = QHBoxLayout()
        file_input_layout.addWidget(file_label)
        file_input_layout.addWidget(file_input)
        file_input_layout.addWidget(file_open)

        cell_size_label = QLabel('格网大小:')
        cell_size_label.setFixedWidth(100)
        cell_size_x_label = QLabel('X:')
        cell_size_y_label = QLabel('Y:')
        cell_size_x_input = QLineEdit()
        cell_size_y_input = QLineEdit()
        cell_size_x_input.setPlaceholderText('X')
        cell_size_x_input.setValidator(QIntValidator())
        cell_size_y_input.setPlaceholderText('Y')
        cell_size_y_input.setValidator(QIntValidator())
        cell_size_x_input.setToolTip('X')
        cell_size_y_input.setToolTip('Y')
        cell_size_x_input.setText(str(self.cell_size[0]))
        cell_size_y_input.setText(str(self.cell_size[1]))

        self.cell_size_x_input = cell_size_x_input
        self.cell_size_y_input = cell_size_y_input

        cell_input_layout = QHBoxLayout()
        cell_input_layout.addWidget(cell_size_label)
        cell_input_layout.addWidget(cell_size_x_label)
        cell_input_layout.addWidget(cell_size_x_input)
        cell_input_layout.addWidget(cell_size_y_label)
        cell_input_layout.addWidget(cell_size_y_input)

        max_memory_label = QLabel('最大文件大小 (MB):')
        max_memory_label.setFixedWidth(100)
        max_memory_input = QLineEdit()
        max_memory_input.setPlaceholderText('最大文件大小')
        max_memory_input.setToolTip('最大文件大小')
        max_memory_input.setText(str(self.max_memory))
        max_memory_input.setValidator(QIntValidator())
        self.max_memory_input = max_memory_input

        ok_button = QPushButton('确定')
        cancel_button = QPushButton('取消')

        ok_button.clicked.connect(self.ok)
        cancel_button.clicked.connect(self.cancel)
        
        button_layout = QHBoxLayout()
        button_layout.setDirection(QHBoxLayout.RightToLeft)
        button_layout.addWidget(ok_button, 0, Qt.AlignRight)
        button_layout.addWidget(cancel_button, 0, Qt.AlignRight)

        main_layout = QVBoxLayout()
        main_layout.addLayout(file_input_layout)
        main_layout.addLayout(name_input_layout)
        main_layout.addLayout(cell_input_layout)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)
    

    def open_file(self):
        file = QFileDialog.getExistingDirectory(self, '选择文件夹', self.file)
        if file:
            self.file = file
            Settings.General().last_path = self.file
            self.file_input.setText(self.file)
    
    def ok(self):
        self.name = self.name_input.text()
        self.max_memory = self.max_memory_input.text()
        self.cell_size = (self.cell_size_x_input.text(), self.cell_size_y_input.text())
        if self.name == '':
            QMessageBox.warning(self, 'Warning', '请选择项目目录!')
            return
        if self.max_memory == '':
            QMessageBox.warning(self, 'Warning', '请输入最大文件大小!')
            return
        if self.cell_size == ('', ''):
            QMessageBox.warning(self, 'Warning', '请输入格网大小!')
            return
        self.max_memory = int(self.max_memory)
        self.cell_size = (int(self.cell_size[0]), int(self.cell_size[1]))
        self.accept()
    
    def cancel(self):
        self.reject()