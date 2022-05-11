from pathlib import Path
from PyQt5.QtWidgets import QDialog, QFileDialog, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox
from PyQt5.QtGui import QIcon, QIntValidator
from PyQt5.QtCore import Qt
from rscder.utils.setting import Settings

class Create(QDialog):

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle('Create Project')
        self.setWindowIcon(QIcon(":/icons/logo.svg"))

        self.file = str(Path(Settings.General().root)/'default')
        self.name = '未命名'
        self.max_memory = Settings.Project().max_memory
        self.cell_size = Settings.Project().cell_size        

        file_label = QLabel('Project Dir:')
        file_label.setFixedWidth(100)
        file_input = QLineEdit()
        file_input.setPlaceholderText('Project Dir')
        file_input.setToolTip('Project Dir')
        file_input.setReadOnly(True)
        file_input.setText(self.file)
        self.file_input = file_input

        file_open = QPushButton('...', self)
        file_open.setFixedWidth(30)
        file_open.clicked.connect(self.open_file)


        name_label = QLabel('Project Name:')
        name_label.setFixedWidth(100)
        name_input = QLineEdit()
        name_input.setPlaceholderText('Project Name')
        name_input.setToolTip('Project Name')
        name_input.setText(self.name)
        self.name_input = name_input


        name_input_layout = QHBoxLayout()
        name_input_layout.addWidget(name_label)
        name_input_layout.addWidget(name_input)

        file_input_layout = QHBoxLayout()
        file_input_layout.addWidget(file_label)
        file_input_layout.addWidget(file_input)
        file_input_layout.addWidget(file_open)

        cell_size_label = QLabel('Cell Size:')
        cell_size_label.setFixedWidth(100)
        cell_size_x_label = QLabel('X:')
        cell_size_y_label = QLabel('Y:')
        cell_size_x_input = QLineEdit()
        cell_size_y_input = QLineEdit()
        cell_size_x_input.setPlaceholderText('Cell Size X')
        cell_size_x_input.setValidator(QIntValidator())
        cell_size_y_input.setPlaceholderText('Cell Size Y')
        cell_size_y_input.setValidator(QIntValidator())
        cell_size_x_input.setToolTip('Cell Size X')
        cell_size_y_input.setToolTip('Cell Size Y')
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

        max_memory_label = QLabel('Max Memory (MB):')
        max_memory_label.setFixedWidth(100)
        max_memory_input = QLineEdit()
        max_memory_input.setPlaceholderText('Max Memory')
        max_memory_input.setToolTip('Max Memory')
        max_memory_input.setText(str(self.max_memory))
        max_memory_input.setValidator(QIntValidator())
        self.max_memory_input = max_memory_input

        ok_button = QPushButton('OK')
        cancel_button = QPushButton('Cancel')

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
        file = QFileDialog.getExistingDirectory(self, 'Open Directory', self.file)
        if file:
            self.file = file
            self.file_input.setText(self.file)
    
    def ok(self):
        self.name = self.name_input.text()
        self.max_memory = self.max_memory_input.text()
        self.cell_size = (self.cell_size_x_input.text(), self.cell_size_y_input.text())
        if self.name == '':
            QMessageBox.warning(self, 'Warning', 'Please input project name!')
            return
        if self.max_memory == '':
            QMessageBox.warning(self, 'Warning', 'Please input max memory!')
            return
        if self.cell_size == ('', ''):
            QMessageBox.warning(self, 'Warning', 'Please input cell size!')
            return
        self.max_memory = int(self.max_memory)
        self.cell_size = (int(self.cell_size[0]), int(self.cell_size[1]))
        self.accept()
    
    def cancel(self):
        self.reject()