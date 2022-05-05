from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, Qt
from rscder.utils.setting import Settings

class PluginDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Plugins')
        self.setWindowIcon(QIcon(":/icons/logo.svg"))
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.plugins = Settings.Plugin().plugins

        self.plugin_table = QTableWidget(len(self.plugins), 2, self)
        self.plugin_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.plugin_table.setColumnWidth(0, 200)
        self.plugin_table.setColumnWidth(1, 500)
        self.plugin_table.setHorizontalHeaderLabels(['Name', 'Path', 'Enabled'])
        self.plugin_table.setEditTriggers(QAbstractItemView.DoubleClicked)
        self.plugin_table.cellDoubleClicked.connect(self.edit_plugin)
        for idx, plugin in enumerate(self.plugins):
            name_item = QTableWidgetItem(plugin['name'])
            path_item = QTableWidgetItem(plugin['path'])
            enabled_item = QTableWidgetItem()
            enabled_item.setCheckState(Qt.Checked if plugin['enabled'] else Qt.Unchecked)

            self.plugin_table.setItem(idx, 0, name_item)
            self.plugin_table.setItem(idx, 1, path_item)
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
        self.has_change = True
        self.plugin_table.insertRow(self.plugin_table.rowCount())
    
    def remove_plugin(self):
        self.has_change = True
        for row in self.plugin_table.selectedItems():
            self.plugin_table.removeRow(row.row())
        
        # for idx in self.plugins
    
    def edit_plugin(self, row, column):
        self.has_change = True
        if column == 0:
            self.plugin_table.item(row, column).setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        elif column == 1:
            open_file = QFileDialog.getOpenFileName(self, 'Open File', '', 'Python Files (*.py)')
            if open_file[0]:
                self.plugin_table.item(row, column).setText(open_file[0])
            else:
                pass
        elif column == 2:
            self.plugin_table.item(row, column).setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)       
        # self.plugin_list.setFixedWidth(200)
    
    def save_plugin(self):

        plugins = []
        for idx in range(self.plugin_table.rowCount()):
            name = self.plugin_table.item(idx, 0).text()
            path = self.plugin_table.item(idx, 1).text()
            enabled = self.plugin_table.item(idx, 2).checkState() == Qt.Checked
            plugins.append({'name': name, 'path': path, 'enabled': enabled})
        Settings.Plugin().plugins = plugins
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