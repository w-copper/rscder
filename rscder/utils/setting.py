from datetime import datetime
import os
from typing import Tuple
from PyQt5.QtCore import QSettings
from rscder.utils.license import LicenseHelper
import yaml

class Settings(QSettings):

    def __init__(self, key):
        super().__init__()
        self.key = key 
    def __enter__(self):
        self.beginGroup(self.key)
        return self
    
    def __exit__(self, *args, **kargs):
        self.endGroup()

    class Plugin:

        PRE='plugin'

        @property
        def root(self):
            _r = './plugins'
            if not os.path.exists(_r):
                os.makedirs(_r)
            return _r

        @property
        def plugins(self):
            plugins_file = os.path.join(self.root, 'plugins.yaml')
            if not os.path.exists(plugins_file):
                with open(plugins_file, 'w') as f:
                    yaml.safe_dump([], f)
            with open(plugins_file, 'r') as f:
                return yaml.safe_load(f)

        @plugins.setter
        def plugins(self, value):
            plugins_file = os.path.join(self.root, 'plugins.yaml')
            with open(plugins_file, 'w') as f:
                yaml.safe_dump(value, f)

    

    class Project:

        PRE= 'project'

        @property
        def cell_size(self) -> Tuple[int, int]:
            with Settings(self.PRE) as s:
                return s.value('cell_size', (100, 100))
        
        @cell_size.setter
        def cell_size(self, value:Tuple[int, int]):
            with Settings(self.PRE) as s:
                s.setValue('cell_size', value)

        @property
        def max_memory(self):
            with Settings(self.PRE) as s:
                return s.value('max_memory', 100)
        
        @max_memory.setter
        def max_memory(self, value):
            with Settings(self.PRE) as s:
                s.setValue('max_memory', value)
        
        @property
        def max_threads(self):
            with Settings(self.PRE) as s:
                return s.value('max_threads', 4)
        
        @max_threads.setter
        def max_threads(self, value):
            with Settings(self.PRE) as s:
                s.setValue('max_threads', value)

    class General:
        
        PRE='general'

        @property
        def size(self):
            with Settings(Settings.General.PRE) as s:
                return s.value('size', (800, 600))
        
        @size.setter
        def size(self, value):
            with Settings(Settings.General.PRE) as s:
                s.setValue('size', value)

        @property
        def last_path(self):
            with Settings(Settings.General.PRE) as s:
                return str(s.value('last_path', ''))
        
        @last_path.setter
        def last_path(self, value):
            with Settings(Settings.General.PRE) as s:
                s.setValue('last_path', str(value))

        @property
        def end_date(self):
            if not os.path.exists('lic/license.lic'):
                return datetime.now()

            with open('lic/license.lic', 'r') as f:
                lic = f.read()[::-1]
            
            lic_helper = LicenseHelper()
            try:
                lic_dic = lic_helper.read_license(lic)

                if lic_helper.check_license_date(lic_dic['time_str']) and lic_helper.check_license_psw(lic_dic['psw']):
                    return lic_dic['time_str']
                else:
                    return datetime.now()
            except:
                return datetime.now()

        @property
        def license(self):
            if not os.path.exists('lic/license.lic'):
                return False

            with open('lic/license.lic', 'r') as f:
                lic = f.read()[::-1]
            
            lic_helper = LicenseHelper()
            try:
                lic_dic = lic_helper.read_license(lic)

                if lic_helper.check_license_date(lic_dic['time_str']) and lic_helper.check_license_psw(lic_dic['psw']):
                    return True
                else:
                    return False
            except:
                return False

        @property
        def root(self):
            with Settings(Settings.General.PRE) as s:
                return s.value('root', './')
        
        @property
        def auto_save(self):
            with Settings(Settings.General.PRE) as s:
                return s.value('auto_save', True)
        
        @auto_save.setter
        def auto_save(self, value):
            if isinstance(value, bool):
                pass
            else:
                if isinstance(value, (int,float)):
                    value = value != 0
                else:
                    value = value is not None
            with Settings(Settings.General.PRE) as s:
                s.setValue('auto_save', value)
            
        @property
        def auto_save_intervel(self):
            with Settings(Settings.General.PRE) as s:
                return s.value('auto_save_intervel', 30)
        
        @auto_save_intervel.setter
        def auto_save_intervel(self, value):
            if isinstance(value, int) and value > 0:
                pass
            else:
                return
            with Settings(Settings.General.PRE) as s:
                s.setValue('auto_save_intervel', value)