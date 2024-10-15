import datetime
from qgis.PyQt import QtWidgets, QtGui, QtCore
from qgis.core import QgsExpressionContextUtils

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

        textEditLabel = QtWidgets.QLabel(self.tr('Annotation'))
        textEditLabelFont = textEditLabel.font()
        textEditLabelFont.setItalic(True)
        textEditLabel.setFont(textEditLabelFont)
        self.layout().addWidget(textEditLabel)

        self.textEdit = QtWidgets.QTextEdit(self)
        self.textEdit.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.layout().addWidget(self.textEdit)

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

        okButton = QtWidgets.QToolButton(self)
        okButton.setText(self.tr('&Ok'))
        okButton.setIcon(QtGui.QIcon(
            ':/plugins/field_annotations/icons/ok.png'))
        okButton.setIconSize(QtCore.QSize(32, 32))
        okButton.setToolButtonStyle(
            QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        okButton.clicked.connect(lambda: self.accept(True))

        buttonBox.addButton(
            cancelButton, QtWidgets.QDialogButtonBox.ButtonRole.RejectRole)
        buttonBox.addButton(
            okButton, QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        self.layout().addWidget(buttonBox)

        okShortcut = QtGui.QShortcut(self)
        okShortcut.setKey(QtGui.QKeySequence('Ctrl+Return'))
        okShortcut.activated.connect(lambda: self.accept(True))

        okShortcut = QtGui.QShortcut(self)
        okShortcut.setKey(QtGui.QKeySequence('Ctrl+S'))
        okShortcut.activated.connect(lambda: self.accept(True))

        okFinishShortcut = QtGui.QShortcut(self)
        okFinishShortcut.setKey(QtGui.QKeySequence('Ctrl+Shift+Return'))
        okFinishShortcut.activated.connect(self.acceptFinish)

        cancelShortcut = QtGui.QShortcut(self)
        cancelShortcut.setKey(QtGui.QKeySequence('Ctrl+Q'))
        cancelShortcut.activated.connect(self.reject)

        self.adjustSize()

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

        self.layer.editBuffer().changeAttributeValues(
            self.feature.id(), {
                self.layer.fields().indexOf('annotation'): annotation,
                self.layer.fields().indexOf('author'): author,
                self.layer.fields().indexOf('dateCreated'): datetime.datetime.now().isoformat()
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
