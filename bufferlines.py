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

    def createFlatBuffer(self,baseline,buflength,step,filename):#main function
        string = "LineString?crs=" + baseline.crs().toWkt()
        self.linelayer = QgsVectorLayer(string,"Buffer Layer", "memory")
        self.lineprovider= self.linelayer.dataProvider()
        self.lineprovider.addAttributes([QgsField('d', QVariant.Double)])
        self.linelayer.updateFields()
        
        bufcurr = 0 + step
        self.list=[]
        self.createLine(0,baseline,step)
        oldfeature = self.buildLine(0,baseline,step,self.list,[],None, QgsGeometry(),QgsGeometry())
        del self.list
        oldfeatureopposite = oldfeature
        while bufcurr <= buflength:
            self.createLine(-bufcurr,baseline,step)
            soslist = self.list
            oldceroline = self.ceroline
            del self.list
            self.createLine(bufcurr,baseline,step)
            sos2list = self.list
            del self.list
            oldfeat1 = self.buildLine(bufcurr,baseline,step,soslist,sos2list,oldceroline,oldfeatureopposite,oldfeature) 
            oldfeat2 = self.buildLine(-bufcurr,baseline,step,sos2list,soslist,self.ceroline,oldfeature,oldfeatureopposite)
            oldfeature = oldfeat1
            oldfeatureopposite = oldfeat2
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
                     self.ceroline = QgsGeometry().fromPolyline([clp2.geometry().asPoint(),clp.geometry().asPoint()])
                   else:
                       self.list.append(vertex)
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
            
    def buildLine(self,bufcurrent,baselinelayer,step, ownlist,othersidelist,nullline, obg, obg2): #constructs the line by checking against intersections
        for baseline in baselinelayer.getFeatures():    
            constructline = QgsFeature() #for check with myself. Construct myself and check for errors
            constructline.setGeometry(QgsGeometry().fromPolyline(ownlist))
            errorlist = []
            errors = constructline.geometry().validateGeometry()
            for error in errors:
                if error.hasWhere():
                  errorlist.append(error.where())
                  
            #put errors into list that are between ceropoint and first point
            segment = QgsGeometry().fromPolyline([baseline.geometry().asPolyline()[0], constructline.geometry().asPolyline()[0]])
            f = self.checkOo(segment,constructline.geometry(),bufcurrent)      
            if f != False:
                errorlist.append(f)
                
            
            if bufcurrent == 0:
              current2 = QgsGeometry()
            else:
              current2 = QgsGeometry().fromPolyline(othersidelist)
              
            self.linetoaddgeom = [] #main buffer for writing multipolyline
            pointid = 0
            obg2inside = False
            obginside = False
            selfinside = False
            sosinside = False
            self.endlist = [] #buffer for the current polyline part
            
            for point in constructline.geometry().asPolyline():
                if pointid == 0:#first point, won't be in final line
                  if self.checkIfInside(baseline.geometry().asPolyline()[0],baseline.geometry().asPolyline()[1], constructline.geometry(), abs(bufcurrent)) == True:
                    selfinside = True
                  if self.checkIfInside(baseline.geometry().asPolyline()[0],baseline.geometry().asPolyline()[1], obg, abs(bufcurrent)-step)== True:
                    obginside = True
                  if self.checkIfInside(baseline.geometry().asPolyline()[0],baseline.geometry().asPolyline()[1], obg2, abs(bufcurrent)-step)== True:
                    obg2inside = True
                  if self.checkIfInside(baseline.geometry().asPolyline()[0],baseline.geometry().asPolyline()[1], current2, abs(bufcurrent)) == True: 
                    sosinside = True
                  
                  if bufcurrent == 0:
                            self.endlist.append(point)#baseline won't be checked for validity, just copied
                  else:
                        d = self.checkAll(segment,errorlist,obg,obg2,current2,bufcurrent, nullline) 
                        while len(d) > 0:
                          for dd in d:
                            if dd == 1:
                                    k = self.checkOo(segment,obg,bufcurrent)
                                    if self.AequalsB(k,obg.asPolyline()[0]) == True:
                                        pass
                                    else:
                                        if obginside == True:
                                            obginside = False
                                        else:
                                            obginside = True
                            else:
                                if dd == 2:
                                  k = self.checkSo(segment,errorlist)
                                  if selfinside == True:
                                      selfinside = False
                                  else:
                                      selfinside = True

                                else:
                                    if dd == 3:
                                      k = self.checkOo(segment,obg2,bufcurrent)
                                      if self.AequalsB(k,obg2.asPolyline()[0]) == True:
                                          pass
                                      else:
                                          if obg2inside == True:
                                              obg2inside = False
                                          else:
                                              obg2inside = True
                                    else:
                                      if dd == 4:
                                        k = self.checkOo(segment,current2,bufcurrent)
                                        if self.AequalsB(k,current2.asPolyline()[0]) == True:
                                            pass
                                        else:
                                            if sosinside == True:
                                                sosinside = False
                                            else:
                                                sosinside = True
                                      else:
                                          pass 
                          segment = QgsGeometry().fromPolyline([k,point])
                          d = self.checkAll(segment,errorlist,obg,obg2,current2,bufcurrent,nullline)    
                else: #every other point
                        if bufcurrent == 0:#assuming that the baseline is valid
                            self.endlist.append(point)
                        else: 
                            vertexminusone = constructline.geometry().vertexAt(pointid-1)
                            segment = QgsGeometry().fromPolyline([vertexminusone,point])
	                    #check for intersections
                            d = self.checkAll(segment,errorlist,obg,obg2,current2,bufcurrent, nullline)
                            while len(d) > 0:
                              for dd in d:
                                if dd == 1:
                                    k = self.checkOo(segment,obg,bufcurrent)
                                    if obginside == True:
                                        obginside = False
                                    else:
                                        obginside = True
                                        k2 = self.insideBuffer(k,segment, step, True)
                                        self.goInside(k2)
                                else:
                                    if dd == 2:
                                        k = self.checkSo(segment,errorlist)
                                        #if on shadowline, pass! TODO
                                        #if k.onSegment(baseline.geometry().asPolyline()[0],baseline.geometry().asPolyline()[1]) == 2: #todo affected by "inaccuracies"?
                                          #pass
                                        #else: 
                                        if selfinside == True:
                                            selfinside = False
                                        else:
                                            selfinside = True
                                            self.goInside(k)
                                    else:
                                        if dd == 3:
                                            k = self.checkOo(segment,obg2,bufcurrent)
                                            if obg2inside == True:
                                                obg2inside = False
                                            else:
                                                obg2inside = True
                                                k2 = self.insideBuffer(k,segment, step, True)
                                                self.goInside(k2)
                                        else:
                                            if dd == 4: 
                                                k = self.checkOo(segment,current2,bufcurrent)
                                                if sosinside == True:
                                                    sosinside = False
                                                else:
                                                    sosinside = True
                                                    self.goInside(k)
                                            else: 
                                                if dd == 5: 
                                                  k = self.checkOo(segment, nullline, bufcurrent)
                                                  dist = QgsGeometry().fromPoint(k).distance(QgsGeometry().fromPoint(nullline.asPolyline()[1]))
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
                                                              obg2inside = True
                                                              self.goInside(k)
                                                      else:                                                         
                                                          if sosinside == True:
                                                              sosinside = False
                                                          else:
                                                              sosinside = True
                                                              self.goInside(k)
                              segment = QgsGeometry().fromPolyline([k,point])
                              self.pointAppend(k,selfinside,obginside,obg2inside,sosinside)
                              d = self.checkAll(segment,errorlist,obg,obg2,current2,bufcurrent,nullline)
                self.pointAppend(point,selfinside,obginside,obg2inside,sosinside)
                #dump linetoaddgeom to feature
            if len(self.endlist)>1:
                self.linetoaddgeom.append((self.endlist))
            linetoadd = QgsFeature()
            linetoadd.setAttributes([bufcurrent])
            linetoadd.setGeometry(QgsGeometry().fromMultiPolyline(self.linetoaddgeom))
            self.lineprovider.addFeatures([linetoadd])
        return QgsGeometry().fromPolyline(ownlist)
            
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
    
    def checkOo(self,osegment,ofeature,bufcurrent):#check if osegment crosses ofeature. returns first intersection or False
        if osegment.intersects(ofeature):
              points = []
              sg = QgsFeature()
              sg.setGeometry(osegment)
              pntid = 0
              for pnt in ofeature.asPolyline():
                segment = self.getSegment(ofeature,pntid)
                if segment == False:
                      pass
                else:
                    if segment.intersects(osegment) == False:
                        pass
                    else:
                        dummy, bits, dummy2 = sg.geometry().splitGeometry(segment.asPolyline(),False)
                        for bit in bits:
                            points.append(bit.asPolyline()[0])
                            points.append(bit.asPolyline()[1])
                        points.append(sg.geometry().asPolyline()[0])
                        points.append(sg.geometry().asPolyline()[1])
                        sg.setGeometry(osegment)
                pntid = pntid + 1       
              if len(points)<2:
                  return False
              else:
                  x = False
                  minlength = osegment.length()  - 0.0000001
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
        else:
           return False
      #TODO: a buffer about (len) away. ideally (bufferlength) from next baseline
            
    def checkSo(self,segment,errorlist):#check if crosses itself (defined by errorlist). Returns first intersection or False
     xx = False
     count = []
     for error in errorlist:
       if self.AequalsB(error,segment.asPolyline()[0]) == True:
           pass
       else:
         if error == segment.asPolyline()[0]:
           pass
         else:
           if QgsGeometry().fromPoint(error).buffer(0.000001,5).intersects(segment) == True:  
               count.append(error)
           else:
             #if error.onSegment(segment.asPolyline()[0],segment.asPolyline()[1]) == 2:
                 #count.append(error)
             #else:
                 pass
      
     if len(count) > 0: #HERE SOME ERROR LURKS
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
   
    
    def checkAll(self,segment,errorlist,obg,obg2,current2,bufcurrent, ceroline):#check if any crosses,
          returnvalue = []
          l = self.checkOo(segment,obg,bufcurrent)
          m = self.checkOo(segment,constructline,errorlist)
          n = self.checkOo(segment,obg2,bufcurrent)
          o = self.checkOo(segment,current2,bufcurrent)
          p = self.checkOo(segment,ceroline,bufcurrent)
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
            #check if first crossing is in ther more than once
            else: 
                for entry in checklist.items():
                    if self.AequalsB(entry[1],coord) == True:
                        returnvalue.append(entry[0])
                del checklist
                return returnvalue
              
              
    def howManyIntersects(self,simpleline,complicatedline): #return how often polyline intersects the simpleline
      tmp = QgsFeature()
      tmp.setGeometry(simpleline)
      splitpoints = []
      pointidx = 0
      for point in complicatedline.asPolyline():
          segmenttocheck = self.getSegment(complicatedline,pointidx)
          if segmenttocheck == False:
              pass
          else:
               if segmenttocheck.intersects(tmp.geometry())  == False:
                   pass
               else:
                   res, bits, dummy = tmp.geometry().splitGeometry(segmenttocheck.asPolyline(),False)
                   for bit in bits:
                       splitpoints.append(bit.asPolyline()[0])
                       splitpoints.append(bit.asPolyline()[-1])
                   tmp.setGeometry(simpleline)
          pointidx = pointidx + 1         
      realsplitpoints = []
      for point in splitpoints:
          if self.AequalsB(point,simpleline.asPolyline()[0]) == True:
              pass
          else:
              if self.AequalsB(point,simpleline.asPolyline()[1]) == True:
                  pass
              else:
                  ais = False
                  for a in realsplitpoints:
                      if self.AequalsB(point,a) == True:
                          pass
                      else:
                          ais = True
                  if ais == True:
                      pass
                  else:
                      realsplitpoints.append(point)
      return len(realsplitpoints)
    
    def checkIfInside(self, point,pointB, line, distance): #checks if fist point of baseline  is "inside" the line
        q = QgsFeature()
        q.setGeometry(QgsGeometry().fromPoint(point))
        self.translate(q.geometry(), point.azimuth(pointB),distance - 0.0000001) #TODO dirty, but avoiding e-09 false positives
        linea = QgsGeometry().fromPolyline([point,pointB])
        if self.howManyIntersects(linea,line)%2 == 1:
            return True
        else:
            return False
          
    def getSegment(self,line, pointid): #returns segment of polyline that ends at pointid
        try:
            if line.adjacentVertices(pointid)[0] == -1:
                return False
            else:
              pointA = line.vertexAt(pointid)
              pointB = line.vertexAt(pointid - 1)
              return QgsGeometry().fromPolyline([pointA,pointB])
        except KeyError:
            return False
                    
    def checkIfStartsWrong(self,segment, pointA,pointB): #check if the first segments go roughly into the same direction
      a = pointA.azimuth(pointB)
      b = segment.asPolyline()[0].azimuth(segment.asPolyline()[1])
      diff12 = self.diffAzimuth(a,b)
      if diff12 >-90:
        if diff12 <90:
          return True
        else:
          return False
      else:
        return False
      
    def AequalsB(self,a,b):#crutch because a==b and a.equals(b) and a.onSegment(b,c) are sometimes wrong?
       buf = QgsGeometry().fromPoint(a).buffer(0.0000001,10)
       if buf.contains(b) == True:
       #if a == b:
         return True
       else:
         return False
     
    def insideBuffer(self,x,segment, step, onend):
        #if onend == True:
            #d = QgsGeometry().fromPoint(segment.asPolyline()[1])
            #az = segment.asPolyline()[0].azimuth(segment.asPolyline()[1])
            #self.translate(d,az,-step)
        return x#.asPoint()
    