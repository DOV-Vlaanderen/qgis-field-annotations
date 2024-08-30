from qgis.PyQt import QtWidgets, QtGui

from .translate import Translatable


class AbstractToolbarButton(QtWidgets.QToolButton):
    def __init__(self, main, parent=None):
        QtWidgets.QToolButton.__init__(self, parent)

        self.main = main
        self.setIcon(QtGui.QIcon(self.getIconPath()))
        self.setToolTip(self.getToolTipText())

        self.clicked.connect(self.run)
        self.populate()

    def getIconPath(self):
        raise NotImplementedError

    def getToolTipText(self):
        raise NotImplementedError

    def populate(self):
        self.setEnabled(True)

    def run(self):
        raise NotImplementedError


class AnnotatePolygonButton(AbstractToolbarButton, Translatable):
    def __init__(self, main, parent=None):
        super().__init__(main, parent)

    def getIconPath(self):
        return ':/plugins/field_annotations/icons/draw_polygon.png'

    def getToolTipText(self):
        return self.tr('Add a polygon annotation')

    def run(self):
        print('add polygon annotation')


class AnnotateLineButton(AbstractToolbarButton, Translatable):
    def __init__(self, main, parent=None):
        super().__init__(main, parent)

    def getIconPath(self):
        return ':/plugins/field_annotations/icons/draw_line.png'

    def getToolTipText(self):
        return self.tr('Add a line annotation')

    def run(self):
        print('add line annotation')


class AnnotatePointButton(AbstractToolbarButton, Translatable):
    def __init__(self, main, parent=None):
        super().__init__(main, parent)

    def getIconPath(self):
        return ':/plugins/field_annotations/icons/draw_point.png'

    def getToolTipText(self):
        return self.tr('Add a point annotation')

    def run(self):
        print('add point annotation')
