import multiprocessing
from alg.txt_export_to import export_to_shp
import os
import glob
from qgis.core import *
class ExportToSHP(multiprocessing.Process):

    def __init__(self, conn, result_path, output_dir):
        super(ExportToSHP, self).__init__()
        self.conn = conn
        self.result_path = result_path
        self.result_list = self.get_result_list()
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def get_result_list(self):
        fl = list(glob.glob(os.path.join(self.result_path, '*.txt')))
        return fl

    def run(self):
        # result = []
        self.conn.send(len(self.result_list))
        qgs = QgsApplication([], False)
        QgsApplication.initQgis()
        for i, p in enumerate(self.result_list):
            o = os.path.basename(p)
            o = os.path.splitext(o)[0]
            r = export_to_shp(p, os.path.join(self.output_dir, o + '.shp'))
            # result.append([r, self.feats[i]])
            self.conn.send([i, r, o])
        # self.conn.send(result)

