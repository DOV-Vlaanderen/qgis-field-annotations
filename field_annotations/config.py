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
