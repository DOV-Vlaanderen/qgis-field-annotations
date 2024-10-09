from enum import Enum
import time
from qgis.PyQt import QtCore

from qgis.core import QgsWkbTypes, QgsExpressionContextUtils, QgsEditFormConfig
from qgis.gui import QgsMapToolDigitizeFeature

from .translate import Translatable
from .dialog import NewAnnotationDialog

class AnnotationType(Enum):
    Point = 1
    Line = 2
    Polygon = 3


class AnnotationState(QtCore.QObject):
    stateChanged = QtCore.pyqtSignal()

    def __init__(self, main):
        super().__init__()
        self.main = main

        self.currentAnnotationType = None
        self.isAnnotating = False

    def setCurrentAnnotationType(self, annotationType):
        if annotationType != self.currentAnnotationType:
            self.currentAnnotationType = annotationType
            self.isAnnotating = self.currentAnnotationType is not None
            self.stateChanged.emit()

    def clearCurrentAnnotationType(self):
        if self.currentAnnotationType is not None:
            self.currentAnnotationType = None
            self.isAnnotating = False
            self.stateChanged.emit()


class AbstractAnnotator:
    def __init__(self, main):
        self.main = main

    def getLayer(self):
        layer = self.main.annotationDb.getLayer(
            self.getLayerName(), self.getHumanLayerName(), self.getGeometryType())
        return self.main.annotationView.addLayer(layer)

    def getLayerName(self):
        raise NotImplementedError

    def getHumanLayerName(self):
        raise NotImplementedError

    def getAnnotationType(self):
        raise NotImplementedError

    def getGeometryType(self):
        raise NotImplementedError

    def createAnnotation(self):
        layer = self.getLayer()
        self.main.annotationState.setCurrentAnnotationType(
            self.getAnnotationType())

        formConfig = layer.editFormConfig()
        formConfig.setSuppress(QgsEditFormConfig.SuppressOn)
        layer.setEditFormConfig(formConfig)

        if not layer.isEditable():
            layer.startEditing()

        layer.afterRollBack.connect(self.endAnnotate)
        layer.afterCommitChanges.connect(self.endAnnotate)

        self.main.iface.setActiveLayer(layer)
        self.main.iface.actionAddFeature().trigger()

        mapToolDigitize = self.main.iface.mapCanvas().mapTool()
        mapToolDigitize.digitizingCompleted.connect(self.featureAdded)
        self.main.iface.mapCanvas().setMapTool(mapToolDigitize)

    def featureAdded(self, feature):
        print('feature added', feature, feature.id())
        layer = self.getLayer()

        dlg = NewAnnotationDialog(self.main, feature)
        result = dlg.exec()

        if result == 1:
            feature.setAttribute(layer.fields().indexOf('author'), 'Roel')
            layer.dataProvider().addFeatures([feature])

    def stopAnnotating(self):
        layer = self.getLayer()
        if layer.isEditable():
            layer.rollBack()

    def endAnnotate(self):
        layer = self.getLayer()

        layer.afterRollBack.disconnect(self.endAnnotate)
        layer.afterCommitChanges.disconnect(self.endAnnotate)

        mapToolDigitize = self.main.iface.mapCanvas().mapTool()
        mapToolDigitize.digitizingCompleted.disconnect(self.featureAdded)

        if layer.isEditable():
            layer.endEditCommand()
        self.main.annotationState.clearCurrentAnnotationType()


class PointAnnotator(AbstractAnnotator, Translatable):
    def __init__(self, main):
        super().__init__(main)

    def getLayerName(self):
        return 'pointAnnotation'

    def getHumanLayerName(self):
        return self.tr('Point annotations')

    def getGeometryType(self):
        return QgsWkbTypes.Point

    def getAnnotationType(self):
        return AnnotationType.Point

class LineAnnotator(AbstractAnnotator, Translatable):
    def __init__(self, main):
        super().__init__(main)

    def getLayerName(self):
        return 'lineAnnotation'

    def getHumanLayerName(self):
        return self.tr('Line annotations')

    def getGeometryType(self):
        return QgsWkbTypes.LineString

    def getAnnotationType(self):
        return AnnotationType.Line


class PolygonAnnotator(AbstractAnnotator, Translatable):
    def __init__(self, main):
        super().__init__(main)

    def getLayerName(self):
        return 'polygonAnnotation'

    def getHumanLayerName(self):
        return self.tr('Polygon annotations')

    def getGeometryType(self):
        return QgsWkbTypes.Polygon

    def getAnnotationType(self):
        return AnnotationType.Polygon

    # def createAnnotation(self):
    #     layer = self.getLayer()
    #     # author = QgsExpressionContextUtils.globalScope().variable('user_full_name')
    #     print(f'creating polygon annotation in layer {layer}')
