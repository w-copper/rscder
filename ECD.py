import os
os.environ['PROJ_LIB'] = os.path.join(os.path.dirname(__file__), 'share/proj')
os.environ['GDAL_DATA'] = os.path.join(os.path.dirname(__file__), 'share')
os.environ['ECD_BASEDIR'] = os.path.dirname(__file__)
BASE_DIR = os.path.dirname(__file__)
from rscder import MulStart
import logging

logging.basicConfig(level=logging.INFO, filename=os.path.join(BASE_DIR, 'log.txt'), filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

if __name__ == '__main__':

    t = MulStart()
    t.run()    