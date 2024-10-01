import os

from qgis.PyQt import QtCore
from qgis.core import (QgsFields, QgsField, QgsCoordinateReferenceSystem,
                       QgsVectorFileWriter, QgsCoordinateTransformContext, QgsVectorLayer, QgsDataProvider)
from qgis.core import QgsProject


class AnnotationDb:
    def __init__(self, main):
        self.main = main
        self.dbPath = None

        self.connectPopulate()

    def connectPopulate(self):
        QgsProject.instance().cleared.connect(self.populate)
        QgsProject.instance().readProject.connect(self.populate)

    def populate(self):
        basePath = QgsProject.instance().absolutePath()
        projectName = QgsProject.instance().baseName()

        if len(basePath) > 0 and len(projectName) > 0:
            self.dbPath = os.path.join(
                basePath, self.main.config.annotationFileName.format(projectName))
        else:
            self.dbPath = None

    def createLayer(self, layerName, geometryType):
        def createNewGpkgLayer(layerName, geometryType, fileExists):
            schema = QgsFields()

            schema.append(QgsField('layer', QtCore.QVariant.String))
            schema.append(QgsField('annotation', QtCore.QVariant.String))
            schema.append(QgsField('photoLocation', QtCore.QVariant.String))

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
                'Cannot create annotation layer without project.')

        if not os.path.exists(self.dbPath):
            createNewGpkgLayer(layerName, geometryType, fileExists=False)
        else:
            # check if layer already exists
            db = QgsVectorLayer(self.dbPath, "test", "ogr")
            layers = [l.split(QgsDataProvider.SUBLAYER_SEPARATOR)[1]
                      for l in db.dataProvider().subLayers()]

            if layerName not in layers:
                createNewGpkgLayer(layerName, geometryType, fileExists=True)

    def getLayer(self, layerName, geometryType):
        self.createLayer(layerName, geometryType)
