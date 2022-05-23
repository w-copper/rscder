import shutil
from rscder.utils.project import Project, PairLayer, ResultPointLayer
from rscder.plugins.basic import BasicPlugin
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QFileDialog, QComboBox, QVBoxLayout, QPushButton, QLabel, QLineEdit, QAction
from PyQt5.QtGui import QIcon
class ExportDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('Export')
        self.setWindowIcon(QIcon(":/icons/logo.png"))

        self.out_path = None
        self.result_layer = None

        result_layer_select_label = QLabel('选择结果:')

        result_layer_select = QComboBox(self)

        result_layer_select.addItem('---', None)
        for layer in Project().layers.values():
            for result_layer in layer.layers:
                if isinstance(result_layer, ResultPointLayer):
                    result_layer_select.addItem( layer.name[:5] + '-' + result_layer.name, result_layer)
        
        for i in range(result_layer_select.count() - 1):
            result_layer_select.setItemIcon(i + 1, QIcon(":/icons/layer.png"))


        def on_result_layer_select(index):
            self.result_layer = result_layer_select.currentData()

        result_layer_select.currentIndexChanged.connect(on_result_layer_select)

        out_path_label = QLabel('输出路径:')
        out_path_text = QLineEdit(self)
        out_path_text.setReadOnly(True)
        out_path_text.setPlaceholderText('选择输出路径')
        
        def on_out_path_btn():
            select_file = QFileDialog.getSaveFileName(self, '选择输出路径', '', '*.txt')
            if select_file[0]:
                out_path_text.setText(select_file[0])
                self.out_path = select_file[0]
        out_path_btn = QPushButton('...', self)
        out_path_btn.clicked.connect(on_out_path_btn)
        
        ok_btn = QPushButton('OK', self)
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton('Cancel', self)
        cancel_btn.clicked.connect(self.reject)


        hbox1 = QHBoxLayout()
        hbox1.addWidget(result_layer_select_label)
        hbox1.addWidget(result_layer_select)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(out_path_label)
        hbox2.addWidget(out_path_text)
        hbox2.addWidget(out_path_btn)

        hbox3 = QHBoxLayout()
        hbox3.addWidget(ok_btn)
        hbox3.addWidget(cancel_btn)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)

        self.setLayout(vbox)

class ExportPlugin(BasicPlugin):

    @staticmethod
    def info():
        return {
            'name': 'Export',
            'description': 'Export to other format',
            'author': 'RSCDER',
        }
    
    def set_action(self):
        self.export_txt = QAction(QIcon(":/icons/document.png"), '导出为 Arcgis 兼容的TXT', self.mainwindow)
        self.export_txt.triggered.connect(self.export_txt_action)

        self.ctx['postop_menu'].addAction(self.export_txt)

        self.ctx['toolbar'].addAction(self.export_txt)

    def export_txt_action(self):
        dialog = ExportDialog(self.mainwindow)
        if dialog.exec_():
            result = dialog.result_layer
            out = dialog.out_path
            if result:
                shutil.copy(result.path, out)
                self.message_box.info('导出成功')