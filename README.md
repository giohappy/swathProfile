# swathProfile
A QGIS plugin that creates aggregate profiles

A swath profile is an aggregate, "averaged" profile of a landscape section. 
The method allows for generalized cross-section evaluation along supposed geomorphologic features, for example along a river or tectonic faults.

This plugin creates a table of sample data along transects derived from buffers of a baseline, which then can be used to create a swath profile.

Instead of cross-sections every n meters along the baseline (method Telbisz et al., 2013), it creates buffer lines at a fixed distance to the baseline and then samples these lines every n meters. 
This method is described in Hergarten et. al, 2014 and avoids over- and undersampling of curved profile parts. 

The plugin runs in two parts. First, it creates buffer lines along the baseline, and secondly, samples along those lines.
The resulting table contains aggregate values, the resulting shapefiles the buffer lines used. The table can be plotted using your favourite plotting tool (as, for example, gnuplot).

Work flow:

* Load a raster layer to be sampled.
* Create a baseline shapefile, in the same CRS as the raster, draw one line.
* Run the plugin
* plot the profile using gnuplot (see example.run) or just a table calculation program.

-----
Options explained:

* Digital Terrain Model: The raster to be sampled
* Baseline Layer: The line representing the center of the profile. Should be one Polyline (multiploylines are not supported yet)
* take a sample every n units along the baseline: How often the lines will be sampled
* the profile should be n map units long: The main distance from the baseline.
* te profile should have data every n map units. How many lines there will be between the baseline and the main distance.
* output table: Comma-separated table with output data
* output shapefile: A shapefile epresenting the sampling lines. 

----
Issues in the  version 0.1.1:

* The layers have to be in the same crs (projection).
* Only one line in the baseline layer is supported.
* The buffer creation is quite slow

----
Literature:
S.Hergarten, J. Robl, K.Stüwe (2014): Extracting topographic swath profiles across curved geomorphic features. Earth Surfaces Dynamics 2, 97-104

T. Telbisz, G. Kovács, B. Skékely, J. Szabó (2013): Topographic swath profile analysis: a generalization and sensitivity evaluation of a digital terrain analysis tool. Zeitschrift für Geomorphologie 57,4, 485--513ß
