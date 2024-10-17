import re

from qgis.core import (
    QgsProject, QgsFillSymbol, QgsLineSymbol, QgsArrowSymbolLayer, QgsMarkerSymbol, Qgis, QgsPalLayerSettings,
    QgsTextFormat, QgsTextBufferSettings, QgsVectorLayerSimpleLabeling)
from qgis.PyQt import QtGui

from .annotate import AnnotationViewMode
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

        self.re_subsetString = re.compile(r'\|subset=[^|]*')

        self.connectPopulate()
        self.populate()

    def connectPopulate(self):
        projectInstance = QgsProject.instance()

        projectInstance.cleared.connect(self.populate)
        projectInstance.readProject.connect(self.populate)
        projectInstance.projectSaved.connect(self.populate)
        projectInstance.layersAdded.connect(self.populate)
        projectInstance.layersRemoved.connect(self.populate)

        layerTreeRoot = projectInstance.layerTreeRoot()
        layerTreeRoot.visibilityChanged.connect(self.populate)

        self.main.iface.mapCanvas().scaleChanged.connect(self.populate)
        self.main.annotationState.stateChanged.connect(self.populate)

    def populate(self):
        currentMode = self.main.annotationState.currentAnnotationViewMode

        if currentMode == AnnotationViewMode.AllAnnotations:
            subsetString = None
        elif currentMode == AnnotationViewMode.VisibleLayers:
            subsetString = '"layerUri" is null'
            projectLayers = QgsProject.instance().mapLayers().values()
            for projectLayer in projectLayers:
                if self.isAnnotatableLayer(projectLayer):
                    subsetString += f" or \"layerUri\"='{self.getLayerUri(projectLayer, escape=True)}'"

        for annotationLayer in self.main.annotationDb.listAnnotationLayers():
            annotationLayer.setSubsetString(subsetString)

    def stripSubsetString(self, dataSourceUri):
        return self.re_subsetString.sub('', dataSourceUri)

    # def isDataSourceUriEqual(self, ds1, ds2):
    #     url1 = urlparse(self.stripSubsetString(ds1))
    #     url2 = urlparse(self.stripSubsetString(ds2))
    #     return url1 == url2

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
            if self.stripSubsetString(projectLayer.dataProvider().dataSourceUri()) == \
                    self.stripSubsetString(layer.dataProvider().dataSourceUri()):
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
        layerTreeRoot = QgsProject.instance().layerTreeRoot()
        annotationGroup = layerTreeRoot.findGroup(self.tr('Field annotations'))

        if annotationGroup is None:
            annotationGroup = layerTreeRoot.insertGroup(
                0, self.tr('Field annotations'))
        else:
            annotationGroup.setItemVisibilityChecked(True)

        if not self.hasLayer(layer):
            QgsProject.instance().addMapLayer(layer, addToLegend=False)
            AnnotationLayerStyler.styleLayer(layer)
            annotationGroup.addLayer(layer)
            return layer
        else:
            lyr = self.findLayer(layer)
            layerTreeRoot.findLayer(lyr).setItemVisibilityChecked(True)
            return lyr

    def isAnnotatableLayer(self, layer):
        """Checks whether the layer is an annotatable layer.

        Parameters
        ----------
        layer : QgsMapLayer
            The layer to evaluate.

        Returns
        -------
        bool
            True if the layer is annotable, False otherwise.
        """
        if layer.dataProvider().name() == 'memory':
            return False

        if self.main.annotationDb.isAnnotationLayer(layer):
            return False

        layerTreeRoot = QgsProject.instance().layerTreeRoot()
        layerTreeLayer = layerTreeRoot.findLayer(layer)
        if layerTreeLayer is None or not layerTreeLayer.isVisible():
            return False

        mapCanvas = self.main.iface.mapCanvas()
        return layer.isInScaleRange(mapCanvas.scale())

    def listAnnotatableLayers(self):
        """List all the annotatable layers in the current project.

        Returns
        -------
        list of QgsMapLayer
            List of all layers in the current project that can be annotated.
        """
        layerTreeRoot = QgsProject.instance().layerTreeRoot()
        return [l for l in layerTreeRoot.layerOrder() if self.isAnnotatableLayer(l)]

    def getLayerUri(self, layer, escape=False):
        dataProvider = layer.dataProvider()
        layerDataSourceUri = self.stripSubsetString(
            dataProvider.dataSourceUri())
        if escape:
            layerDataSourceUri = layerDataSourceUri.replace('\'', '\'\'')
        return f'{dataProvider.name()}://{layerDataSourceUri}'
