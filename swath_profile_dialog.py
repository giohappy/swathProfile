# -*- coding: utf-8 -*-
"""
/***************************************************************************
 swathProfileDialog
                                 A QGIS plugin
 This plugin creates profiles along a baseline
                             -------------------
        begin                : 2015-06-04
        git sha              : $Format:%H$
        copyright            : (C) 2015 by Maximilian Krambach
        email                : maximilian.krambach@gmx.de
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

import os

from PyQt4 import QtGui, uic

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'swath_profile_dialog_base.ui'))


class swathProfileDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(swathProfileDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.button_box.accepted.connect(self.run)
        self.button_box.rejected.connect(self.close)
        self.cmdBrowseOutput.clicked.connect(self.output_table)
        self.cmdBrowseOutputshp.clicked.connect(self.output_shape)
        
     
    def output_table(self):
       self.tablename= unicode(QtGui.QFileDialog.getSaveFileName(self, "Save File","","*.csv"))
       self.outputTableBox.clear()
       self.outputTableBox.setText(self.tablename)
       
    def output_shape(self):
       self.dirname = unicode(QtGui.QFileDialog.getSaveFileName(self, "Output Shape","","*.shp"))
       self.outputShapeBox.clear()
       self.outputShapeBox.setText(self.dirname)
       
    def run(self):
        pass
        return
    
    def close(self):
        pass


