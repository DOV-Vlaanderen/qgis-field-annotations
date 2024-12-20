# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ThemeSwitcher
                                 A QGIS plugin
 This plugin adds a popup to easily switch between layer themes
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-07-23
        git sha              : $Format:%H$
        copyright            : (C) 2024 by Roel Huybrechts
        email                : roel@huybrechts.re
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication

# Initialize Qt resources from file resources.py
from .resources import *

from .field_annotations.annotate import AnnotationState
from .field_annotations.config import Config
from .field_annotations.data import AnnotationDb
from .field_annotations.mapview import AnnotationView
from .field_annotations.toolbar import FieldAnnotationsToolbar
from .field_annotations.translate import Translatable
from .field_annotations.actions import ConfigurationDialogAction

import os.path


class FieldAnnotations(Translatable):
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Initialise the plugin.

        Setup the translation.

        Parameters
        ----------
        iface : QGisInterface
            Link to the main QGIS interface.
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'FieldAnnotations_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        self.pluginName = self.tr('Field annotations')

        # Declare instance attributes
        self.toolbar = None

        self.config = Config(self)
        self.annotationState = AnnotationState(self)
        self.annotationDb = AnnotationDb(self)
        self.annotationView = AnnotationView(self)

        self.configDialogAction = ConfigurationDialogAction(self)

    def initGui(self):
        """Create the toolbar."""
        self.toolbar = self.iface.addToolBar(self.pluginName)
        FieldAnnotationsToolbar(self.toolbar, self)

        self.iface.addPluginToMenu(self.pluginName, self.configDialogAction)

    def unload(self):
        """Called when disabling the plugin or exiting QGIS.

        Remove the toolbar and close the dialog.
        """
        self.toolbar.parentWidget().removeToolBar(self.toolbar)
        self.iface.removePluginMenu(self.pluginName, self.configDialogAction)
