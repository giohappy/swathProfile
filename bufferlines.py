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
        
    def pointAdd(self,vertex,azimuth,bufcurrent): 
        pnkt= QgsFeature()
        pnkt.setGeometry(QgsGeometry().fromPoint(vertex))
        self.translate(pnkt.geometry(),azimuth,bufcurrent)
        self.list.append(pnkt.geometry().asPoint())
  
    def createLine(self,bufcurrent,baselinelayer,step): 
        baselines = baselinelayer.getFeatures()
        for baseline in baselines:
            self.list = []
            pid = 0
            for point in baseline.geometry().asPolyline():
                vertex= baseline.geometry().vertexAt(pid)
                vertexplusonenr = baseline.geometry().adjacentVertices(pid)[1]
                vertexminusonenr = baseline.geometry().adjacentVertices(pid)[0]
                
                if vertexminusonenr == -1: #first point
                   vertex2= baseline.geometry().vertexAt(vertexplusonenr)
                   azimuth = vertex.azimuth(vertex2)
                   if not bufcurrent == 0.0:
                       self.pointAdd(vertex,azimuth,bufcurrent)
                   else:
                       self.list.append(vertex)
                else:
                    if vertexplusonenr == -1: #last point
                        vertex2 = baseline.geometry().vertexAt(vertexminusonenr)
                        azimuth = vertex2.azimuth(vertex)
                        if not bufcurrent == 0.0:
                            self.pointAdd(vertex,azimuth,bufcurrent)
                        else:
                            self.list.append(vertex)
                                                
                    else:#average point: One azimuth upsteam, one downstream
                        vertex3 = baseline.geometry().vertexAt(vertexplusonenr)
                        vertex2 = baseline.geometry().vertexAt(vertexminusonenr)
                        az2 = vertex2.azimuth(vertex)
                        az3 = vertex.azimuth(vertex3)
                        
                        diffazimuth = az2-az3
                        
                        if bufcurrent > 0.0: #positive buffer; different treatment of big and small angles
                            if diffazimuth%360<=180:
                                azimuth = self.meanAzimuth(az2,az3)
                                dist =  self.CalculateSharpDistance(az2,az3,bufcurrent)
                                self.pointAdd(vertex,azimuth,dist)
                            else:          
                                azimutha = az2
                                while diffazimuth%360>180:
                                    self.pointAdd(vertex,azimutha,bufcurrent)
                                    azimutha = azimutha + 5
                                    diffazimuth = (azimutha - az3)%360
                                azimutha = az3 
                                self.pointAdd(vertex,azimutha,bufcurrent)                         
                        else: 
                            if bufcurrent == 0: #Buffer: Zero
                                self.list.append(vertex)
        
                            else:#negative buffer
                               if diffazimuth%360>=180:
                                   azimuth = self.meanAzimuth(az2,az3)
                                   dist =  - self.CalculateSharpDistance(az2,az3,bufcurrent)
                                   self.pointAdd(vertex,azimuth,dist)
                               else: 
                                   azimutha = az2
                                   while diffazimuth%360<180:
                                        self.pointAdd(vertex,azimutha,bufcurrent)
                                        azimutha = azimutha - 5
                                        diffazimuth = (azimutha - az3)%360
                                   azimutha = az3 
                                   self.pointAdd(vertex,azimutha,bufcurrent)
                pid = baseline.geometry().adjacentVertices(pid)[1]
            constructline = QgsFeature()
            templist = []
            a = baseline.geometry().asPolyline()[0]
            templist.append(a)
            for item in self.list:
	        templist.append(item)
            constructline.setGeometry(QgsGeometry().fromPolyline(templist))
            errorlist = []
            errors = constructline.geometry().validateGeometry()
            for error in errors:
                if error.hasWhere():
                  errorlist.append(error.where())
            #get the feature one closer to baseline
            oldbaseline = None
            if bufcurrent == 0:
              expr = ''
            if bufcurrent < 0:
              expr = "d='" + str(bufcurrent + step) + "'"
            if bufcurrent > 0:
              expr =  "d='" + str(bufcurrent - step) + "'"
            
            ob = self.linelayer.getFeatures(QgsFeatureRequest().setFilterExpression(expr))
            for o in ob: 
                oldbaseline = o
            #go through list, check for intersections, create features
            self.linetoaddgeom = []
            self.endlist = []
            
            #state of starting point: outside self
            oin = False
            sin = False
            
            pointid = 0
            for point in constructline.geometry().asPolyline():
                if pointid == 0:
                    pass
                else:
                    if oldbaseline == None:
                        self.endlist.append(point)#baseline is always valid?
                    else:
                        obg = oldbaseline.geometry()
                        vertexminusone = constructline.geometry().vertexAt(pointid - 1) 
                        segbegin = vertexminusone
                        segment = QgsGeometry().fromPolyline([segbegin,point])
                        if self.checkCrossing(segment,errorlist,obg) == True: #while!
                            oin, sin, segbegin = self.doCrossing(segment,errorlist,obg,oin,sin,point)
                            segment = QgsGeometry().fromPolyline([segbegin.asPoint(),point])
                        if oin == False:
                            if sin == False:
                                self.endlist.append(point)
                pointid = pointid +1 
            if len(self.endlist)>1:
                self.linetoaddgeom.append((self.endlist))
            linetoadd = QgsFeature()
            linetoadd.setAttributes([bufcurrent])
            linetoadd.setGeometry(QgsGeometry().fromMultiPolyline(self.linetoaddgeom))
            self.lineprovider.addFeatures([linetoadd])
            #clean up, just to make sure no clutter remains. Probably unneccesary
            del self.list
            del self.linetoaddgeom
            del self.endlist
            del templist
            del errorlist
            
              	
    def createFlatBuffer(self,baseline,buflength,step,filename):#main function
        self.crs = baseline.crs().toWkt()
        string = "LineString?crs=" + self.crs
        self.linelayer = QgsVectorLayer(string,"Buffer Layer", "memory")
        self.lineprovider= self.linelayer.dataProvider()
        self.lineprovider.addAttributes([QgsField('d', QVariant.Double)])
        self.linelayer.updateFields()
        bufcurr = 0 + step
        self.createLine(0,baseline,step)        
        while bufcurr <= buflength:
            self.createLine(-bufcurr,baseline,step)
            self.createLine(bufcurr,baseline,step)
            bufcurr = bufcurr + step
        QgsVectorFileWriter.writeAsVectorFormat(self.linelayer, filename, "utf-8", baseline.crs(), "ESRI Shapefile")

    def meanAzimuth(self,angle1,angle2):#calculate mean angle between two lines
        x = math.cos(math.radians(angle1)) + math.cos(math.radians(angle2))
        y = math.sin(math.radians(angle1))+ math.sin(math.radians(angle2))
        return math.degrees(math.atan2(y,x))
      
    def diffAzimuth(self,angle1,angle2):#calculate angle between two lines
        diff = angle1 - angle2
        if diff < -180:
            dif = diff + 360
        if diff > 180:
            diff = diff -  360
        return diff
     
    def CalculateSharpDistance(self,az2,az3,bufcurrent): #calculate distance on "inner" angles
        half= self.meanAzimuth(az2,az3)
        diff = self.diffAzimuth(az2,half)
        if diff <(-90):
            return (1/ math.cos(math.radians(diff))*bufcurrent)
        else:
            if diff == (-90):
                 return bufcurrent
            else:
                if diff < 0:
                    return -(1/ math.cos(math.radians(diff))*bufcurrent)
                else:
                    if diff <90:
                        return (1/ math.cos(math.radians(diff))*bufcurrent)
                    else:
                        if diff == 90:
                            return bufcurrent
                        else:
                            if diff >90:
                                return -(1/ math.cos(math.radians(diff))*bufcurrent)
                            
    def checkOo(self,segment,obg):#check if crosses oldbaseline. returns intersection or False
        if segment.crosses(obg):
            if segment.intersection(obg).asPoint() != QgsPoint(0,0):
                return segment.intersection(obg)
                
            else:
                return False
        else:
            return False
        
      
    def checkSo(self,segment,errorlist):#check if crosses itself (defined by errorlist). Returns intersection or False
     k = False
     for error in errorlist:
       #ugly hack: add a tiny buffer to error, so line "sees" it
       buf = QgsGeometry().fromPoint(error).buffer(0.00001,5)
       if segment.crosses(buf) == True:
           if segment.intersection(buf).asPoint() != QgsPoint(0,0):
               k = segment.intersection(buf)
     return k
 
    def checkCrossing(self, segment, errorlist,obg): #check if there is any crossing
        oo = self.checkOo(segment, obg)
        so = self.checkSo(segment,errorlist)
        if oo == False:
            if so == False:
                return False
            else:
                return True
        else:
            return True
        
    def goInside(self, vertex): #end a line segment
         self.endlist.append(vertex.asPoint())
         if len(self.endlist)>1:
             self.linetoaddgeom.append(self.endlist)
             del self.endlist
             self.endlist = []

    def doCrossing(self,segment,errorlist,obg,oin,sin,vertex): #actually cross
        so = self.checkSo(segment,errorlist)
        oo = self.checkOo(segment,obg)
        if so == False:
            if oo == False:
                pass #should not happen
            else: 
                oin,k = self.crossO(oin,sin,segment,obg)
        else:
            if oo == False:
                sin,k = self.crossS(oin,sin,segment,errorlist)
            else:
                if self.firstPoint(oo,so,vertex) == False:
                    oin,k = self.crossO(oin,sin,segment,obg)
                else:
                    sin, k = self.crossS(oin,sin,segment,errorlist)
        return oin,sin,k 
      
    def crossO(self,oin,sin,segment,obg):#cross the oldbaseline
        k = self.checkOo(segment,obg)
        if oin == False:
            oin = True
            if sin == False:
                self.goInside(k)
            else:
                pass
        else:
            oin = False
            if sin == True: 
                pass
            else:
                self.endlist.append(k.asPoint())
        return oin, k
     
    def crossS(self,oin,sin,segment, errorlist):#cross itself
        k = self.checkSo(segment,errorlist)
        if sin == False:
            sin = True
            if oin == False:
                self.goInside(k)
            else: #oin == True
                pass
        else:
            sin = False
            if oin == True:
                pass
            else:
                self.endlist.append(k.asPoint())
        return sin, k
    
    def firstPoint(self, v1,v2,v0): #which point is earlier?
        one = v1.distance(QgsGeometry().fromPoint(v0))
        two = v2.distance(QgsGeometry().fromPoint(v0))
        if one > two:
            return False
        else:
            return True