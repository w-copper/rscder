import os
import shutil
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from rscder.plugins.loader import PluginLoader
from rscder.utils.setting import Settings

class PluginDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Plugins')
        self.setWindowIcon(QIcon(":/icons/logo.svg"))
        self.setMinimumWidth(900)
        self.setMinimumHeight(600)
        self.plugins = list(Settings.Plugin().plugins)

        self.plugin_table = QTableWidget(len(self.plugins), 3, self)
        self.plugin_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.plugin_table.setColumnWidth(0, 200)
        self.plugin_table.setColumnWidth(1, 500)
        self.plugin_table.setHorizontalHeaderLabels(['Name', 'Module', 'Enabled'])
        self.plugin_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.plugin_table.cellDoubleClicked.connect(self.edit_plugin)
        for idx, plugin in enumerate(self.plugins):
            name_item = QTableWidgetItem(plugin['name'])
            module_item = QTableWidgetItem(plugin['module'])
            enabled_item = QTableWidgetItem()
            enabled_item.setCheckState(Qt.Checked if plugin['enabled'] else Qt.Unchecked)

            self.plugin_table.setItem(idx, 0, name_item)
            self.plugin_table.setItem(idx, 1, module_item)
            self.plugin_table.setItem(idx, 2, enabled_item)
    
        self.add_button = QPushButton('Add', self)
        self.add_button.clicked.connect(self.add_plugin)
        self.remove_button = QPushButton('Remove', self)
        self.remove_button.clicked.connect(self.remove_plugin)
        self.save_button = QPushButton('Save', self)
        self.save_button.clicked.connect(self.save_plugin)
        self.cancel_button = QPushButton('Cancel', self)
        self.cancel_button.clicked.connect(self.close)
    
        layout = QVBoxLayout(self)
        layout.addWidget(self.plugin_table)
        hlayout = QHBoxLayout()
        hlayout.addWidget(self.add_button)
        hlayout.addWidget(self.remove_button)
        hlayout.addWidget(self.save_button)
        hlayout.addWidget(self.cancel_button)
        layout.addLayout(hlayout)
        self.setLayout(layout)
        self.has_change = False

    def add_plugin(self):
        plugin_directory = QFileDialog.getExistingDirectory(self, 'Select Plugin Directory', '.')
        if plugin_directory is not None:
            info = PluginLoader.load_plugin_info(plugin_directory)
            print(info)
           
            if info is not None:
                try:
                    dst = PluginLoader.copy_plugin_to_3rd(plugin_directory)
                except:
                    QMessageBox.warning(self, 'Warning', 'Failed to copy plugin to 3rd party directory')
                    return
                
                info['module'] = os.path.basename(plugin_directory)
                info['enabled'] = True
                info['path'] = dst
                self.has_change = True
                
                self.plugin_table.insertRow(self.plugin_table.rowCount())
                name_item = QTableWidgetItem(info['name'])
                module_item = QTableWidgetItem(info['module'])
                enabled_item = QTableWidgetItem('启用')
                enabled_item.setCheckState(Qt.Checked)
                self.plugin_table.setItem(self.plugin_table.rowCount() - 1, 0, name_item)
                self.plugin_table.setItem(self.plugin_table.rowCount() - 1, 1, module_item)
                self.plugin_table.setItem(self.plugin_table.rowCount() - 1, 2, enabled_item)
                self.plugins.append(info)
        else:
            pass
        
    
    def remove_plugin(self):
        self.has_change = True
        row_ids = list( row.row() for row in self.plugin_table.selectionModel().selectedRows())
        row_ids.sort(reverse=True)
        for row in row_ids:
            self.plugin_table.removeRow(row)
            info = self.plugins.pop(row)
            try:
                shutil.rmtree(info['path'])
            except:
                pass
        # for idx in self.plugins
    
    def edit_plugin(self, row, column):
        self.has_change = True
        if column == 2:
            self.plugin_table.item(row, column).setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)       
    
    def save_plugin(self):

        for idx in range(self.plugin_table.rowCount()):
            enabled = self.plugin_table.item(idx, 2).checkState() == Qt.Checked
            self.plugins[idx]['enabled'] = enabled            
        Settings.Plugin().plugins = self.plugins
        self.has_change = False
        self.close()

    def closeEvent(self, event):
        if self.has_change:
            reply = QMessageBox.question(self, 'Message', "Do you want to save the changes?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.save_plugin()
                event.accept()
            else:
                event.accept()
        else:
            event.accept()