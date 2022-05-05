from rscder.utils.setting import Settings
from PyQt5.QtCore import QObject, pyqtSignal
from rscder.plugins.basic import BasicPlugin
import importlib
import os
import sys
import inspect

class PluginLoader(QObject):

    plugin_loaded = pyqtSignal()

    def __init__(self, ctx):
        self.ctx = ctx
    
    def load_plugin(self):
        plugins = Settings.Plugin().plugins
        for plugin in plugins:
            name = plugin['name']
            path = plugin['path']
            try:
                module = importlib.import_module(path)
                for oname, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, BasicPlugin) and obj != BasicPlugin and obj != PluginLoader and oname == name:
                        obj(self.ctx)
            except Exception as e:
                self.ctx['message_box'].error(f'{name} load error: {e}')
                # print(e)

        self.plugin_loaded.emit()