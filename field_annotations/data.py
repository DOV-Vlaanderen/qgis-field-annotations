import os

from qgis.PyQt import QtCore
from qgis.core import (QgsFields, QgsField, QgsCoordinateReferenceSystem,
                       QgsVectorFileWriter, QgsCoordinateTransformContext, QgsVectorLayer, QgsDataProvider)
from qgis.core import QgsProject


class AnnotationDb:
    """Class managing the annotation database and layers."""
    def __init__(self, main):
        """Initialisation.

        Parameters
        ----------
        main : FieldAnnotations
            Reference to main plugin instance.
        """
        self.main = main
        self.dbPath = None

        self.connectPopulate()
        self.populate()

    def connectPopulate(self):
        """Connect the populate method to the necessary signals."""
        QgsProject.instance().cleared.connect(self.populate)
        QgsProject.instance().readProject.connect(self.populate)
        QgsProject.instance().projectSaved.connect(self.populate)

    def populate(self):
        """Set the database path according to project state."""
        basePath = QgsProject.instance().absolutePath()
        projectName = QgsProject.instance().baseName()

        if len(basePath) > 0 and len(projectName) > 0:
            self.dbPath = os.path.join(
                basePath, self.main.config.annotationFileName.format(projectName))
        else:
            self.dbPath = None

    def getLayer(self, annotator):
        """Get required data layer based on given annotator.

        Will create the database and the layer if it does not already exist.

        Parameters
        ----------
        annotator : AbstractAnnotator
            Annotator instance to get the layer for.
        """
        def createNewGpkgLayer(layerName, geometryType, fields, fileExists):
            """Create a new geopackage layer.

            If the database does not exist already, it will create the database and the layer.
            If the database already exists, it will add the layer to it.
            It the database and layer already exists, it will overwrite the layer.

            Parameters
            ----------
            layerName : str
                Technical name of the layer.
            geometryType : QgsWkbTypes
                Geometry type of the layer.
            fields : list of QgsField
                List of fields for the layer.
            fileExists : bool
                True if the database already exists, False otherwise.

            Returns
            -------
            QgsVectorLayer
                Vector layer instance with the required setup.
            """
            schema = QgsFields()

            for field in fields:
                schema.append(field)

            crs = QgsCoordinateReferenceSystem('epsg:4326')
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "GPKG"
            options.fileEncoding = 'utf8'
            options.layerName = layerName
            if fileExists:
                options.actionOnExistingFile = QgsVectorFileWriter.ActionOnExistingFile.CreateOrOverwriteLayer

            QgsVectorFileWriter.create(
                fileName=self.dbPath,
                fields=schema,
                geometryType=geometryType,
                srs=crs,
                transformContext=QgsCoordinateTransformContext(),
                options=options)

        if self.dbPath is None:
            raise RuntimeError(
                'Cannot get annotation layer without project.')

        layerName = annotator.getLayerName()
        humanLayerName = annotator.getHumanLayerName()
        geometryType = annotator.getGeometryType()
        fields = annotator.getFields()

        if not os.path.exists(self.dbPath):
            createNewGpkgLayer(layerName, geometryType,
                               fields, fileExists=False)
        else:
            # check if layer already exists in database
            db = QgsVectorLayer(self.dbPath, "test", "ogr")
            layers = [l.split(QgsDataProvider.SUBLAYER_SEPARATOR)[1]
                      for l in db.dataProvider().subLayers()]

            if layerName not in layers:
                createNewGpkgLayer(layerName, geometryType,
                                   fields, fileExists=True)

        return QgsVectorLayer(f'{self.dbPath}|layername={layerName}', humanLayerName, "ogr")

    def isAnnotationLayer(self, layer):
        """Checks whether the given layer is an annotation layer.

        Parameters
        ----------
        layer : QgsMapLayer
            Layer to check

        Returns
        -------
        bool
            True if the layer is used to store annotations, False otherwise.
        """
        if layer.dataProvider().name() != 'ogr':
            return False

        if self.dbPath is None:
            return False

        return layer.dataProvider().dataSourceUri().startswith(self.dbPath)

    def listAnnotationLayers(self):
        """Return a list of all annotation layers in the current project.

        Returns
        -------
        list of QgsVectorLayer
            List of layers used to store annotations.
        """
        return [l for l in QgsProject.instance().mapLayers().values() if self.isAnnotationLayer(l)]
