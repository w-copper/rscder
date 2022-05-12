import logging
import shutil
from rscder.utils.setting import Settings
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal
from rscder.plugins.basic import BasicPlugin
import importlib
import os
import sys
import inspect

class PluginLoader(QObject):

    plugin_loaded = pyqtSignal()

    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx
        self.plugins = []

    @staticmethod
    def copy_plugin_to_3rd(dir, random_suffix=True):
        if not os.path.exists(Settings.Plugin().root):
            os.makedirs(Settings.Plugin().root)
        return shutil.copytree(dir, 
                os.path.join(Settings.Plugin().root,
                             os.path.basename(dir)))
    
    @staticmethod
    def load_plugin_info(path):
        
        sys.path.insert(0, os.path.join(path, '..'))
        info = None
        try:
            module = importlib.import_module(os.path.basename(path))
            mes = inspect.getmembers(module)
            for name, obj in mes:
                # logging
                logging.info(f'{name}:{obj}')
                if inspect.isclass(obj) and issubclass(obj, BasicPlugin):
                    info = obj.info()
                    break
        except Exception as e:
            logging.info(str(e))
            QMessageBox.critical(None, 'Error', f'{path} load error: {e}')
        finally:
            sys.path.pop(0)
        return info

    def load_plugin(self):
        plugins = Settings.Plugin().plugins
        if Settings.Plugin().root not in sys.path:
            sys.path.insert(0, Settings.Plugin().root)
        for plugin in plugins:
            # path = plugin['path']
            if not plugin['enabled']:
                continue
            try:
                module = importlib.import_module(plugin['module'])
                for oname, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and issubclass(obj, BasicPlugin) and obj != BasicPlugin and obj != PluginLoader:
                        self.plugins.append(obj(self.ctx))
                        break
            except Exception as e:
                self.ctx['message_box'].error(f'{plugin["name"]} load error: {e}')
        

        self.plugin_loaded.emit()