from qgis.PyQt import QtWidgets, QtCore, QtGui

from .translate import Translatable


class QResizingPixmapLabel(QtWidgets.QLabel):
    def __init__(self, path, image=None, parent=None):
        super().__init__(parent)
        self.path = path
        self.image = image

        self.setMinimumSize(1, 1)
        self.setScaledContents(False)
        self._pixmap = None

        if self.image is None:
            imageReader = QtGui.QImageReader(self.path)
            imageReader.setAutoTransform(True)
            self.image = imageReader.read()

        self.setPixmap(QtGui.QPixmap.fromImage(self.image))

    def heightForWidth(self, width):
        if self._pixmap is None:
            return int(self.height())
        else:
            return int(self._pixmap.height() * width / self._pixmap.width())

    def scaledPixmap(self):
        scaled = self._pixmap.scaled(
            self.size() * self.devicePixelRatioF(),
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation
        )
        scaled.setDevicePixelRatio(self.devicePixelRatioF())
        return scaled

    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        super().setPixmap(pixmap)

    def sizeHint(self):
        width = self.width()
        return QtCore.QSize(width, self.heightForWidth(width))

    def resizeEvent(self, event):
        if self._pixmap is not None:
            super().setPixmap(self.scaledPixmap())
            self.setAlignment(QtCore.Qt.AlignCenter)


class QResizingPixmapPreviewLabel(QResizingPixmapLabel):

    def mouseReleaseEvent(self, event):
        dlg = PhotoPreviewDialog(self.path, parent=self)
        if dlg.exec():
            pass


class QResizingPixmapCloseLabel(QResizingPixmapLabel):

    def mouseReleaseEvent(self, event):
        if self.parent() is not None:
            self.parent().accept()


class PhotoPreviewDialog(QtWidgets.QDialog, Translatable):
    def __init__(self, photoPath, parent=None):
        QtWidgets.QDialog.__init__(self, parent)
        self.photoPath = photoPath

        self.setWindowTitle(self.tr(u'Photo preview'))
        self.setLayout(QtWidgets.QVBoxLayout())

        self.addWidgets()

    def addWidgets(self):
        self.addPhotoWidget()
        self.addButtonBoxWidget()
        self.addShortcuts()

    def addPhotoWidget(self):
        photoLabel = QResizingPixmapCloseLabel(self.photoPath, parent=self)
        self.layout().addWidget(photoLabel)

    def addButtonBoxWidget(self):
        buttonBox = QtWidgets.QDialogButtonBox(self)
        buttonBox.setOrientation(QtCore.Qt.Orientation.Horizontal)

        deleteButton = QtWidgets.QToolButton(self)
        deleteButton.setText(self.tr('&Remove'))
        deleteButton.setIcon(QtGui.QIcon(
            ':/plugins/field_annotations/icons/cancel.png'))
        deleteButton.setIconSize(QtCore.QSize(32, 32))
        deleteButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        deleteButton.clicked.connect(self.reject)

        self.okButton = QtWidgets.QToolButton(self)
        self.okButton.setText(self.tr('&Close'))
        self.okButton.setIcon(QtGui.QIcon(
            ':/plugins/field_annotations/icons/ok.png'))
        self.okButton.setIconSize(QtCore.QSize(32, 32))
        self.okButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.okButton.clicked.connect(self.accept)

        buttonBox.addButton(
            deleteButton, QtWidgets.QDialogButtonBox.ButtonRole.RejectRole)
        buttonBox.addButton(
            self.okButton, QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        self.layout().addWidget(buttonBox)

    def addShortcuts(self):
        self.okShortcutCtrlReturn = QtGui.QShortcut(self)
        self.okShortcutCtrlReturn.setKey(QtGui.QKeySequence('Ctrl+Return'))
        self.okShortcutCtrlReturn.activated.connect(self.accept)

        self.okShortcutCtrlS = QtGui.QShortcut(self)
        self.okShortcutCtrlS.setKey(QtGui.QKeySequence('Ctrl+S'))
        self.okShortcutCtrlS.activated.connect(self.accept)

        cancelShortcut = QtGui.QShortcut(self)
        cancelShortcut.setKey(QtGui.QKeySequence('Ctrl+Q'))
        cancelShortcut.activated.connect(self.destroy)

    def reject(self):
        self.parent().parent().removePhoto(self.photoPath)
        super().reject()
