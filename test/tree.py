from PyQt5 import QtCore
from PyQt5.QtWidgets import QDesktopWidget
import sys
from PyQt5.QtWidgets import *

# import tree  # tree.py文件


class myTreeWidget:
    def __init__(self, objTree):
        self.myTree = objTree
        # 设置列数
        self.myTree.setColumnCount(1)
        # 设置树形控件头部的标题
        self.myTree.setHeaderLabels(['机构列表'])

        # 设置根节点
        self.root = QTreeWidgetItem(self.myTree)
        self.root.setText(0, '本单位')

        # 设置树形控件的列的宽度
        self.myTree.setColumnWidth(0, 100)

        # 设置子节点1
        child1 = QTreeWidgetItem(self.root)
        child1.setText(0, '市场部')
        self.root.addChild(child1)

        # 设置子节点11
        child11 = QTreeWidgetItem(child1)
        child11.setText(0, '销售班')

        # 设置子节点2
        child2 = QTreeWidgetItem(self.root)
        child2.setText(0, '财务部')

        # 设置子节点21
        child21 = QTreeWidgetItem(child2)
        child21.setText(0, '财务一班')

        # 加载根节点的所有属性与子控件
        self.myTree.addTopLevelItem(self.root)

        # TODO 优化2 给节点添加响应事件
        self.myTree.clicked.connect(self.onClicked)

        # 节点全部展开
        self.myTree.expandAll()

    def onClicked(self):
        item = self.myTree.currentItem()
        print('Key=%s' % (item.text(0)))


class MyPyQTMainForm(QMainWindow):
    """
    主界面
    """

    def __init__(self):
        """
        初始化
        """
        super(MyPyQTMainForm, self).__init__()
        # self.setupUi(self)
        # 创建树控件对象
        layout = QVBoxLayout()
    
        tree_widget = QTreeWidget()
        # layout.addWidget(tree_widget)
        # self.setLayout(layout)
        self.layout().addWidget(tree_widget)
        self.myTreeTest = myTreeWidget(tree_widget)
        # self.myTreeTest = myTreeWidget(self.treeWidget)

    def center(self):
        """
        定义一个函数使得窗口居中显示
        """
        # 获取屏幕坐标系
        screen = QDesktopWidget().screenGeometry()
        # 获取窗口坐标系
        size = self.geometry()
        newLeft = (screen.width() - size.width()) / 2
        newTop = (screen.height() - size.height()) / 2
        self.move(int(newLeft), int(newTop))

    def addNode(self):
        """
        添加节点
        """
        print('--- addTreeNode ---')
        item = self.myTreeTest.myTree.currentItem()
        node = QTreeWidgetItem(item)
        node.setText(0, '后勤部')

    def deleteNode(self):
        """
        删除节点
        """
        print('--- delTreeNode ---')
        item = self.myTreeTest.myTree.currentItem()
        root = self.myTreeTest.myTree.invisibleRootItem()
        for item in self.myTreeTest.myTree.selectedItems():
            (item.parent() or root).removeChild(item)

    def modifyNode(self):
        """
        修改节点
        """
        print('--- modifyTreeNode ---')
        item = self.myTreeTest.myTree.currentItem()
        item.setText(0, '办公室')


"""
主函数
"""
if __name__ == '__main__':
    app = QApplication(sys.argv)
    myPyMainForm = MyPyQTMainForm()
    # 主窗口显示在屏幕中间
    myPyMainForm.center()

    # 禁止最大化按钮
    myPyMainForm.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint | QtCore.Qt.WindowCloseButtonHint)
    # 禁止拉伸窗口大小
    myPyMainForm.setFixedSize(myPyMainForm.width(), myPyMainForm.height())

    # 显示主界面
    myPyMainForm.show()
    sys.exit(app.exec_())