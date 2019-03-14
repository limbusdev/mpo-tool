MPO Tool
========

![](./camera.png)![](./mpo_split.png)![](./anaglyph.png)![](jps_cross.png)![](./jps_parallel.png)

MPO Tool is a little piece of software for splitting and converting MPO 3D photos. It is written in python2.7 (because there is no Python Imaging Library for Python3 yet) and GTK+3 (via GObject-Introspection).


Use MPO Tool to convert MPO to JPS.

Dependencies Ubuntu/Debian:
gir1.2-gexiv2-0.4
libgexiv2-dev
python-imaging
python-gi

Progressbar does not work yet, so just be patient - the application works - have
a look in your target folder and you will see the progress.

Start MPO Tool in its folder with ./mpo-tool-gui.py from the commandline.
You will see the GUI and get progress information in your terminal.

License: GPL 3.0
Author: Georg Eckert
Date: 2019-03-14
Version: 0.7.1

Copyright Georg Eckert 2014
