from PyQt5.QtWidgets import QDialog, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from utils.setting import Settings
class Create(QDialog):

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle('Create Project')
        self.setWindowIcon(QIcon(":/icons/logo.svg"))

        self.file = str(Settings.General().root)
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

        name_label = QLabel('Project Name:')
        name_label.setFixedWidth(100)
        name_input = QLineEdit()
        name_input.setPlaceholderText('Project Name')
        name_input.setToolTip('Project Name')

        name_input_layout = QHBoxLayout()
        name_input_layout.addWidget(name_label)
        name_input_layout.addWidget(name_input)

        file_input_layout = QHBoxLayout()
        file_input_layout.addWidget(file_label)
        file_input_layout.addWidget(file_input)

        cell_size_label = QLabel('Cell Size:')
        cell_size_label.setFixedWidth(100)
        cell_size_x_label = QLabel('X:')
        cell_size_y_label = QLabel('Y:')
        cell_size_x_input = QLineEdit()
        cell_size_y_input = QLineEdit()
        cell_size_x_input.setPlaceholderText('Cell Size X')
        cell_size_y_input.setPlaceholderText('Cell Size Y')
        cell_size_x_input.setToolTip('Cell Size X')
        cell_size_y_input.setToolTip('Cell Size Y')

        cell_input_layout = QHBoxLayout()
        cell_input_layout.addWidget(cell_size_label)
        cell_input_layout.addWidget(cell_size_x_label)
        cell_input_layout.addWidget(cell_size_x_input)
        cell_input_layout.addWidget(cell_size_y_label)
        cell_input_layout.addWidget(cell_size_y_input)

        ok_button = QPushButton('OK')
        cancel_button = QPushButton('Cancel')
        
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
    
