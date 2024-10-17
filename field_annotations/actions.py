from qgis.PyQt import QtWidgets, QtGui
from qgis.core import QgsProject

from .annotate import AnnotationViewMode, PolygonAnnotator, PointAnnotator, LineAnnotator, AnnotationErrorType
from .translate import Translatable


class AbstractToolbarButton(QtWidgets.QToolButton):
    """Abstract base class for the toolbar buttons."""
    def __init__(self, main, annotator, parent=None):
        """Initialisation.

        Parameters
        ----------
        main : FieldAnnotations
            Reference to main plugin instance.
        annotator : AbstractAnnotator
            Reference to associated Annotator instance.
        parent : QToolBar, optional
            Parent toolbar, by default None
        """
        QtWidgets.QToolButton.__init__(self, parent)

        self.main = main
        self.annotator = annotator

        self.setIcon(QtGui.QIcon(self.getIconPath()))
        self.setToolTip(self.getToolTipValidText(False))
        self.setCheckable(True)

        self.connectPopulate()

        self.clicked.connect(self.run)
        self.populate()

    def getIconPath(self):
        """Get the resource path to the icon.

        Raises
        ------
        NotImplementedError
            Implement this in a subclass.
        """
        raise NotImplementedError

    def getToolTipValidText(self, isAnnotating):
        """Get the valid text for the tooltip.

        Parameters
        ----------
        isAnnotating: bool
            Whether we are currently already annotating.

        Raises
        ------
        NotImplementedError
            Implement this in a subclass.
        """
        raise NotImplementedError

    def getToolTipErrorText(self, annotationErrorType):
        """Get the error text for the tooltip.

        Parameters
        ----------
        annotationErrorType: AnnotationErrorType
            The type of annotation error.

        Raises
        ------
        NotImplementedError
            Implement this in a subclass.
        """
        raise NotImplementedError

    def connectPopulate(self):
        """Connect the populate method to the necessary signals."""
        projectInstance = QgsProject.instance()

        projectInstance.cleared.connect(self.populate)
        projectInstance.readProject.connect(self.populate)
        projectInstance.projectSaved.connect(self.populate)
        projectInstance.layersAdded.connect(self.populate)
        projectInstance.layersRemoved.connect(self.populate)
        self.main.annotationState.stateChanged.connect(self.populate)

        layerTreeRoot = projectInstance.layerTreeRoot()
        layerTreeRoot.visibilityChanged.connect(self.populate)

        self.main.iface.mapCanvas().scaleChanged.connect(self.populate)

    def populate(self):
        """Populate the button state.

        Sets the button state (enabled/disabled and checked/unchecked) and the button tooltip
        depending on the application state.
        """
        hasLayers = len(self.main.annotationView.listAnnotatableLayers()) > 0
        hasProjectPath = len(QgsProject.instance().absolutePath()) > 0

        self.setChecked(self.main.annotationState.currentAnnotationType ==
                        self.annotator.getAnnotationType())

        if hasLayers and hasProjectPath and not self.main.annotationState.isAnnotating:
            self.setEnabled(True)
            self.setToolTip(self.getToolTipValidText(False))
        elif hasLayers and hasProjectPath and self.main.annotationState.isAnnotating:
            self.setEnabled(
                self.main.annotationState.currentAnnotationType == self.annotator.getAnnotationType())
            if self.isEnabled():
                self.setToolTip(self.getToolTipValidText(True))
            else:
                self.setToolTip(self.getToolTipErrorText(
                    AnnotationErrorType.AlreadyAnnotating))
        elif not hasProjectPath:
            self.setEnabled(False)
            self.setToolTip(self.getToolTipErrorText(
                AnnotationErrorType.NoProject))
        else:
            self.setEnabled(False)
            self.setToolTip(self.getToolTipErrorText(
                AnnotationErrorType.NoLayers))
            if self.main.annotationState.isAnnotating:
                self.annotator.stopAnnotating()

    def run(self):
        """Called when the button is clicked.

        Starts or stops the annotator depending on annotation state.
        """
        if not self.main.annotationState.isAnnotating:
            self.annotator.createAnnotation()
        else:
            self.annotator.stopAnnotating()


class AnnotatePolygonButton(AbstractToolbarButton, Translatable):
    """Button to create a polygon annotation."""
    def __init__(self, main, parent=None):
        annotator = PolygonAnnotator(main)
        super().__init__(main, annotator, parent)

    def getIconPath(self):
        return ':/plugins/field_annotations/icons/draw_polygon.png'

    def getToolTipValidText(self, isAnnotating):
        if not isAnnotating:
            return self.tr('Add a polygon annotation')
        else:
            return self.tr('Stop annotating and save pending annotations.')

    def getToolTipErrorText(self, annotationErrorType):
        if annotationErrorType == AnnotationErrorType.AlreadyAnnotating:
            return self.tr('Already annotating, finish annotation first.')
        elif annotationErrorType == AnnotationErrorType.NoProject:
            return self.tr('Cannot annotate without project, save your project first.')
        elif annotationErrorType == AnnotationErrorType.NoLayers:
            return self.tr('No layers available to annotate, add a layer first.')


class AnnotateLineButton(AbstractToolbarButton, Translatable):
    """Button to create a line annotation."""
    def __init__(self, main, parent=None):
        annotator = LineAnnotator(main)
        super().__init__(main, annotator, parent)

    def getIconPath(self):
        return ':/plugins/field_annotations/icons/draw_line.png'

    def getToolTipValidText(self, isAnnotating):
        if not isAnnotating:
            return self.tr('Add a line annotation')
        else:
            return self.tr('Stop annotating and save pending annotations.')

    def getToolTipErrorText(self, annotationErrorType):
        if annotationErrorType == AnnotationErrorType.AlreadyAnnotating:
            return self.tr('Already annotating, finish annotation first.')
        elif annotationErrorType == AnnotationErrorType.NoProject:
            return self.tr('Cannot annotate without project, save your project first.')
        elif annotationErrorType == AnnotationErrorType.NoLayers:
            return self.tr('No layers available to annotate, add a layer first.')


class AnnotatePointButton(AbstractToolbarButton, Translatable):
    """Button to create a point annotation."""
    def __init__(self, main, parent=None):
        annotator = PointAnnotator(main)
        super().__init__(main, annotator, parent)

    def getIconPath(self):
        return ':/plugins/field_annotations/icons/draw_point.png'

    def getToolTipValidText(self, isAnnotating):
        if not isAnnotating:
            return self.tr('Add a point annotation')
        else:
            return self.tr('Stop annotating and save pending annotations.')

    def getToolTipErrorText(self, annotationErrorType):
        if annotationErrorType == AnnotationErrorType.AlreadyAnnotating:
            return self.tr('Already annotating, finish annotation first.')
        elif annotationErrorType == AnnotationErrorType.NoProject:
            return self.tr('Cannot annotate without project, save your project first.')
        elif annotationErrorType == AnnotationErrorType.NoLayers:
            return self.tr('No layers available to annotate, add a layer first.')


class ToggleAnnotationViewButton(QtWidgets.QToolButton, Translatable):
    """Button to toggle between all notes and visible layer notes."""

    def __init__(self, main, parent=None):
        super().__init__(parent)

        self.main = main
        self.setIcon(QtGui.QIcon(
            ':/plugins/field_annotations/icons/map_notes.png'))
        self.setCheckable(True)

        self.connectPopulate()

        self.clicked.connect(self.run)
        self.populate()

    def connectPopulate(self):
        projectInstance = QgsProject.instance()

        projectInstance.cleared.connect(self.populate)
        projectInstance.readProject.connect(self.populate)
        projectInstance.projectSaved.connect(self.populate)
        projectInstance.layersAdded.connect(self.populate)
        projectInstance.layersRemoved.connect(self.populate)
        self.main.annotationState.stateChanged.connect(self.populate)

        layerTreeRoot = projectInstance.layerTreeRoot()
        layerTreeRoot.visibilityChanged.connect(self.populate)

        self.main.annotationState.stateChanged.connect(self.populate)

    def populate(self):
        hasLayers = len(self.main.annotationView.listAnnotatableLayers()) > 0
        hasProjectPath = len(QgsProject.instance().absolutePath()) > 0

        self.setEnabled(hasLayers and hasProjectPath)

        currentMode = self.main.annotationState.currentAnnotationViewMode

        if currentMode == AnnotationViewMode.VisibleLayers:
            self.setChecked(True)
            self.setToolTip(self.tr('Show all annotations.'))
        elif currentMode == AnnotationViewMode.AllAnnotations:
            self.setChecked(False)
            self.setToolTip(
                self.tr('Show annotations for visible layers only.'))

    def run(self):
        self.main.annotationState.toggleAnnotationViewMode()
