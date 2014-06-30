#! /usr/bin/env python2

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

###############################################################################
# IMPORT ----------------------------------------------------------------------
import sys
import os
import subprocess # for calling system commands like exiftool
from cStringIO import StringIO
try:
    from PIL import Image # Python Imaging Library
except ImportError:
    exit('You need to install PIL first. Try: sudo apt-get install python-imag'
         'ing')
try:
    from gi.repository import Gtk, GObject # GTK
except ImportError:
    exit('You need to install GObject Introspection first. Try: sudo apt-get i'
         'nstall python-gi')
from beehivelib.bhgui import HelpWindow # BeeHiveLib
from parallax_adjustment_tool import parallax_adjustment_tool # PAT

###############################################################################
# MAIN MPO-Tool CLASS ---------------------------------------------------------
###################

class MPOTool(object):
    """
    Class of the Main Application

    USAGE:
        app = MPOTool()
        app.run()
    """
    def __init__(self):
        """
        Initialize Application
        """
        # INITIALIZE
        # variables -----------------------------------------------------------
        self.executing_path = os.path.dirname(__file__)
        self.cancel = False
        self.target = os.path.expanduser('~')
        self.conversion_mode = 'stereo'
        self.jps_mode = 'xview'
        self.image_quality = 85
        self.parallax = 0
        self.parallax_shift = 0
        self.exiftool_message = ('It seems that ExifTool is not installed on y'
                                 'your system. MPO Tool needs ExifTool to work'
                                 ' properly. Please install and try again.')
        self.gui_mode = "stereo"
        self.discard_r_image = False
        self.create_parallax_txt = True

        # Gtk.Builder() -------------------------------------------------------
        self.dialog_builder = Gtk.Builder()
        self.dialog_builder.add_from_file(
            os.path.join(self.executing_path, 'mpo-tool.glade'))
        self.dialog_builder.connect_signals(self)
    
        # IMPORT OBJECTS ------------------------------------------------------
            # Windows
        self.mainwindow = self.dialog_builder.get_object('mainwindow')
            # Entries
        self.entry_source = self.dialog_builder.get_object('entry_source')
        self.entry_target = self.dialog_builder.get_object('entry_target')
            # Labels
        self.label_notification = self.dialog_builder.get_object(
                                      'label_notification')
            # Spinbuttons
        self.spinbutton_quality = self.dialog_builder.get_object(
                                      'spinbutton_quality')
        self.spinbutton_resize = self.dialog_builder.get_object(
                                      'spinbutton_resize')
        self.spinbutton_parallax = self.dialog_builder.get_object(
                                      'spinbutton_parallax')
            # Checkbuttons
        self.checkbutton_parallax_txt = self.dialog_builder.get_object(
                                            'checkbutton_parallax_txt')
        self.checkbutton_discard_r_image = self.dialog_builder.get_object(
                                               'checkbutton_discard_r_image')
            # Progressbars
        self.progressbar = self.dialog_builder.get_object('progressbar')
            # Buttons
        self.button_convert = self.dialog_builder.get_object('button_convert')
        self.button_cancel = self.dialog_builder.get_object('button_cancel')
        self.button_getdir_source = self.dialog_builder.get_object(
                                        'button_getdir_source')
        self.button_getdir_target = self.dialog_builder.get_object(
                                        'button_getdir_target')
            # Dialogs
        self.aboutdialog = self.dialog_builder.get_object('aboutdialog')
            # Frames
        self.frame_mode = self.dialog_builder.get_object('frame_mode')
        self.frame_options = self.dialog_builder.get_object('frame_options')
        
        # INITIALIZE OBJECTS --------------------------------------------------
        self.entry_target.set_text(self.target)
        self.button_convert.set_sensitive(False)

    ###########################################################################
    # METHODS -----------------------------------------------------------------
    def run(self):
        try:
            self.mainwindow.show_all()
            self.warning_dialog()
            Gtk.main()
        except KeyboardInterrupt:
            pass

    def quit(self):
        Gtk.main_quit()

    ###########################################################################
    # CALLBACKS ---------------------------------------------------------------

    # BUTTON: Cancel ----------------------------------------------------------
    def on_button_cancel_clicked(self, *args):
        self.cancel = True

    # BUTTON: Close -----------------------------------------------------------
    def on_mainwindow_delete_event(self, *args):
        self.quit()

    # BUTTON: About -----------------------------------------------------------
    def on_button_about_clicked(self, *args):
        '''show aboutdialog'''
        self.aboutdialog.run()
        self.aboutdialog.hide()

    # BUTTON: Help ------------------------------------------------------------
    def on_button_help_clicked(self, *args):
        """show help window"""
        help_window = HelpWindow()
        help_window.configure(
            os.path.join(self.executing_path, 'mpo-help.txt'), 'MPO-Tool Help')
        help_window.run()

    # BUTTON: Convert ---------------------------------------------------------
    def on_button_convert_clicked(self, *args):
        # check if ExifTool is installed
        exiftool_inst = self.whereis('exiftool')
        if exiftool_inst is not None:
            self.label_notification.set_markup("<i>Conversion Started ...</i>")
            self.set_gui_mode('convert')
            # Start conversion
            self.convert_mpo()
            self.set_gui_mode(self.gui_mode)
        else:
            # Show warning dialog.
            dialog = Gtk.MessageDialog(self.mainwindow, 0, Gtk.MessageType.WARNING,
                Gtk.ButtonsType.CANCEL, "ExifTool not found.")
            dialog.format_secondary_text(self.exiftool_message)
            dialog.run()
            dialog.destroy()

    # TOGGLEBUTTON: define toggle-event for radio button stereo ---------------
    def on_radiobutton_stereo_toggled(self, button):
        if button.get_active():
            print('CONVERSION MODE: JPS Stereo Crossview')
            self.conversion_mode = 'stereo'
            self.set_gui_mode('stereo')
            # Set JPS Mode
            self.jps_mode = 'xview'

    # TOGGLEBUTTON: define toggle-event for radio button jps parallel ---------
    def on_radiobutton_jps_parallel_toggled(self, button):
        if button.get_active():
            print('CONVERSION MODE: JPS Stereo Parallel')
            self.conversion_mode = 'stereo'
            self.set_gui_mode('stereo')
            # Set JPS Mode
            self.jps_mode = 'parallel'

    # TOGGLEBUTTON: define toggle-event for radio button split ----------------
    def on_radiobutton_split_toggled(self, button):
        if button.get_active():
            print('CONVERSION MODE: Split MPO to L/R JPEG')
            self.conversion_mode = 'split'
            self.set_gui_mode('split')

    # TOGGLEBUTTON: define toggle-event for radio button anaglyph -------------
    def on_radiobutton_anaglyph_toggled(self, button):
        if button.get_active():
            print('CONVERSION MODE: Red/Cyan Anaglyph 3D')
            self.conversion_mode = 'anaglyph'
            self.set_gui_mode('stereo')
            
    # TOGGLEBUTTON: define toggle-event for radio button fixmpo -------------
    def on_radiobutton_fixmpo_toggled(self, button):
        if button.get_active():
            print('CONVERSION MODE: Fix MPO')
            self.conversion_mode = 'fixmpo'
            self.set_gui_mode('fixmpo')
            
    # CHECKBUTTON: Parallax.txt -----------------------------------------------
    def on_checkbutton_parallax_txt_toggled(self, button):
        if button.get_active():
            print('Create parallax.txt: ON')
            self.create_parallax_txt = True
        else:
            print('Create parallax.txt: OFF')
            self.create_parallax_txt = False
            
    # CHECKBUTTON: Discard right image ----------------------------------------
    def on_checkbutton_discard_r_image_toggled(self, button):
        if button.get_active():
            print('Discard right image: ON')
            self.discard_r_image = True
        else:
            print('Discard right image: OFF')
            self.discard_r_image = False

    # BUTTON: get sourcefiles -------------------------------------------------
    def on_button_getdir_source_clicked(self, button):
        # Create FileChooserDialog
        dialog = Gtk.FileChooserDialog(
            "Please choose source file(s)", self.mainwindow,
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
            self.source = dialog.get_filenames()
            self.entry_source.set_text(
                str(len(self.source)) + ' File(s) in '
                + os.path.dirname(dialog.get_filenames()[0]))
            print(
                  'Chose ' + str(len(self.source)) + ' File(s) in '
                  + os.path.dirname(dialog.get_filenames()[0])
                  + ' for conversion')
            # Activate Convert-Button
            self.button_convert.set_sensitive(True)
        dialog.destroy()

    # BUTTON: set target folder -----------------------------------------------
    def on_button_getdir_target_clicked(self, button):
        dialog = Gtk.FileChooserDialog(
            "Please choose a target folder", self.mainwindow,
            Gtk.FileChooserAction.SELECT_FOLDER,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.target = dialog.get_filename()
            self.entry_target.set_text(self.target)
        dialog.destroy()
        print('TARGET DIRECTORY: ' + self.target)

    # BUTTON: Parallax Adjustment Tool - PAT
    def on_button_parallax_adjustment_clicked(self, *args):
        '''Starts the parallax adjustment tool.'''
        pat = parallax_adjustment_tool.window_main()
        pat.run()

    ###########################################################################
    #### FUNCTIONS ------------------------------------------------------------
    def set_gui_mode(self, mode):
        """
        Sets GUI elements sensitive or non-sensitive, depending on the
        applications state.
        
        USAGE:
            set_gui_mode(mode)
            
        MODES:
        config ... when user sets input files and so on, before conversion
        convert ... conversion startet, only cancel button sensitive
        fixmpo ... disables target folder setting and convert options
        """
        if mode == 'stereo':
            self.gui_mode = "stereo"
			
            self.checkbutton_parallax_txt.set_visible(False)
            self.checkbutton_discard_r_image.set_visible(False)
            self.frame_mode.set_sensitive(True)
            self.frame_options.set_sensitive(True)
            self.button_convert.set_sensitive(True)
            self.button_convert.set_visible(True)
            self.button_getdir_source.set_sensitive(True)
            self.button_getdir_target.set_sensitive(True)
            self.button_cancel.set_sensitive(False)
            self.button_cancel.set_visible(False)
        elif mode == 'convert':
            self.frame_mode.set_sensitive(False)
            self.frame_options.set_sensitive(False)
            self.button_convert.set_sensitive(False)
            self.button_convert.set_visible(False)
            self.button_getdir_source.set_sensitive(False)
            self.button_getdir_target.set_sensitive(False)
            self.button_cancel.set_sensitive(True)
            self.button_cancel.set_visible(True)
        elif mode == 'fixmpo':
            self.gui_mode = "fixmpo"
			
            self.checkbutton_parallax_txt.set_visible(False)
            self.checkbutton_discard_r_image.set_visible(False)
            self.frame_mode.set_sensitive(True)
            self.frame_options.set_sensitive(False)
            self.button_convert.set_sensitive(True)
            self.button_convert.set_visible(True)
            self.button_getdir_source.set_sensitive(True)
            self.button_getdir_target.set_sensitive(False)
            self.button_cancel.set_sensitive(False)
            self.button_cancel.set_visible(False)
        elif mode == "split":
            self.gui_mode = 'split'
			
            self.checkbutton_parallax_txt.set_visible(True)
            self.checkbutton_discard_r_image.set_visible(True)
            self.frame_mode.set_sensitive(True)
            self.frame_options.set_sensitive(True)
            self.button_convert.set_sensitive(True)
            self.button_convert.set_visible(True)
            self.button_getdir_source.set_sensitive(True)
            self.button_getdir_target.set_sensitive(True)
            self.button_cancel.set_sensitive(False)
            self.button_cancel.set_visible(False)
        # refresh GUI
        while Gtk.events_pending():
            Gtk.main_iteration()
    
    def warning_dialog(self):
        dialog = Gtk.MessageDialog(self.mainwindow,
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

    def whereis(self, program):
        '''Finds out whether a given programm is in pythons PATH variable'''
        answer = None
        for path in os.environ.get('PATH', '').split(':'):
            if os.path.exists(os.path.join(path, program)) and \
                not os.path.isdir(os.path.join(path, program)):
                answer = os.path.join(path, program)
        return answer
      
    def fixmpo(self, source):
        '''fixes MPO files which where corrupted by editing
           metadata with exiv2'''
        # Getting Comment
        comment = str(subprocess.check_output(
                ["exiftool", "-p", "'$Comment'", source]))
        
        print('Saved comment: ' + comment)
        # Removing the Comment with ExifTool
        subprocess.call(["exiftool", "-comment=", '-overwrite_original', source])
        if comment:
            # Readding comment with ExifTool
            subprocess.call(["exiftool", ("-comment=" + "'" + comment + "'"),
                             '-overwrite_original', source])
        else:
            print("No comment available ... skip!")

    def copy_exif(self, source, target, embedded=False):
        '''
        Uses ExifTool to copy EXIF-Metadata from source- to target-file
        '''
        # For left image
        if embedded:
            subprocess.call(["exiftool", "-tagsFromFile", source,
                             '-overwrite_original', target])
        # For right image
        else:
            subprocess.call(["exiftool", '-ee', "-tagsFromFile", source,
                             '-overwrite_original', target])

    def get_parallax(self, source):
        '''
        Uses ExifTool to extract 3D Parallax from EXIF
        '''
        try:
            # Extract Parallax from embedded file (-ee -b)
            parallax = float(subprocess.check_output(
                ["exiftool", '-ee', '-b', '-Parallax', source]))
            # Get parallax correction
            parallax = parallax + self.spinbutton_parallax.get_value()
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

    def extract_from_mpo(self, mpo_file_obj):
        '''
        Extract left and right image from mpo 3d image file.

        USAGE:
            left_img, right_img, img_buffer = extract_from_mpo(mpo_file_obj)

        mpo_file_obj ... object of the open mpo 3d file
        img_buffer ... empty StringIO object, close it after using
        '''
        # Create Object with Double-JPG as Left Image
        left_img = Image.open(mpo_file_obj)

        # skip SOI and APP1 markers of 1st image
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

        return (left_img, right_img, img_buffer)

    def mpo2lr(self, source):
        '''
        Saves left and right image object as jpeg files and a txt file
        containing the parallax value
        '''
        # Make Savenames
        savename_r = os.path.join(
            self.target, os.path.basename(source)[:-4] + '-R.' + 'jpg')
        savename_l = os.path.join(
            self.target, os.path.basename(source)[:-4] + '-L.' + 'jpg')
        savename_parallax = os.path.join(
            self.target,  os.path.basename(source)[:-4] + '-Parallax.' + 'txt')
        # Save Images
        subprocess.call(["exiftool", "-all=", "--exif:all", "-o", savename_l, source])
        subprocess.call(["exiftool", "-overwrite_original", "-tagsFromFile",
                         source, savename_l])
        subprocess.call(["exiftool", "-mpf:all=", savename_l])
        if not self.discard_r_image:
            subprocess.call(["exiftool", "-mpimage2", "-b", "-W", savename_r, source])
            subprocess.call(["exiftool", "-overwrite_original", "-tagsFromFile",
                             source, savename_r])
            subprocess.call(["exiftool", "-mpf:all=", savename_r])

        if self.create_parallax_txt:
            # Save Parallax-Value in Textfile
            parallax = self.get_parallax(source)
            with open(savename_parallax, 'w') as parallax_file:
                parallax_file.write(str(parallax))

    def lr2anaglyph(self, left_img, right_img, source):
        '''Creates red-cyan 3d image from given left and right frames.'''
        # split RGB to R, G and B in PIL
        lred, lgreen, lblue = left_img.split()
        rred, rgreen, rblue = right_img.split()
        # merge from left red channel and right cyan channels
        rc3d = Image.merge('RGB', (lred, rgreen, rblue))
        # save image
        savename = os.path.join(
            self.target, os.path.basename(source)[:-4] + '-RC3D.' + 'jpg')
        rc3d.save(savename, quality=self.image_quality)
        # Copy EXIF Data from Source to Target file
        self.copy_exif(source, savename)

    def lr2jps(self, left_img, right_img, source):
        '''Takes 2 image-objects and puts them together to a stereo-image'''
        print('Convert to JPS file ...')
        x, y = left_img.size
        # create image object for stereo image
        stereo = Image.new("RGB", (x*2, y))
        # XVIEW: Left image on right and vice versa
        # PARALLEL: Left image on left and vice versa
        if self.jps_mode == 'xview':
            stereo.paste(right_img, (0,0))
            stereo.paste(left_img, (x, 0))
        elif self.jps_mode == 'parallel':
            stereo.paste(left_img, (0,0))
            stereo.paste(right_img, (x, 0))

        # Save Stereo-JPEG
        savename = os.path.join(
                   self.target, (os.path.basename(source)[:-3] + 'jps'))
        stereo.save(savename, 'JPEG', quality = self.image_quality)

        # Copy EXIF Data from Source to Target file
        self.copy_exif(source, savename)

    def fit_canvas(self, dimension, value, img_obj):
        '''
        Resizes image-object while keeping aspect ratio.
        USAGE:
            Example:
            img_object = fit_canvas(dimension='y', value='1080', img_object)
        
        Resizes the given image object height to 1080 and automatically
        calculates the image width to keep the original aspect ratio.

        dimensions ... x, y
        '''
        xorg, yorg = img_obj.size
        if dimension is 'y':
            ynew = value
            xnew = 2 * int(xorg/2*ynew/yorg)       
        elif dimension is 'x':
            xnew = value
            ynew = 2 * int(yorg/2*xnew/xorg)
        img_obj = img_obj.resize((xnew, ynew), Image.ANTIALIAS)
        return img_obj

    def convert_mpo(self):
        '''does the mpo conversion depending on the set mode
           Mode:
               stereo - side-by-side JPS stereo (xview/parallel)
               split - save left and right image seperately
               anaglyph - create Red-Cyan anaglyph image
        '''
        # set start value for progress bar
        self.progressbar.set_fraction(0)
        # refresh GUI
        while Gtk.events_pending():
            Gtk.main_iteration()
        # set loop-counter
        counter = 0
        # count mpo files
        mpo_count = len(self.source)
        print('Start conversion of ' + str(mpo_count) + ' File(s) ...')

        # get resize-height from spinbutton
        target_height = int(self.spinbutton_resize.get_value())
        print('Images will be resized to y = ' + str(target_height))

        # get save-jpg-quality from spinbutton
        self.image_quality = int(self.spinbutton_quality.get_value())
        print('JPEG output quality is set to ' + str(self.image_quality) + ' %.')

        # CONVERSION ---------------------------------------------------- START
        for i in self.source:
            if self.conversion_mode == 'fixmpo':
                # CONVERSION-MODE: FixMpo
                self.fixmpo(i)
            # CONVERSION MODE: Split MPO ------------------------------
            elif self.conversion_mode == 'split':
                self.mpo2lr(i)
            # ---------------------------------------------------------
            else:
			    # open file
                with open(i, 'rb') as mpo_file:
                    print('Open file ' + i)

                    # Extract L and R frames --------------------------------------
                    split_worked = True
                    try:
                        left, right, img_buffer = self.extract_from_mpo(mpo_file)
                    except:
                        print('ERROR: Could not split ' + i + '. Either file is no'
                              't an MPO 3D file or right Image is missing (happens'
                              ' if you rotate MPO files).')
                        print('Ignore file ' + i + ' ...')
                        split_worked = False

                    # Proceed only after extraction -------------------------------
                    if split_worked:

                        # Resize images
                        if target_height > 0:
                            left = self.fit_canvas('y', target_height, left)
                            right = self.fit_canvas('y', target_height, right)

                        # PARALLAX: set parallax_value
                        parallax = self.get_parallax(i)

                        # Crop according to parallax value
                        (left, right) = self.parallax_crop(
                                        parallax, left, right)

                        # CONVERSION MODE: Anaglyph -------------------------------
                        if self.conversion_mode == 'anaglyph':
                            self.lr2anaglyph(left, right, i)
                        # ---------------------------------------------------------

                        # CONVERSION MODE: Stero 3D JPS ---------------------------
                        elif self.conversion_mode == 'stereo':
                            self.lr2jps(left, right, i)
                        # ---------------------------------------------------------

            # progressbar
            counter += 1
            # python2: 1/3 = 0, float(1)/3 = 0.333; python3: 1/3 = 0.333
            progress_value = float(counter) / mpo_count
            self.progressbar.set_fraction(progress_value)
            # set label notification
            self.label_notification.set_markup("<i>Conversion:</i> File "
                + str(counter) + " of " + str(mpo_count))
            # refresh GUI
            while Gtk.events_pending():
                Gtk.main_iteration()
            # CLI progress
            print('Converted: ' + str(counter) + ' of ' + str(mpo_count))
            
            # Check Cancel Button
            if self.cancel:
                break
                print('Conversion cancelled by user.')
                self.label_notification.set_markup(
                    "<i>Cancelled after:</i> File " + os.path.basename(i))
                self.cancel = False

        # Close image buffer
        if self.conversion_mode is not "fixmpo":
            if self.conversion_mode is not "split":
                img_buffer.close()
        # set label notification
        self.label_notification.set_markup(
           "<b><i>Conversion Finished</i></b>")
        # update progressbar
        self.progressbar.set_fraction(1.0)

# START
if __name__ == '__main__':
    app = MPOTool()
    app.run()
