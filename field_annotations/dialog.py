from qgis.PyQt import QtWidgets, QtGui, QtCore

from .translate import Translatable


class NewAnnotationDialog(QtWidgets.QDialog, Translatable):
    def __init__(self, main, feature):
        """Initialise the dialog.

        Parameters
        ----------
        main : ThemeSwitcher
            Reference to main ThemeSwitcher instance
        """
        QtWidgets.QDialog.__init__(self)
        self.main = main
        self.feature = feature

        # self.iconPath = ':/plugins/theme_switcher/map.png'
        # self.setWindowIcon(QtGui.QIcon(self.iconPath))

        self.setWindowTitle(self.tr(u'New annotation'))
        self.setLayout(QtWidgets.QVBoxLayout())

        label = QtWidgets.QLabel(self.tr('Add annotation'))
        labelFont = label.font()
        labelFont.setBold(True)
        labelFont.setPointSize(12)
        label.setFont(labelFont)
        self.layout().addWidget(label)

        # self.layout().addWidget(ThemeSwitcherWidget(self, self.themeConfig))

        self.layout().addStretch()

        buttonBox = QtWidgets.QDialogButtonBox(self)
        buttonBox.setOrientation(QtCore.Qt.Orientation.Horizontal)
        buttonBox.setStandardButtons(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttonBox.button(
            QtWidgets.QDialogButtonBox.Ok).clicked.connect(self.accept)
        buttonBox.button(
            QtWidgets.QDialogButtonBox.Cancel).clicked.connect(self.reject)
        self.layout().addWidget(buttonBox)

        self.adjustSize()
