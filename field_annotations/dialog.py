import datetime
import os
import shutil
import uuid
import subprocess

from qgis.PyQt import QtWidgets, QtGui, QtCore
from qgis.core import QgsExpressionContextUtils


from .config import PhotoConfig
from .translate import Translatable
from .photo import PhotoWidget
from .widgets import QLabelBold, QLabelItalic


class NewAnnotationDialog(QtWidgets.QDialog, Translatable):
    """Dialog to enter details of a new annotation."""
    def __init__(self, main, layer, feature):
        """Initialisation.

        Parameters
        ----------
        main : FieldAnnotations
            Reference to main plugin instance.
        layer : QgsVectorLayer
            Vector layer where the annotation will be added.
        feature : QgsFeature
            Annotation feature that was drawn and will be added on accepting the dialog.
        """
        QtWidgets.QDialog.__init__(self)
        self.main = main
        self.layer = layer
        self.feature = feature

        self.shouldStopAnnotating = False

        self.iconPath = ':/plugins/field_annotations/icons/write_note.png'
        self.setWindowIcon(QtGui.QIcon(self.iconPath))

        self.setWindowTitle(self.tr(u'New annotation'))
        self.setLayout(QtWidgets.QVBoxLayout())

        self.addWidgets()

    def getTranslationStrings(self):
        """Get the translated strings.

        Returns
        -------
        dict of <str, str>
            String and their translated value.
        """
        return {
            'Annotation': self.tr('Annotation'),
            'For layer': self.tr('For layer'),
            'No layer': self.tr('No layer'),
            '&Cancel': self.tr('&Cancel'),
            '&Ok': self.tr('&Ok'),
            '&Save': self.tr('&Save')
        }

    def addWidgets(self):
        """Add the necessary widgets to the dialog."""
        self.addAnnotationWidget()
        self.addLayerSelectorWidget()
        self.addButtonBoxWidget()
        self.addShortcuts()

    def addAnnotationWidget(self):
        """Add the widget to write the annotation text."""
        textEditLabel = QLabelItalic(
            self.getTranslationStrings().get('Annotation'))
        self.layout().addWidget(textEditLabel)

        self.textEdit = QtWidgets.QTextEdit(self)
        self.textEdit.setTabChangesFocus(True)
        self.textEdit.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.layout().addWidget(self.textEdit)

    def addLayerSelectorWidget(self):
        """Add the widget to select an annotatable layer."""
        layerSelectorLabel = QLabelItalic(
            self.getTranslationStrings().get('For layer'))
        self.layout().addWidget(layerSelectorLabel)

        self.layerSelector = QtWidgets.QComboBox(self)
        self.layerSelector.addItem(QtGui.QIcon(
            ':/plugins/field_annotations/icons/no_map.png'), self.getTranslationStrings().get('No layer'), None)

        for l in self.main.annotationView.listAnnotatableLayers():
            self.layerSelector.addItem(QtGui.QIcon(
                ':/plugins/field_annotations/icons/map.png'), l.name(), l)
            self.layout().addWidget(self.layerSelector)

    def addButtonBoxWidget(self):
        """Add the button box widget with the dialog's ok and cancel buttons."""
        buttonBox = QtWidgets.QDialogButtonBox(self)
        buttonBox.setOrientation(QtCore.Qt.Orientation.Horizontal)

        cancelButton = QtWidgets.QToolButton(self)
        cancelButton.setText(self.getTranslationStrings().get('&Cancel'))
        cancelButton.setIcon(QtGui.QIcon(
            ':/plugins/field_annotations/icons/cancel.png'))
        cancelButton.setIconSize(QtCore.QSize(32, 32))
        cancelButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        cancelButton.clicked.connect(self.reject)

        if self.main.config.autoSave:
            self.okButton = QtWidgets.QToolButton(self)
            self.okButton.setText(self.getTranslationStrings().get('&Save'))
            self.okButton.setIcon(QtGui.QIcon(
                ':/plugins/field_annotations/icons/save.png'))
            self.okButton.setIconSize(QtCore.QSize(32, 32))
            self.okButton.setToolButtonStyle(
                QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            self.okButton.clicked.connect(self.acceptFinish)
        else:
            self.okButton = QtWidgets.QToolButton(self)
            self.okButton.setText(self.getTranslationStrings().get('&Ok'))
            self.okButton.setIcon(QtGui.QIcon(
                ':/plugins/field_annotations/icons/ok.png'))
            self.okButton.setIconSize(QtCore.QSize(32, 32))
            self.okButton.setToolButtonStyle(
                QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            self.okButton.clicked.connect(lambda: self.accept(True))

        buttonBox.addButton(
            cancelButton, QtWidgets.QDialogButtonBox.ButtonRole.RejectRole)
        buttonBox.addButton(
            self.okButton, QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        self.layout().addWidget(buttonBox)

    def addShortcuts(self):
        """Add the keyboard shortcuts."""
        self.okShortcutCtrlReturn = QtGui.QShortcut(self)
        self.okShortcutCtrlReturn.setKey(QtGui.QKeySequence('Ctrl+Return'))
        self.okShortcutCtrlReturn.activated.connect(lambda: self.accept(True))

        self.okShortcutCtrlS = QtGui.QShortcut(self)
        self.okShortcutCtrlS.setKey(QtGui.QKeySequence('Ctrl+S'))
        self.okShortcutCtrlS.activated.connect(lambda: self.accept(True))

        self.okFinishShortcut = QtGui.QShortcut(self)
        self.okFinishShortcut.setKey(QtGui.QKeySequence('Ctrl+Shift+Return'))
        self.okFinishShortcut.activated.connect(self.acceptFinish)

        cancelShortcut = QtGui.QShortcut(self)
        cancelShortcut.setKey(QtGui.QKeySequence('Ctrl+Q'))
        cancelShortcut.activated.connect(self.reject)

    def accept(self, superAccept=True):
        """Update the feature with the annotation text and other data values.

        When superAccept is True, accept the dialog too and close it.

        Parameters
        ----------
        superAccept : bool, optional
            When True, the dialog itself will be accepted and closed.
        """
        annotation = self.textEdit.toPlainText()
        author = QgsExpressionContextUtils.globalScope().variable('user_full_name')

        layer = self.layerSelector.currentData()
        if layer is not None:
            layerUri = self.main.annotationView.getLayerUri(layer)
            layerName = layer.name()
        else:
            layerUri = layerName = None

        self.layer.editBuffer().changeAttributeValues(
            self.feature.id(), {
                self.layer.fields().indexOf('annotation'): annotation,
                self.layer.fields().indexOf('author'): author,
                self.layer.fields().indexOf('dateCreated'): datetime.datetime.now().isoformat(),
                self.layer.fields().indexOf('layerUri'): layerUri,
                self.layer.fields().indexOf('layerName'): layerName,
            }, {})

        if superAccept:
            super().accept()

    def acceptFinish(self):
        """Update the feature and initiate stop annotating."""
        self.accept(superAccept=False)
        self.shouldStopAnnotating = True
        super().accept()

    def reject(self):
        """Reject the changes and close the dialog.

        Removes the feature from the edit buffer.
        """
        self.layer.editBuffer().deleteFeature(self.feature.id())
        super().reject()


class NewPhotoAnnotationDialog(NewAnnotationDialog, Translatable):
    """Dialog to add photos and enter details of a new photo annotation."""

    photoListChanged = QtCore.pyqtSignal()

    def __init__(self, main, layer, feature):
        """Initialisation.

        Parameters
        ----------
        main : FieldAnnotations
            Reference to main plugin instance.
        layer : QgsVectorLayer
            Vector layer where the annotation will be added.
        feature : QgsFeature
            Annotation feature that was drawn and will be added on accepting the dialog.
        """
        self.photosToAdd = []
        self.timer = None

        super().__init__(main, layer, feature)

        self.setWindowTitle(self.tr(u'New photo annotation'))

        self.textEdit.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Minimum)

        self.connectValidate()

    def connectValidate(self):
        """Connect the validation method to the changes of state that should trigger validation."""
        self.photoListChanged.connect(self.validate)

    def validate(self):
        """Validate the state: only allow saving if there is at least one photo."""
        hasPhotos = len(self.photosToAdd) > 0

        if not hasPhotos:
            self.textEdit.setText("")

        self.textEdit.setEnabled(hasPhotos)
        self.okButton.setEnabled(hasPhotos)
        self.okShortcutCtrlReturn.setEnabled(hasPhotos)
        self.okShortcutCtrlS.setEnabled(hasPhotos)
        self.okFinishShortcut.setEnabled(hasPhotos)

    def addPhotos(self, photos):
        """Add the given photos to the list of photos that will be saved with the annotation.

        Parameters
        ----------
        photos : list of str
            List of absolute paths of photos to add.
        """
        self.photosToAdd.extend(photos)
        self.photoWidget.addPhotos(photos)
        self.photoListChanged.emit()

    def updatePhotos(self):
        """Update the list of photos based on the photos returned from the photo widget."""
        self.photosToAdd = self.photoWidget.getPhotos()
        self.photoListChanged.emit()

    def getTranslationStrings(self):
        """Get the translated strings.

        Returns
        -------
        dict of <str, str>
            String and their translated value.
        """
        return {
            'Annotation': self.tr('Annotation'),
            'For layer': self.tr('For layer'),
            'No layer': self.tr('No layer'),
            '&Cancel': self.tr('&Cancel'),
            '&Ok': self.tr('&Ok')
        }

    def addWidgets(self):
        """Add the necessary widgets to the dialog and validate."""
        self.addPhotoButtonWidget()
        self.addPhotoWidget()
        self.addAnnotationWidget()
        self.addLayerSelectorWidget()
        self.addProgressWidget()
        self.addButtonBoxWidget()
        self.addShortcuts()

        self.validate()

    def addPhotoButtonWidget(self):
        """Add the widget with the photo buttons."""
        photoButtonWidget = QtWidgets.QWidget(self)
        photoButtonWidget.setLayout(QtWidgets.QHBoxLayout())

        photoButtonWidget.layout().addStretch()

        if self.main.config.photoConfig.canTakePhotos():
            takePhotoButton = QtWidgets.QToolButton(self)
            takePhotoButton.setText(self.tr('&Take photo'))
            takePhotoButton.setIcon(QtGui.QIcon(
                ':/plugins/field_annotations/icons/take_photo.png'))
            takePhotoButton.setIconSize(QtCore.QSize(32, 32))
            takePhotoButton.setToolButtonStyle(
                QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            takePhotoButton.clicked.connect(self.takePhoto)
            photoButtonWidget.layout().addWidget(takePhotoButton)

        importPhotoButton = QtWidgets.QToolButton(self)
        importPhotoButton.setText(self.tr('&Import photos'))
        importPhotoButton.setIcon(QtGui.QIcon(
            ':/plugins/field_annotations/icons/import_photo.png'))
        importPhotoButton.setIconSize(QtCore.QSize(32, 32))
        importPhotoButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        importPhotoButton.clicked.connect(self.importPhoto)
        photoButtonWidget.layout().addWidget(importPhotoButton)

        self.layout().addWidget(photoButtonWidget)

    def addPhotoWidget(self):
        """Add the photo widget to show added photos."""
        self.photoWidget = PhotoWidget(self)
        self.photoWidget.photoListChanged.connect(self.updatePhotos)
        self.layout().addWidget(self.photoWidget)

    def addProgressWidget(self):
        """Add the progressbar widget to show progress while copying the photos."""
        self.progressWidget = QtWidgets.QProgressBar(self)
        self.progressWidget.setEnabled(False)
        self.progressWidget.setVisible(False)
        self.layout().addWidget(self.progressWidget)

    def takePhoto(self):
        """Take new photos with the configured photo application."""

        def loadPhotos():
            """Load new photos into the dialog."""
            toAdd = [f for f in self.main.config.photoConfig.getPhotosSince(
                photoAppStartedAt) if f not in self.photosToAdd]
            self.addPhotos(toAdd)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(loadPhotos)

        photoAppStartedAt = datetime.datetime.now()
        subprocess.Popen(self.main.config.photoConfig.photoAppCommand)
        self.timer.start(1000)

    def importPhoto(self):
        """Import a selection of existing photos into the annotation dialog."""
        photoSelectionDialog = QtWidgets.QFileDialog(self)
        photoSelectionDialog.setWindowTitle(self.tr('Import photos'))
        photoSelectionDialog.setFileMode(
            QtWidgets.QFileDialog.FileMode.ExistingFiles)
        photoSelectionDialog.setNameFilter(
            self.tr("Images (*.jpg *.jpeg *.png *.JPG *.JPEG *.PNG)"))

        if photoSelectionDialog.exec_():
            self.addPhotos(photoSelectionDialog.selectedFiles())

    def copyPhotos(self):
        """Copy the photos from their current location into a location close to the project.

        Returns
        -------
        str
            Full system path of the location where the photos were saved.
        """
        self.setEnabled(False)
        self.progressWidget.setEnabled(True)
        self.progressWidget.setVisible(True)
        self.progressWidget.setMaximum(len(self.photosToAdd))
        counter = 0
        self.progressWidget.setValue(counter)

        annotationId = str(uuid.uuid4())
        destFolder = os.path.join(
            self.main.config.photoConfig.photoPath, annotationId)

        destFolderRelative = os.path.join(
            self.main.config.photoConfig.photoPathRelative, annotationId)

        if not os.path.exists(destFolder):
            os.makedirs(destFolder)

        for photo in self.photosToAdd:
            destFile = os.path.join(destFolder, os.path.basename(photo))
            if self.main.config.photoConfig.photoSaveAction == PhotoConfig.PhotoSaveAction.Copy:
                shutil.copyfile(photo, destFile)
            elif self.main.config.photoConfig.photoSaveAction == PhotoConfig.PhotoSaveAction.Move:
                shutil.move(photo, destFile)
            counter += 1
            self.progressWidget.setValue(counter)

        return destFolderRelative

    def reject(self):
        """Called when dialog is cancelled. Stop the timer."""
        if self.timer is not None:
            self.timer.stop()

        super().reject()

    def accept(self, superAccept=True):
        """Update the feature with the annotation text and other data values, and copy the photos.

        When superAccept is True, accept the dialog too and close it.

        Parameters
        ----------
        superAccept : bool, optional
            When True, the dialog itself will be accepted and closed.
        """
        if self.timer is not None:
            self.timer.stop()

        photoPath = self.copyPhotos()

        self.layer.editBuffer().changeAttributeValues(
            self.feature.id(), {
                self.layer.fields().indexOf('photoPath'): photoPath
            }, {})

        super().accept(superAccept)
