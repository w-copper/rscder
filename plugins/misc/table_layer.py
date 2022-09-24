from datetime import datetime
import math
from random import random
from osgeo import gdal
from rscder.utils.project import Project
import os
from rscder.utils.project import BasicLayer, ResultPointLayer

def table_layer(pth:str,layer:BasicLayer, name, send_message = None):
    if send_message is not None:
        send_message.emit('正在计算表格结果...')
    cell_size = layer.layer_parent.cell_size
    ds = gdal.Open(pth)
    xsize = ds.RasterXSize
    ysize = ds.RasterYSize
    geo = ds.GetGeoTransform()

    out_csv = os.path.join(Project().other_path, f'{name}_table_result_{ int(datetime.now().timestamp() * 1000) }.csv')
    yblocks = ysize // cell_size[1] + 1
    xblocks = xsize // cell_size[0] + 1
    with open(out_csv, 'w') as f:
        f.write('x,y,diff,status\n')
        for j in range(yblocks):
            block_xy = (0, j * cell_size[1])
            block_size = (xsize, cell_size[1])
            if block_xy[1] + block_size[1] > ysize:
                block_size = (xsize, ysize - block_xy[1])
            block_data = ds.ReadAsArray(*block_xy, *block_size)
            for i in range(xblocks):
                start_x = i * cell_size[0]
                end_x = start_x + cell_size[0]
                if end_x > xsize:
                    end_x = xsize
                block_data_xy = block_data[:, start_x:end_x]
                
                center_x = start_x + cell_size[0] // 2
                center_y = j * cell_size[1] + cell_size[1] // 2
                center_x = center_x * geo[1] + geo [0]
                center_y = center_y * geo[5] + geo [3]
                f.write(f'{center_x},{center_y},{block_data_xy.mean() * 100},{int(block_data_xy.mean() > 0.5)}\n')

    result_layer = ResultPointLayer(out_csv, enable=True, proj=layer.proj, geo=layer.geo,result_path={})
    # print(result_layer.result_path)
    layer.layer_parent.add_result_layer(result_layer)
    if send_message is not None:
        send_message.emit('计算完成')