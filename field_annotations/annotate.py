from dataclasses import dataclass
from enum import Enum
import os
from qgis.PyQt import QtCore

from qgis.core import QgsWkbTypes, QgsEditFormConfig, QgsField

from .translate import Translatable
from .dialog import NewAnnotationDialog, NewPhotoAnnotationDialog


class AnnotationType(Enum):
    Point = 1
    Line = 2
    Polygon = 3
    Photo = 4


class AnnotationViewMode(Enum):
    AllAnnotations = 1
    VisibleLayers = 2


class AnnotationErrorType(Enum):
    AlreadyAnnotating = 1
    NoProject = 2
    NoLayers = 3


@dataclass
class ExpressionField:
    expression: str
    field: QgsField


class AnnotationState(QtCore.QObject):
    """Class to save annotation state."""
    stateChanged = QtCore.pyqtSignal()

    def __init__(self, main):
        """Initialisation.

        Parameters
        ----------
        main : FieldAnnotations
            Reference to main plugin instance.
        """
        super().__init__()
        self.main = main

        self.currentAnnotationType = None
        self.currentAnnotationLayer = None
        self.isAnnotating = False

        self.currentAnnotationViewMode = AnnotationViewMode.AllAnnotations

    def setCurrentAnnotationType(self, annotationType):
        """Set annotation state depending on current annotation type.

        Parameters
        ----------
        annotationType : AnnotationType
            Currently active annotation type.
        """
        if annotationType != self.currentAnnotationType:
            self.currentAnnotationType = annotationType
            self.isAnnotating = self.currentAnnotationType is not None
            self.stateChanged.emit()

    def clearCurrentAnnotationType(self):
        """Clear the current annotation type, when annotating is disabled."""
        if self.currentAnnotationType is not None:
            self.currentAnnotationType = None
            self.isAnnotating = False
            self.stateChanged.emit()

    def setCurrentAnnotationLayer(self, layer):
        """Set current annotation layer.

        Parameters
        ----------
        layer : QgsMapLayer
            Layer to save.
        """
        if layer != self.currentAnnotationLayer:
            self.currentAnnotationLayer = layer
            self.stateChanged.emit()

    def clearCurrentAnnotationLayer(self):
        """Clear the current annotation layer."""
        if self.currentAnnotationLayer is not None:
            self.currentAnnotationLayer = None
            self.stateChanged.emit()

    def setCurrentAnnotationViewMode(self, annotationViewMode):
        """Set the current annotation view mode.

        Parameters
        ----------
        annotationViewMode : AnnotationViewMode
            Currently active annotation view mode.
        """
        if not isinstance(annotationViewMode, AnnotationViewMode):
            raise TypeError('Wrong annotationViewMode provided.')

        if self.currentAnnotationViewMode != annotationViewMode:
            self.currentAnnotationViewMode = annotationViewMode
            self.stateChanged.emit()

    def toggleAnnotationViewMode(self):
        """Toggle the current annotation view mode, switch between all annotations and visible layers."""
        newModeMap = {
            AnnotationViewMode.VisibleLayers: AnnotationViewMode.AllAnnotations,
            AnnotationViewMode.AllAnnotations: AnnotationViewMode.VisibleLayers
        }
        self.setCurrentAnnotationViewMode(
            newModeMap.get(self.currentAnnotationViewMode))


class AbstractAnnotator:
    """Abstract base class for Annotators."""

    def __init__(self, main):
        """Initialisation.

        Parameters
        ----------
        main : FieldAnnotations
            Reference to main plugin instance.
        """
        self.main = main

    def getLayer(self):
        """Get the associated data layer, and add it to the map view when necessary.

        Returns
        -------
        QgsVectorLayer
            Data layer to save annotations to.
        """
        layer = self.main.annotationDb.getLayer(self)
        return self.main.annotationView.addLayer(layer, self)

    def getLayerName(self):
        """Get the technical name of the layer.

        Raises
        ------
        NotImplementedError
            Implement this in a subclass.
        """
        raise NotImplementedError

    def getHumanLayerName(self):
        """Get the human readable name of the layer.

        Raises
        ------
        NotImplementedError
            Implement this in a subclass.
        """
        raise NotImplementedError

    def getAnnotationType(self):
        """Get the annotation type of the annotator.

        Raises
        ------
        NotImplementedError
            Implement this in a subclass.
        """
        raise NotImplementedError

    def getGeometryType(self):
        """Get the geometry type of the annotations and the layer.

        Raises
        ------
        NotImplementedError
            Implement this in a subclass.
        """
        raise NotImplementedError

    def getFields(self):
        """Get the necessary fields for this annotation type (and layer)"""
        return [
            QgsField('annotation', QtCore.QVariant.String),
            QgsField('dateCreated', QtCore.QVariant.DateTime),
            QgsField('author', QtCore.QVariant.String),
            QgsField('layerUri', QtCore.QVariant.String),
            QgsField('layerName', QtCore.QVariant.String)
        ]

    def getExpressionFields(self):
        """Get virtual expression fields for this annotation type (and layer)"""
        return []

    def createAnnotation(self):
        """Create a new annotation."""
        layer = self.getLayer()
        self.main.annotationState.setCurrentAnnotationType(
            self.getAnnotationType())

        formConfig = layer.editFormConfig()
        formConfig.setSuppress(QgsEditFormConfig.SuppressOn)
        layer.setEditFormConfig(formConfig)

        if not layer.isEditable():
            layer.startEditing()

        layer.featureAdded.connect(self.featureAdded)
        layer.beforeRollBack.connect(self.disconnectFeatureAdded)
        layer.beforeCommitChanges.connect(self.disconnectFeatureAdded)
        layer.afterRollBack.connect(self.endAnnotate)
        layer.afterCommitChanges.connect(self.endAnnotate)

        self.main.iface.setActiveLayer(layer)
        self.main.iface.actionAddFeature().trigger()

    def disconnectFeatureAdded(self):
        """Disconnect the featureAdded signal."""
        layer = self.getLayer()
        try:
            layer.featureAdded.disconnect(self.featureAdded)
        except TypeError:
            # when not connected we get a TypeError
            pass

    def featureAdded(self, id):
        """Called when a new feature is drawn on the map.

        Open the dialog to write the annotation.

        Parameters
        ----------
        id : int
            Feature id of the newly added feature.
        """
        layer = self.getLayer()

        feature = layer.editBuffer().addedFeatures().get(id)
        if feature is not None:
            self.showAnnotationDialog(layer, feature)

    def showAnnotationDialog(self, layer, feature):
        """Show the new annotation dialog.

        Parameters
        ----------
        layer : QgsVectorLayer
            Vector layer where the annotation will be added.
        feature : QgsFeature
            Annotation feature that was drawn and will be added on accepting the dialog.
        """
        dlg = NewAnnotationDialog(self.main, layer, feature)
        dlg.exec()

        if dlg.shouldStopAnnotating == True:
            self.stopAnnotating()

    def stopAnnotating(self):
        """Stop annotating and commit the changes."""
        layer = self.getLayer()
        self.disconnectFeatureAdded()

        if layer.isEditable():
            layer.commitChanges()

    def endAnnotate(self):
        """End annotating state and disable editing on layer.

        Called automatically after commit, so stopAnnotating() will implicitly call endAnnotate() too.
        """
        layer = self.getLayer()
        self.disconnectFeatureAdded()

        layer.afterRollBack.disconnect(self.endAnnotate)
        layer.afterCommitChanges.disconnect(self.endAnnotate)

        if layer.isEditable():
            layer.endEditCommand()

        self.main.annotationState.clearCurrentAnnotationLayer()
        self.main.annotationState.clearCurrentAnnotationType()


class PointAnnotator(AbstractAnnotator, Translatable):
    """Annotator to create point annotations."""

    def __init__(self, main):
        super().__init__(main)

    def getLayerName(self):
        return 'pointAnnotation'

    def getHumanLayerName(self):
        return self.tr('Point annotations')

    def getGeometryType(self):
        return QgsWkbTypes.Point

    def getAnnotationType(self):
        return AnnotationType.Point


class LineAnnotator(AbstractAnnotator, Translatable):
    """Annotator to create line annotations."""

    def __init__(self, main):
        super().__init__(main)

    def getLayerName(self):
        return 'lineAnnotation'

    def getHumanLayerName(self):
        return self.tr('Line annotations')

    def getGeometryType(self):
        return QgsWkbTypes.LineString

    def getAnnotationType(self):
        return AnnotationType.Line


class PolygonAnnotator(AbstractAnnotator, Translatable):
    """Annotator to create polygon annotations."""

    def __init__(self, main):
        super().__init__(main)

    def getLayerName(self):
        return 'polygonAnnotation'

    def getHumanLayerName(self):
        return self.tr('Polygon annotations')

    def getGeometryType(self):
        return QgsWkbTypes.Polygon

    def getAnnotationType(self):
        return AnnotationType.Polygon


class PhotoAnnotator(AbstractAnnotator, Translatable):
    """Annotator to create photo annotations."""

    def __init__(self, main):
        super().__init__(main)

    def getLayerName(self):
        return 'photoAnnotation'

    def getHumanLayerName(self):
        return self.tr('Photo annotations')

    def getGeometryType(self):
        return QgsWkbTypes.Point

    def getAnnotationType(self):
        return AnnotationType.Photo

    def getFields(self):
        fields = super().getFields()
        fields.extend([
            QgsField('photoPath', QtCore.QVariant.String)
        ])
        return fields

    def getExpressionFields(self):
        fields = super().getExpressionFields()
        fields.extend([
            ExpressionField(expression=f" @project_folder + '{os.sep}' + photoPath ",
                            field=(QgsField('photoPathAbsolute',
                                   QtCore.QVariant.String))
                            )
        ])
        return fields

    def showAnnotationDialog(self, layer, feature):
        """Show the new annotation dialog.

        Parameters
        ----------
        layer : QgsVectorLayer
            Vector layer where the annotation will be added.
        feature : QgsFeature
            Annotation feature that was drawn and will be added on accepting the dialog.
        """
        dlg = NewPhotoAnnotationDialog(self.main, layer, feature)
        dlg.exec()

        if dlg.shouldStopAnnotating == True:
            self.stopAnnotating()
