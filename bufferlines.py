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
#TODO: Beginning state is wrong somewhere, and passing through own ceroline makes lines disappear completely

from qgis.analysis import QgsGeometryAnalyzer
import math
from PyQt4.QtCore import QCoreApplication, QVariant
from qgis.core import * 


class bufferLines():

    def createFlatBuffer(self,baseline,buflength,step,filename):#main function
        string = "LineString?crs=" + baseline.crs().toWkt()
        self.linelayer = QgsVectorLayer(string,"Buffer Layer", "memory")
        self.lineprovider= self.linelayer.dataProvider()
        self.lineprovider.addAttributes([QgsField('d', QVariant.Double)])
        self.linelayer.updateFields()
        
        string = "LineString?crs=" + baseline.crs().toWkt()
        self.poly = QgsVectorLayer(string,"Buffer Layer", "memory")
        self.polyp= self.poly.dataProvider()
        self.polyp.addAttributes([QgsField('d', QVariant.Double)])
        self.poly.updateFields()
        QgsMapLayerRegistry.instance().addMapLayer(self.poly)
        
        bufcurr = 0 + step
        self.list=[]
        ceroline = self.createLine(0,baseline,step)
        oldceroline = ceroline
        oldfeaturelist = self.buildLine(0,baseline,step,self.list,[],ceroline, [],[])
        del self.list
        oldfeatureoppositelist = oldfeaturelist
        while bufcurr <= buflength:
            ceroline = self.createLine(-bufcurr,baseline,step)
            soslist = self.list
            del self.list
            oldceroline = self.createLine(bufcurr,baseline,step)
            sos2list = self.list
            del self.list
            oldfeat1 = self.buildLine(bufcurr,baseline,step,sos2list,soslist,oldceroline,oldfeatureoppositelist,oldfeaturelist) 
            oldfeat2 = self.buildLine(-bufcurr,baseline,step,soslist,sos2list,ceroline,oldfeaturelist,oldfeatureoppositelist)
            oldfeaturelist = oldfeat1
            oldfeatureoppositelist = oldfeat2
            bufcurr = bufcurr + step
        QgsVectorFileWriter.writeAsVectorFormat(self.linelayer, filename, "utf-8", baseline.crs(), "ESRI Shapefile")

    def translate(self,geom,azimuth,buflength): #pushes a geometry by azimuth and distance
        dx = math.sin(math.radians(azimuth-90))*buflength
        dy = math.cos(math.radians(azimuth-90))*buflength
        geom.translate(dx,dy)
        
    def pointAppend(self,k,selfinside,obginside,obg2inside,sosinside): #puts a point to self.list if it is outside
      if selfinside == False:
        if obginside == False:
          if obg2inside == False:
            if sosinside == False:
              self.endlist.append(k)
              
    def pointAdd(self,vertex,azimuth,bufcurrent): #adds a list to line buffer
        pnkt= QgsFeature()
        pnkt.setGeometry(QgsGeometry().fromPoint(vertex))
        self.translate(pnkt.geometry(),azimuth,bufcurrent)
        self.list.append(pnkt.geometry().asPoint())
        
    def createLine(self,bufcurrent,baselinelayer,step): #creates the construction line point after point
        baselines = baselinelayer.getFeatures()
        for baseline in baselines:
            self.list = []
            #first, fill self.list with all potential points along the buffer, treating all
            #kind of corners
            pid = 0
            
            for point in baseline.geometry().asPolyline():
                vertex= baseline.geometry().vertexAt(pid)
                vertexplusonenr = baseline.geometry().adjacentVertices(pid)[1]
                vertexminusonenr = baseline.geometry().adjacentVertices(pid)[0]
                if vertexminusonenr == -1: #first point
                   vertex2= baseline.geometry().vertexAt(vertexplusonenr)
                   azimuth = vertex.azimuth(vertex2)
                   if not bufcurrent == 0:
                     self.pointAdd(vertex,azimuth,bufcurrent)
                     #calculate cero leine which should not be crossed later on
                     clp = QgsFeature()
                     clp.setGeometry(QgsGeometry().fromPoint(vertex))
                     self.translate(clp.geometry(),azimuth,-bufcurrent)
                     clp2 = QgsFeature()
                     clp2.setGeometry(QgsGeometry().fromPoint(vertex))
                     self.translate(clp2.geometry(),azimuth,bufcurrent)
                     ceroline = QgsGeometry().fromPolyline([clp2.geometry().asPoint(),clp.geometry().asPoint()])
                   else:
                       self.list.append(vertex)
                       ceroline = QgsGeometry()
                else:
                    if vertexplusonenr == -1: #last point
                        vertex2 = baseline.geometry().vertexAt(vertexminusonenr)
                        azimuth = vertex2.azimuth(vertex)
                        if not bufcurrent == 0:
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
        return ceroline
                
    def buildLine(self,bufcurrent,baselinelayer,step, ownlist,othersidelist,nullline, obglist, obg2list): #constructs the line by checking against intersections
        for baseline in baselinelayer.getFeatures():    
            #create indexes for the five lines to check
            
            slay = QgsVectorLayer("Linestring?crs="+baselinelayer.crs().toWkt(), "slay","memory")
            sind= QgsSpatialIndex()
            for i,j in list(enumerate(ownlist[1:])):
              point1 = j 
              point2 = ownlist[i]
              a = QgsFeature()
              a.setGeometry(QgsGeometry().fromPolyline([point1,point2]))
              slay.dataProvider().addFeatures([a])
            for feature in slay.getFeatures():
                sind.insertFeature(feature)
            olay = QgsVectorLayer("Linestring?crs="+baselinelayer.crs().toWkt(),"otherlayer","memory")
            osind= QgsSpatialIndex()
            for i,j in list(enumerate(othersidelist[1:])):
              point1 = j 
              point2 = othersidelist[i]
              a = QgsFeature()
              a.setGeometry(QgsGeometry().fromPolyline([point1,point2]))
              olay.dataProvider().addFeatures([a])
              for feature in olay.getFeatures():
                osind.insertFeature(feature)
            obglay = QgsVectorLayer("Linestring?crs="+baselinelayer.crs().toWkt(),"obglay","memory")
            obgind= QgsSpatialIndex()
            for i,j in list(enumerate(obglist[1:])):
              point1 = j 
              point2 = obglist[i]
              a = QgsFeature()
              a.setGeometry(QgsGeometry().fromPolyline([point1,point2]))
              obglay.dataProvider().addFeatures([a])
            for feature in obglay.getFeatures():
              obgind.insertFeature(feature)
              
              
            obg2lay = QgsVectorLayer("Linestring?crs="+baselinelayer.crs().toWkt(),"obg2lay","memory")
            ob2gind= QgsSpatialIndex()
            for i,j in list(enumerate(obg2list[1:])):
              point1 = j 
              point2 = obg2list[i]
              a = QgsFeature()
              a.setGeometry(QgsGeometry().fromPolyline([point1,point2]))
              obg2lay.dataProvider().addFeatures([a])
            for feature in obg2lay.getFeatures(): 
                ob2gind.insertFeature(feature)
              
            zind = QgsSpatialIndex()
            zlay = QgsVectorLayer("Linestring?crs="+baselinelayer.crs().toWkt(),"ceroline","memory")
            a = QgsFeature()
            a.setGeometry(nullline)
            zlay.dataProvider().addFeatures([a])
            self.polyp.addFeatures([a])
            for feature in zlay.getFeatures(): 
              zind.insertFeature(feature)
            segment = QgsGeometry().fromPolyline([baseline.geometry().asPolyline()[0], ownlist[0]])
            self.linetoaddgeom = [] #main buffer for writing multipolyline
            self.endlist = [] #buffer for the current polyline part
            
            pointid = 0 #iterator
            obg2inside = False
            obginside = False
            selfinside = False
            sosinside = False
            
            for point in ownlist:
                if pointid == 0:#first point, won't be in final line
                      if self.checkIfInside(baseline.geometry().asPolyline()[0],baseline.geometry().asPolyline()[1], sind,slay, abs(bufcurrent)) == True: 
                        selfinside = True
                      if abs(bufcurrent) == step:
                        pass
                      else:
                        if self.checkIfInside(baseline.geometry().asPolyline()[0],baseline.geometry().asPolyline()[1], obgind,obglay, abs(bufcurrent)-step)== True:
                          obginside = True
                        if self.checkIfInside(baseline.geometry().asPolyline()[0],baseline.geometry().asPolyline()[1], ob2gind,obg2lay, abs(bufcurrent)-step)== True:
                          obg2inside = True
                      if self.checkIfInside(baseline.geometry().asPolyline()[0],baseline.geometry().asPolyline()[1], osind,olay, abs(bufcurrent)) == True: 
                        sosinside = True
                      if bufcurrent == 0:
                          self.endlist.append(point)#baseline won't be checked for validity, just copied
                      else:    
                        d = self.checkAll(segment,sind,obgind,ob2gind,osind,bufcurrent,zind,slay,olay,obglay,obg2lay,zlay) 
                        #count intersection and change states accordingly
                        while len(d) > 0:
                            for dd in d:
                              if dd == 1:
                                    k = self.checkOo(segment,obgind,obglay,bufcurrent)
                                    if self.AequalsB(k,obglist[0]) == True:
                                        pass
                                    else:
                                        if obginside == True:
                                            obginside = False
                                        else:
                                            obginside = True
                              else:
                                if dd == 2:
                                  k = self.checkOo(segment,sind,slay,bufcurrent)
                                  if selfinside == True:
                                      selfinside = False
                                  else:
                                      selfinside = True
                                else:
                                    if dd == 3:
                                      k = self.checkOo(segment,ob2gind,obg2lay,bufcurrent)
                                      if self.AequalsB(k,obg2list[0]) == True: 
                                          pass
                                      else:
                                          if obg2inside == True:
                                              obg2inside = False
                                          else:
                                              obg2inside = True
                                    else:
                                      if dd == 4:
                                        k = self.checkOo(segment,osind,olay,bufcurrent)
                                        if self.AequalsB(k,othersidelist[0]) == True: 
                                            pass
                                        else:
                                            if sosinside == True:
                                                sosinside = False
                                            else:
                                                sosinside = True
                                      else:
                                          pass 
                            segment = QgsGeometry().fromPolyline([k,point])
                            d = self.checkAll(segment,sind,obgind,ob2gind,osind,bufcurrent,zind,slay,olay,obglay,obg2lay,zlay)
                else: #every other point
                        if bufcurrent == 0:#assuming that the baseline is valid
                            self.endlist.append(point)
                        else: 
                            vertexminusone = ownlist[pointid-1]
                            segment = QgsGeometry().fromPolyline([vertexminusone,point])
	                    #check for intersections
                            #check changing states and switch all variables
                            d = self.checkAll(segment,sind,obgind,ob2gind,osind,bufcurrent,zind,slay,olay,obglay,obg2lay,zlay)
                            while len(d) > 0:
                              print d
                              for dd in d:
                                if dd == 1:
                                    k = self.checkOo(segment,obgind,obglay,bufcurrent)
                                    if obginside == True:
                                        obginside = False
                                    else:
                                        obginside = True
                                        self.beInside(k)
                                else:
                                    if dd == 2:
                                        k = self.checkOo(segment,sind,slay,bufcurrent)
                                        if selfinside == True:
                                            selfinside = False
                                        else:
                                            selfinside = True
                                            self.goInside(k)
                                    else:
                                        if dd == 3:
                                            k = self.checkOo(segment,ob2gind,obg2lay,bufcurrent)
                                            if obg2inside == True:
                                                obg2inside = False
                                            else:
                                                obg2inside = True
                                                self.beInside(k)
                                        else:
                                            if dd == 4: 
                                                k = self.checkOo(segment,osind,olay,bufcurrent)
                                                if sosinside == True:
                                                    sosinside = False
                                                else:
                                                    sosinside = True
                                                    self.goInside(k)
                                            else: 
                                                if dd == 5:
                                                    k = self.checkOo(segment, zind, zlay,bufcurrent)
                                                    dist = QgsGeometry().fromPoint(k).distance(QgsGeometry().fromPoint(ownlist[0]))
                                                    if self.backwardsCeroline(segment,baseline.geometry().asPolyline()[0],baseline.geometry().asPolyline()[1]) == False:
                                                        if dist >= 2*abs(bufcurrent)-step: 
                                                          if sosinside == True:
                                                            sosinside = False
                                                          else:
                                                            sosinside = True
                                                            self.goInside(k)   
                                                          if obg2inside == True:
                                                              obg2inside = False
                                                          else:
                                                              obg2inside = True
                                                              self.goInside(k)
                                                          if obginside == True:
                                                              obginside = False
                                                          else:
                                                              obginside = True
                                                              self.goInside(k)     
                                                        else: 
                                                            if dist >= step:
                                                                if sosinside == True:
                                                                  sosinside = False
                                                                else:
                                                                    sosinside = True
                                                                    self.goInside(k)
                                                                if obginside == True:
                                                                    obginside = False
                                                                else:
                                                                    obginside = True
                                                                    self.goInside(k)
                                                            else:                                                         
                                                                if sosinside == True:
                                                                    sosinside = False
                                                                else:
                                                                    sosinside = True
                                                                    self.goInside(k)
                                                    else: #TODO exotic cases
                                                          print sosinside,selfinside,obginside,obg2inside
                                                     
                                                    #if dist >= 2*abs(bufcurrent)-step: 
                                                          if selfinside == True:
                                                            selfinside = False
                                                          else:
                                                            selfinside = True
                                                            self.goInside(k)   
                                                          if obg2inside == True:
                                                              obg2inside = False
                                                          else:
                                                              obg2inside = True
                                                              self.goInside(k)
                                                          if obginside == True:
                                                              obginside = False
                                                          else:
                                                              obginside = True
                                                              self.goInside(k)     
                                                        #else: 
                                                            #if dist >= step:
                                                                #if selfinside == True:
                                                                  #selfinside = False
                                                                #else:
                                                                    #selfinside = True
                                                                    #self.goInside(k)
                                                                #if obginside == True:
                                                                    #obginside = False
                                                                #else:
                                                                    #obginside = True
                                                                    #self.goInside(k)
                                                            #else:                                                         
                                                                #if selfinside == True:
                                                                    #sosinside = False
                                                                #else:
                                                                    #selfinside = True
                                                                    #self.goInside(k)    
                              segment = QgsGeometry().fromPolyline([k,point])
                              self.pointAppend(k,selfinside,obginside,obg2inside,sosinside)
                              d = self.checkAll(segment,sind,obgind,ob2gind,osind,bufcurrent,zind,slay,olay,obglay,obg2lay,zlay)
                self.pointAppend(point,selfinside,obginside,obg2inside,sosinside)
                pointid = pointid + 1
                
            #dump linetoaddgeom to feature
            if len(self.endlist)>1:
                self.linetoaddgeom.append((self.endlist))
            linetoadd = QgsFeature()
            linetoadd.setAttributes([bufcurrent])
            linetoadd.setGeometry(QgsGeometry().fromMultiPolyline(self.linetoaddgeom))
            self.lineprovider.addFeatures([linetoadd])
            
            del slay, sind, olay, osind, obglay,obgind, obg2lay,ob2gind, zlay, zind
        return ownlist
            
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
                            
    def goInside(self,k): #write a point and then prepare for write to feature. Also, clear endlist so we won't continue the line
         self.endlist.append(k)
         if len(self.endlist) > 1:
             self.linetoaddgeom.append(self.endlist)
         del self.endlist
         self.endlist = []
         
    def beInside(self,k): #prepare for write to feature without writing the point.
         if len(self.endlist) > 1:
           self.linetoaddgeom.append(self.endlist)
         del self.endlist
         self.endlist = []
    
    def checkOo(self,osegment,index,layer,bufcurrent):#check if osegment crosses indexed feature. returns first intersection or False
        points = []
        req = []
        for idy in index.intersects(osegment.boundingBox()):
            req.append(idy)
        request = QgsFeatureRequest().setFilterFids(req)
        for segment in layer.getFeatures(request):
            if segment.geometry() == None:
              pass
            else:
              if segment.geometry().equals(osegment)== True:
                pass
              else:
                if segment.geometry().intersects(osegment) == True:
                  inter = segment.geometry().intersection(osegment)
                  points.append(inter.asPoint())
                else:
                  pass
              
        if len(points)==0:
            return False
        else:
            x = False
            minlength = osegment.length()
            for pnt in points:
                ptdist = QgsGeometry().fromPoint(pnt).distance(QgsGeometry().fromPoint(osegment.asPolyline()[0]))
                if ptdist > 0.0000001: 
                    if ptdist < minlength:
                        minlength = ptdist
                        x = pnt
                    else:
                        pass
                else:
                    pass
            return x
        if len(count) > 0: 
         seglen = abs(segment.length())
         for pnt in count:
            ptdist = abs(QgsGeometry().fromPoint(pnt).distance(QgsGeometry().fromPoint(segment.asPolyline()[0]))) 
            if ptdist > 0.0000001: 
                if ptdist < seglen :
                    xx = pnt
                    seglen = ptdist
                else:
                    pass
            else:
                pass
         return xx
       
        else:
         return False
     
    def checkAll(self,segment,sind,obgind,ob2gind,osind,bufcurrent,zind,slay,olay,obglay,obg2lay,zlay):#check if any crosses exist
          returnvalue = []
          l = self.checkOo(segment,obgind,obglay,bufcurrent)
          m = self.checkOo(segment,sind,slay,bufcurrent)
          n = self.checkOo(segment,ob2gind,obg2lay,bufcurrent)
          o = self.checkOo(segment,osind,olay,bufcurrent)
          p = self.checkOo(segment,zind,zlay,bufcurrent)
          checklist = {}
          if l != False:
              checklist[1] = l
          if m != False:
              checklist[2] = m
          if n != False:
              checklist[3] = n
          if o != False:
              checklist[4] = o
          if p != False:
              checklist[5] = p
          if len(checklist) == 0:
            del checklist
            return returnvalue   
          else:
            maxdist = segment.length()
            #get the first crossing
            for entry in checklist.items():
              dist = QgsGeometry().fromPoint(entry[1]).distance(QgsGeometry().fromPoint(segment.asPolyline()[0]))
              if dist <= maxdist:
                if dist > 0.0000001:
                  maxdist = dist
                  x = entry[0]
                  coord = entry[1]
            if len(checklist) == 1:
                del checklist
                returnvalue.append(x)
                return returnvalue
            #check if first crossing is in there more than once
            else: 
                for entry in checklist.items():
                    if self.AequalsB(entry[1],coord) == True:
                        returnvalue.append(entry[0])
                    else:
                        pass
                del checklist
                return returnvalue
              
    def checkIfInside(self, point,pointB, index,layer, distance): #checks if fist point of baseline  is "inside" the line given by a(spatial)index
        e = QgsFeature()
        e.setGeometry(QgsGeometry().fromPoint(point))
        dx = math.sin(math.radians(point.azimuth(pointB)))*(distance - 0.0000001)
        dy = math.cos(math.radians(point.azimuth(pointB)))*(distance - 0.0000001)
        e.geometry().translate(dx,dy)
        linea = QgsGeometry().fromPolyline([point,e.geometry().asPoint()])
        count = 0
        req = []
        for n in index.intersects(linea.boundingBox()):
          req.append(n)
        request = QgsFeatureRequest().setFilterFids(req)
        for f in layer.getFeatures(request):  
          if f.geometry().intersects(linea):
              if self.AequalsB(f.geometry().intersection(linea).asPoint(),point) == True:
                  pass
              else:
                  count = count + 1 
        if count%2 == 1:
            return True
        else:
            return False
                    
    def AequalsB(self,a,b):#crutch because a==b and a.equals(b) and a.onSegment(b,c) are sometimes wrong?
       buf = QgsGeometry().fromPoint(a).buffer(0.0000001,10)
       if buf.contains(b) == True:
         return True
       else:
         return False
     
    def backwardsCeroline(self,segment,pointA,pointB): 
        a = pointA.azimuth(pointB)
        b = segment.asPolyline()[0].azimuth(segment.asPolyline()[1])
        diff12 = self.diffAzimuth(a,b)
        if diff12 >-90:
          if diff12 <90:
            return False
          else:
            return True
        else:
          return True
    