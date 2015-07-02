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
* Modify output CSV to your needs (e.g. sorting)
* plot the profile using gnuplot (see example.run) or just a table calculation program.

----
Issues in the experimental version 0.1:

* The layers have to be in the same crs (projection).
* Only one line in the baseline layer is supported.
* GRASS raster layers seem to be using up large amount of memory in large datasets (aborted testing after 10 GB)
* The buffer creation produces artifacts on complicated lines, where beginnng or end points intersect their own buffer.

----
Literature:
S.Hergarten, J. Robl, K.Stüwe (2014): Extracting topographic swath profiles across curved geomorphic features. Earth Surfaces Dynamics 2, 97-104

T. Telbisz, G. Kovács, B. Skékely, J. Szabó (2013): Topographic swath profile analysis: a generalization and sensitivity evaluation of a digital terrain analysis tool. Zeitschrift für Geomorphologie 57,4, 485--513ß
