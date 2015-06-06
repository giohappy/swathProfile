# swathProfile
A QGIS plugin that creates aggregate profiles

A swath profile is an aggregate, "averaged" profile of a landscape section. 
The method allows for generalized cross-section evaluation along supposed geomorphologic features, for example along a river or tectonic faults.

This plugin creates a table of sample data along transects derived from buffers of a baseline, which then can be used to create a swath profile.

Instead of cross-sections every n meters along the baseline (method Telbisz et al., 2013), it creates buffer lines at a fixed distance to the baseline and then samples these lines every n meters. 
This methos is described in Hergarten et. al, 2014 and avoids over- and undersampling of curved profile parts. 

The resulting table contains x, y coordinates, the position relative to the baseline, and the raster values. NoValue Data are represented as "None"
It can be used with statistical analysis to form aggregates, as min, max, median, quartiles etc. See below for an example how to aggregate with R and plot with gnuplot.

---
Literature:

S.Hergarten, J. Robl, K.Stüwe (2014): Extracting topographic swath profiles across curved geomorphic features. Earth Surfaces Dynamics 2, 97-104
T. Telbisz, G. Kovács, B. Skékely, J. Szabó (2013): Topographic swath profile analysis: a generalization and sensitivity evaluation of a digital terrain analysis tool. Zeitschrift für Geomorphologie 57,4, 485--513


---

example r script to create aggregate tables:

totalx <- read.table("output.csv", quote="\"", na.strings='None')
total <- totalx[complete.cases(totalx), ]
mean <- aggregate(total[4],total[3],FUN = mean)
min <- aggregate(total[4],total[3],FUN = min)
max <- aggregate(total[4],total[3],FUN = max)
sd <- aggregate(total[4],total[3],FUN = sd)
median <- aggregate(total[4],total[3],FUN = median)
quart25 <- aggregate(total[4],total[3],FUN= function(x) quantile(x,probs=0.25))
quart75 <- aggregate(total[4],total[3],FUN= function(x) quantile(x,probs=0.75))
write.table(mean,"mean.csv")
write.table(max,"max.csv")
write.table(min,"min.csv")
write.table(median,"median.csv")
write.table(sd,"sd.csv")
write.table(quart25,"quart25.csv")
write.table(quart75,"quart75.csv")

---
example gnuplot script to plot:


set terminal postscript eps size 11,8
set output "swath_profile.eps"
set key top left
set title "Swath profile"
set encoding utf8
set size ratio -40
set xlabel 'distance (m)'
set ylabel 'elevation (m)'
set xtics nomirror 500
set ytics nomirror 2.5
set style fill solid 0.5
set grid ytics xtics
set border lw 0.05
set style data lines

plot "< paste quart25.csv quart75.csv" using 2:($3):($6) with filledcurves x1 title "quartiles", \
'median.csv' using 2:3 lt 1 lw 3 title "median",\
'min.csv' using 2:3 lt 3 title "minimum", \
'max.csv' using 2:3 lt 3 title "maximum"
    
