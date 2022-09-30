
def imageRC2geo(geo:list,x,y):
    '''
    根据GDAL的六参数模型将影像图上坐标（行列号）转为投影坐标或地理坐标（根据具体数据的坐标系统转换）
    :param geo: GDAL地理数据,getGeotransform
    '''
    trans = geo
    px = trans[0] + x * trans[1] + y * trans[2]
    py = trans[3] + x * trans[4] + y * trans[5]
    return [px, py]

def geo2imageRC(geo:list,px,py):
    '''
    根据GDAL的六 参数模型将给定的投影或地理坐标转为影像图上坐标（行列号）,return x,y
    '''
    dTemp = geo[1] * geo[5] - geo[2] *geo[4]
    x= int((geo[5] * (px - geo[0]) -geo[2] * (py - geo[3])) / dTemp + 0.5)
    y = int((geo[1] * (py - geo[3]) -geo[4] * (px - geo[0])) / dTemp + 0.5)
    return [x,y]