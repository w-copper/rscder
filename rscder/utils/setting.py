from datetime import datetime
import os
from typing import Tuple
from PyQt5.QtCore import QSettings
from rscder.utils.license import LicenseHelper

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
            return './3rd'

        @property
        def plugins(self):
            with Settings(Settings.Plugin.PRE) as s:
                pl = s.value('plugins', [])
                if pl is None:
                    return []
                return pl
        @plugins.setter
        def plugins(self, value):
            with Settings(Settings.Plugin.PRE) as s:
                s.setValue('plugins', value)


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
        