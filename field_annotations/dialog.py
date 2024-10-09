from qgis.PyQt import QtWidgets, QtGui, QtCore

from .translate import Translatable


class NewAnnotationDialog(QtWidgets.QDialog, Translatable):
    def __init__(self, main):
        """Initialise the dialog.

        Parameters
        ----------
        main : ThemeSwitcher
            Reference to main ThemeSwitcher instance
        """
        QtWidgets.QDialog.__init__(self)
        self.main = main

        # self.iconPath = ':/plugins/theme_switcher/map.png'
        # self.setWindowIcon(QtGui.QIcon(self.iconPath))

        self.setWindowTitle(self.tr(u'New annotation'))
