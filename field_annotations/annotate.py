from qgis.PyQt import QtCore

from qgis.core import QgsWkbTypes, QgsExpressionContextUtils

from .translate import Translatable

class AnnotationState(QtCore.QObject):
    stateChanged = QtCore.pyqtSignal()

    def __init__(self, main):
        super().__init__()
        self.main = main

        self.isAnnotating = False

    def setAnnotating(self, state):
        if state != self.isAnnotating:
            self.isAnnotating = state
            self.stateChanged.emit()


class AbstractAnnotator:
    def __init__(self, main):
        self.main = main

    def getLayer(self):
        layer = self.main.annotationDb.getLayer(
            self.getLayerName(), self.getHumanLayerName(), self.getGeometryType())
        self.main.annotationView.addLayer(layer)

    def getLayerName(self):
        raise NotImplementedError

    def getHumanLayerName(self):
        raise NotImplementedError

    def getGeometryType(self):
        raise NotImplementedError

    def createAnnotation(self):
        raise NotImplementedError


class PointAnnotator(AbstractAnnotator, Translatable):
    def __init__(self, main):
        super().__init__(main)

    def getLayerName(self):
        return 'pointAnnotation'

    def getHumanLayerName(self):
        return self.tr('Point annotations')

    def getGeometryType(self):
        return QgsWkbTypes.Point

    def createAnnotation(self):
        layer = self.getLayer()
        print('creating point annotation')


class LineAnnotator(AbstractAnnotator, Translatable):
    def __init__(self, main):
        super().__init__(main)

    def getLayerName(self):
        return 'lineAnnotation'

    def getHumanLayerName(self):
        return self.tr('Line annotations')

    def getGeometryType(self):
        return QgsWkbTypes.LineString

    def createAnnotation(self):
        layer = self.getLayer()
        print('creating line annotation')


class PolygonAnnotator(AbstractAnnotator, Translatable):
    def __init__(self, main):
        super().__init__(main)

    def getLayerName(self):
        return 'polygonAnnotation'

    def getHumanLayerName(self):
        return self.tr('Polygon annotations')

    def getGeometryType(self):
        return QgsWkbTypes.Polygon

    def createAnnotation(self):
        layer = self.getLayer()
        # author = QgsExpressionContextUtils.globalScope().variable('user_full_name')
        print(f'creating polygon annotation in layer {layer}')
