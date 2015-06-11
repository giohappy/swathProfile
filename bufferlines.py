# -*- coding: utf-8 -*-
"""
/***************************************************************************
 buffer Lines

 This creates buffer lines for a baseline with the ends "cut off"
                              -------------------
        begin                : 2015-06-11
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

from qgis.analysis import QgsGeometryAnalyzer
import math
from PyQt4.QtCore import QCoreApplication, QVariant
from qgis.core import * 


class bufferLines():

    def translate(self,geom,azimuth,buflength):
        dx = math.sin(math.radians(azimuth-90))*buflength
        dy = math.cos(math.radians(azimuth-90))*buflength
        geom.translate(dx,dy)

    def initlayer(self,lyr):
        string = "Linestring?crs=" + self.crs
        layer = QgsVectorLayer(string,"construction layer", "memory")
        return layer

    def createLine(self,buflength,baselinelayer):
        for baseline in baselinelayer.getFeatures(): 
            pid = 0
            #define buffer
            self.buffer = QgsFeature()
            self.buffer.setGeometry(baseline.geometry().buffer(abs(buflength) - 0.000001,20))

            #get every section, translate them
            for point in baseline.geometry().asPolyline():
                vertex= baseline.geometry().vertexAt(pid)
                vertexplusonenr = baseline.geometry().adjacentVertices(pid)[1]
                vertexminusonenr = baseline.geometry().adjacentVertices(pid)[0]
                if vertexminusonenr == -1:
                   vertex2= baseline.geometry().vertexAt(vertexplusonenr)
                   azimuth = vertex.azimuth(vertex2)
                   line = QgsFeature()
                   line.setGeometry(QgsGeometry().fromPolyline([vertex,vertex2]))
                   self.translate(line.geometry(),azimuth,buflength)
                   self.lineprovider.addFeatures([line])
                else:
                    if vertexplusonenr == -1:
                        vertex2= baseline.geometry().vertexAt(vertexminusonenr)
                        line = QgsFeature()
                        line.setGeometry(QgsGeometry().fromPolyline([vertex,vertex2]))
                        self.translate(line.geometry(),azimuth,buflength)
                        self.lineprovider.addFeatures([line])
                    else:
                        vertex2= baseline.geometry().vertexAt(vertexminusonenr)
                        azimuth = vertex2.azimuth(vertex)
                        line = QgsFeature()
                        line.setGeometry(QgsGeometry().fromPolyline([vertex,vertex2]))
                        self.translate(line.geometry(),azimuth,buflength)
                        self.lineprovider.addFeatures([line])
              
                        vertex3= baseline.geometry().vertexAt(vertexplusonenr)
                        azimuth = vertex.azimuth(vertex3)
                        line = QgsFeature()
                        line.setGeometry(QgsGeometry().fromPolyline([vertex,vertex3]))
                  
                        self.translate(line.geometry(),azimuth,buflength)
                        self.lineprovider.addFeatures([line])
                        self.createcurves(buflength,vertex,vertex2,vertex3)
                pid = pid + 1
  

    def createcurves(self,buflength,vertex,vertex2,vertex3):
       diffazimuth = ((vertex2.azimuth(vertex))-(vertex.azimuth(vertex3)))
       step = 0
       if buflength <0:
                  stepfactor = -5
                  while diffazimuth%360<180:
                      azimutha = vertex2.azimuth(vertex) + step
                      azimuthb = vertex2.azimuth(vertex) + step 
                      vertexageom = QgsGeometry().fromPoint(vertex)
                      self.translate(vertexageom,azimutha,buflength)
                      vertexbgeom = QgsGeometry().fromPoint(vertex)
                      self.translate(vertexbgeom,azimuthb,buflength)
                      cl = QgsFeature()
                      cl.setGeometry(QgsGeometry.fromPolyline([vertexageom.asPoint(),vertexbgeom.asPoint()]))
                      self.lineprovider.addFeatures([cl])
                      step = step  + stepfactor
                      diffazimuth = (azimutha - vertex.azimuth(vertex3))%360
                  azimutha = vertex2.azimuth(vertex) + step
                  azimuthb = vertex2.azimuth(vertex) + step - 5
                  vertexageom = QgsGeometry().fromPoint(vertex)
                  self.translate(vertexageom,azimutha,buflength)
                  vertexbgeom = QgsGeometry().fromPoint(vertex)
                  self.translate(vertexbgeom,azimuthb,buflength)
                  cl = QgsFeature()
                  cl.setGeometry(QgsGeometry.fromPolyline([vertexageom.asPoint(),vertexbgeom.asPoint()]))
                  self.lineprovider.addFeatures([cl])  
       else:
           stepfactor = 5
           diffazcondition = diffazimuth%360<180
           while diffazimuth%360>180:
               azimutha = vertex2.azimuth(vertex) + step
               azimuthb = vertex2.azimuth(vertex) + step - 5
               vertexageom = QgsGeometry().fromPoint(vertex)
               self.translate(vertexageom,azimutha,buflength)
               vertexbgeom = QgsGeometry().fromPoint(vertex)
               self.translate(vertexbgeom,azimuthb,buflength)
               cl = QgsFeature()
               cl.setGeometry(QgsGeometry.fromPolyline([vertexageom.asPoint(),vertexbgeom.asPoint()]))
               self.lineprovider.addFeatures([cl])
               step = step  + stepfactor
               diffazimuth = (azimutha - vertex.azimuth(vertex3))%360
              
           azimutha = vertex2.azimuth(vertex) + step
           azimuthb = vertex2.azimuth(vertex) + step - 5
           vertexageom = QgsGeometry().fromPoint(vertex)
           self.translate(vertexageom,azimutha,buflength)
           vertexbgeom = QgsGeometry().fromPoint(vertex)
           self.translate(vertexbgeom,azimuthb,buflength)
           cl = QgsFeature()
           cl.setGeometry(QgsGeometry.fromPolyline([vertexageom.asPoint(),vertexbgeom.asPoint()]))
           self.lineprovider.addFeatures([cl])


    def dissolveBuffer(self, layer, filename):
       QgsGeometryAnalyzer().dissolve(layer,filename)

    def createFlatBuffer(self,baseline,buflength,step,filename):
       #main function
       #init temporary memory layer
       self.crs = baseline.crs().toWkt()
       self.line2layer = self.initlayer("line2layer")
       self.line2provider= self.line2layer.dataProvider()
       self.line2provider.addAttributes([QgsField("d", QVariant.Double)])
       self.line2layer.updateFields()
       
       bufcurrent = - buflength
       while bufcurrent <= buflength:
           self.linelayer = self.initlayer("linelayer")
           self.lineprovider = self.linelayer.dataProvider()
           self.createLine(bufcurrent,baseline)
           self.cleanLine(self.linelayer,bufcurrent)
           bufcurrent = bufcurrent + step

       self.dissolveBuffer(self.line2layer, filename)
       return True, filename



    def cleanLine(self,line, buflength):
        
        for feature in line.getFeatures():
            list = []
            if feature.geometry().intersects(self.buffer.geometry()):
                if feature.id() ==0:
                    pointnull = feature.geometry().asPolyline()[0]
                    if not self.buffer.geometry().contains(pointnull):
                        list.append(pointnull)
                if feature.geometry().adjacentVertices(feature.id())[1] == -1:
                    pointend = feature.geometry().asPolyline()[1]
                    if not self.buffer.geometry().contains(pointend):
                        list.append(pointend)
            for ifeat in self.linelayer.getFeatures():
                if not ifeat.id()==feature.id():
                    if ifeat.geometry().boundingBox().intersects(feature.geometry().boundingBox()):
                        inter = ifeat.geometry().intersection(feature.geometry())
                        if inter.asPoint() == QgsPoint(0,0):
                            pass
                        else:
                            if self.buffer.geometry().contains(inter):
                                pass
                            else:
                                list.append(inter.asPoint())
            
                if len(list) > 1:
                    line = QgsFeature()
                    line.setGeometry(QgsGeometry.fromPolyline(list))
                    line.setAttributes([buflength])
                    self.line2provider.addFeatures([line])     
            else: 
                feature.setAttributes([buflength])
                self.line2provider.addFeatures([feature])
                
        return self.line2layer
