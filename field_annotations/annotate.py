from qgis.PyQt import QtCore

from qgis.core import QgsWkbTypes


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
        return self.main.annotationDb.getLayer(self.getLayerName(), self.getGeometryType())

    def getLayerName(self):
        raise NotImplementedError

    def getGeometryType(self):
        raise NotImplementedError

    def createAnnotation(self):
        raise NotImplementedError


class PointAnnotator(AbstractAnnotator):
    def __init__(self, main):
        super().__init__(main)

    def getLayerName(self):
        return 'pointAnnotation'

    def getGeometryType(self):
        return QgsWkbTypes.Point

    def createAnnotation(self):
        layer = self.getLayer()
        print('creating point annotation')


class LineAnnotator(AbstractAnnotator):
    def __init__(self, main):
        super().__init__(main)

    def getLayerName(self):
        return 'lineAnnotation'

    def getGeometryType(self):
        return QgsWkbTypes.LineString

    def createAnnotation(self):
        layer = self.getLayer()
        print('creating line annotation')


class PolygonAnnotator(AbstractAnnotator):
    def __init__(self, main):
        super().__init__(main)

    def getLayerName(self):
        return 'polygonAnnotation'

    def getGeometryType(self):
        return QgsWkbTypes.Polygon

    def createAnnotation(self):
        layer = self.getLayer()
        print('creating polygon annotation')
