import shutil
import subprocess
import os
path = os.path.dirname(os.path.realpath(__file__))
icon_path = os.path.join(path, '..', 'icons')
with open(os.path.join(path, '..', 'res.qrc'), 'w') as f:
    f.write(f'<RCC>\n')
    f.write(f'    <qresource prefix="/">\n')
    for icon in os.listdir(icon_path):
        f.write(f'        <file>{os.path.join("icons", icon)}</file>\n')
    f.write(f'    </qresource>\n')
    f.write(f'</RCC>\n')

subprocess.run(['pyrcc5', 'res.qrc', '-o', 'rc.py'], cwd=os.path.join(path, '..'))

shutil.rmtree(icon_path)