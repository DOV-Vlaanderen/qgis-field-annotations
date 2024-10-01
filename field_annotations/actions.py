from qgis.PyQt import QtWidgets, QtGui
from qgis.core import QgsProject

from .annotate import PolygonAnnotator, PointAnnotator, LineAnnotator
from .translate import Translatable


class AbstractToolbarButton(QtWidgets.QToolButton):
    def __init__(self, main, parent=None):
        QtWidgets.QToolButton.__init__(self, parent)

        self.main = main
        self.setIcon(QtGui.QIcon(self.getIconPath()))
        self.setToolTip(self.getToolTipText())
        self.setCheckable(True)

        self.connectPopulate()

        self.clicked.connect(self.run)
        self.populate()

    def getIconPath(self):
        raise NotImplementedError

    def getToolTipText(self):
        raise NotImplementedError

    def connectPopulate(self):
        projectInstance = QgsProject.instance()

        projectInstance.cleared.connect(self.populate)
        projectInstance.readProject.connect(self.populate)
        projectInstance.projectSaved.connect(self.populate)
        projectInstance.layersAdded.connect(self.populate)
        projectInstance.layersRemoved.connect(self.populate)
        self.main.annotationState.stateChanged.connect(self.populate)

    def populate(self):
        hasLayers = len(QgsProject.instance().mapLayers()) > 0
        hasProjectPath = len(QgsProject.instance().absolutePath()) > 0

        print('is annotating', self.main.annotationState.isAnnotating)

        if hasLayers and hasProjectPath and not self.main.annotationState.isAnnotating:
            self.setEnabled(True)
            self.setToolTip(self.getToolTipText())
        elif not hasProjectPath:
            self.setEnabled(False)
            self.setToolTip(
                self.tr('Cannot annotate without project, save your project first.'))
        elif hasLayers:
            self.setEnabled(False)
            self.setToolTip(
                self.tr('Already annotating, finish annotation first.'))
        else:
            self.setEnabled(False)
            self.setToolTip(
                self.tr('No layers available to annotate, add a layer first.'))

    def run(self):
        self.setChecked(True)
        self.main.annotationState.setAnnotating(True)

        self.annotator.createAnnotation()

        self.main.annotationState.setAnnotating(False)
        self.setChecked(False)


class AnnotatePolygonButton(AbstractToolbarButton, Translatable):
    def __init__(self, main, parent=None):
        super().__init__(main, parent)
        self.annotator = PolygonAnnotator(main)

    def getIconPath(self):
        return ':/plugins/field_annotations/icons/draw_polygon.png'

    def getToolTipText(self):
        return self.tr('Add a polygon annotation')


class AnnotateLineButton(AbstractToolbarButton, Translatable):
    def __init__(self, main, parent=None):
        super().__init__(main, parent)
        self.annotator = LineAnnotator(main)

    def getIconPath(self):
        return ':/plugins/field_annotations/icons/draw_line.png'

    def getToolTipText(self):
        return self.tr('Add a line annotation')

class AnnotatePointButton(AbstractToolbarButton, Translatable):
    def __init__(self, main, parent=None):
        super().__init__(main, parent)
        self.annotator = PointAnnotator(main)

    def getIconPath(self):
        return ':/plugins/field_annotations/icons/draw_point.png'

    def getToolTipText(self):
        return self.tr('Add a point annotation')
