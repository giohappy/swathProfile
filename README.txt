Swath profile

This plugin creates a table of sample data along transects derived from buffers of a baseline, which then can be used to create a swath profile.
A swath profile is an aggregate, "averaged" profile of a landscape section. 
The method allows for generalized cross-section evaluation along supposed geomorphologic features, for example along a river or tectonic faults.

Instead of cross-sections every n meters along the baseline (method Telbisz et al., 2013), it creates lines at a fixed distance to the baseline and then samples these lines every n meters. 
This methos is described in Hergarten et. al, 2014 and avoids over- and undersampling of profile sections. 

The resulting table contains aggregate values for each distance to the baseline, which can then be plotted using your favourite plotting tool (e.g. gnuplot). See the example.run provided for a gnuplot example. The resulting shapefile contains the information about the lines created.  
The plugin is in an early phase, as the buffer creation still needs improvement. the main issue for the time being is the speed of the calculation.

Work flow: 
* Load raster to be sampled into QGIS.
* Create a shapefile with a baseline in it. Currently only one simple polyline is supported (no multi-part lines)
* Run the plugin
* Plot the csv file

Options explained:
* Digital Terrain Model: The raster to be sampled
* Baseline Layer: The line representing the center of the profile. Should be one Polyline (multiploylines are not supported yet)
* take a sample every n units along the baseline: How often the lines will be sampled
* the profile should be n map units long: The main distance from the baseline.
* te profile should have data every n map units. How many lines there will be between the baseline and the main distance.
* output table: Comma-separated table with output data
* output lines shapefile: A shapefile representing the sampling lines. 
* output points shapefile: A shapefile representing the sites sampled.

---
Literature:

S.Hergarten, J. Robl, K.Stüwe (2014): Extracting topographic swath profiles across curved geomorphic features. Earth Surfaces Dynamics 2, 97-104.

T. Telbisz, G. Kovács, B. Skékely, J. Szabó (2013): Topographic swath profile analysis: a generalization and sensitivity evaluation of a digital terrain analysis tool. Zeitschrift für Geomorphologie 57,4, 485--513
