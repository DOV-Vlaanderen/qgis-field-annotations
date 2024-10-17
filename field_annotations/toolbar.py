from .actions import AnnotatePolygonButton, AnnotateLineButton, AnnotatePointButton, ToggleAnnotationViewButton


class FieldAnnotationsToolbar:
    def __init__(self, toolbar, main):
        """Initialise the toolbar.

        Add the AnnotateButtons to the toolbar.

        Parameters
        ----------
        toolbar : QToolBar
            Reference to toolbar.
        main : FieldAnnotations
            Reference to main plugin instance.
        """
        self.toolbar = toolbar
        self.main = main

        self.toolbar.addWidget(AnnotatePolygonButton(self.main, self.toolbar))
        self.toolbar.addWidget(AnnotateLineButton(self.main, self.toolbar))
        self.toolbar.addWidget(AnnotatePointButton(self.main, self.toolbar))
        self.toolbar.addSeparator()
        self.toolbar.addWidget(
            ToggleAnnotationViewButton(self.main, self.toolbar))
