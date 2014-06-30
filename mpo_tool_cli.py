#! /usr/bin/env python

import sys
import os
import subprocess
from PIL import Image

def mpo2lr(mpo_fname, destination, parallax2txt=True):
    os.system('exiftool -trailer:all= ' + mpo_fname
              + ' -o ' + destination + '-L.JPG')
    os.system('exiftool ' + mpo_fname + ' -mpimage2 -b > '
              + destination + '-R.JPG')
    if parallax2txt:
        with open(destination + '-parallax.txt', 'w') as parallax_txt:
            parallax = float(subprocess.check_output(
                ["exiftool", '-ee', '-b', '-Parallax', mpo_fname]))
            parallax_txt.write(str(parallax))

def lr2anaglyph(l_fname, r_fname, rc_fname, parallax, jpg_quality=100):
    l_img = Image.open(l_fname)
    r_img = Image.open(r_fname)
    (x, y) = l_img.size
    parallax_shift = x/100*parallax
    if parallax < 0:
        r_img = r_img.crop((-1*parallax_shift, 0, x, y))
        l_img = l_img.crop((0, 0, x + parallax_shift, y))
    elif parallax > 0:
        l_img = l_img.crop((parallax_shift, 0, x, y))
        r_img = r_img.crop((0, 0, x - parallax_shift, y))
    lred, lgreen, lblue = l_img.split()
    rred, rgreen, rblue = r_img.split()
    rc3d = Image.merge('RGB', (lred, rgreen, rblue))
    rc3d.save(rc_fname + '-rc3d.JPG', quality=jpg_quality)

if __name__ == '__main__':
    if sys.argv[1] == '-mpo2lr':
        mpo2lr(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == '-lr2anaglyph':
        lr2anaglyph(sys.argv[2], sys.argv[3], sys.argv[4],
               int(sys.argv[5]), int(sys.argv[6]))
