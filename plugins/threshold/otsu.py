import numpy as np

def OTSU(hist):
   
    u1=0.0#背景像素的平均灰度值
    u2=0.0#前景像素的平均灰度值
    th=0.0

    #总的像素数目
    PixSum= np.sum(hist)
    #各灰度值所占总像素数的比例
    PixRate=hist / PixSum
    #统计各个灰度值的像素个数
    Max_var = 0
    #确定最大类间方差对应的阈值
    GrayScale = len(hist)
    for i in range(1,len(hist)):#从1开始是为了避免w1为0.
        u1_tem=0.0
        u2_tem=0.0
        #背景像素的比列
        w1=np.sum(PixRate[:i])
        #前景像素的比例
        w2=1.0-w1
        if w1==0 or w2==0:
            pass
        else:#背景像素的平均灰度值
            for m in range(i):
                u1_tem=u1_tem+PixRate[m]*m
            u1 = u1_tem * 1.0 / w1
             #前景像素的平均灰度值
            for n in range(i,GrayScale):
                u2_tem = u2_tem + PixRate[n]*n
            u2 = u2_tem / w2
            #print(u1)
            #类间方差公式：G=w1*w2*(u1-u2)**2
            tem_var=w1*w2*np.power((u1-u2),2)
            #print(tem_var)
            #判断当前类间方差是否为最大值。
            if Max_var<tem_var:
                Max_var=tem_var#深拷贝，Max_var与tem_var占用不同的内存空间。
                th=i
    return th 
