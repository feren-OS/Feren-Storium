#!/usr/bin/python3

import gi
gi.require_version('Gtk', '3.0')

import sys

import os

from gi.repository import Gtk, Gio, Gdk, GLib, Pango, GObject, GdkPixbuf
from threading import Thread
from queue import Queue, Empty


def should_load(): #Should this module be loaded?
    return True


####Store Window
class DebugWindow(object):
    def __init__(self):

        self.current_page = ""

        #systemstate.first_run = self._check_first_run()
        #systemstate.first_run = True

        self._start_page = 'home.html'

        self._build_app()
        
    def close(self, p1 = None, p2 = None):
        #try:
            #os.file.remove(pidfile)
        #except:
            #pass
        Gtk.main_quit(p1, p2)
        
    def gotopkgpagebtn_pressed(self, gtk_widget):
        self.storebrain.gui_module.mainpage._goto_packageview(self.textboxpkgpage.get_text())
        
    def testiceinfo_pressed(self, gtk_widget):
        print(self.storebrain.get_sources(self.textboxpkgpage.get_text()))
        
    def testiteminfo_pressed(self, gtk_widget):
        print(self.storebrain.get_item_info_default(self.textboxpkgpage.get_text()))
        
    def addmessage_pressed(self, gtk_widget):
        self.storebrain.gui_module.mainpage.add_message("info", self.addmessagetbox.get_text(), self.testbutton_pressed, "button test")
        
    def addmessagenobtn_pressed(self, gtk_widget):
        self.storebrain.gui_module.mainpage.add_message("info", self.addmessagetbox.get_text())
        
    def testbutton_pressed(self, gtk_widget):
        print("button press test")

    def _build_app(self):
        # build window
        self.w = Gtk.Window()
        self.w.set_position(Gtk.WindowPosition.CENTER)
        self.w.set_title("Storium Demo - Debug Module")
        self.w.set_resizable(False)
        
        yeet = Gtk.VBox()
        self.w.add(yeet)
        
        self.textboxpkgpage = Gtk.Entry()
        self.textboxpkgpage.set_placeholder_text("package to view")
        self.gotopkgpagebtn = Gtk.Button(label="go to package page")
        
        yeet.pack_start(self.textboxpkgpage, True, False, 4)
        yeet.pack_start(self.gotopkgpagebtn, True, False, 4)
        
        self.gotopkgpagebtn.connect("clicked", self.gotopkgpagebtn_pressed)
        
        self.icegetinfo = Gtk.Button(label="get sources")
        
        yeet.pack_start(self.icegetinfo, True, False, 4)
        
        self.icegetinfo.connect("clicked", self.testiceinfo_pressed)
        
        self.itemgetinfo = Gtk.Button(label="get item info")
        
        yeet.pack_start(self.itemgetinfo, True, False, 4)
        
        self.itemgetinfo.connect("clicked", self.testiteminfo_pressed)
        
        self.addmessagetbox = Gtk.Entry()
        self.addmessagetbox.set_placeholder_text("message test")
        self.addmessage = Gtk.Button(label="add message")
        self.addmessagenobtn = Gtk.Button(label="add message (no btn)")
        
        yeet.pack_start(self.addmessagetbox, True, False, 4)
        yeet.pack_start(self.addmessage, True, False, 4)
        yeet.pack_start(self.addmessagenobtn, True, False, 4)
        
        self.addmessage.connect("clicked", self.addmessage_pressed)
        self.addmessagenobtn.connect("clicked", self.addmessagenobtn_pressed)
        
        #back_img = Gtk.Image()
        #back_img.set_from_icon_name("go-previous-symbolic", Gtk.IconSize.BUTTON);

        #back_btn = Gtk.Button(image=back_img)
        #back_btn.set_sensitive(False)
        #back_btn.set_name("back-btn")
        #back_btn.set_tooltip_text("Back")
        
        #status_img = Gtk.Image()
        #status_img.set_from_icon_name("folder-download-symbolic", Gtk.IconSize.BUTTON);
        #self.status_btn = Gtk.ToggleButton(image=status_img)
        #self.status_btn.set_name("status-btn")
        #self.status_btn.set_always_show_image(True)
        #self.status_handle_id = self.status_btn.connect("clicked", self._status_pressed)
        #self.status_btn.set_tooltip_text("See tasks and updates...")
        
        self.w.connect('delete-event', self.close)

        self.w.show_all()

    def run(self):
        Gtk.main()
    

class main():
    def __init__(self, storebrain):
        self.storebrain = storebrain
    
    
    def init(self):
        global app
        app = DebugWindow()
        app.storebrain = self.storebrain
        app.run()