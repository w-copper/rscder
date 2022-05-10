from distutils.core import setup
import shutil
from Cython.Build import cythonize
import sys
import os

for plugin in os.listdir('plugins'):
    if os.path.isdir(os.path.join('plugins', plugin)):
        setup( 
            name = plugin,
            ext_modules = cythonize(os.path.join('plugins', plugin, '*.py'), exclude=[ f'plugins/{plugin}/__init__.py']),
            script_args = ['build_ext', '-b', 'plugin-build'],
        )
        shutil.copy(os.path.join('plugins', plugin, '__init__.py'), os.path.join('plugin-build', plugin, '__init__.py'))
        