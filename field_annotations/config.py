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


class PhotoConfigPresetWindows10(Translatable):

    @staticmethod
    def getKey():
        return 'Windows10'

    def getName(self):
        return self.tr('Windows 10')

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


class PhotoConfigPresetLinuxCheese(Translatable):

    @staticmethod
    def getKey():
        return 'LinuxCheese'

    def getName(self):
        return self.tr('Linux')

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


class PhotoConfigPresetCustom(Translatable):

    @staticmethod
    def getKey():
        return 'Custom'

    def getName(self):
        return self.tr('Custom')

    @staticmethod
    def isEnabled():
        return True

    @staticmethod
    def getPhotoAppCommand():
        return None

    @staticmethod
    def getPhotoFileLocation():
        return None


class PhotoConfig:
    def __init__(self, config):
        """Initialisation of photo configuration.

        Parameters
        ----------
        config : Config
            Main configuration instance.
        """
        self.config = config
        self.photoBasePath = '{}-qgis-field-photos'

        self.photoPresets = [
            PhotoConfigPresetCustom,
            PhotoConfigPresetLinuxCheese,
            PhotoConfigPresetWindows10
        ]

        self.photoPreset = PhotoConfigPresetCustom
        self.photoAppCommand = None
        self.photoFileLocation = None

    def populate(self, basePath, projectName):
        """Populate the photo path based on the given input.

        Parameters
        ----------
        basePath : str
            Directory where the project is located
        projectName : str
            File name of the QGis project.
        """
        if len(basePath) > 0 and len(projectName) > 0:
            self.photoPath = os.path.join(
                basePath, self.photoBasePath.format(projectName))
            self.photoPathRelative = self.photoBasePath.format(projectName)
        else:
            self.photoPath = None
            self.photoPathRelative = None

        settings = QgsSettings()

        self.photoPreset = None
        presetKey = settings.value("fieldAnnotations/photo/preset", None)
        if presetKey is not None:
            photoPresets = [
                p for p in self.photoPresets if p.getKey() == presetKey]
            if len(photoPresets) > 0:
                self.photoPreset = photoPresets[0]

        self.photoAppCommand = settings.value(
            "fieldAnnotations/photo/appCommand", None)
        self.photoFileLocation = settings.value(
            "fieldAnnotations/photo/fileLocation", None)

    def canTakePhotos(self):
        """Whether taking photo's should be enabled.

        Returns
        -------
        bool
            True if we can take photo's, False otherwise.
        """
        return self.photoAppCommand is not None

    def getPhotosSince(self, timestamp):
        """Get all the photos that were modified in the photo file location directory since a given timestamp.

        Parameters
        ----------
        timestamp : datetime.datetime
            Timestamp to use for comparing against.

        Yields
        ------
        str
            Absolute path of files that were added.
        """
        unixTimestamp = int(timestamp.timestamp())
        for f in os.listdir(self.photoFileLocation):
            if os.path.getmtime(os.path.join(self.photoFileLocation, f)) >= unixTimestamp:
                yield os.path.join(self.photoFileLocation, f)

    def _stripValue(self, value):
        """Strip the value and return None if empty.

        Parameters
        ----------
        value : str
            Value to strip.

        Returns
        -------
        str or None
            Stripped value if non-empty string, else None.
        """
        value = value.strip()
        return value if value != '' else None

    def setPhotoAppCommand(self, value):
        """Set the photo application command.

        Parameters
        ----------
        value : str
            Command or path of the photo application.
        """
        self.photoAppCommand = self._stripValue(value)

    def setPhotoFileLocation(self, value):
        """Set the photo file location.

        Parameters
        ----------
        value : str
            Absolute path to the location the photo's taken by the application will be stored.
        """
        self.photoFileLocation = self._stripValue(value)

    def setPhotoPreset(self, preset):
        """Set the photo preset to the given value.

        Parameters
        ----------
        preset : PhotoConfigPreset
            Photo config preset to use.
        """
        self.photoPreset = preset.getKey()

    def save(self):
        """Save the settings."""
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
        """Add the photo settings widgets to the dialog."""
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
            name = preset().getName()
            self.photoAppPresetCombobox.addItem(name, preset)
            self.photoAppPresetCombobox.model().item(ix, 0).setEnabled(preset.isEnabled())

        self.photoAppPresetCombobox.currentIndexChanged.connect(
            self.updatePhotoPreset)

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

        presetIndex = self.photoAppPresetCombobox.findData(
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
            ':/plugins/field_annotations/icons/save.png'))
        self.saveButton.setIconSize(QtCore.QSize(32, 32))
        self.saveButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.saveButton.clicked.connect(lambda: self.accept(True))

        buttonBox.addButton(
            cancelButton, QtWidgets.QDialogButtonBox.ButtonRole.RejectRole)
        buttonBox.addButton(
            self.saveButton, QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        self.layout().addWidget(buttonBox)

    def updatePhotoPreset(self):
        """Update the photo command and file location based on the selected preset."""
        currentPreset = self.photoAppPresetCombobox.currentData()

        if currentPreset.getPhotoAppCommand() is None:
            self.photoAppCommandEdit.setEnabled(True)
        else:
            self.photoAppCommandEdit.setEnabled(False)
            self.photoAppCommandEdit.setText(
                currentPreset.getPhotoAppCommand())

        if currentPreset.getPhotoFileLocation() is None:
            self.photoFileLocationEdit.setReadOnly(False)
        else:
            self.photoFileLocationEdit.setReadOnly(True)
            self.photoFileLocationEdit.setFilePath(
                currentPreset.getPhotoFileLocation())

    def accept(self, *args):
        """Save updated config and close the dialog."""
        self.photoConfig.setPhotoPreset(
            self.photoAppPresetCombobox.currentData())
        self.photoConfig.setPhotoAppCommand(self.photoAppCommandEdit.text())
        self.photoConfig.setPhotoFileLocation(
            self.photoFileLocationEdit.filePath())
        self.photoConfig.save()
        super().accept()
