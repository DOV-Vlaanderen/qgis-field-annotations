from qgis.PyQt import QtWidgets


class QLabelItalic(QtWidgets.QLabel):
    """Widget for an italic label."""
    def __init__(self, text, parent=None):
        """Initialisation.

        Parameters
        ----------
        text : str
            Text to show on the label
        parent : QWidget, optional
            Parent widget, by default None
        """
        super().__init__(text, parent=parent)

        font = self.font()
        font.setItalic(True)
        self.setFont(font)


class QLabelBold(QtWidgets.QLabel):
    """Widget for a bold label."""
    def __init__(self, text, parent=None):
        """Initialisation.

        Parameters
        ----------
        text : str
            Text to show on the label
        parent : QWidget, optional
            Parent widget, by default None
        """
        super().__init__(text, parent=parent)

        font = self.font()
        font.setBold(True)
        self.setFont(font)
