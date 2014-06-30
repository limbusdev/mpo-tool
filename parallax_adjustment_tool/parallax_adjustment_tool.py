#! /usr/bin/env python

'''
    Copyright Georg Eckert 2013

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

################################################################################
# IMPORT -----------------------------------------------------------------------
import sys
import os
import subprocess
import array
from cStringIO import StringIO
    #Pythin Imaging Library
from PIL import Image
    # GTK
from gi.repository import Gtk, GObject, GdkPixbuf, Gdk

################################################################################
# MAIN MPO-Tool CLASS ----------------------------------------------------------
###################

class window_main(object):
    """
    Class of the Main Application

    USAGE:
        app = window_main()
        app.run()
    """
    def __init__(self):
        """
        Initialize Application
        """
        # INITIALIZE
        # variables ------------------------------------------------------------
        self.executing_path = os.path.dirname(__file__)
        self.filelist = []
        self.browsing_index = 0
        self.image_open = False

        # Gtk.Builder() --------------------------------------------------------
        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.path.join(self.executing_path,
                                   'parallax_adjustment_tool.glade'))
        self.builder.connect_signals(self)
    
        # IMPORT OBJECTS -------------------------------------------------------
            # OBJECT: Windows
        self.window_main = self.builder.get_object('window_main')
            # OBJECT: Buttons
        self.button_back = self.builder.get_object('button_back')
        self.button_forth = self.builder.get_object('button_forth')
        self.button_fit = self.builder.get_object('button_fit')
        self.button_zoom_in = self.builder.get_object('button_zoom_in')
        self.button_zoom_out = self.builder.get_object('button_zoom_out')
        self.button_open = self.builder.get_object('button_open')
            # OBJECT: Togglebuttons
        self.spinbutton_parallax = self.builder.get_object('spinbutton_parallax')
            # OBJECT: Dialogs
        self.aboutdialog = self.builder.get_object('aboutdialog')
            # OBJECT: Images
        self.image_main = self.builder.get_object('image_main')
            # OBJECT: Viewports
        self.box_img = self.builder.get_object('box_img')

        # IMAGE WIDGET --------------------------------------------------------
        self.allocation_image = self.box_img.get_allocation()
        self.pixbuf = self.image_main.get_pixbuf()
        self.width_new = 100
        self.height_new = 100

    ############################################################################
    # METHODS ------------------------------------------------------------------
    def run(self):
        try:
            self.window_main.show_all()
            self.warning_dialog()
            Gtk.main()
        except KeyboardInterrupt:
            pass

    def quit(self):
        Gtk.main_quit()

    ############################################################################
    # CALLBACKS ----------------------------------------------------------------

    # BUTTON: Close
    def on_window_main_delete_event(self, *args):
        self.quit()

    # BUTTON: About
    def on_button_about_clicked(self, *args):
        '''show aboutdialog'''
        self.aboutdialog.run()
        self.aboutdialog.hide()

    # BUTTON: Back
    def on_button_back_clicked(self, *args):
        if self.browsing_index == (len(self.filelist) - 1):
            self.browsing_index = 0
        else:
            self.browsing_index += 1
        self.index_changed()

    # BUTTON: Forth
    def on_button_forth_clicked(self, *args):
        if self.browsing_index == 0:
            self.browsing_index = len(self.filelist) - 1
        else:
            self.browsing_index -= 1
        self.index_changed()

    # BUTTON: Fit
    def on_button_fit_clicked(self, *args):
        self.autoresize()

    # BUTTON: Zoom in
    def on_button_zoom_in_clicked(self, *args):
        # Resize
        self.width_new *= 1.1
        self.height_new *= 1.1
        pixbuf_resized = self.pixbuf.scale_simple(
                             self.width_new,
                             self.height_new,
                             GdkPixbuf.InterpType.BILINEAR)
        self.image_main.set_from_pixbuf(pixbuf_resized)

    # BUTTON: Zoom out
    def on_button_zoom_out_clicked(self, *args):
        # Resize
        self.width_new *= 0.9
        self.height_new *= 0.9
        pixbuf_resized = self.pixbuf.scale_simple(
                             self.width_new,
                             self.height_new,
                             GdkPixbuf.InterpType.BILINEAR)
        self.image_main.set_from_pixbuf(pixbuf_resized)

    # BUTTON: Open
    def on_button_open_clicked(self, *args):
        '''
        Open folder, get filelist and set toolbar sensitive
        '''
        # Create FileChooserDialog
        dialog = Gtk.FileChooserDialog(
            "Please choose source file(s)", self.window_main,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        # allow multiple selection
        dialog.set_select_multiple(True)
        # Create FileFilter
        mpo_filter = Gtk.FileFilter()
        mpo_filter.set_name("MPO 3D Images")
        mpo_filter.add_pattern("*.mpo")
        mpo_filter.add_pattern("*.MPO")
        dialog.add_filter(mpo_filter)
        # Run dialog
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.image_open = True
            self.filelist = dialog.get_filenames()
            # Set toolbar buttons sensitive
            self.toolbar_sensitive(True)
            self.browsing_index = 0
            self.index_changed()
        dialog.destroy()

    # RESIZE
    def on_window_main_check_resize(self, window):
        if self.image_open:
            size = self.box_img.get_allocation()
            size_old = self.allocation_image
            # Check
            if size.width <> size_old.width or size.height <> size_old.height:
                print('Window resized, resize image ...')
                self.autoresize()

    # SPINBUTTON: Parallax-Value
    def on_spinbutton_parallax_value_changed(self, *args):
        print('Parallax-Value changed to '
              + str(self.spinbutton_parallax.get_value())
              + '. Refresh image.')
        # Anaglyph
        self.mpo2cr3d(self.filelist[self.browsing_index])
        self.autoresize()

    # BUTTON: Reset Parallax
    def on_button_reset_parallax_clicked(self, *args):
        '''Read parallax value from file and reset spinbutton.'''
        self.index_changed()   

    ############################################################################
    #### FUNCTIONS -------------------------------------------------------------
    def warning_dialog(self):
        dialog = Gtk.MessageDialog(self.window_main,
                                   0,
                                   Gtk.MessageType.WARNING,
                                   Gtk.ButtonsType.OK,
                                   "Did you backup your files?")
        dialog.format_secondary_text(
            "Please keep backups of your MPO 3D photos before using this "
            "application. If anything goes wrong, there is no way of "
            " restoring your files.")
        dialog.run()
        dialog.destroy()

    def filter_filelist(self):
        '''
        Filter filelist for image files
        '''
        pass

    def toolbar_sensitive(self, set_sensitive = True):
        '''
        Set toolbar buttons back, forth, fit, zoom in/out and edit sensitive
        or non-sensitive
        '''
        self.button_back.set_sensitive(set_sensitive)
        self.button_forth.set_sensitive(set_sensitive)
        self.button_fit.set_sensitive(set_sensitive)
        self.button_zoom_in.set_sensitive(set_sensitive)
        self.button_zoom_out.set_sensitive(set_sensitive)
        self.spinbutton_parallax.set_sensitive(set_sensitive)

    def index_changed(self):
        '''
        Displays image belonging to the new index in filelist.
        '''
        print('Show ' + self.filelist[self.browsing_index])
        # Set Window-Title with name of displayed image
        self.window_main.set_title('Parallax Adjustment Tool - '
            + os.path.basename(self.filelist[self.browsing_index]))
        # Get parallax value from 3D file
        self.spinbutton_parallax.set_value(
            self.get_parallax(self.filelist[self.browsing_index]))

    def autoresize(self):
        '''
        Resizes Images automatically to depending on the window-size
        '''
        self.allocation_image = self.box_img.get_allocation()
        width = self.pixbuf.get_width()
        height = self.pixbuf.get_height()
        # Calculate aspect ratio size
        if width >= height:
            self.width_new = self.allocation_image.width - 10
            self.height_new = int(height*self.width_new/width) 
        else:
            self.height_new = self.allocation_image.height - 10
            self.width_new = int(width*self.height_new/height)
        # Resize
        pixbuf_resized = self.pixbuf.scale_simple(
                             self.width_new,
                             self.height_new,
                             GdkPixbuf.InterpType.BILINEAR)
        self.image_main.set_from_pixbuf(pixbuf_resized)

    def get_parallax(self, source):
        '''
        Uses ExifTool to extract 3D Parallax from EXIF
        '''
        try:
            # Extract Parallax from embedded file (-ee -b)
            parallax = float(subprocess.check_output(
                ["exiftool", '-ee', '-b', '-Parallax', source]))
        except:
            print('ERROR: No parallax value found.')
            parallax = 0
        print('Parallax-Value set to: ' + str(parallax))
        return parallax

    def get_parallax_shift(self, parallax, orig_width):
        '''
        Calculates the parallax-shift value, depending on parallax and width
        '''
        parallax_shift = orig_width/100*parallax
        return parallax_shift

    def parallax_crop(self, parallax, left_img, right_img):
        '''Crops images according to the given parallax value'''
        # Get original image width
        (x, y) = left_img.size
        # Calculate shift between L and R
        parallax_shift = int(self.get_parallax_shift(parallax, x))

        if parallax < 0:
            # If parallax <0, cut away from left on left image and from right 
            # on the right image
            right_img = right_img.crop((-1*parallax_shift, 0, x, y))
            left_img = left_img.crop((0, 0, x + parallax_shift, y))

        elif parallax > 0:
            # If parallax >0, cut away from left on right image and from right
            # on the left image
            left_img = left_img.crop((parallax_shift, 0, x, y))
            right_img = right_img.crop((0, 0, x - parallax_shift, y))

        return (left_img, right_img)

    def mpo2cr3d(self, source_file):
        '''
        Extract left and right image from mpo 3d image file.

        USAGE:
            left_img, right_img, img_buffer = extract_from_mpo(mpo_file_obj)

        mpo_file_obj ... object of the open mpo 3d file
        img_buffer ... empty StringIO object, close it after using
        '''
        # Create Object with Double-JPG as Left Image
        left_img = Image.open(source_file)

        # skip SOI and APP1 markers of 1st image
        mpo_file_obj = open(source_file, 'rb')
        mpo_file_obj.seek(4)
        # read both images to a string object
        data = mpo_file_obj.read()

        # Search for second JPG
        # find SOI and APP1 markers of 2nd image in the string
        start2nd_jpg = data.find('\xFF\xD8\xFF\xE1')
        # wrap 2nd image in StringIO object
        img_buffer = StringIO(data[start2nd_jpg:])

        # Create image object for right image
        right_img = Image.open(img_buffer)

        # Resize Image objects for speed
        (x,y) = left_img.size
        if x > 1024 or y > 1024:
            xnew = 1024
            ynew = int(y*xnew/x)
            left_img = left_img.resize((xnew, ynew), Image.ANTIALIAS)
            right_img = right_img.resize((xnew, ynew), Image.ANTIALIAS)

        # cut images regarding to parallax
        left_img, right_img = self.parallax_crop(
                                  self.spinbutton_parallax.get_value(),
                                  left_img, right_img)

        # Create Anaglyph image
        rc3d = self.lr2anaglyph(left_img, right_img)

        # Convert PIL image to GdkPixbuf
        self.pixbuf = self.image2pixbuf(rc3d)

        mpo_file_obj.close()
        img_buffer.close()

    def image2pixbuf(self,img):
        file1 = StringIO()  
        img.save(file1, "ppm")
        contents = file1.getvalue()  
        file1.close()  
        loader = GdkPixbuf.PixbufLoader()  
        loader.write(contents)  
        pixbuf = loader.get_pixbuf()  
        loader.close()  
        return pixbuf 

    def lr2anaglyph(self, left_img, right_img):
        '''Creates red-cyan 3d image from given left and right frames.'''
        # split RGB to R, G and B in PIL
        lred, lgreen, lblue = left_img.split()
        rred, rgreen, rblue = right_img.split()
        # merge from left red channel and right cyan channels
        rc3d = Image.merge('RGB', (lred, rgreen, rblue))
        # save image
        # SAVE MPO NOT YET IMPLEMENTED
        return rc3d

# START
if __name__ == '__main__':
    app = window_main()
    app.run()
