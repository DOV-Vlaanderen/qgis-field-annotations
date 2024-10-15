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

    def getLayer(self, layerName, humanLayerName, geometryType):
        """Get required data layer based on the parameters.

        Will create the database and the layer if it does not already exist.

        Parameters
        ----------
        layerName : str
            Technical name of the layer.
        humanLayerName : str
            Human readable name of the layer.
        geometryType : QgsWkbTypes
            Geometry type of the layer.
        """
        def createNewGpkgLayer(layerName, geometryType, fileExists):
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
            fileExists : bool
                True if the database already exists, False otherwise.

            Returns
            -------
            QgsVectorLayer
                Vector layer instance with the required setup.
            """
            schema = QgsFields()

            schema.append(QgsField('annotation', QtCore.QVariant.String))
            schema.append(QgsField('dateCreated', QtCore.QVariant.DateTime))
            schema.append(QgsField('author', QtCore.QVariant.String))

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

        if not os.path.exists(self.dbPath):
            createNewGpkgLayer(layerName, geometryType, fileExists=False)
        else:
            # check if layer already exists in database
            db = QgsVectorLayer(self.dbPath, "test", "ogr")
            layers = [l.split(QgsDataProvider.SUBLAYER_SEPARATOR)[1]
                      for l in db.dataProvider().subLayers()]

            if layerName not in layers:
                createNewGpkgLayer(layerName, geometryType, fileExists=True)

        return QgsVectorLayer(f'{self.dbPath}|layername={layerName}', humanLayerName, "ogr")
