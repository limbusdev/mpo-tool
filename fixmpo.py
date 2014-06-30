#! /usr/bin/env python

import sys
import os
import subprocess # for calling system commands like exiftool

def fixmpo(source):
    '''fixes MPO files which where corrupted by editing
       metadata with exiv2'''
    # Getting Comment
    comment = str(subprocess.check_output(
        ["exiftool", "-p", "'$Comment'", source]))
    print('Saved comment: ' + comment)
    # Removing the Comment with ExifTool
    subprocess.call(["exiftool", "-comment=", source])
    # Readding comment with ExifTool
    subprocess.call(["exiftool", ("-comment=" + "'" + comment + "'"), source])