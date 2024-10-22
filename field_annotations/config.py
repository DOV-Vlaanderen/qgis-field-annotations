import os
import re

from qgis.PyQt import QtCore

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

        # self.photoAppCommand = os.path.join(
        #     os.environ['SYSTEMROOT'], 'explorer.exe') + \
        #     " shell:AppsFolder\\Microsoft.WindowsCamera_8wekyb3d8bbwe!App"

        # self.photoFileLocation = os.path.join(
        #     os.environ['USERPROFILE'], 'Pictures', 'Camera Roll')

        # self.photoFileFilter = re.compile(
        #     r'^WIN_([0-9]{8}_[0-9]{2}_[0-9]{2}_[0-9]{2}).*\.jpg$')
