from qgis.PyQt import QtWidgets, QtCore, QtGui


class QResizingPixmapLabel(QtWidgets.QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.setMinimumSize(1, 1)
        self.setScaledContents(False)
        self._pixmap = None

        self.softRemove = False

    def mouseDoubleClickEvent(self, event):
        if self._pixmap is not None:
            self.softRemove = not self.softRemove

            effect = QtWidgets.QGraphicsOpacityEffect(self)
            effect.setOpacity(0.3)

            if self.softRemove:
                self.setGraphicsEffect(effect)
            else:
                self.setGraphicsEffect(None)

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

class ImageDisplayWidget(QtWidgets.QLabel):
    def __init__(self, parent, max_enlargement=2.0):
        super().__init__(parent)
        self.max_enlargement = max_enlargement
        # self.setSizePolicy(QtWidgets.QSizePolicy.Expanding,
        #                    QtWidgets.QSizePolicy.Expanding)
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setMinimumSize(1, 1)
        self.__image = None

    def setImage(self, image):
        self.__image = image
        self.resize(self.sizeHint())
        self.update()

    def sizeHint(self):
        if self.__image is not None:
            return self.__image.size() * self.max_enlargement
        else:
            return QtCore.QSize(1, 1)

    def resizeEvent(self, event):
        if self.__image is not None:
            pixmap = QtGui.QPixmap.fromImage(self.__image)
            scaled = pixmap.scaled(event.size(), QtCore.Qt.KeepAspectRatio)
            self.setPixmap(scaled)
        super().resizeEvent(event)


class PhotoAspectRatioLabel(QtWidgets.QLabel):
    def __init__(self, parent):
        super().__init__(parent)

        self.pixmapWidth = 0
        self.pixmapHeight = 0

    def setPixmap(self, pixmap):
        self.pixmapWidth = pixmap.width()
        self.pixmapHeight = pixmap.height()

        self.updateMargins()
        super().setPixmap(pixmap)

    def resizeEvent(self, event):
        self.updateMargins()
        super().resizeEvent(event)

    def updateMargins(self):
        if (self.pixmapWidth <= 0 or self.pixmapHeight <= 0):
            return

        w = self.width()
        h = self.height()

        if (w <= 0 or h <= 0):
            return

        if (w * self.pixmapHeight > h * self.pixmapWidth):
            m = int((w - (self.pixmapWidth * h / self.pixmapHeight)) / 2)
            self.setContentsMargins(m, 0, m, 0)
        else:
            m = int((h - (self.pixmapHeight * w / self.pixmapWidth)) / 2)
            self.setContentsMargins(0, m, 0, m)
