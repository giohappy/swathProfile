# -*- coding: utf-8 -*-
"""
/***************************************************************************
 buffer Lines

 This creates non-intersecting buffer lines for a baseline with the ends 
 "cut off".
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

    def createFlatBuffer(self,baselinelayer,buflength,step,filename):
        self.string = "LineString?crs=" + baselinelayer.crs().toWkt()
        self.bstring = "Point?crs=" + baselinelayer.crs().toWkt()
        self.linelayer = QgsVectorLayer(self.string,"Buffer Layer", "memory")
        self.lineprovider= self.linelayer.dataProvider()
        self.lineprovider.addAttributes([QgsField('d', QVariant.Double)])
        self.linelayer.updateFields()
        self.baselinelayer = QgsVectorLayer(self.string,"Baseline layer", "memory")
        self.baselineprovider= self.baselinelayer.dataProvider()
        self.baselinelayer.updateFields()
        self.baselineindex = QgsSpatialIndex()
        self.CreateErrorLayer()
        currentbuffer = -buflength
        baselinelist = []
        linelist = []
        baselines = baselinelayer.getFeatures()
        for baseline in baselines:
            for point in baseline.geometry().asPolyline():
                baselinelist.append(point)
            for i,j in list(enumerate(baselinelist[1:])):
                linelist.append(self.drawLine(j,baselinelist[i]))
            feature=QgsFeature()
            feature.setGeometry(QgsGeometry().fromPolyline(baselinelist))
            self.baselineprovider.addFeatures([feature])
            for feature in self.baselinelayer.getFeatures():
                self.baselineindex.insertFeature(feature)
        while currentbuffer <= buflength:
            baselines = baselinelayer.getFeatures()
            for baseline in baselines:
                if currentbuffer == 0:
                    feature=QgsFeature()
                    feature.setGeometry(QgsGeometry().fromPolyline(baselinelist))
                    feature.setAttributes([0])
                    self.lineprovider.addFeatures([feature])
                else:
                    lineplus=self.createLine(baseline,currentbuffer)
                    self.buildLine(lineplus, currentbuffer,step)
            currentbuffer = currentbuffer + step
        self.writeFile(filename,baselinelayer.crs())
        
    # constructs a list of all points at buffer length
    def createLine(self,baseline,currentbuffer):
        pointid = 0
        blgeom = baseline.geometry()
        pointlist = []
        for point in blgeom.asPolyline():
            vertex = blgeom.vertexAt(pointid)
            vertexup = blgeom.adjacentVertices(pointid)[1]
            vertexdown = blgeom.adjacentVertices(pointid)[0]
            
            if vertexdown == -1:
                vertex2 = blgeom.vertexAt(vertexup)
                azimuth = vertex.azimuth(vertex2)
                pushedpoint = self.pushPoint(vertex,azimuth,currentbuffer)
                pointlist.append(pushedpoint)
                
            if vertexup == -1:
                vertex2 = blgeom.vertexAt(vertexdown)
                azimuth = vertex2.azimuth(vertex)
                pushedpoint = self.pushPoint(vertex,azimuth,currentbuffer)
                pointlist.append(pushedpoint)
                               
            if vertexup != -1 and vertexdown != -1:
                vertex3 = blgeom.vertexAt(vertexup)
                vertex2 = blgeom.vertexAt(vertexdown)
                azimuth2 = vertex2.azimuth(vertex)
                azimuth3 = vertex.azimuth(vertex3)
                diffazimuth = self.diffAzimuth(azimuth2,azimuth3)
               
                if currentbuffer > 0:
                   if diffazimuth<0:
                       point1 = self.pushPoint(vertex,azimuth2,currentbuffer)
                       pointlist.append(point1)
                       point2 = self.pushPoint(vertex,azimuth3,currentbuffer)
                       pointlist.append(point2)
                   else:
                       azimutha = azimuth2
                       while diffazimuth>=0:
                           pushedpoint = self.pushPoint(
                           vertex,azimutha,currentbuffer)
                           pointlist.append(pushedpoint)
                           azimutha = azimutha + 5
                           diffazimuth = self.diffAzimuth(azimutha,azimuth3)
                       pushedpoint = self.pushPoint(
                       vertex,azimuth3,currentbuffer)
                       pointlist.append(pushedpoint)
                else:
                   if diffazimuth>0:
                       point1 = self.pushPoint(vertex,azimuth2,currentbuffer)
                       pointlist.append(point1)
                       point2 = self.pushPoint(vertex,azimuth3,currentbuffer)
                       pointlist.append(point2)
                   else:
                       azimutha = azimuth2
                       while diffazimuth<=0:
                           pushedpoint = self.pushPoint(
                           vertex,azimutha,currentbuffer)
                           pointlist.append(pushedpoint)
                           azimutha = azimutha - 5
                           diffazimuth = self.diffAzimuth(azimutha,azimuth3)
                       pushedpoint = self.pushPoint(
                       vertex,azimuth3,currentbuffer)
                       pointlist.append(pushedpoint)                   
            pointid = pointid + 1
        return pointlist

    #pushes a point a distance
    def pushPoint(self,point,azimuth,dist):
        pushedpoint= QgsFeature()
        pushedpoint.setGeometry(QgsGeometry().fromPoint(point))
        dx = math.sin(math.radians(azimuth-90))*dist
        dy = math.cos(math.radians(azimuth-90))*dist
        pushedpoint.geometry().translate(dx,dy)
        return pushedpoint.geometry().asPoint()
    
    #calculates the difference between bearings
    def diffAzimuth(self,angle1,angle2):
        a = angle2 - angle1
        a = (a + 180) % 360 - 180
        return a
       
    #draws a line from A to B
    def drawLine(self,a,b):
        line = QgsFeature()
        line.setGeometry(QgsGeometry().fromPolyline([a,b]))
        return line.geometry().asPolyline()
         
    #writes linelist(list of line geometries) to file
    def writeLine(self,linelist,currentbuffer):
            linetoadd = QgsFeature()
            linetoadd.setAttributes([currentbuffer])
            linetoadd.setGeometry(QgsGeometry().fromMultiPolyline(
            linelist))
            self.lineprovider.addFeatures([linetoadd])

    #writes the file 
    def writeFile(self,filename,crs):
        QgsVectorFileWriter.writeAsVectorFormat(
        self.linelayer, filename, "utf-8", crs, "ESRI Shapefile")
    
    #takes the point list and constructs lines 
    def buildLine(self,pointlist,currentbuffer,step):
        templine = []
        self.CreateErrorLayer()
        errors = self.validateLine(pointlist,currentbuffer)
        for item in errors:
            a = QgsFeature()
            a.setGeometry(QgsGeometry().fromPoint(item.where()))
            self.errorsprovider.addFeatures([a])
        for item in self.errorslayer.getFeatures():
            self.errorsindex.insertFeature(item)
        for i,j in list(enumerate(pointlist[1:])):
            pointb = j
            pointa = pointlist[i]
            try:
                lastvalid = templine[-1][-1]
                lastvalida = self.ErrorInbetween(lastvalid,pointa,errors)
                if self.AequalsB(lastvalida,pointa) == False:
                    pass
                else:
                    if self.checkIfLineinside(
                    lastvalid,pointa,currentbuffer) == False:
                        templine.append([lastvalid,pointa])
            except IndexError:
                pass
            x = self.ErrorInbetween(pointa,pointb,errors)
            if self.checkIfLineinside(pointa,x,currentbuffer) == False: #this toggles ERROR
                    templine.append([pointa,x])
            while self.AequalsB(x,pointb) == False:
                x2 = x
                x = self.ErrorInbetween(x2,pointb,errors)
                if self.checkIfLineinside(x2,x,currentbuffer) == False:
                    templine.append([x2,x])
        
        self.writeLine(templine,currentbuffer)
        
    #get all errors. Make line longer to capture all errors
    def validateLine(self,pointlist,currentbuffer):
        pointlistcorrected = []
        az = pointlist[0].azimuth(pointlist[1]) -90
        pushedpoint = self.pushPoint(pointlist[0],az,abs(currentbuffer)*10) #TODO get some real value
        pointlistcorrected.append(pushedpoint)
        for item in pointlist:
            pointlistcorrected.append(item)
        az = pointlist[-1].azimuth(pointlist[-2]) -90
        pushedpoint = self.pushPoint(pointlist[-1],az,abs(currentbuffer)*10) #TODO get some real value
        pointlistcorrected.append(pushedpoint)
        a = QgsGeometry().fromPolyline(pointlistcorrected)
        errors = a.validateGeometry()
        return errors
                
    #tests if two points are roughly(0.0000001) equal 
    def AequalsB(self,a,b):
        if QgsGeometry().fromPoint(a).distance(QgsGeometry().fromPoint(b))<0.0000001:
            return True
        else:
            return False
     
       
    #checks if there is an item in errorlist between a and b, 
    #returns first error or b
    def ErrorInbetween(self, a,b, errors):
        fin = b
        errorlist = []
        req = []
        lineab = QgsGeometry().fromPolyline([a,b])
        for idx in self.errorsindex.intersects(lineab.boundingBox()):
            req.append(idx)
        request = QgsFeatureRequest().setFilterFids(req)
        for inter in self.errorslayer.getFeatures(request):
            buf = inter.geometry().buffer(0.000001,5)
            if buf.intersects(lineab) == False:
                pass
            else:
                if self.AequalsB(inter.geometry().asPoint(),a):
                    pass
                else:
                    a1 = buf.intersection(lineab).asPolyline()[0]
                    a2 = buf.intersection(lineab).asPolyline()[1]
                    realintersect = QgsPoint((a1.x()+a2.x())/2,(a1.y()+a2.y())/2)
                    errorlist.append(realintersect)
        currentdistance = lineab.length()
        for item in errorlist:
            if QgsGeometry().fromPoint(item).distance(
                QgsGeometry().fromPoint(a)) < currentdistance:
                currentdistance = QgsGeometry().fromPoint(item).distance(
                QgsGeometry().fromPoint(a))
                fin = item
        return fin
    
    #recreates the error layer and index
    def CreateErrorLayer(self):
        self.errorslayer = QgsVectorLayer(self.bstring,"error layer", "memory")
        self.errorsprovider= self.errorslayer.dataProvider()
        self.errorsindex = QgsSpatialIndex()
        #QgsMapLayerRegistry.instance().addMapLayer(self.errorslayer)
        
    #checks if a or b are inside the dist    
    def checkIfLineinside(self, a, b, dist):
       dist = abs(dist)
       req = []
       for idx in self.baselineindex.nearestNeighbor(a,5):
            req.append(idx)
       for idx in self.baselineindex.nearestNeighbor(b,5):
            req.append(idx)
       request = QgsFeatureRequest().setFilterFids(req)
       for nearline in self.baselinelayer.getFeatures(request):
          if QgsGeometry().fromPoint(a).distance(
          nearline.geometry()) < (dist - dist/1000):
              return True
          if QgsGeometry().fromPoint(b).distance(
          nearline.geometry()) < (dist - dist/1000):
              return True
       return False
   
   #TODO check if step and buflength add up, else center on 0