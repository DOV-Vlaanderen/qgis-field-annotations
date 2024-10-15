from qgis.core import (
    QgsProject, QgsFillSymbol, QgsLineSymbol, QgsArrowSymbolLayer, QgsMarkerSymbol, Qgis, QgsPalLayerSettings,
    QgsTextFormat, QgsTextBufferSettings, QgsVectorLayerSimpleLabeling)
from qgis.PyQt import QtGui

from .translate import Translatable


class AnnotationLayerStyler:
    """Class with helper methods to style new annotation layers."""
    @staticmethod
    def styleLayer(layer):
        """Entry method to style a layer.

        Will call the relevant method depending on the layers geometry type.

        Parameters
        ----------
        layer : QgsVectorLayer
            Vector layer to style.
        """
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
        """Style a polygon layer.

        Parameters
        ----------
        layer : QgsVectorLayer
            Vector layer to style.
        """
        props = layer.renderer().symbol().symbolLayer(0).properties()
        props['color'] = '112,68,134,64'
        props['outline_color'] = '112,68,134,255'
        props['outline_width'] = '1'
        layer.renderer().setSymbol(
            QgsFillSymbol.createSimple(props))

    @staticmethod
    def styleLineLayer(layer):
        """Style a line layer.

        Parameters
        ----------
        layer : QgsVectorLayer
            Vector layer to style.
        """
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
        """Style a point layer.

        Parameters
        ----------
        layer : QgsVectorLayer
            Point layer to style.
        """
        props = layer.renderer().symbol().symbolLayer(0).properties()
        props['color'] = '112,68,134,64'
        props['outline_color'] = '112,68,134,255'
        props['size'] = '3.8'
        props['outline_width'] = '0.6'
        layer.renderer().setSymbol(
            QgsMarkerSymbol.createSimple(props))

    @staticmethod
    def styleLabels(layer, field='annotation'):
        """Style labels for the layer.

        Parameters
        ----------
        layer : QgsVectorLayer
            Vector layer to style.
        field : str, optional
            Field to use for the labels, by default 'annotation'
        """
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
    """Helper class to show annotation layers on the map."""
    def __init__(self, main):
        """Initialisation.

        Parameters
        ----------
        main : FieldAnnotations
            Reference to main plugin instance.
        """
        self.main = main

    def findLayer(self, layer):
        """Find the given layer in the current map view and return it.

        Will return an existing map layer that matches the source data provider URI of the given layer.

        Parameters
        ----------
        layer : QgsVectorLayer
            Vector layer to find.

        Returns
        -------
        QgsVectorLayer or None
            Existing vector layer matching the given layer, or None if none could be found.
        """
        projectLayers = QgsProject.instance().mapLayers().values()

        for projectLayer in projectLayers:
            if projectLayer.dataProvider().dataSourceUri() == layer.dataProvider().dataSourceUri():
                return projectLayer

    def hasLayer(self, layer):
        """Check if the current map view already has the given layer.

        Parameters
        ----------
        layer : QgsVectorLayer
            Vector layer to find.

        Returns
        -------
        bool
            True if the layer already exists, False otherwise.
        """
        return self.findLayer(layer) is not None

    def addLayer(self, layer):
        """Add the given vector layer to the map.

        Will return an existing layer if it was already added to the map.

        Parameters
        ----------
        layer : QgsVectorLayer
            Vector layer to add.

        Returns
        -------
        QgsVectorLayer
            Vector layer in the map view.
        """
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
