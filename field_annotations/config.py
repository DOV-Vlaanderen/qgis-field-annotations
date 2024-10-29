import os
import re

from qgis.PyQt import QtCore
from qgis.core import QgsProject

from .translate import Translatable


class Config(QtCore.QObject, Translatable):
    """Class to centralise all common configuration."""
    configChanged = QtCore.pyqtSignal()

    def __init__(self, main):
        """Initialise the configuration.

        Parameters
        ----------
        main : FieldAnnotations
            Reference to main plugin instance.
        """
        super().__init__()
        self.main = main

        self.annotationFileName = '{}-qgis-field-annotations.gpkg'
        self.photoBasePath = '{}-qgis-field-photos'

        self.dbPath = None
        self.photoPath = None

        # self.photoAppCommand = os.path.join(
        #     os.environ['SYSTEMROOT'], 'explorer.exe') + \
        #     " shell:AppsFolder\\Microsoft.WindowsCamera_8wekyb3d8bbwe!App"

        # self.photoFileLocation = os.path.join(
        #     os.environ['USERPROFILE'], 'Pictures', 'Camera Roll')

        # self.photoFileFilter = re.compile(
        #     r'^WIN_([0-9]{8}_[0-9]{2}_[0-9]{2}_[0-9]{2}).*\.jpg$')

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
                basePath, self.annotationFileName.format(projectName))
            self.photoPath = os.path.join(
                basePath, self.photoBasePath.format(projectName))
        else:
            self.dbPath = None
            self.photoPath = None
