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
            
            
            #construction site: for checking if we intersect ourselves or are inside the buffer
            
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
                  
            #get the feature one inside
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

            #go through list, check for intersections, creatre features
            
            self.linetoaddgeom = []
            pointid = 0
            oldinside = False
            if abs(bufcurrent) == (0 + step):
                oldinside = False
            selfinside = False
            self.endlist = []
            
            for point in constructline.geometry().asPolyline():
                if pointid == 0:#first point, definitely "outside"
                    pass
                else:
                    if pointid == 1:
                        if oldbaseline == None:
                            self.endlist.append(point)
                        else:
                            obg = oldbaseline.geometry()
                            vertexminusone = constructline.geometry().vertexAt(pointid - 1)
                            segment = QgsGeometry().fromPolyline([vertexminusone,point])
                            d = self.checkBoth(segment,errorlist,obg)
                            while d > 0:
                                if d == 1:
                                    k = self.checkOo(segment,obg)#HERE ERROR
                                    if oldinside == True:
                                       oldinside = False
                                    else:
                                        oldinside = True
                                else:
                                    k = self.checkSo(segment,errorlist)
                                    if selfinside == True:
                                        selfinside = False
                                    else:
                                        selfinside = True
                                segment = QgsGeometry().fromPolyline([k,point])
                                d = self.checkBoth(segment,errorlist,obg)
                            
                            if selfinside == False:
                                if oldinside == False:
                                    self.endlist.append(point)
                                                      
                    else:
                        if oldbaseline == None:#assuming that the baseline is valid
                            self.endlist.append(point)
                        else:#oldbaseline exists. 
                            obg = oldbaseline.geometry()
                            vertexminusone = constructline.geometry().vertexAt(pointid - 1)
	                    segment = QgsGeometry().fromPolyline([vertexminusone,point])
                            d = self.checkBoth(segment,errorlist,obg)
                            while d > 0:
                                if d == 1:
                                    k = self.checkOo(segment,obg)
                                    if oldinside == True:
                                        oldinside = False
                                        if selfinside == True:
                                            pass
                                        else: 
                                            self.endlist.append(k)
                                    else:
                                        oldinside = True
                                        if selfinside == True:
                                            pass
                                        else:
                                            self.goInside(k)
                                else:
                                    if d == 2:
                                        k = self.checkSo(segment,errorlist)
                                        if selfinside == True:
                                            selfinside = False
                                            if oldinside == True:
                                                pass
                                            else:
                                                self.endlist.append(k)
                                        else:
                                            selfinside = True
                                            if oldinside == True:
                                                pass
                                            else:
                                                self.goInside(k)
                                segment = QgsGeometry().fromPolyline([k,point])
                                d = self.checkBoth(segment,errorlist,obg)
                            if selfinside == False:
                                if oldinside == False:
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

    def meanAzimuth(self,angle1,angle2):#calculate the mean bering between two lines
        x = math.cos(math.radians(angle1)) + math.cos(math.radians(angle2))
        y = math.sin(math.radians(angle1))+ math.sin(math.radians(angle2))
        return math.degrees(math.atan2(y,x))
      
    def diffAzimuth(self,angle1,angle2):#calculates the the angle between two lines
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
                            

    def goInside(self,k): #write a point and then prepare for dump to to feature
         self.endlist.append(k)
         if len(self.endlist) > 1:
             self.linetoaddgeom.append(self.endlist)
         del self.endlist
         self.endlist = []
    
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
        
    def checkOo(self,segment,obg):#check if crosses oldbaseline. returns intersection or False # TODO what if there's TWO?
        if segment.crosses(obg):
            seg = segment
            #get all bits and return the one which is earliest TODO dirty
            dummy, bits, dummy2 = seg.splitGeometry(obg.asPolyline(),False)
            bits.append(seg)
            if len(bits) <= 1:
                return False
            else:
                for bit in bits:
                    points = [bit.asPolyline()[0], bit.asPolyline()[1]]
                    pd = segment.length()
                for point in points:
                    pt =QgsGeometry().fromPoint(point).distance(QgsGeometry().fromPoint(segment.asPolyline()[0])) 
                    if pt < pd:
                        if pt > 0:
                            pd = QgsGeometry().fromPoint(point).distance(QgsGeometry().fromPoint(segment.asPolyline()[0]))
                            x = point
                return x
        else:
            return False
            
    def checkSo(self,segment,errorlist):#check if crosses itself (defined by errorlist). Returns intersection or False
     k = False
     count = 0
     for error in errorlist:
       if error == segment.asPolyline()[0]:
           pass
       else:
           if error == segment.asPolyline()[1]:
               pass
           else: 
               if error.onSegment(segment.asPolyline()[0],segment.asPolyline()[1]) == 2:
                   k = error
               else:
                   pass
               
     if count > 1:
         pass#TODO check if there is more than one error in segment, return the earliest
     return k
    
    def checkBoth(self,segment,errorlist,obg):#check if any crosses, 0 or 1 (OO) or 2 (SO)
          k = self.checkSo(segment,errorlist)
          l = self.checkOo(segment,obg)
          if k != False:
              if l != False:
                  distA = QgsGeometry().fromPoint(segment.asPolyline()[0]).distance(QgsGeometry().fromPoint(k))
                  print segment.asPolyline()[0], l
                  distB = QgsGeometry().fromPoint(segment.asPolyline()[0]).distance(QgsGeometry().fromPoint(l))
                  if distA < distB:
                      return 1
                  else:
                      return 2
                      
              else:
                  return 2
          else:
              if l == True:
                  return 1
              else:
                  return 0
              
          