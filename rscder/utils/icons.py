from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QObject
from .misc import singleton

@singleton
class IconInstance(QObject):

    def __init__(self, parent) -> None:
        super().__init__(parent)

        self.GRID_ON = QIcon('./icons/格网开.png')
        self.AI_DETECT = QIcon('./icons/AI变化检测.png')
        self.EVALUATION = QIcon('./icons/精度评估.png')   
        self.SPLASH = QIcon('./icons/splash.png')
        self.HELP = QIcon('./icons/帮助.png') 
        self.LOGO = QIcon('./icons/变化检测.png')
        self.CHANGE = QIcon('./icons/变化检测.png')
        self.OK = QIcon('./icons/ok.svg')
        self.CANCEL = QIcon('./icons/cancel.svg')
        self.PLUGINS = QIcon('./icons/插件配置.png')
        self.CREATE = QIcon('./icons/创建工程.png')
        self.OPEN = QIcon('./icons/打开工程.png')
        self.SAVE = QIcon('./icons/工程保存.png')
        self.TOOLS = QIcon('./icons/工具.png')
        self.TOOLBOX = QIcon('./icons/工具箱.png')
        self.LOCATION = QIcon('./icons/定位.png')
        self.UNSUPERVISED = QIcon('./icons/非监督.png')
        self.ROAD_CHANGE = QIcon('./icons/道路变化.png')
        self.LANDSIDE = QIcon('./icons/海岸变化.png')
        self.SUPERVISED = QIcon('./icons/监督.png')
        self.VIEW_SETTING = QIcon('./icons/视图设置.png')
        self.FILTER = QIcon('./icons/滤波.png')
        self.PAN = QIcon('./icons/平移.png')
        self.CLOUD_REMOVE = QIcon('./icons/去云.png')
        self.WEAK_SUPERVISED = QIcon('./icons/弱监督.png')
        self.DELETE = QIcon('./icons/删除.png')
        self.VECTOR = QIcon('./icons/矢量.png')
        self.WATER_CHANGE = QIcon('./icons/水体变化.png')
        self.ZOOM_TO = QIcon('./icons/缩放到.png')

        self.LAYER = QIcon('./icons/图层.png')
        self.GRID_OFF = QIcon('./icons/格网关闭.png')
        self.DOCUMENT = QIcon('./icons/文档.png')
        self.FILE = QIcon('./icons/文件.png')
        self.SELECT = QIcon('./icons/选择要素.png')
        self.RASTER = QIcon('./icons/影像.png')
        self.VEGETATION = QIcon('./icons/植被变化.png')
        self.NOISE = QIcon('./icons/噪声处理.png')

        self.DATA_LOAD = QIcon('./icons/数据加载.png')
    
        self.EXCIT = QIcon('./icons/退出.png')

        self.ZOOM_IN = QIcon('./icons/放大.png')
        self.ZOOM_OUT = QIcon('./icons/缩小.png')