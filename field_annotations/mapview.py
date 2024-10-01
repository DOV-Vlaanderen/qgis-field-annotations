from qgis.core import QgsProject, QgsFillSymbol, QgsLineSymbol, QgsArrowSymbolLayer, QgsMarkerSymbol, Qgis

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
            {'is_curved': '1', 'is_repeated': '1'})
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
        print(props)
        props['color'] = '112,68,134,64'
        props['outline_color'] = '112,68,134,255'
        props['size'] = '3.8'
        props['outline_width'] = '0.6'
        layer.renderer().setSymbol(
            QgsMarkerSymbol.createSimple(props))


class AnnotationView(Translatable):
    def __init__(self, main):
        self.main = main

    def hasLayer(self, layer):
        layers = QgsProject.instance().mapLayers().values()

        return layer.dataProvider().dataSourceUri() in [
            layer.dataProvider().dataSourceUri()
            for layer in layers if layer.dataProvider() is not None
        ]

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
