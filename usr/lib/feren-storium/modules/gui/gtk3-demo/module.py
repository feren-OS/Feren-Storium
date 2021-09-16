#!/usr/bin/python3

import gi

gi.require_version('WebKit2', '4.0')
gi.require_version('Gtk', '3.0')

import sys
import urllib.request #Grabbing files from internet
import urllib.error
import locale #Translations go brrr
import gettext #Translations go brrr
import getpass #Used for finding username
import colorsys #Used for page recolourisation

import os

from gi.repository import Gtk, Gio, Gdk, GLib, Pango, GObject, GdkPixbuf
from threading import Thread
from queue import Queue, Empty
from notify2 import Notification, init as NotifyInit



####Application Details Header
class AppDetailsHeader(Gtk.VBox):

    def __init__(self):
        
        Gtk.Box.__init__(self)
        
        self.app_icon = Gtk.Image()
        self.app_icon.set_from_icon_name("deb", Gtk.IconSize.DND)
        
        self.app_title = Gtk.Label()
        self.app_title.set_label("APPLICATION TITLE")
        
        self.app_shortdesc = Gtk.Label()
        self.app_shortdesc.set_label("APPLICATION SHORT DESCRIPTION")
        
        self.app_source_dropdown = Gtk.ComboBox()
        
        self.app_mgmt_progress = Gtk.ProgressBar()
        
        buttonsbox = Gtk.Box()
        
        self.installapp_btn = Gtk.Button(label=("Install"))
        self.installappnosource_btn = Gtk.Button(label=("Install..."))
        self.updateapp_btn = Gtk.Button(label=("Update"))
        self.removeapp_btn = Gtk.Button(label=("Remove"))
        
        buttonsbox.pack_start(self.installapp_btn, False, False, 4)
        buttonsbox.pack_start(self.installappnosource_btn, False, False, 4)
        buttonsbox.pack_start(self.updateapp_btn, False, False, 4)
        buttonsbox.pack_start(self.removeapp_btn, False, False, 4)
        
        self.pack_start(self.app_icon, False, False, 4)
        self.pack_start(self.app_title, True, False, 4)
        self.pack_start(self.app_shortdesc, True, False, 4)
        self.pack_start(self.app_source_dropdown, False, False, 4)
        self.pack_start(self.app_mgmt_progress, True, False, 4)
        self.pack_start(buttonsbox, True, False, 4)
        
        pass



####AppView
class AppMainView(Gtk.Stack):

    def __init__(self):
        Gtk.Stack.__init__(self)
        
        self.sw = Gtk.ScrolledWindow()
        self.sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        mainbox = Gtk.VBox()
        
        mainlbl = Gtk.Label(label=("Application Listings"))
        
        self.applistbox = Gtk.FlowBox()
        self.applistbox.set_valign(Gtk.Align.START)
        
        
        
        themeslbl = Gtk.Label(label=("Themes Listings"))
        
        #TODO: Turn these into a box and do the math https://python-gtk-3-tutorial.readthedocs.io/en/latest/layout.html
        self.themelistbox = Gtk.FlowBox()
        self.themelistbox.set_valign(Gtk.Align.START)
        
        
        
        websiteslbl = Gtk.Label(label=("Websites Listings"))
        
        #TODO: Turn these into a box and do the math https://python-gtk-3-tutorial.readthedocs.io/en/latest/layout.html
        self.websiteslistbox = Gtk.FlowBox()
        self.websiteslistbox.set_valign(Gtk.Align.START)
        
        
        
        self.sw.add(mainbox)
        self.add_named(self.sw, "mainbox")
        mainbox.pack_start(mainlbl, True, False, 4)
        mainbox.pack_start(self.applistbox, True, True, 4)
        mainbox.pack_start(themeslbl, True, False, 4)
        mainbox.pack_start(self.themelistbox, True, True, 4)
        mainbox.pack_start(websiteslbl, True, False, 4)
        mainbox.pack_start(self.websiteslistbox, True, True, 4)
        mainbox.pack_end(Gtk.Box(), True, True, 4)
        
        
        
        # build tasks page
        taskspage = Gtk.VBox(spacing=8)
        
        taskslabel_box = Gtk.Box()
        taskslabel = Gtk.Label(label="Currently working on these tasks:")
        taskslabel_box.pack_start(taskslabel, False, False, 0)
        
        self.tasksitems = Gtk.FlowBox()
        self.tasksitems.set_margin_top(4)
        self.tasksitems.set_margin_bottom(4)
        self.tasksitems.set_min_children_per_line(1)
        self.tasksitems.set_max_children_per_line(1)
        self.tasksitems.set_row_spacing(4)
        self.tasksitems.set_homogeneous(True)
        self.tasksitems.set_valign(Gtk.Align.START)
        
        updateslabel_box = Gtk.Box()
        updateslabel = Gtk.Label(label="Updates are available for:")
        updateslabel_box.pack_start(updateslabel, False, False, 0)
        
        self.updatesitems = Gtk.FlowBox()
        self.updatesitems.set_margin_top(4)
        self.updatesitems.set_margin_bottom(4)
        self.updatesitems.set_min_children_per_line(1)
        self.updatesitems.set_max_children_per_line(1)
        self.updatesitems.set_row_spacing(4)
        self.updatesitems.set_homogeneous(True)
        self.updatesitems.set_valign(Gtk.Align.START)
        
        installedlabel_box = Gtk.Box()
        installedlabel = Gtk.Label(label="Currently installed:")
        installedlabel_box.pack_start(installedlabel, False, False, 0)
        
        self.installeditems = Gtk.FlowBox()
        self.installeditems.set_margin_top(4)
        self.installeditems.set_margin_bottom(4)
        self.installeditems.set_min_children_per_line(1)
        self.installeditems.set_max_children_per_line(1)
        self.installeditems.set_row_spacing(4)
        self.installeditems.set_homogeneous(True)
        self.installeditems.set_valign(Gtk.Align.START)
                
        taskspage.pack_start(taskslabel_box, False, True, 0)
        taskspage.pack_start(self.tasksitems, False, True, 0)
        taskspage.pack_start(updateslabel_box, False, True, 0)
        taskspage.pack_start(self.updatesitems, False, True, 0)
        taskspage.pack_start(installedlabel_box, False, True, 0)
        taskspage.pack_start(self.installeditems, False, True, 0)
        
        # build another scrolled window widget and add our tasks view
        self.sw2 = Gtk.ScrolledWindow()
        self.sw2.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        taskspage.set_margin_bottom(8)
        taskspage.set_margin_top(8)
        taskspage.set_margin_left(10)
        taskspage.set_margin_right(10)
        
        self.sw2.add(taskspage)
        
        
        self.add_named(self.sw2, "tasks")
        
        
        
        # build search page
        searchpage = Gtk.VBox(spacing=8)
        
        self.searchresults = Gtk.FlowBox()
        self.searchresults.set_margin_top(4)
        self.searchresults.set_margin_bottom(4)
        self.searchresults.set_min_children_per_line(1)
        self.searchresults.set_max_children_per_line(1)
        self.searchresults.set_row_spacing(4)
        self.searchresults.set_homogeneous(True)
        self.searchresults.set_valign(Gtk.Align.START)
        
        searchpage.pack_start(self.searchresults, False, True, 0)
        
        # build another scrolled window widget and add our search view
        self.sw3 = Gtk.ScrolledWindow()
        self.sw3.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        searchpage.set_margin_bottom(8)
        searchpage.set_margin_top(8)
        searchpage.set_margin_left(10)
        searchpage.set_margin_right(10)
        
        self.sw3.add(searchpage)
        
        
        self.add_named(self.sw3, "search")
        
        
        
        # build package page
        packagepage = Gtk.VBox(spacing=8)
        
        templabel_box = Gtk.Box()
        templabel = Gtk.Label(label="Package Page Placeholder")
        templabel_box.pack_start(templabel, False, False, 0)
        
        packagepage.pack_start(templabel, False, True, 0)
        
        # build another scrolled window widget and add our search view
        self.sw4 = Gtk.ScrolledWindow()
        self.sw4.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        packagepage.set_margin_bottom(8)
        packagepage.set_margin_top(8)
        packagepage.set_margin_left(10)
        packagepage.set_margin_right(10)
        
        self.sw4.add(packagepage)
        
        
        self.add_named(self.sw4, "packagepage")
    


    def toggle_back(self, newstate):
        backbtnthread = Thread(target=self._toggle_back,
                            args=(newstate,))
        backbtnthread.start()
    
    def _toggle_back(self, newstate):
        GLib.idle_add(self.__toggle_back, newstate)
    
    def __toggle_back(self, newstate):
        self.back_btn.set_sensitive(newstate)

    def _back_action(self, data):
        self.toggle_back(False)
        #Remove from back history
        self.back_button_history = self.back_button_history[:-1]
        pass
        #TODO
        
    def _goto_page(self, page):
        self.set_visible_child(page)
        
    def _goto_packageview(self, packagename):
        #TODO
        pass

    def _btn_goto_packageview(self, btn, packagename):
        self._goto_packageview(packagename)

    def _generate_apps_list(self, category):
        pass

    def _generate_websites_list(self, category):
        pass

    def update_insite_information(self, packagename, packagetype):
        pass
            
    def packagepagestuff(self):
        pass

    #def _push_config(self):
        ## TODO: push notification should be connected to angularjs and use a
        ## broadcast event any suitable controllers will be able to listen and
        ## respond accordingly, for now we just use jQuery to manually toggle
        #current_page = app.current_page



####Store Window
class StoreWindow(object):
    def __init__(self):

        self.current_page = ""

        #systemstate.first_run = self._check_first_run()
        #systemstate.first_run = True

        self._start_page = 'home.html'

        self._build_app()

    def build_app_post_splashscreen(self, mainwindow, maintoolbar, mv):
        GLib.idle_add(self._build_app_post_splashscreen, mainwindow, maintoolbar, mv)

    def _build_app_post_splashscreen(self, mainwindow, maintoolbar, mv):
        # build rest of window
        box_application_header = AppDetailsHeader()
        #box_application_header.set_visible(False)
        box_application_header.parent_window = self.w
        # add the box to the parent window and show
        mainwindow.pack_start(maintoolbar, False, True, 0)
        mainwindow.pack_start(box_application_header, False, True, 0)
        mainwindow.pack_end(mv, True, True, 0)
        mv.AppDetailsHeader = box_application_header
        self.w.show_all()

    def _build_app(self):
        # build window
        self.w = Gtk.Window()
        self.w.set_position(Gtk.WindowPosition.CENTER)
        self.w.set_title("Store")
        self.w.set_default_size(850, 640)
        self.w.set_size_request(850, 540)
        #self.w.set_resizable(False)

        #This allows Store to be natively recognised as an application associated with its .desktop file
        GLib.set_prgname('/usr/bin/feren-storium')
        
        back_img = Gtk.Image()
        back_img.set_from_icon_name("go-previous-symbolic", Gtk.IconSize.BUTTON);

        back_btn = Gtk.Button(image=back_img)
        back_btn.set_sensitive(False)
        back_btn.set_name("back-btn")
        
        status_img = Gtk.Image()
        status_img.set_from_icon_name("folder-download-symbolic", Gtk.IconSize.BUTTON);
        self.status_btn = Gtk.ToggleButton(image=status_img)
        self.status_btn.set_name("status-btn")
        self.status_btn.set_always_show_image(True)
        self.status_handle_id = self.status_btn.connect("clicked", self._status_pressed)
        
        search_img = Gtk.Image()
        search_img.set_from_icon_name("edit-find-symbolic", Gtk.IconSize.BUTTON);
        self.search_btn = Gtk.ToggleButton(image=search_img)
        self.search_btn.set_name("search-btn")
        self.search_handle_id = self.search_btn.connect("clicked", self._search_pressed)
        
        mainmenu = Gio.Menu()
        mainmenu.append("hello")
        mainmenu.append("world")
        menu_btn_img = Gtk.Image()
        menu_btn_img.set_from_icon_name("open-menu-symbolic", Gtk.IconSize.BUTTON);
        menu_btn = Gtk.MenuButton(image=menu_btn_img)
        menu_btn.set_use_popover(False)
        menu_btn.set_menu_model(mainmenu)
        
        self.gohome_btn = Gtk.ToggleButton(label=("Items Page"))
        self.gohome_btn.set_name("gohome-btn")
        self.gohome_handle_id = self.gohome_btn.connect("clicked", self._gohome_pressed)
        
        #For the splash screen
        mainwindowstack = Gtk.Stack()
        mainwindowstack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        #Use a titlebar-toolbar approach
        mainwindow = Gtk.VBox()
        mainwindow.set_spacing(0)
        maintoolbar = Gtk.Toolbar()
        maintoolbar.get_style_context().add_class(Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)
        maintoolbarcontents = Gtk.ToolItem()
        maintoolbarcontents.set_expand(True)
        maintoolbar.insert(maintoolbarcontents, 0)
        header = Gtk.Box()
        #maintoolbarcontents.set_border_width(2)
        maintoolbarcontents.add(header)
        header.set_spacing(6)
        toolbarspacer=Gtk.Alignment()
        
        #Logo
        logoimageandbox = Gtk.Box(spacing=8)
        logotypebox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        store_logoimg = Gtk.Image()
        store_logoimg.set_from_icon_name("softwarecenter", Gtk.IconSize.DND);
        
        store_logotype1 = Gtk.Label(label=("Feren Storium"))
        
        store_logotype1_box = Gtk.Box()
        store_logotype1_box.pack_start(store_logotype1, False, False, 0)
        
        logotypebox.pack_start(store_logotype1_box, False, False, 0)
        logoimageandbox.pack_start(store_logoimg, False, False, 0)
        logoimageandbox.pack_end(logotypebox, False, False, 0)
            
        header.pack_start(back_btn, False, True, 0)
        header.pack_start(logoimageandbox, False, True, 0)
        header.pack_start(toolbarspacer, True, True, 0)
        
        buttoncentering = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        buttoncenteringbtns = Gtk.Box(spacing=4)
        buttoncentering.set_center_widget(buttoncenteringbtns)
        
        buttoncenteringbtns.pack_start(self.gohome_btn, False, True, 0)
        buttoncenteringbtns.pack_start(self.status_btn, False, True, 0)
        buttoncenteringbtns.pack_start(self.search_btn, False, True, 0)
        buttoncenteringbtns.pack_start(menu_btn, False, True, 0)
        
        header.pack_end(buttoncentering, False, False, 0)
        
        mainwindowstack.add_named(mainwindow, "window")
        
        # build page container
        mv = AppMainView()
        mv.get_style_context().add_class(Gtk.STYLE_CLASS_VIEW)

        mv.back_btn = back_btn
        mv.back_signal_handler = mv.back_btn.connect("clicked", mv._back_action)
        mv.header = header
        
        mv.StoreGUI = self
        
        mv.connect("notify::visible-child", self.page_changed)
        
        #handle_id is needed to block events as otherwise the button active state changes cause button press events to occur (for whatever stupid reason) which ultimately leads to a Stack Overflow as the event code retriggers the event by triggering the button press yet again looping the cycle indefinitely

        # build scrolled window widget and add our appview stack
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        self.w.add(mainwindowstack)
        
        self.w.connect('delete-event', self.close)

        self._window = self.w
        self.mainpage = mv

        self.w.show_all()
        
        thread = Thread(target=self.build_app_post_splashscreen,
                        args=(mainwindow, maintoolbar, mv))
        thread.daemon = True
        thread.start()

    def run(self):
        Gtk.main()

    def _gohome_pressed(self, gtk_widget):
        self.mainpage._goto_page(self.mainpage.sw)

    def _search_pressed(self, gtk_widget):
        self.mainpage._goto_page(self.mainpage.sw3)

    def _status_pressed(self, gtk_widget):
        self.mainpage._goto_page(self.mainpage.sw2)

    def close(self, p1 = None, p2 = None):
        try:
            os.file.remove(pidfile)
        except:
            pass
        Gtk.main_quit(p1, p2)

    def page_changed(self, gtk_widget, value):
        #Toggle block buttons first
        self.gohome_btn.handler_block(self.gohome_handle_id)
        self.status_btn.handler_block(self.status_handle_id)
        self.search_btn.handler_block(self.search_handle_id)
        
        #Do their toggles and then unblock
        self.gohome_btn.set_active(False)
        self.status_btn.set_active(False)
        self.search_btn.set_active(False)
        
        
        if self.mainpage.get_visible_child() == self.mainpage.sw2: # Tasks
            self.status_btn.set_active(True)
        elif self.mainpage.get_visible_child() == self.mainpage.sw3: # Search
            self.search_btn.set_active(True)
        elif self.mainpage.get_visible_child() == self.mainpage.sw4: # Package Page
            pass
        else:
            self.gohome_btn.set_active(True)
            
        #Now unblock the signals
        self.gohome_btn.handler_unblock(self.gohome_handle_id)
        self.status_btn.handler_unblock(self.status_handle_id)
        self.search_btn.handler_unblock(self.search_handle_id)
            

    def _check_first_run(self):
        pass
    

class Module():
    def init(self):
        global app
        app = StoreWindow()
        app.run()