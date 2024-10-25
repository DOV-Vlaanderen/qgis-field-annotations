import datetime
import math

from qgis.PyQt import QtWidgets, QtGui, QtCore
from qgis.core import QgsExpressionContextUtils

from .photo import PhotoAspectRatioLabel, ImageDisplayWidget, QResizingPixmapLabel

from .translate import Translatable


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

    def addWidgets(self):
        self.addAnnotationWidget()
        self.addLayerSelectorWidget()
        self.addButtonBoxWidget()
        self.addShortcuts()

    def addAnnotationWidget(self):
        textEditLabel = QtWidgets.QLabel(self.tr('Annotation'))
        textEditLabelFont = textEditLabel.font()
        textEditLabelFont.setItalic(True)
        textEditLabel.setFont(textEditLabelFont)
        self.layout().addWidget(textEditLabel)

        self.textEdit = QtWidgets.QTextEdit(self)
        self.textEdit.setTabChangesFocus(True)
        self.textEdit.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.layout().addWidget(self.textEdit)

    def addLayerSelectorWidget(self):
        layerSelectorLabel = QtWidgets.QLabel(self.tr('For layer'))
        layerSelectorLabelFont = layerSelectorLabel.font()
        layerSelectorLabelFont.setItalic(True)
        layerSelectorLabel.setFont(layerSelectorLabelFont)
        self.layout().addWidget(layerSelectorLabel)

        self.layerSelector = QtWidgets.QComboBox(self)
        self.layerSelector.addItem(QtGui.QIcon(
            ':/plugins/field_annotations/icons/no_map.png'), self.tr('No layer'), None)

        for l in self.main.annotationView.listAnnotatableLayers():
            self.layerSelector.addItem(QtGui.QIcon(
                ':/plugins/field_annotations/icons/map.png'), l.name(), l)
            self.layout().addWidget(self.layerSelector)

    def addButtonBoxWidget(self):
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

        self.okButton = QtWidgets.QToolButton(self)
        self.okButton.setText(self.tr('&Ok'))
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

        # self.adjustSize()

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


class PhotoWidget(QtWidgets.QWidget, Translatable):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        self.photoImages = []

        layout = QtWidgets.QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(10)

        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)

        # self.scrollWidget = QtWidgets.QScrollArea(self)
        # self.scrollWidget.setLayout(layout)

        self.setLayout(layout)
        # self.layout().addWidget(self.scrollWidget)

        # QtWidgets.QScroller.grabGesture(
        #     self.scrollWidget.viewport(), QtWidgets.QScroller.LeftMouseButtonGesture)

    def addPhotos(self, photos):
        for i in reversed(range(self.layout().count())):
            try:
                self.layout().itemAt(i).widget().setParent(None)
            except AttributeError:
                continue

        for photo in photos:
            imageReader = QtGui.QImageReader(photo)
            imageReader.setAutoTransform(True)
            photoImage = imageReader.read()
            self.photoImages.append(photoImage)

        size = math.ceil(math.sqrt(len(self.photoImages)))
        print(size)
        for i in range(size):
            for ix, photoImage in enumerate(self.photoImages[(i*size): ((i*size)+size)]):
                photoLabel = QResizingPixmapLabel(self)
                photoLabel.setSizePolicy(
                    QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
                photoLabel.setPixmap(QtGui.QPixmap.fromImage(photoImage))
                photoLabel.setMinimumSize(100, 100)
                # photoLabel.adjustSize()
                print('adding photo', i, ix, photoLabel)
                self.layout().addWidget(
                    photoLabel, i, ix, QtCore.Qt.AlignmentFlag.AlignCenter)

        self.adjustSize()


class NewPhotoAnnotationDialog(NewAnnotationDialog, Translatable):
    photoListChanged = QtCore.pyqtSignal()

    def __init__(self, main, layer, feature):
        self.photosToAdd = []

        super().__init__(main, layer, feature)

        self.setWindowTitle(self.tr(u'New photo annotation'))

        self.textEdit.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding,
            QtWidgets.QSizePolicy.Policy.Minimum)

        self.connectValidate()

    def connectValidate(self):
        self.photoListChanged.connect(self.validate)

    def validate(self):
        hasPhotos = len(self.photosToAdd) > 0

        if not hasPhotos:
            self.textEdit.setText("")

        self.textEdit.setEnabled(hasPhotos)
        self.okButton.setEnabled(hasPhotos)
        self.okShortcutCtrlReturn.setEnabled(hasPhotos)
        self.okShortcutCtrlS.setEnabled(hasPhotos)
        self.okFinishShortcut.setEnabled(hasPhotos)

    def addPhotos(self, photos):
        self.photosToAdd.extend(photos)
        self.photoWidget.addPhotos(photos)
        self.photoListChanged.emit()

    def addWidgets(self):
        self.addPhotoButtonWidget()
        self.addPhotoWidget()
        self.addAnnotationWidget()
        self.addLayerSelectorWidget()
        self.addButtonBoxWidget()
        self.addShortcuts()

        self.validate()

    def addPhotoButtonWidget(self):
        photoButtonWidget = QtWidgets.QWidget(self)
        photoButtonWidget.setLayout(QtWidgets.QHBoxLayout())

        photoButtonWidget.layout().addStretch()

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
        self.photoWidget = PhotoWidget(self)
        self.layout().addWidget(self.photoWidget)

    def takePhoto(self):
        print('taking photo')

    def importPhoto(self):
        print('import photos')
        photoSelectionDialog = QtWidgets.QFileDialog(self)
        photoSelectionDialog.setWindowTitle(self.tr('Import photos'))
        photoSelectionDialog.setFileMode(
            QtWidgets.QFileDialog.FileMode.ExistingFiles)
        photoSelectionDialog.setNameFilter(
            self.tr("Images (*.jpg *.jpeg *.png *.JPG *.JPEG *.PNG)"))

        if photoSelectionDialog.exec_():
            self.addPhotos(photoSelectionDialog.selectedFiles())
