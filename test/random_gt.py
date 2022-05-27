from osgeo import gdal

pth = r"D:\CVEO\2021-12-22-CDGUI\LZY_DATA\未命名1\bcdm\AAA.-BBB._68252_cmi_otsu_bcdm.tif"
npth = r'D:\CVEO\2021-12-22-CDGUI\LZY_DATA\未命名1\bcdm\gt.tif'
ds = gdal.Open(pth)
out_ds = gdal.GetDriverByName('GTiff').Create(npth, ds.RasterXSize, ds.RasterYSize, 1, gdal.GDT_Byte)
out_ds.SetGeoTransform(ds.GetGeoTransform())
out_ds.SetProjection(ds.GetProjection())

data = ds.ReadAsArray()
data[100:200, 100:200] = 0
out_ds.GetRasterBand(1).WriteArray(data)


out_ds.FlushCache()
del out_ds
del ds