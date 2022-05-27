from PyQt5.QtCore import QObject, pyqtSignal
from rscder.utils.project import PairLayer


class BasicPlugin(QObject):

    send_message = pyqtSignal(str)

    '''
    插件基类
    ctx: 
    layer_tree: layer tree
    pair_canvas: pair canvas
    message_box: message box
    result_table: result table
    project: project instance
    mainwindow: mainwindow
    toolbar: toolbar
    statusbar: statusbar
    menu: menu
        file_menu: file menu
    '''
    @staticmethod
    def info():
        '''
        Plugin info
        '''
        raise NotImplementedError

    def __init__(self, ctx:dict) -> None:
        super().__init__(ctx['mainwindow'])
        self.ctx = ctx
        self.layer_tree = ctx['layer_tree']
        self.pair_canvas = ctx['pair_canvas']
        self.message_box = ctx['message_box']
        self.result_table = ctx['result_table']
        self.project = ctx['project']
        self.mainwindow = ctx['mainwindow']
        self.set_action()
        # self.project.layer_load.connect(self.on_data_load)
        self.project.project_init.connect(self.setup)
        self.send_message.connect(self.message_box.info)
        

    def set_action(self):
        '''
        When App start
        '''
        pass

    def setup(self):
        '''
        When project create
        '''
        pass

    def get_layer(self, layer_id)-> PairLayer:
        return self.project.layers[layer_id]

    def on_data_load(self, layer_id):
        '''
        When data load
        '''
        pass