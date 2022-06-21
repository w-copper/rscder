# 变化检测
王铜
CVEO团队

# 环境
Python3.7 + PyQt + QGIS

## 配置方式
conda create -f conda.yaml


# 打包方式

1. 打包keygen:

```
nuitka keygen.py --standalone --plugin-enable=qt-plugins --plugin-enable=numpy --show-progress --include-package=qgis --plugin-enable=pylint-warnings --output-dir=package --windows-disable-console --windows-icon-from-ico=logo.ico --no-pyi-file 
```

2. 打包主体：

```
nuitka RSCDer.py --standalone --plugin-enable=qt-plugins --plugin-enable=numpy --show-progress --include-package=qgis --plugin-enable=pylint-warnings --output-dir=package --windows-disable-console --windows-icon-from-ico=logo.ico --no-pyi-file 

```

3. 打包插件：

```
python setup.py
```

# 功能

1. 证书检查与生成
   1. 基于MAC地址与过期时间进行证书生成，启动时检查证书，过期则退出
2. 工程管理
   1. 以工程为单位进行数据管理与生产
   2. 提供工程保存与导入功能
   3. 提供多种格式的栅格数据导入（TIF、PNG、BMP、JPG）等
   4. 提供矢量数据导入
3. 基本工具
   1. 双视图同步浏览
   2. 格网展示
