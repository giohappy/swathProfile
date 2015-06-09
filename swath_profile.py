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
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QFileInfo, QVariant
from PyQt4.QtGui import QAction, QIcon, QMessageBox
from qgis.analysis import QgsGeometryAnalyzer
from qgis.core import * 
# Initialize Qt resources from file resources.py
import resources_rc
# Import the code for the dialog
from swath_profile_dialog import swathProfileDialog
import os.path
import os, math
import numpy


class swathProfile:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
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
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'swathProfile')
        self.toolbar.setObjectName(u'swathProfile')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
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
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

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
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

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
        # show the dialog
        #loop the GUI until each required parameter is checked
        chekk = "0"
        self.dlg.inputRasterBox.clear()
        self.dlg.inputBaselineBox.clear()
        layers = QgsMapLayerRegistry.instance().mapLayers().values()
        for layer in layers:
            if layer.type() == QgsMapLayer.VectorLayer and layer.geometryType() == QGis.Line:
                self.dlg.inputBaselineBox.addItem( layer.name(), layer )
            if layer.type() == QgsMapLayer.RasterLayer:
                self.dlg.inputRasterBox.addItem( layer.name(), layer )
        while chekk != "1":
            self.dlg.show()
            result = self.dlg.exec_()
            #if okay pressed, check for parameters
            if result: #if okay is pressed
              chekk = self.checkempties() #check parameters
              if chekk=="1":
                  self.operate()
            else:
              chekk = "1" #end check loop and stop running
            
    def checkempties(self):
      #check if all input criteria are met   
      
      index = self.dlg.inputBaselineBox.currentIndex()
      self.baselinelayer= self.dlg.inputBaselineBox.itemData(index)
      index = self.dlg.inputRasterBox.currentIndex()
      self.raster= self.dlg.inputRasterBox.itemData(index)
      self.file_to_store = self.dlg.outputTableBox.text()
      self.linesshape = self.dlg.outputShapeBox.text()
      
      if self.baselinelayer == None:
          #error
          QMessageBox.information(None, "swath profile", "No baseline layer detected")
          return "0"
      else:
        if self.baselinelayer.isValid():
            features = self.baselinelayer.getFeatures()
            count = 0
            for f in features:
                count = count +1
            if count > 1:
                QMessageBox.information(None, "swath profile", "Too many lines in the baselinlayer. Only one feature in the layer is supported for now")
                return "0"
            else:
                if self.raster != None:
                    #check outputtable 
                    if self.file_to_store == "":
                      QMessageBox.information(None, "swath profile", "No output table. Please specifiy an output table.")
                      return "0"
                    else:
                        #check shapefileoutput
                        if self.linesshape == "":
                          QMessageBox.information(None, "swath profile", "No output line shape. Please specifiy an shapefile for the output swath lines.")
                          return "0"
                        else:
                            if self.linesshape.endswith(".shp"):
                              return "1"
                            else:
                                self.linesshape = self.linesshape + ".shp"
                                return "1"
                else:
                    QMessageBox.information(None, "swath profile", "No raster to sample found.")
                    return "0"
        else:
            QMessageBox.information(None, "swath profile", "No line layer found.")
            return "0"
      
      
    
    def operate(self):
      #run
      #define variables
      self.profLen = float(self.dlg.lengthProfilesBox.text())
      self.splitLen = float(self.dlg.distProfilesBox.text())
      self.res = float(self.dlg.resolutionBox.text())
      #create lines for profile
      self.createlines()
        
      #query along lines
      
      self.opened_file= os.open(self.file_to_store,os.O_APPEND|os.O_CREAT|os.O_RDWR)

      data = "dist, median, mean, min, max, sd, quart25,quart75\n"
      os.write(self.opened_file, data)


      samplelen=0
      baselines = self.baselinelayer.getFeatures()
      for baseline in baselines:
        segmentlen = baseline.geometry().length()
        datalist =[]         
        while samplelen <= segmentlen:
          qpoint = baseline.geometry().interpolate(samplelen).asPoint()
          ident = self.raster.dataProvider().identify(qpoint, QgsRaster.IdentifyFormatValue)
          position= 0
          
          try:
            datalist.append(ident.results()[1]) 
          except KeyError:
            pass
          samplelen=samplelen+self.splitLen
        nmean = str(numpy.mean(datalist))
        nmedian = str(numpy.median(datalist))
        nmin = str(numpy.min(datalist))
        nmax = str(numpy.max(datalist))
        nsd = str(numpy.std(datalist))
        nq25 = str(numpy.percentile(datalist,25))
        nq75 = str(numpy.percentile(datalist,75))
        data = "0,"+ nmedian+ "," + nmean+ ","+nmin + ","+ nmax+ ","+nsd+ ","+  nq25+ ","+ nq75+"\n"
        os.write(self.opened_file, data)
          
      lines = self.lineshapelayer.getFeatures()
      for feature in lines:
        samplelen=0
        datalist =[]        
        segmentlen = feature.geometry().length()
        while samplelen <= segmentlen:
          qpoint = feature.geometry().interpolate(samplelen).asPoint()
          ident = self.raster.dataProvider().identify(qpoint, QgsRaster.IdentifyFormatValue)
          position= feature['d']
          try:
            datalist.append(ident.results()[1])
          except KeyError:
            pass
          finally:
            samplelen = samplelen+self.splitLen

        nmedian = str(numpy.median(datalist))
        nmean = str(numpy.mean(datalist))
        nmin = str(numpy.min(datalist))
        nmax = str(numpy.max(datalist))
        nsd = str(numpy.std(datalist))
        nq25 = str(numpy.percentile(datalist,25))
        nq75 = str(numpy.percentile(datalist,75))
        data = str(position)+","+nmedian+","+ nmean+ ","+ nmin+ ","+ nmax+ ","+nsd+ "," + nq25+ ","+nq75+"\n"
        os.write(self.opened_file, data)
        
      os.close(self.opened_file)
      
              
    def createlines(self):
      baselinecrs= self.baselinelayer.crs()
      epsg = baselinecrs.toWkt()
      tmpf= "LineString?crs="+ epsg
      self.linelayer = QgsVectorLayer(tmpf, "Sample lines", "memory")
      self.lineprovider = self.linelayer.dataProvider()
      res = self.linelayer.dataProvider().addAttributes([QgsField("d", QVariant.Double)])
      self.linelayer.updateFields()
      
      baselines= self.baselinelayer.getFeatures()
      for baseline in baselines:
        profilepos = 0 + self.res
        while profilepos <= (self.profLen/2):
          #buffer
          bufferfeature= QgsFeature()
          baselinebuffer=baseline.geometry().buffer(profilepos,20)
          bufferfeature.setGeometry(baselinebuffer)
          
          #calculate cutline 1
          
          vertexplusone= baseline.geometry().interpolate(0.001).asPoint()
          vertex = baseline.geometry().interpolate(0).asPoint()
          azimuth = (vertex.azimuth(vertexplusone)*math.pi/180) - math.pi
          deltax= math.cos(math.pi - azimuth)* (self.profLen/2 + self.res)
          deltay= math.sin(azimuth)* (self.profLen/21123 + self.res)
          newpx = vertex.x()+ deltax
          newpy = vertex.y()+ deltay
          newpxo = vertex.x()- deltax
          newpyo = vertex.y()- deltay
          cutline1= QgsFeature()
          cutline1.setGeometry(QgsGeometry.fromPolyline([QgsPoint(newpx,newpy),QgsPoint(vertex.x(),vertex.y()),QgsPoint(newpxo,newpyo)]))
          
          #calculate cutline 2
          vertexminusone= baseline.geometry().interpolate((baseline.geometry().length())- 0.001).asPoint()
          vertex = baseline.geometry().interpolate(baseline.geometry().length()).asPoint()
          azimuth = (vertex.azimuth(vertexminusone)*math.pi/180) - math.pi
          deltax= math.cos(math.pi - azimuth)* (self.profLen/2 + self.res)
          deltay= math.sin(azimuth)* (self.profLen/2 + self.res)
          newpx = vertex.x()+ deltax
          newpy = vertex.y()+ deltay
          newpxo = vertex.x()- deltax
          newpyo = vertex.y()- deltay
          cutline2= QgsFeature()
          cutline2.setGeometry(QgsGeometry.fromPolyline([QgsPoint(newpx,newpy),QgsPoint(vertex.x(),vertex.y()),QgsPoint(newpxo,newpyo)]))
          
          #cut at cutlines
          bufferfeature.geometry().reshapeGeometry(cutline2.geometry().asPolyline())
          bufferfeature.geometry().reshapeGeometry(cutline1.geometry().asPolyline())
          
          vertexcount= 0
          for x in bufferfeature.geometry().asPolygon():
            for z in x:
              vertexcount = vertexcount+1    
          i = 1
          while i <= vertexcount:
            ver= bufferfeature.geometry().adjacentVertices(i-1)[1]
            vertd= bufferfeature.geometry().vertexAt(ver)
            vert = bufferfeature.geometry().vertexAt(i-1)
            line=QgsFeature()
            line.setGeometry(QgsGeometry.fromPolyline([vertd, vert]))
            
            k= line.geometry().asPolyline()
            if k[0].azimuth(k[1])> 0:
              profileps = 0 - profilepos
            else:
              profileps = profilepos
            line.setAttributes([profileps])
            i=i+1
            if not line.geometry().intersects(baseline.geometry()):
              self.lineprovider.addFeatures([line])
          
          profilepos = profilepos + self.res
          self.linelayer.updateExtents()
        QgsGeometryAnalyzer().dissolve(self.linelayer, self.linesshape, onlySelectedFeatures=False, uniqueIdField=0,p=None)
        self.lineshapelayer = QgsVectorLayer(self.linesshape, "distance lines", "ogr")
        QgsMapLayerRegistry.instance().addMapLayer(self.lineshapelayer)
        self.lineshapelayer.updateExtents()
