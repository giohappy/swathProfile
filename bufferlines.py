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

    def createFlatBuffer(self,baseline,buflength,step,filename):
        #Main function. Call this from outside
        #needs: a line feature with ONE polyline (baseline)
        #a buffer distance that is applied to either side 
        #(a 500 will give a total profile length of 1000)
        #steps of distance between the buffers
        #filename: a shapefile name for output
        string = "LineString?crs=" + baseline.crs().toWkt()
        self.linelayer = QgsVectorLayer(string,"Buffer Layer", "memory")
        self.lineprovider= self.linelayer.dataProvider()
        self.lineprovider.addAttributes([QgsField('d', QVariant.Double)])
        self.linelayer.updateFields()
        bufcurr = 0 + step
        self.list=[]
        #copy the baseline
        ceroline, endline = self.createLine(0,baseline,step)
        oldfeatind = QgsSpatialIndex() 
        oldfeatlay = QgsVectorLayer(string, "old features", "memory")
        oflist,of = self.buildLine(0,baseline,step,self.list,[],ceroline, 
        endline, oldfeatind,oldfeatlay)
        del self.list
        ofolist = oflist
        for line in of:
          for i,j in list(enumerate(line[1:])):
              a = QgsFeature()
              a.setGeometry(QgsGeometry().fromPolyline([j,line[i]]))
              oldfeatlay.dataProvider().addFeatures([a])
        for feature in oldfeatlay.getFeatures():
          oldfeatind.insertFeature(feature)
        
        #loop and create the buffer lines
        while bufcurr <= buflength:
            ceroline,endline = self.createLine(-bufcurr,baseline,step)
            soslist = self.list
            del self.list
            oldceroline,oldendline = self.createLine(bufcurr,baseline,step)
            sos2list = self.list
            del self.list
            oldfeat1, of1 = self.buildLine(bufcurr,baseline,step,sos2list,soslist,
            oldceroline,oldendline,oldfeatind,oldfeatlay) 
            oldfeat2,of2 = self.buildLine(-bufcurr,baseline,step,soslist,sos2list,
            ceroline,endline,oldfeatind,oldfeatlay)
            for of1line in of1:
              for i,j in list(enumerate(of1line[1:])):
                a = QgsFeature()
                a.setGeometry(QgsGeometry().fromPolyline([j,of1line[i]]))
                oldfeatlay.dataProvider().addFeatures([a])
            for of2line in of2:
              for i,j in list(enumerate(of2line[1:])):
                a = QgsFeature()
                a.setGeometry(QgsGeometry().fromPolyline([j,of2line[i]]))
                oldfeatlay.dataProvider().addFeatures([a])
            for feature in oldfeatlay.getFeatures():
              oldfeatind.insertFeature(feature)
            oflist = oldfeat1
            ofolist = oldfeat2
            bufcurr = bufcurr + step
        #write to file
        QgsVectorFileWriter.writeAsVectorFormat(
                            self.linelayer, filename, "utf-8", baseline.crs(), 
                            "ESRI Shapefile")

    def translate(self,geom,azimuth,buflength): 
        #pushes a geometry by azimuth and distance, rotated by 90 degrees
        dx = math.sin(math.radians(azimuth-90))*buflength
        dy = math.cos(math.radians(azimuth-90))*buflength
        geom.translate(dx,dy)
        
    def pointAppend(self,k,selfinside,oldfeatind,oldfeatlay,step,segment): 
        #puts a point to self.list if it is outside
      if selfinside == False:
          if self.tooClose(k,oldfeatind, oldfeatlay, step) == False:
              self.endlist.append(k)
          else: #selftooclose == True TODO
              d = self.getLastValid(k,oldfeatind,oldfeatlay,step,segment)
              if d != False:
                  self.goInside(d)
              else:
                  self.beInside(k)
      else:
        self.goInside(k)
              
    def pointAdd(self,vertex,azimuth,bufcurrent): 
        #adds a point to self.list
        pnkt= QgsFeature()
        pnkt.setGeometry(QgsGeometry().fromPoint(vertex))
        self.translate(pnkt.geometry(),azimuth,bufcurrent)
        self.list.append(pnkt.geometry().asPoint())
        
    def createLine(self,bufcurrent,baselinelayer,step): 
        #creates the construction line point after point
        baselines = baselinelayer.getFeatures()
        for baseline in baselines:
            self.list = []
            #first, fill self.list with all potential points along the buffer, 
            #treating all kind of corners
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
                     #calculate cero line which should not be crossed later on
                     clp = QgsFeature()
                     clp.setGeometry(QgsGeometry().fromPoint(vertex))
                     self.translate(clp.geometry(),azimuth,-bufcurrent)
                     clp2 = QgsFeature()
                     clp2.setGeometry(QgsGeometry().fromPoint(vertex))
                     self.translate(clp2.geometry(),azimuth,bufcurrent)
                     ceroline = QgsGeometry().fromPolyline(
                     [clp2.geometry().asPoint(),clp.geometry().asPoint()])                
                   else:
                       self.list.append(vertex)
                       ceroline = QgsGeometry()
                else:
                    if vertexplusonenr == -1: #last point
                        vertex2 = baseline.geometry().vertexAt(vertexminusonenr)
                        azimuth = vertex2.azimuth(vertex)
                        if not bufcurrent == 0:
                            self.pointAdd(vertex,azimuth,bufcurrent)
                            #create end line which hould not be crossed
                            clp = QgsFeature()
                            clp.setGeometry(QgsGeometry().fromPoint(vertex))
                            self.translate(clp.geometry(),azimuth,-bufcurrent)
                            clp2 = QgsFeature()
                            clp2.setGeometry(QgsGeometry().fromPoint(vertex))
                            self.translate(clp2.geometry(),azimuth,bufcurrent)
                            endline = QgsGeometry().fromPolyline([
                            clp2.geometry().asPoint(),
                            clp.geometry().asPoint()])
                        else:
                            self.list.append(vertex)
                            endline = QgsGeometry()
                    else:#average point: One azimuth upstream, one downstream
                        vertex3 = baseline.geometry().vertexAt(vertexplusonenr)
                        vertex2 = baseline.geometry().vertexAt(vertexminusonenr)
                        az2 = vertex2.azimuth(vertex)
                        az3 = vertex.azimuth(vertex3)
                        diffazimuth = az2-az3
                        if bufcurrent > 0.0: 
                        #positive buffer; different treatment of big and 
                        #small angles.
                            if diffazimuth%360<=180: #sharp angles 
                                azimuth = self.meanAzimuth(az2,az3)
                                dist =  self.CalculateSharpDistance(
                                az2,az3,bufcurrent)
                                self.pointAdd(vertex,azimuth,dist)
                            else:          
                                azimutha = az2
                                while diffazimuth%360>180: 
                                #open angle gets intermediate points ewery 5deg
                                    self.pointAdd(vertex,azimutha,bufcurrent)
                                    azimutha = azimutha + 5
                                    diffazimuth = (azimutha - az3)%360
                                azimutha = az3 
                                self.pointAdd(vertex,azimutha,bufcurrent)                         
                        else: 
                            if bufcurrent == 0: 
                                #Buffer: Zero; just copy the baseline
                                self.list.append(vertex)
                            else:
                            #negative buffer. Numbers and orientations are 
                            #slightly different
                               if diffazimuth%360>=180:
                                   azimuth = self.meanAzimuth(az2,az3)
                                   dist =  - self.CalculateSharpDistance(
                                   az2,az3,bufcurrent)
                                   self.pointAdd(vertex,azimuth,dist)
                               else: 
                                   azimutha = az2
                                   while diffazimuth%360<180:
                                        self.pointAdd(
                                        vertex,azimutha,bufcurrent)
                                        azimutha = azimutha - 5
                                        diffazimuth = (azimutha - az3)%360
                                   azimutha = az3 
                                   self.pointAdd(vertex,azimutha,bufcurrent)
                pid = baseline.geometry().adjacentVertices(pid)[1]
        return ceroline, endline
                
    def buildLine(self,bufcurrent,baselinelayer,step, ownlist,othersidelist,
    nullline, endline,oldfeatind, oldfeatlay): 
        #constructs the line by checking against intersections and tracking 
        #inside/outside
        for baseline in baselinelayer.getFeatures():    
            #create indexes for the lines to check. 
            slay = QgsVectorLayer(
            "Linestring?crs="+baselinelayer.crs().toWkt(), "slay","memory")
            sind= QgsSpatialIndex()
            for i,j in list(enumerate(ownlist[1:])):
              point1 = j 
              point2 = ownlist[i]
              a = QgsFeature()
              a.setGeometry(QgsGeometry().fromPolyline([point1,point2]))
              slay.dataProvider().addFeatures([a])
            for feature in slay.getFeatures():
                sind.insertFeature(feature)
            olay = QgsVectorLayer(
            "Linestring?crs="+baselinelayer.crs().toWkt(),"otherlayer","memory")
            osind= QgsSpatialIndex()
            for i,j in list(enumerate(othersidelist[1:])):
              point1 = j 
              point2 = othersidelist[i]
              a = QgsFeature()
              a.setGeometry(QgsGeometry().fromPolyline([point1,point2]))
              olay.dataProvider().addFeatures([a])
            for feature in olay.getFeatures():
              osind.insertFeature(feature)
            zind = QgsSpatialIndex()
            zlay = QgsVectorLayer(
            "Linestring?crs="+baselinelayer.crs().toWkt(),"ceroline","memory")
            a = QgsFeature()
            a.setGeometry(nullline)
            zlay.dataProvider().addFeatures([a])
            b = QgsFeature()
            b.setGeometry(endline)
            zlay.dataProvider().addFeatures([a])
            for feature in zlay.getFeatures(): 
              zind.insertFeature(feature)
            segment = QgsGeometry().fromPolyline(
            [baseline.geometry().asPolyline()[0], ownlist[0]])
            self.linetoaddgeom = [] #main list for writing multipolyline
            self.endlist = [] #list for the current polyline part
            
            #initial states
            pointid = 0 #iterator
            selfinside = False
                       
            for point in ownlist:
                if pointid == 0:#first point, won't be in final line.
                #the first point has a fixed state and will be the reference. 
                #First, a check if the baseline starts inside its own buffer, 
                #then the first "shadow" line to the first point will be
                #evaluated, but not created. 
                      if self.checkIfInside(
                      baseline.geometry().asPolyline()[0],
                      baseline.geometry().asPolyline()[1], 
                      sind,slay, abs(bufcurrent)) == True: 
                        selfinside = True
                      if self.checkIfInside(
                      baseline.geometry().asPolyline()[0],
                      baseline.geometry().asPolyline()[1], 
                      osind,olay, abs(bufcurrent)) == True: 
                          if selfinside == False:
                              selfinside = True
                          else:
                              selfinside = False
                              
                      if bufcurrent == 0:
                          self.endlist.append(point)
                          #baseline won't be checked for validity, just copied
                      else:    
                        #count intersections and change states accordingly. 
                        #Ignore crossing lines at the beginning
                        d = self.checkAll(segment,sind,
                        osind,bufcurrent,zind,slay,olay,zlay) 
                        while len(d) > 0:
                            for dd in d:
                              if dd == 2:
                                k = self.checkOo(segment,sind,slay,bufcurrent)
                                if self.AequalsB(k,ownlist[0]) == True: 
                                  pass
                                else:
                                  if selfinside == True:
                                      selfinside = False
                                  else:
                                      selfinside = True
                              else:
                                  if dd == 4:
                                    k = self.checkOo(
                                    segment,osind,olay,bufcurrent)
                                    if self.AequalsB(
                                    k,othersidelist[0]) == True: 
                                        pass
                                    else:
                                        if selfinside == True:
                                            selfinside = False
                                        else:
                                            selfinside = True
                                  else:
                                      pass 
                            segment = QgsGeometry().fromPolyline([k,point])
                            d = self.checkAll(segment,sind,
                            osind,bufcurrent,zind,slay,olay,zlay)
                else: 
                #every other point will be checked for crossing between point 
                #and previous point, until no untracked crossing remains.
                        if bufcurrent == 0:#just passing the baseline
                            self.endlist.append(point)
                        else: 
                            vertexminusone = ownlist[pointid-1]
                            segment = QgsGeometry().fromPolyline(
                            [vertexminusone,point])
                            #check for intersections
                            #check changing states and switch variables
                            d = self.checkAll(segment,sind,
                            osind,bufcurrent,zind,slay,olay,zlay)
                            while len(d) > 0:
                              for dd in d:
                                if dd == 2:
                                    k = self.checkOo(segment,sind,slay,
                                    bufcurrent)
                                    if selfinside == True:
                                        selfinside = False
                                    else:
                                        selfinside = True
                                else:
                                    if dd == 4: 
                                      k = self.checkOo(segment,osind,
                                      olay,bufcurrent)
                                      if selfinside == True:
                                        selfinside = False
                                      else:
                                        selfinside = True
                                    else: 
                                        k = self.checkOo(segment,zind, zlay,bufcurrent)
                                        if selfinside == True:
                                            selfinside = False
                                        else:
                                            selfinside = True
                              self.pointAppend(k,selfinside,oldfeatind,oldfeatlay,step,segment)
                              segment = QgsGeometry().fromPolyline([k,point])
                              d = self.checkAll(segment,sind,
                              osind,bufcurrent,zind,slay,olay,zlay)
                #add the end of the section to the line, if it is outside
                self.pointAppend(point,selfinside,oldfeatind,oldfeatlay,step,segment)
                pointid = pointid + 1
                
            #dump linetoaddgeom(list of polylines created) to feature
            if len(self.endlist)>1:
                self.linetoaddgeom.append((self.endlist))
            linetoadd = QgsFeature()
            linetoadd.setAttributes([bufcurrent])
            linetoadd.setGeometry(QgsGeometry().fromMultiPolyline(
            self.linetoaddgeom))
            self.lineprovider.addFeatures([linetoadd])
            
            #clean up #TODO unnecessary?
            del slay,sind,olay,osind,zlay,zind
        return ownlist, self.linetoaddgeom
            
    def meanAzimuth(self,angle1,angle2):
        #calculate the mean bearing between two lines
        x = math.cos(math.radians(angle1)) + math.cos(math.radians(angle2))
        y = math.sin(math.radians(angle1))+ math.sin(math.radians(angle2))
        return math.degrees(math.atan2(y,x))
      
    def diffAzimuth(self,angle1,angle2):
        #calculates the the angle between two lines
        diff = angle1 - angle2
        if diff < -180:
            dif = diff + 360
        if diff > 180:
            diff = diff -  360
        return diff
     
    def CalculateSharpDistance(self,az2,az3,bufcurrent): 
        #calculate distance on "inner" angles, pure buffer distance is too low
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
                                return -(1/ math.cos(math.radians(diff))\
                                *bufcurrent)
             
    def beInside(self,k): 
        #prepare for writing to feature without writing the point. 
         if len(self.endlist) > 1:
           self.linetoaddgeom.append(self.endlist)
         del self.endlist
         self.endlist = []
    
    def goInside(self,k): 
        #write a point and then prepare the line for writing to feature. 
        #Also, clear endlist so we won't continue the line
         self.endlist.append(k)
         if len(self.endlist) > 1:
             self.linetoaddgeom.append(self.endlist)
         del self.endlist
         self.endlist = []
    
    def checkOo(self,osegment,index,layer,bufcurrent):
        #check if osegment crosses indexed feature. 
        #returns first intersection or False
        points = []
        req = []
        #get the features that are in the area out of the index
        for idy in index.intersects(osegment.boundingBox()):
            req.append(idy)
        request = QgsFeatureRequest().setFilterFids(req)
        #check for intersections
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
            #get the first occurence of an intersection
            x = False
            minlength = osegment.length()
            for pnt in points:
                ptdist = abs(QgsGeometry().fromPoint(pnt).distance(
                QgsGeometry().fromPoint(osegment.asPolyline()[0])))
                if ptdist > 0.0000001: 
                    if ptdist < minlength:
                        minlength = ptdist
                        x = pnt
            return x
     
    def checkAll(self,segment,sind,osind,bufcurrent,zind,
    slay,olay,zlay):
          #check if any crosses exist
          #returns a list of crossings that are on the first intersection point
          returnvalue = []
          m = self.checkOo(segment,sind,slay,bufcurrent)
          o = self.checkOo(segment,osind,olay,bufcurrent)
          p = self.checkOo(segment,zind,zlay,bufcurrent)
          checklist = {}
          if m != False:
              checklist[2] = m
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
            x = None
            for entry in checklist.items():
              dist = QgsGeometry().fromPoint(entry[1]).distance(
              QgsGeometry().fromPoint(segment.asPolyline()[0]))
              if dist <= maxdist:
                if dist > 0.0000001:
                  maxdist = dist
                  x = entry[0]
                  coord = entry[1]
            if len(checklist) == 1:
                del checklist
                if x != None:
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
              
    def checkIfInside(self, point,pointB, index,layer, distance): 
        #checks if fist point of baseline  is "inside" the line given by index
        #create a line along the general starting direction, about current 
        #buffer length long
        e = QgsFeature()
        e.setGeometry(QgsGeometry().fromPoint(point))
        dx=math.sin(math.radians(point.azimuth(pointB)))*(distance - 0.0000001)
        dy=math.cos(math.radians(point.azimuth(pointB)))*(distance - 0.0000001)
        e.geometry().translate(dx,dy)
        linea = QgsGeometry().fromPolyline([point,e.geometry().asPoint()])
        #now fetch features in the vincinity
        count = 0
        req = []
        for n in index.intersects(linea.boundingBox()):
          req.append(n)
        request = QgsFeatureRequest().setFilterFids(req)
        #check for intersections, count them
        for f in layer.getFeatures(request):  
          if f.geometry().intersects(linea):
              if self.AequalsB(f.geometry().intersection(linea).asPoint(),
              point) == True:
                  pass
              else:
                  if f.geometry().intersection(linea).asPoint()!= QgsPoint(0,0):
                      count = count + 1 
        if count%2 == 1: #odd number: we are inside
            return True
        else: #even number. We are inside and outside again
            return False
          
    def AequalsB(self,a,b):
        #tests if two points are roughly(0.0000001) equal
        #crutch because a==b and a.equals(b) and a.onSegment(b,c) are sometimes 
        #wrong?
       buf = QgsGeometry().fromPoint(a).buffer(0.0000001,10)
       if buf.contains(b) == True:
         return True
       else:
         return False
        
    def tooClose(self,point,oldfeatind,oldfeatlay,step):
        #check if the point comes too close to the indexed line
        dist = step
        n = oldfeatind.nearestNeighbor(point,1)
        request = QgsFeatureRequest().setFilterFids(n)
        #check for intersections, count them
        k = False
        for f in oldfeatlay.getFeatures(request): 
          dist = f.geometry().distance(QgsGeometry().fromPoint(point))
          if dist < (step - (step/100)):
            k = True
          else:
            pass
        return k
      
        #get the last valid (not too close) point of a segment
    def getLastValid(self,k,oldfeatind,oldfeatlay,step,segment):
        n = oldfeatind.nearestNeighbor(k,1) 
        request = QgsFeatureRequest().setFilterFids(n)
        x = False
        dist = segment.length()
        for f in oldfeatlay.getFeatures(request): 
          bf = f.geometry().buffer(step,10)
          inter = bf.intersection(segment)
          if len(inter.asPolyline()) > 0:
              ipt = QgsGeometry().fromPoint(inter.asPolyline()[0])
              ipt1 = QgsGeometry().fromPoint(inter.asPolyline()[1])
              pt0 = QgsGeometry().fromPoint(segment.asPolyline()[0])
              if ipt1.distance(pt0) < dist:
                  dist = ipt1.distance(pt0)
                  x = inter.asPolyline()[1]
              if ipt.distance(pt0) < dist:
                  dist = ipt.distance(pt0)
                  x = inter.asPolyline()[0]
        return x
    
    #TODO check for invalid geometry (duplicate point)