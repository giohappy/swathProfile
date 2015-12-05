# -*- coding: utf-8 -*-
"""
/***************************************************************************
 swathProfile
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
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication,\
QFileInfo, QVariant
from PyQt4.QtGui import QAction, QIcon, QMessageBox
from qgis.analysis import QgsGeometryAnalyzer
from qgis.core import * 
import resources_rc
from swath_profile_dialog import swathProfileDialog
from bufferlines import bufferLines
import os.path
import os, math
import numpy

class swathProfile:

    def __init__(self, iface):
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'swathProfile_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)
        # Create the dialog (after translation) and keep reference
        self.dlg = swathProfileDialog()
        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&swath profile')
        self.toolbar = self.iface.addToolBar(u'swathProfile')
        self.toolbar.setObjectName(u'swathProfile')

    def tr(self, message):
        return QCoreApplication.translate('swathProfile', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToRasterMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        icon_path = ':/plugins/swathProfile/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'swath profile'),
            callback=self.run,
            parent=self.iface.mainWindow())

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginRasterMenu(
                self.tr(u'&swath profile'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def run(self):
        # show the dialog, loop the GUI until each required parameter is checked
        chekk = False
        self.dlg.inputRasterBox.clear()
        self.dlg.inputBaselineBox.clear()
        layers = QgsMapLayerRegistry.instance().mapLayers().values()
        for layer in layers:
            if layer.type() == QgsMapLayer.VectorLayer and\
            layer.geometryType() == QGis.Line:
                self.dlg.inputBaselineBox.addItem( layer.name(), layer )
            if layer.type() == QgsMapLayer.RasterLayer:
                self.dlg.inputRasterBox.addItem( layer.name(), layer )
        while chekk != True:
            self.dlg.show()
            result = self.dlg.exec_()
            #if okay pressed, check for parameters
            if result: 
              chekk = self.checkempties()
              if chekk==True:
                  self.operate()
              else:
                  break
            else:
              chekk = True #end check loop and stop running
            
    def checkempties(self):# check if all input criteria are met
      index = self.dlg.inputBaselineBox.currentIndex()
      self.baselinelayer= self.dlg.inputBaselineBox.itemData(index)
      index = self.dlg.inputRasterBox.currentIndex()
      self.raster= self.dlg.inputRasterBox.itemData(index)
      self.file_to_store = self.dlg.outputTableBox.text()
      self.linesshape = self.dlg.outputShapeBox.text()
      
      if self.baselinelayer == None:
          QMessageBox.information(None, "swath profile",
          "No baseline layer detected")
          return False
      else:
        if self.baselinelayer.isValid():
            features = self.baselinelayer.getFeatures()
            count = 0
            for f in features:
                count = count +1
            if count > 1:
                QMessageBox.information(None, "swath profile", 
                "Too many lines. Only one feature is supported for now")
                return False
            else:
                if self.raster == None:
                    QMessageBox.information(None, "swath profile",
                    "No raster to sample found.")
                    return False
                else:
                    if self.file_to_store == "":
                      QMessageBox.information(None, "swath profile", 
                      "No output table. Please specifiy an output table.")
                      return False
                    else:
                        self.remove(self.file_to_store, '\/:*?"<>|\x00')
                        if os.path.exists(self.file_to_store):
                            pass
                        else:
                            if os.access(os.path.dirname(self.file_to_store),
                            os.W_OK):
                                pass
                            else:
                                QMessageBox.information(None, "swath profile", 
                                "Invalid output table filename. \
                                Please specifiy a writable filename.")
                                return False
                        if self.linesshape == "": 
                          QMessageBox.information(None, "swath profile", 
                          "No output line shape. Please specifiy an shapefile \
                          for the output swath lines.")
                          return False
                        else:
                            self.remove(self.linesshape,'\/:*?"<>|\x00')
                            if self.linesshape.endswith(".shp"):
                                pass
                            else:
                                self.linesshape = self.linesshape + ".shp"
                            if os.path.exists(self.linesshape):
                                return True
                            else:
                                if os.access(os.path.dirname(self.file_to_store),
                                os.W_OK):
                                    return True
                                else:
                                    QMessageBox.information(None, "swath profile", 
                                    "Invalid output shape filename. Please \
                                    specifiy a writable filename.")
                                    return False                    
        else:
            QMessageBox.information(None, "swath profile", 
            "No valid baseline layer found.")
            return False
      
    def operate(self): #run. First, create buffer lines, and then sample
      self.profLen = float(self.dlg.lengthProfilesBox.text())
      self.splitLen = float(self.dlg.distProfilesBox.text())
      self.res = float(self.dlg.resolutionBox.text())
      #create lines for profile. In extra file
      bufferLines().createFlatBuffer(self.baselinelayer,
                self.profLen,self.res,self.linesshape)
      self.lineshapelayer = QgsVectorLayer(
      self.linesshape, "Lineshapelayer", "ogr")
      QgsMapLayerRegistry.instance().addMapLayer(self.lineshapelayer)
      self.opened_file= os.open(self.file_to_store,os.O_CREAT|os.O_RDWR)
      #write header
      data = "dist, median, mean, min, max, sd, quart25,quart75, sample size\n"
      os.write(self.opened_file, data)
      #aggregate values
      for f in self.lineshapelayer.getFeatures():
          samplelen=0
          self.datalist =[]        
          segmentlen = f.geometry().length()
          while samplelen <= segmentlen:
              qpoint = f.geometry().interpolate(samplelen).asPoint()
              ident = self.raster.dataProvider().identify(qpoint,
              QgsRaster.IdentifyFormatValue)
              self.position= f['d']
              try:
                  if ident.results()[1] == None:
                      pass
                  else:
                      self.datalist.append(ident.results()[1])
              except KeyError:
                  pass
              samplelen = samplelen+self.splitLen
              
          self.aggregate(self.datalist)
      os.close(self.opened_file)

    def aggregate(self,datalist): #aggregate data
        if len(datalist) != 0:
            nmedian = str(numpy.median(datalist))
            nmean = str(numpy.mean(datalist))
            nmin = str(numpy.min(datalist))
            nmax = str(numpy.max(datalist))
            nsd = str(numpy.std(datalist))
            nq25 = str(numpy.percentile(datalist,25))
            nq75 = str(numpy.percentile(datalist,75))
            nn = str(len(datalist))
            data = str(self.position)+","+nmedian+","+ nmean+ ","+ nmin+ ","\
            + nmax+ ","+nsd+ "," + nq25+ ","+nq75+","+nn+"\n"
            os.write(self.opened_file, data)
        else:
            data = str(self.position)+",,,,,,,,\n"
            os.write(self.opened_file, data)
    def remove(self,value, deletechars):
        for c in deletechars:
            value = value.replace(c,'')
        return value;
       
           
           
      
#TODO:
#reprojection before querying
#replacing csv instead of only appending