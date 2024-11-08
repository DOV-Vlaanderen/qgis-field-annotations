import os
import re

from qgis.PyQt import QtCore, QtWidgets, QtGui
from qgis.core import QgsProject, QgsSettings
from qgis.gui import QgsFileWidget

from .translate import Translatable
from .widgets import QLabelBold, QLabelItalic


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
        self.dbPath = None

        self.photoConfig = PhotoConfig(self)

        self.connectPopulate()
        self.populate()

    def connectPopulate(self):
        """Connect the populate method to the necessary signals."""
        QgsProject.instance().cleared.connect(self.populate)
        QgsProject.instance().readProject.connect(self.populate)
        QgsProject.instance().projectSaved.connect(self.populate)

    def populate(self):
        """Set the database and photo paths according to project state."""
        basePath = QgsProject.instance().absolutePath()
        projectName = QgsProject.instance().baseName()

        if len(basePath) > 0 and len(projectName) > 0:
            self.dbPath = os.path.join(
                basePath, self.annotationFileName.format(projectName))
        else:
            self.dbPath = None

        self.photoConfig.populate(basePath, projectName)


class PhotoConfigPresetWindows10:

    # self.photoFileFilter = re.compile(
    #     r'^WIN_([0-9]{8}_[0-9]{2}_[0-9]{2}_[0-9]{2}).*\.jpg$')

    @staticmethod
    def isEnabled():
        return 'SYSTEMROOT' in os.environ and 'USERPROFILE' in os.environ

    @staticmethod
    def getPhotoAppCommand():
        if 'SYSTEMROOT' in os.environ:
            return os.path.join(os.environ['SYSTEMROOT'], 'explorer.exe') + \
                " shell:AppsFolder\\Microsoft.WindowsCamera_8wekyb3d8bbwe!App"

    @staticmethod
    def getPhotoFileLocation():
        if 'USERPROFILE' in os.environ:
            return os.path.join(os.environ['USERPROFILE'], 'Pictures', 'Camera Roll')


class PhotoConfigPresetLinuxCheese:

    @staticmethod
    def isEnabled():
        return os.path.exists('/usr/bin/cheese')

    @staticmethod
    def getPhotoAppCommand():
        return '/usr/bin/cheese'

    @staticmethod
    def getPhotoFileLocation():
        if 'HOME' in os.environ:
            return os.path.join(os.environ['HOME'], 'Pictures', 'Webcam')


class PhotoConfig:
    def __init__(self, config):
        self.config = config
        self.photoBasePath = '{}-qgis-field-photos'

        self.photoPresets = {
            'Custom': None,
            'Windows 10': PhotoConfigPresetWindows10,
            'Linux': PhotoConfigPresetLinuxCheese
        }

        self.photoPreset = 'Custom'
        self.photoAppCommand = None
        self.photoFileLocation = None

    def populate(self, basePath, projectName):
        if len(basePath) > 0 and len(projectName) > 0:
            self.photoPath = os.path.join(
                basePath, self.photoBasePath.format(projectName))
        else:
            self.photoPath = None

        settings = QgsSettings()
        self.photoPreset = settings.value(
            "fieldAnnotations/photo/preset", None)
        self.photoAppCommand = settings.value(
            "fieldAnnotations/photo/appCommand", None)
        self.photoFileLocation = settings.value(
            "fieldAnnotations/photo/fileLocation", None)

    def canTakePhotos(self):
        return self.photoAppCommand is not None

    def getPhotosSince(self, timestamp):
        unixTimestamp = int(timestamp.timestamp())
        for f in os.listdir(self.photoFileLocation):
            if os.path.getmtime(os.path.join(self.photoFileLocation, f)) >= unixTimestamp:
                yield os.path.join(self.photoFileLocation, f)

    def _stripValue(self, value):
        value = value.strip()
        return value if value != '' else None

    def setPhotoAppCommand(self, value):
        self.photoAppCommand = self._stripValue(value)

    def setPhotoFileLocation(self, value):
        self.photoFileLocation = self._stripValue(value)

    def setPhotoPreset(self, value):
        self.photoPreset = self._stripValue(value)

    def save(self):
        settings = QgsSettings()
        settings.setValue("fieldAnnotations/photo/preset", self.photoPreset)
        settings.setValue("fieldAnnotations/photo/appCommand",
                          self.photoAppCommand)
        settings.setValue("fieldAnnotations/photo/fileLocation",
                          self.photoFileLocation)


class ConfigDialog(QtWidgets.QDialog, Translatable):
    def __init__(self, main):
        """Initialisation.

        Parameters
        ----------
        main : FieldAnnotations
            Reference to main plugin instance.
        """
        QtWidgets.QDialog.__init__(self)
        self.main = main

        self.photoConfig = self.main.config.photoConfig

        self.setWindowTitle(self.tr(u'Field annotation settings'))
        self.setLayout(QtWidgets.QVBoxLayout())

        self.setMinimumSize(400, 300)

        self.addWidgets()

    def addWidgets(self):
        """Add the necessary widgets to the dialog."""
        self.addPhotoSettingsWidgets()
        self.addButtonBoxWidget()

    def addPhotoSettingsWidgets(self):
        label = QLabelBold(self.tr('Photo annotation settings'))
        labelFont = label.font()
        labelFont.setPointSize(12)
        label.setFont(labelFont)
        self.layout().addWidget(label)

        photoAppPresetLabel = QLabelItalic(
            self.tr('Photo application preset'))
        self.layout().addWidget(photoAppPresetLabel)

        self.photoAppPresetCombobox = QtWidgets.QComboBox(self)

        for ix, preset in enumerate(self.photoConfig.photoPresets):
            name = preset
            clz = self.photoConfig.photoPresets[name]

            self.photoAppPresetCombobox.addItem(name, clz)
            if clz is None:
                self.photoAppPresetCombobox.model().item(ix, 0).setEnabled(True)
            else:
                self.photoAppPresetCombobox.model().item(ix, 0).setEnabled(clz.isEnabled())

        self.photoAppPresetCombobox.currentIndexChanged.connect(
            self.updatePreset)

        self.layout().addWidget(self.photoAppPresetCombobox)

        photoAppCommandLabel = QLabelItalic(
            self.tr('Photo application command'))
        self.layout().addWidget(photoAppCommandLabel)

        self.photoAppCommandEdit = QtWidgets.QLineEdit(self)
        if self.photoConfig.photoAppCommand is not None:
            self.photoAppCommandEdit.setText(self.photoConfig.photoAppCommand)
        self.layout().addWidget(self.photoAppCommandEdit)

        photoFileLocationLabel = QLabelItalic(
            self.tr('Photo file location'))
        self.layout().addWidget(photoFileLocationLabel)

        self.photoFileLocationEdit = QgsFileWidget(self)
        self.photoFileLocationEdit.setStorageMode(
            QgsFileWidget.StorageMode.GetDirectory)
        if self.photoConfig.photoFileLocation is not None:
            self.photoFileLocationEdit.setFilePath(
                self.photoConfig.photoFileLocation)
        self.layout().addWidget(self.photoFileLocationEdit)

        self.layout().addStretch()

        presetIndex = self.photoAppPresetCombobox.findText(
            self.photoConfig.photoPreset)
        if presetIndex > -1:
            self.photoAppPresetCombobox.setCurrentIndex(presetIndex)

    def addButtonBoxWidget(self):
        """Add the button box widget with the dialog's ok and cancel buttons."""
        buttonBox = QtWidgets.QDialogButtonBox(self)
        buttonBox.setOrientation(QtCore.Qt.Orientation.Horizontal)

        cancelButton = QtWidgets.QToolButton(self)
        cancelButton.setText(self.tr('&Cancel'))
        cancelButton.setIcon(QtGui.QIcon(
            ':/plugins/field_annotations/icons/cancel.png'))
        cancelButton.setIconSize(QtCore.QSize(32, 32))
        cancelButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        cancelButton.clicked.connect(self.reject)

        self.saveButton = QtWidgets.QToolButton(self)
        self.saveButton.setText(self.tr('&Save'))
        self.saveButton.setIcon(QtGui.QIcon(
            ':/plugins/field_annotations/icons/ok.png'))
        self.saveButton.setIconSize(QtCore.QSize(32, 32))
        self.saveButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.saveButton.clicked.connect(lambda: self.accept(True))

        buttonBox.addButton(
            cancelButton, QtWidgets.QDialogButtonBox.ButtonRole.RejectRole)
        buttonBox.addButton(
            self.saveButton, QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        self.layout().addWidget(buttonBox)

    def updatePreset(self):
        currentPreset = self.photoAppPresetCombobox.currentData()
        if currentPreset is None:
            self.photoAppCommandEdit.setEnabled(True)
            self.photoFileLocationEdit.setReadOnly(False)
        else:
            self.photoAppCommandEdit.setEnabled(False)
            self.photoAppCommandEdit.setText(
                currentPreset.getPhotoAppCommand())
            self.photoFileLocationEdit.setReadOnly(True)
            self.photoFileLocationEdit.setFilePath(
                currentPreset.getPhotoFileLocation())

    def accept(self, *args):
        self.photoConfig.setPhotoPreset(
            self.photoAppPresetCombobox.currentText())
        self.photoConfig.setPhotoAppCommand(self.photoAppCommandEdit.text())
        self.photoConfig.setPhotoFileLocation(
            self.photoFileLocationEdit.filePath())
        self.photoConfig.save()
        super().accept()
