import math

from qgis.PyQt import QtWidgets, QtCore, QtGui

from .translate import Translatable


class PhotoWidget(QtWidgets.QWidget, Translatable):
    """Widget to present a list of photos in a grid."""
    photoListChanged = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        """Initialisation.

        Parameters
        ----------
        parent : QWidget, optional
            Parent widget, by default None
        """
        super().__init__(parent)
        self.parent = parent

        self.photos = []

        layout = QtWidgets.QGridLayout()
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(10)

        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)

        self.setLayout(layout)

    def removePhoto(self, photo):
        """Remove single photo from the widget.

        Parameters
        ----------
        photo : str
            Full file path of the photo to remove.
        """
        keepPhotos = [p[0] for p in self.photos if p[0] != photo]
        self.photos.clear()
        self.addPhotos(keepPhotos)
        self.photoListChanged.emit()

    def addPhotos(self, photos):
        """Add the given photos to the widget.

        Parameters
        ----------
        photos : list of str
            List of full file paths of the photos to add.
        """
        for i in reversed(range(self.layout().count())):
            try:
                self.layout().itemAt(i).widget().setParent(None)
            except AttributeError:
                continue

        for photo in photos:
            imageReader = QtGui.QImageReader(photo)
            imageReader.setAutoTransform(True)
            photoImage = imageReader.read()
            self.photos.append((photo, photoImage))

        size = math.ceil(math.sqrt(len(self.photos)))
        for i in range(size):
            for ix, photo in enumerate(self.photos[(i*size): ((i*size)+size)]):
                photoLabel = QResizingPixmapPreviewLabel(
                    photo[0], photo[1], self)
                photoLabel.setSizePolicy(
                    QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
                photoLabel.setMinimumSize(100, 100)
                self.layout().addWidget(
                    photoLabel, i, ix, QtCore.Qt.AlignmentFlag.AlignCenter)

        self.adjustSize()

    def getPhotos(self):
        """Get the full file paths of the photos in the widget.

        Returns
        -------
        list of str
            List of full file paths of the photos in the widget.
        """
        return [p[0] for p in self.photos]


class QResizingPixmapLabel(QtWidgets.QLabel):
    def __init__(self, path, image=None, parent=None):
        """Initialisation.

        Parameters
        ----------
        path : str
            Full file path of an image.
        image : QImage, optional
            Image representation of the file, will be created if None, by default None
        parent : QWidget, optional
            Parent widget, by default None
        """
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
        """Calculate the height for the given width, retaining the aspect ratio.

        Parameters
        ----------
        width : float
            Width to use for calculation.

        Returns
        -------
        int
            Corresponding height for the width, retaining aspect ratio.
        """
        if self._pixmap is None:
            return int(self.height())
        else:
            return int(self._pixmap.height() * width / self._pixmap.width())

    def scaledPixmap(self):
        """Return a scaled version of the pixmap.

        Returns
        -------
        QPixmap
            Scaled pixmap
        """
        scaled = self._pixmap.scaled(
            self.size() * self.devicePixelRatioF(),
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation
        )
        scaled.setDevicePixelRatio(self.devicePixelRatioF())
        return scaled

    def setPixmap(self, pixmap):
        """Set the pixmap to the given pixmap.

        Parameters
        ----------
        pixmap : QPixmap
            The pixmap to set.
        """
        self._pixmap = pixmap
        super().setPixmap(pixmap)

    def sizeHint(self):
        """Return a size hint based on the width, and height calculated based on aspect ratio.

        Returns
        -------
        QSize
            Size hint.
        """
        width = self.width()
        return QtCore.QSize(width, self.heightForWidth(width))

    def resizeEvent(self, event):
        """Scale the pixmap after a resize of the widget."""
        if self._pixmap is not None:
            super().setPixmap(self.scaledPixmap())
            self.setAlignment(QtCore.Qt.AlignCenter)


class QResizingPixmapPreviewLabel(QResizingPixmapLabel):
    """A version of the QResizingPixmapLabel that opens a preview dialog when clicking it."""

    def mouseReleaseEvent(self, event):
        """Open the preview dialog on click."""
        dlg = PhotoPreviewDialog(self.path, parent=self)
        if dlg.exec():
            pass


class QResizingPixmapCloseLabel(QResizingPixmapLabel):
    """A version of the QResizingPixmapLabel that closes the parent dialog when clicking it."""

    def mouseReleaseEvent(self, event):
        """Close the parent dialog on click."""
        if self.parent() is not None:
            self.parent().accept()


class PhotoPreviewDialog(QtWidgets.QDialog, Translatable):
    """A dialog to preview a bigger version of the given image, and allow to remove it from the list."""

    def __init__(self, photoPath, parent=None):
        """Initialisation.

        Parameters
        ----------
        photoPath : str
            Full path of the photo to preview.
        parent : QWidget, optional
            Parent widget, by default None
        """
        QtWidgets.QDialog.__init__(self, parent)
        self.photoPath = photoPath

        self.setWindowTitle(self.tr(u'Photo preview'))
        self.setLayout(QtWidgets.QVBoxLayout())

        self.addWidgets()

    def addWidgets(self):
        """Add the necessary widgets to the dialog."""
        self.addPhotoWidget()
        self.addButtonBoxWidget()
        self.addShortcuts()

    def addPhotoWidget(self):
        """Add the widget to show the photo."""
        photoLabel = QResizingPixmapCloseLabel(self.photoPath, parent=self)
        self.layout().addWidget(photoLabel)

    def addButtonBoxWidget(self):
        """Add the button box widget with the dialog's remove and close buttons."""
        buttonBox = QtWidgets.QDialogButtonBox(self)
        buttonBox.setOrientation(QtCore.Qt.Orientation.Horizontal)

        deleteButton = QtWidgets.QToolButton(self)
        deleteButton.setText(self.tr('&Remove'))
        deleteButton.setIcon(QtGui.QIcon(
            ':/plugins/field_annotations/icons/delete.png'))
        deleteButton.setIconSize(QtCore.QSize(32, 32))
        deleteButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        deleteButton.clicked.connect(self.reject)

        self.okButton = QtWidgets.QToolButton(self)
        self.okButton.setText(self.tr('&Close'))
        self.okButton.setIcon(QtGui.QIcon(
            ':/plugins/field_annotations/icons/cancel.png'))
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
        """Add the keyboard shortcuts."""
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
        """Remove the photo from the parent NewPhotoAnnotationDialog on reject."""
        self.parent().parent().removePhoto(self.photoPath)
        super().reject()
