#! /usr/bin/env python3.2

"""
BeeHive GUI Library

This Library provides modules for GUIs like Dialogs, Special Windows and so on.
"""

# IMPORT
    # GTK
from gi.repository import Gtk
import os

from random import randint # TippsWindow

class HelpWindow(object):
    """
    Opens a Help Window and displays given File with GTK Markup

    USAGE:
        app = beehivelibgui.HelpWindow()
        app.run()

        # optional:
        app.configure(help_file_name = 'help.txt', window_title = 'Help')
    """
    def __init__(self):
        """
        Initialize Window
        """
        # INITIALIZE
        # build dialog with Gtk.Builder()
        self.dialog_builder = Gtk.Builder()
        self.dialog_builder.add_from_file(
            os.path.join(os.path.dirname(__file__), 'beehiveguilib_help.glade'))
        self.dialog_builder.connect_signals(self)
    
        # import objects
        self.window_help = self.dialog_builder.get_object('window_help')
        self.label_helptext = self.dialog_builder.get_object('label_helptext')

        # configure objects
        self.help_file_name = 'help.txt'
        self.window_title = 'Hilfe'

    # RUN
    def run(self):
        # load from file
        with open(self.help_file_name,'r') as helpfile:
            helptext = helpfile.read()
        self.label_helptext.set_markup(helptext)
        del helptext

        # set window title
        self.window_help.set_title(self.window_title)

        # open window
        self.window_help.show_all()
        Gtk.main()

    # FUNCTIONS
    def configure(self, help_file_name = 'help.txt', window_title = 'Hilfe'):
        self.help_file_name = help_file_name
        self.window_title = window_title
                
    # CALLBACKS
    def on_window_help_delete_event(self, *args):
        Gtk.main_quit()
