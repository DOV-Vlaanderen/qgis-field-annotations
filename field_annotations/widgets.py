from qgis.PyQt import QtWidgets


class QLabelItalic(QtWidgets.QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent=parent)

        font = self.font()
        font.setItalic(True)
        self.setFont(font)


class QLabelBold(QtWidgets.QLabel):
    def __init__(self, text, parent=None):
        super().__init__(text, parent=parent)

        font = self.font()
        font.setBold(True)
        self.setFont(font)
