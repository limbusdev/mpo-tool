# MPO Tool

![](./camera.png)

## Introduction

MPO Tool is a little piece of software for splitting and converting MPO 3D photos. It is written in python2.7 (because there is no Python Imaging Library for Python3 yet) and GTK+3 (via GObject-Introspection).


Use MPO Tool to convert MPO to JPS.


## What can it do?

+ Split MPO files to seperate JPGs
+ Create an anaglphy red/cyan JPG from MPO
+ Create a cross looking image
+ Create a parallel looking image

![](./mpo_split.png)![](./anaglyph.png)![](jps_cross.png)![](./jps_parallel.png)

## Dependencies

### Ubuntu/Debian:

+ gir1.2-gexiv2-0.4
+ libgexiv2-dev
+ python-imaging
+ python-gi

## Troubleshooting

Progressbar does not work yet, so just be patient - the application works - have
a look in your target folder and you will see the progress.

## How to use

Start MPO Tool in its folder with ./mpo-tool-gui.py from the commandline.
You will see the GUI and get progress information in your terminal.

## License

License: GPL 3.0
Author: Georg Eckert
Date: 2019-03-14
Version: 0.7.1

Copyright Georg Eckert 2014
