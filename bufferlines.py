# -*- coding: utf-8 -*-
"""
/***************************************************************************
 buffer Lines

 This creates buffer lines for a baseline with the ends "cut off".
 
 Main Flow: createFlatBuffer -> createLine ->  buildLine
 
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
        self.linelayer = QgsVectorLayer(self.string,"Buffer Layer", "memory")
        self.lineprovider= self.linelayer.dataProvider()
        self.lineprovider.addAttributes([QgsField('d', QVariant.Double)])
        self.linelayer.updateFields()
        self.oldselflayer = QgsVectorLayer(self.string,"Temp Layer", "memory")
        self.oldselfprovider= self.oldselflayer.dataProvider()
        self.oldselfprovider.addAttributes([QgsField('d', QVariant.Double)])
        self.oldselflayer.updateFields()
        self.getSelfLayer()
        self.selfindex = QgsSpatialIndex()
        self.oldindex = QgsSpatialIndex()
        currentbuffer = 0 + step
        #2. copy the baseline
        baselinelist = []
        linelist = []
        baselines = baselinelayer.getFeatures()
        for baseline in baselines:
            for point in baseline.geometry().asPolyline():
                baselinelist.append(point)
            self.constructPhantomLine(baselinelist, 0)
            for feature in self.selflayer.getFeatures():
                self.selfindex.insertFeature(feature)
            for i,j in list(enumerate(baselinelist[1:])):
                linelist.append(self.drawLine(j,baselinelist[i]))
        self.writeLine(linelist,0)
        #3. loop through steps for each (for now being one) baseline
        while currentbuffer <= buflength:
            baselines = baselinelayer.getFeatures()
            for baseline in baselines:
                lineplus=self.createLine(baseline,currentbuffer)
                lineminus=self.createLine(baseline,0-currentbuffer)
                self.firstline = QgsGeometry().fromPolyline(
                [lineminus[0],lineplus[0]])
                self.endline = QgsGeometry().fromPolyline(
                [lineminus[-1],lineplus[-1]])
                self.putInOldIndex()
                self.constructPhantomLine(lineplus,currentbuffer)
                self.constructPhantomLine(lineminus,currentbuffer)
                self.selfindex = QgsSpatialIndex()
                for feature in self.selflayer.getFeatures():
                    self.selfindex.insertFeature(feature)
                self.buildLine(lineplus,currentbuffer,step)
                self.buildLine(lineminus,0-currentbuffer,step)
            currentbuffer = currentbuffer + step
        self.writeFile(filename,baselinelayer.crs())
        
    def constructPhantomLine(self,pointlist,currentbuffer):
        linelist = []
        for i,j in list(enumerate(pointlist[1:])):
            linelist.append(self.drawLine(j,pointlist[i]))
        for line in linelist:
            feature=QgsFeature()
            feature.setGeometry(QgsGeometry().fromPolyline(line))
            feature.setAttributes([currentbuffer])
            self.selfprovider.addFeatures([feature])
            
    # constructs a list of all points at buffer length
    def createLine(self,baseline,currentbuffer):
        pointid = 0
        blgeom = baseline.geometry()
        #create list of points to be connected 
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
                pushedpoint2 = self.pushPoint(vertex,azimuth,
                0 - currentbuffer)
                self.ceroline = QgsGeometry().fromPolyline([
                pushedpoint2,vertex,pushedpoint])
            
            if vertexup == -1:
                vertex2 = blgeom.vertexAt(vertexdown)
                azimuth = vertex2.azimuth(vertex)
                pushedpoint = self.pushPoint(vertex,azimuth,currentbuffer)
                pointlist.append(pushedpoint)
                pushedpoint2 = self.pushPoint(vertex,azimuth,0 - currentbuffer)
                self.endline = QgsGeometry().fromPolyline([
                pushedpoint2,vertex,pushedpoint])
                
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

    #calculates the mean azimuth
    def meanAzimuth(self,angle1,angle2):
        x = math.cos(math.radians(angle1)) + math.cos(math.radians(angle2))
        y = math.sin(math.radians(angle1)) + math.sin(math.radians(angle2))
        return math.degrees(math.atan2(y,x))    
    
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
       
    #puts self.indexed stuff to oldindex and clears selfindex
    def putInOldIndex(self): 
        self.oldindex = QgsSpatialIndex()
        for feature in self.selflayer.getFeatures():
            f = QgsFeature()
            f.setGeometry(feature.geometry())
            f.setAttributes([feature['d']])
            self.oldselfprovider.addFeatures([f])
        for feature in self.oldselflayer.getFeatures():#TODO switch for 2.8 and later for faster indexing
            self.oldindex.insertFeature(feature)
        del self.selflayer
        self.getSelfLayer()
        self.selfindex = QgsSpatialIndex()
       
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

    #wites the file 
    def writeFile(self,filename,crs):
        QgsVectorFileWriter.writeAsVectorFormat(
        self.linelayer, filename, "utf-8", crs, "ESRI Shapefile")
    
    #takes the point list and paints lines by 
    #checking against spatial index crossings TODO too slow
    def buildLine(self,pointlist,currentbuffer,step):
        linelist = []
        templine = []
        for i,j in list(enumerate(pointlist[1:])):
            pointb = j
            pointa = pointlist[i]
            laststate = False
            #first point
            if i == 0:
                if self.checkifInside(pointa,step) == False:
                    templine.append(pointa)
                    laststate = False
            pointx = self.checkCrossings(pointa,pointb)
            while self.AequalsB(pointx,pointb) == False:
                if self.checkifInside(pointx,step) == False:
                    if laststate == True:
                        try:
                            x = self.checkCrossings(templine[-1],pointx)
                            if self.AequalsB(x,pointx) == False:
                                templine = []
                        except IndexError:
                            pass
                    templine.append(pointx)
                    laststate = False
                else: 
                    if laststate == False:
                        if len(templine) > 1:
                            linelist.append(QgsGeometry().
                            fromPolyline(templine).asPolyline())
                        try:
                            templine = [templine[-1]]
                        except IndexError:
                            templine = []
                    laststate = True
                pointx = self.checkCrossings(pointx,pointb)
            if self.checkifInside(pointb,step) == False:
                if laststate == True:
                    try: 
                        x = self.checkCrossings(templine[-1],pointb)
                        if self.AequalsB(x,pointb) == False:
                           templine = []
                    except IndexError:
                        pass
                templine.append(pointb)
                laststate = False
            else:
                if laststate == False:
                    if len(templine) > 1:
                        linelist.append(QgsGeometry().
                        fromPolyline(templine).asPolyline())
                    try:
                        templine = [templine[-1]]
                    except IndexError:
                        templine = []
                laststate = True
        if laststate == False:
            if len(templine) > 1:
               linelist.append(QgsGeometry().fromPolyline(templine).asPolyline())
            templine = []    
        self.writeLine(linelist,currentbuffer)
        
    #checks if line intersects any existing lines TODO too slow
    def checkCrossings(self,a,b):
        crossing = b
        line = QgsGeometry().fromPolyline([a,b])
        req = []
        intersections = []     
        for idx in self.oldindex.intersects(line.boundingBox()):
            req.append(idx)
        request = QgsFeatureRequest().setFilterFids(req)
        for segment in self.oldselflayer.getFeatures(request):
            if segment.geometry() == None:
               pass
            else:
                if segment.geometry().equals(line)== True:
                    pass
                else:
                    if segment.geometry().intersects(line) == True: 
                        intersections.append(
                        segment.geometry().intersection(line))
                    else:
                        pass
        req = []
        for idx in self.selfindex.intersects(line.boundingBox()):
            req.append(idx)
        request = QgsFeatureRequest().setFilterFids(req)
        for segment in self.selflayer.getFeatures(request):
            if segment.geometry() == None:
               pass
            else:
                if segment.geometry().equals(line)== True:
                    pass
                else:
                    if segment.geometry().intersects(line) == True: 
                        intersections.append(
                        segment.geometry().intersection(line))
                    else:
                        pass
        if self.firstline.intersects(line) == True:
            intersections.append(self.firstline.intersection(line))
        if self.endline.intersects(line) == True:
            intersections.append(self.endline.intersection(line))    
        currentdistance = line.length()
        for inter in intersections:
            if self.AequalsB(inter.asPoint(),a) == True:
                pass
            else:
                dist = QgsGeometry().fromPoint(
                inter.asPoint()).distance(QgsGeometry().fromPoint(a))
                if dist < currentdistance:
                    if dist > 0.0000001:
                        currentdistance = dist
                        crossing  = inter.asPoint()
        return crossing
        
        
    #check if a is too close to oldfeatures
    def checkifInside(self, a, step):
       req = []
       for idx in self.oldindex.nearestNeighbor(a,10):
            req.append(idx)
       request = QgsFeatureRequest().setFilterFids(req)
       near = False
       for nearline in self.oldselflayer.getFeatures(request):
          geom = QgsGeometry().fromPoint(a)
          if geom.distance(nearline.geometry()) < (step - step/100): 
             near = True
       return near
                
    #tests if two points are roughly(0.0000001) equal #TODO eats up time
    def AequalsB(self,a,b):
        buf = QgsGeometry().fromPoint(a).buffer(0.0000001,10)
        if buf.contains(b) == True:
            return True
        else:
            return False        
     
    #recreates self.selflayer 
    def getSelfLayer(self):
        self.selflayer = QgsVectorLayer(self.string,"Temp Layer", "memory")
        self.selfprovider= self.selflayer.dataProvider()
        self.selfprovider.addAttributes([QgsField('d', QVariant.Double)])
        self.selflayer.updateFields()