#!/usr/bin/python3

import gi
gi.require_version('Gtk', '3.0')

import sys

import os

from gi.repository import Gtk, Gio, Gdk, GLib, Pango, GObject, GdkPixbuf
from threading import Thread
from queue import Queue, Empty


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
        self.storebrain.gui_module.main.mainpage._goto_packageview(self.textboxpkgpage.get_text())
        
    def testiceinstall_pressed(self, gtk_widget):
        bonuses = []
        if self.checkboxnekocap.get_active() == True:
            bonuses.append("nekocap")
        if self.checkboxdarkread.get_active() == True:
            bonuses.append("darkreader")
        if self.checkboxublock.get_active() == True:
            bonuses.append("ublock")
        
        self.storebrain.package_module("peppermint-ice").pkgstorage_add(self.textboxicepkgname.get_text())
        
        self.storebrain.package_module("peppermint-ice").install_package(self.textboxicepkgname.get_text(), self.textboxicesource.get_text(), bonuses)
        
    def testiceremove_pressed(self, gtk_widget):
        self.storebrain.package_module("peppermint-ice").pkgstorage_add(self.textboxicepkgname.get_text())
        
        self.storebrain.package_module("peppermint-ice").remove_package(self.textboxicepkgname.get_text(), self.textboxicesource.get_text())
        
    def testiceinfo_pressed(self, gtk_widget):
        print(self.storebrain.get_item_info(self.textboxicepkgname.get_text(), "peppermint-ice"))
        
    def testiteminfo_pressed(self, gtk_widget):
        print(self.storebrain.get_item_info(self.textboxpkgpage.get_text()))
        
    def setpkgprogress_pressed(self, gtk_widget):
        self.storebrain.set_progress(self.storebrain.gui_module.main.mainpage.current_item_viewed, self.storebrain.gui_module.main.mainpage.current_source_viewed, int(self.textboxpkgprogress.get_text()))

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
        
        self.textboxicepkgname = Gtk.Entry()
        self.textboxicepkgname.set_placeholder_text("ice package to manage")
        self.textboxicesource = Gtk.Entry()
        self.textboxicesource.set_placeholder_text("browser to aim for")
        self.checkboxublock = Gtk.CheckButton(label="add ublock")
        self.checkboxnekocap = Gtk.CheckButton(label="add nekocap")
        self.checkboxdarkread = Gtk.CheckButton(label="add darkreader")
        self.iceinstall = Gtk.Button(label="ice install")
        self.iceremove = Gtk.Button(label="ice remove")
        self.icegetinfo = Gtk.Button(label="ice get info")
        
        yeet.pack_start(self.textboxicepkgname, True, False, 4)
        yeet.pack_start(self.textboxicesource, True, False, 4)
        yeet.pack_start(self.checkboxublock, True, False, 4)
        yeet.pack_start(self.checkboxnekocap, True, False, 4)
        yeet.pack_start(self.checkboxdarkread, True, False, 4)
        yeet.pack_start(self.iceinstall, True, False, 4)
        yeet.pack_start(self.iceremove, True, False, 4)
        yeet.pack_start(self.icegetinfo, True, False, 4)
        
        self.iceinstall.connect("clicked", self.testiceinstall_pressed)
        self.iceremove.connect("clicked", self.testiceremove_pressed)
        self.icegetinfo.connect("clicked", self.testiceinfo_pressed)
        
        self.itemgetinfo = Gtk.Button(label="get info")
        
        yeet.pack_start(self.itemgetinfo, True, False, 4)
        
        self.itemgetinfo.connect("clicked", self.testiteminfo_pressed)
        
        self.textboxpkgprogress = Gtk.Entry()
        self.textboxpkgprogress.set_placeholder_text("package progress (0-100)")
        self.setpkgprogress = Gtk.Button(label="set package progress")
        
        yeet.pack_start(self.textboxpkgprogress, True, False, 4)
        yeet.pack_start(self.setpkgprogress, True, False, 4)
        
        self.setpkgprogress.connect("clicked", self.setpkgprogress_pressed)
        
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