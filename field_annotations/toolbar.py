from .actions import AnnotatePolygonButton, AnnotateLineButton, AnnotatePointButton


class FieldAnnotationsToolbar:
    def __init__(self, toolbar, main):
        """Initialise the toolbar.

        Add the ToolbarButton to the toolbar.

        Parameters
        ----------
        toolbar : QToolBar
            Reference to toolbar.
        main : ThemeSwitcher
            Reference to main ThemeSwitcher instance.
        """
        self.toolbar = toolbar
        self.main = main

        self.toolbar.addWidget(AnnotatePolygonButton(self.main, self.toolbar))
        self.toolbar.addWidget(AnnotateLineButton(self.main, self.toolbar))
        self.toolbar.addWidget(AnnotatePointButton(self.main, self.toolbar))
