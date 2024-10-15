from qgis.core import (
    QgsProject, QgsFillSymbol, QgsLineSymbol, QgsArrowSymbolLayer, QgsMarkerSymbol, Qgis, QgsPalLayerSettings,
    QgsTextFormat, QgsTextBufferSettings, QgsVectorLayerSimpleLabeling)
from qgis.PyQt import QtGui

from .translate import Translatable


class AnnotationLayerStyler:
    @staticmethod
    def styleLayer(layer):
        geometryType = layer.geometryType()

        if geometryType == Qgis.GeometryType.Polygon:
            AnnotationLayerStyler.stylePolygonLayer(layer)
        elif geometryType == Qgis.GeometryType.Line:
            AnnotationLayerStyler.styleLineLayer(layer)
        elif geometryType == Qgis.GeometryType.Point:
            AnnotationLayerStyler.stylePointLayer(layer)

        AnnotationLayerStyler.styleLabels(layer)

    @staticmethod
    def stylePolygonLayer(layer):
        props = layer.renderer().symbol().symbolLayer(0).properties()
        props['color'] = '112,68,134,64'
        props['outline_color'] = '112,68,134,255'
        props['outline_width'] = '1'
        layer.renderer().setSymbol(
            QgsFillSymbol.createSimple(props))

    @staticmethod
    def styleLineLayer(layer):
        props = layer.renderer().symbol().symbolLayer(0).properties()
        lineSymbol = QgsLineSymbol.createSimple(props)

        arrow = QgsArrowSymbolLayer.create(
            {'is_curved': '0', 'is_repeated': '1'})
        lineSymbol.changeSymbolLayer(0, arrow)

        props = arrow.subSymbol().symbolLayer(0).properties()
        props['color'] = '112,68,134,255'
        props['outline_color'] = '112,68,134,255'
        props['outline_width'] = '0'
        props['outline_style'] = 'no'
        arrow.setSubSymbol(QgsFillSymbol.createSimple(props))

        layer.renderer().setSymbol(lineSymbol)

    @staticmethod
    def stylePointLayer(layer):
        props = layer.renderer().symbol().symbolLayer(0).properties()
        props['color'] = '112,68,134,64'
        props['outline_color'] = '112,68,134,255'
        props['size'] = '3.8'
        props['outline_width'] = '0.6'
        layer.renderer().setSymbol(
            QgsMarkerSymbol.createSimple(props))

    @staticmethod
    def styleLabels(layer, field='annotation'):
        label_settings = QgsPalLayerSettings()
        label_settings.enabled = True
        label_settings.fieldName = field

        if layer.geometryType() == Qgis.GeometryType.Line:
            label_settings.placement = Qgis.LabelPlacement.Curved
        else:
            label_settings.placement = Qgis.LabelPlacement.AroundPoint

        label_format = QgsTextFormat()
        label_format.setSize(10)
        label_format.setNamedStyle('Regular')
        label_format.setColor(QtGui.QColor(50, 20, 65, 255))

        label_buffer = QgsTextBufferSettings()
        label_buffer.setEnabled(True)
        label_buffer.setSize(1)
        label_buffer.setColor(QtGui.QColor(255, 255, 255, 192))
        label_format.setBuffer(
            label_buffer
        )
        label_settings.setFormat(
            label_format
        )

        layer.setLabeling(QgsVectorLayerSimpleLabeling(label_settings))
        layer.setLabelsEnabled(True)


class AnnotationView(Translatable):
    def __init__(self, main):
        self.main = main

    def findLayer(self, layer):
        projectLayers = QgsProject.instance().mapLayers().values()

        for projectLayer in projectLayers:
            if projectLayer.dataProvider().dataSourceUri() == layer.dataProvider().dataSourceUri():
                return projectLayer

    def hasLayer(self, layer):
        return self.findLayer(layer) is not None

    def addLayer(self, layer):
        if not self.hasLayer(layer):
            QgsProject.instance().addMapLayer(layer, addToLegend=False)

            root = QgsProject.instance().layerTreeRoot()
            annotationGroup = root.findGroup(self.tr('Field annotations'))

            if annotationGroup is None:
                annotationGroup = root.insertGroup(
                    0, self.tr('Field annotations'))

            AnnotationLayerStyler.styleLayer(layer)
            annotationGroup.addLayer(layer)
            return layer
        else:
            return self.findLayer(layer)
