from qgis.PyQt import QtWidgets, QtGui
from qgis.core import QgsProject

from .annotate import PolygonAnnotator, PointAnnotator, LineAnnotator
from .translate import Translatable


class AbstractToolbarButton(QtWidgets.QToolButton):
    def __init__(self, main, annotator, parent=None):
        QtWidgets.QToolButton.__init__(self, parent)

        self.main = main
        self.annotator = annotator

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

        self.setChecked(self.main.annotationState.currentAnnotationType ==
                        self.annotator.getAnnotationType())

        if hasLayers and hasProjectPath and not self.main.annotationState.isAnnotating:
            self.setEnabled(True)
            self.setToolTip(self.getToolTipText())
        elif hasLayers and hasProjectPath and self.main.annotationState.isAnnotating:
            self.setEnabled(
                self.main.annotationState.currentAnnotationType == self.annotator.getAnnotationType())
            if self.isEnabled():
                self.setToolTip(self.getToolTipText())
            else:
                self.setToolTip(
                    self.tr('Already annotating, finish annotation first.'))
        elif not hasProjectPath:
            self.setEnabled(False)
            self.setToolTip(
                self.tr('Cannot annotate without project, save your project first.'))
        else:
            self.setEnabled(False)
            self.setToolTip(
                self.tr('No layers available to annotate, add a layer first.'))

    def run(self):
        if not self.main.annotationState.isAnnotating:
            self.annotator.createAnnotation()
        else:
            self.annotator.saveAnnotations()


class AnnotatePolygonButton(AbstractToolbarButton, Translatable):
    def __init__(self, main, parent=None):
        annotator = PolygonAnnotator(main)
        super().__init__(main, annotator, parent)

    def getIconPath(self):
        return ':/plugins/field_annotations/icons/draw_polygon.png'

    def getToolTipText(self):
        return self.tr('Add a polygon annotation')


class AnnotateLineButton(AbstractToolbarButton, Translatable):
    def __init__(self, main, parent=None):
        annotator = LineAnnotator(main)
        super().__init__(main, annotator, parent)

    def getIconPath(self):
        return ':/plugins/field_annotations/icons/draw_line.png'

    def getToolTipText(self):
        return self.tr('Add a line annotation')

class AnnotatePointButton(AbstractToolbarButton, Translatable):
    def __init__(self, main, parent=None):
        annotator = PointAnnotator(main)
        super().__init__(main, annotator, parent)

    def getIconPath(self):
        return ':/plugins/field_annotations/icons/draw_point.png'

    def getToolTipText(self):
        return self.tr('Add a point annotation')
