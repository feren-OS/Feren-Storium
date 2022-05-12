#!/usr/bin/python3

import gi

gi.require_version('WebKit2', '4.0')
gi.require_version('Gtk', '3.0')

import sys
import locale #Translations go brrr
import gettext #Translations go brrr
import getpass #Used for finding username

import os
import time

from gi.repository import Gtk, Gio, Gdk, GLib, Pango, GObject, GdkPixbuf
from threading import Thread
from queue import Queue, Empty


####Application icon (used for application details page, and tasks buttons)
class AppItemIcon(Gtk.Stack):

    def __init__(self, storeapi):
        Gtk.Stack.__init__(self)
        GObject.threads_init()


        self.storeapi = storeapi

        self.app_iconimg = Gtk.Image()
        self.app_iconimg_loading = Gtk.Spinner()
        self.app_iconimg_loading_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.app_iconimg_loading_box.set_center_widget(self.app_iconimg_loading)

        self.add_named(self.app_iconimg_loading_box, "load")
        self.add_named(self.app_iconimg, "icon")

        self.desired_size = 48

        self.show_all()


    def set_icon(self, iconname, iconlocal, iconuri, itemid):
        thread = Thread(target=self._set_icon,
                        args=(iconname, iconlocal, iconuri, itemid))
        thread.daemon = True
        thread.start()

    def _set_icon(self, iconname, iconlocal, iconuri, itemid):
        GLib.idle_add(self.set_visible_child, self.app_iconimg_loading_box)
        GLib.idle_add(self.app_iconimg_loading.start,)

        #TODO: Try to get from icon set first
        try:
            raise
        except: #Get it from fallback location
            try: #TODO: Try to get from icon set
                iconurilocat = self.storeapi.getFallbackIconLocation(iconlocal, iconuri, itemid)
            except:
                #TODO: Change to store-missing-icon
                #TODO: iconurilocat = "icon:store-missing-icon"
                iconurilocat = "/usr/share/icons/Inspire/256/apps/feren-store.png"

        if iconurilocat.startswith("icon:"):
            #TODO
            pass
        else:
            icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file(iconurilocat)
            icon_pixbuf = icon_pixbuf.scale_simple(self.desired_size, self.desired_size, GdkPixbuf.InterpType.BILINEAR)


        GLib.idle_add(self.app_iconimg.set_from_pixbuf, icon_pixbuf)
        GLib.idle_add(self.app_iconimg_loading.stop,)
        GLib.idle_add(self.set_visible_child, self.app_iconimg)






####Application Details Header
class AppDetailsHeader(Gtk.VBox):

    def __init__(self, guimain):
        Gtk.Box.__init__(self)
        self.guimain = guimain






        self.app_icon = AppItemIcon(guimain.storeapi)

        self.app_title = Gtk.Label()
        self.app_title.set_label("APPLICATION TITLE")

        self.app_shortdesc = Gtk.Label()
        self.app_shortdesc.set_label("APPLICATION SHORT DESCRIPTION")

        self.app_source_dropdown = Gtk.ComboBox()
        #NOTE TO SELF: NEVER put this in the dropdown refreshing code - it'll cause duplicated labels
        cell = Gtk.CellRendererText()
        self.app_source_dropdown.pack_start(cell, True)
        self.app_source_dropdown.add_attribute(cell, "text", 0)
        #self.app_source_dropdown.connect("changed", self.on_source_dropdown_changed)

        self.app_subsource_dropdown = Gtk.ComboBox()
        cell2 = Gtk.CellRendererText()
        self.app_subsource_dropdown.pack_start(cell2, True)
        self.app_subsource_dropdown.add_attribute(cell2, "text", 0)
        #self.app_subsource_dropdown.connect("changed", self.on_subsource_dropdown_changed)

        self.app_mgmt_progress = Gtk.ProgressBar()

        buttonsbox = Gtk.Box()

        self.installapp_btn = Gtk.Button(label=("Install"))
        self.installappnosource_btn = Gtk.Button(label=("Install..."))
        self.updateapp_btn = Gtk.Button(label=("Update"))
        self.removeapp_btn = Gtk.Button(label=("Remove"))
        self.cancelapp_btn = Gtk.Button(label=("Cancel"))

        buttonsbox.pack_start(self.installapp_btn, False, False, 4)
        buttonsbox.pack_start(self.installappnosource_btn, False, False, 4)
        buttonsbox.pack_start(self.updateapp_btn, False, False, 4)
        buttonsbox.pack_start(self.removeapp_btn, False, False, 4)
        buttonsbox.pack_start(self.cancelapp_btn, False, False, 4)

        self.pack_start(self.app_icon, False, False, 4)
        self.pack_start(self.app_title, True, False, 4)
        self.pack_start(self.app_shortdesc, True, False, 4)
        self.pack_start(self.app_source_dropdown, False, False, 4)
        self.pack_start(self.app_subsource_dropdown, False, False, 4)
        self.pack_start(self.app_mgmt_progress, True, False, 4)
        self.pack_start(buttonsbox, True, False, 4)


        #self.installapp_btn.connect("clicked", self.installapp_pressed)
        #self.installappnosource_btn.connect("clicked", self.installappnosource_pressed)
        #self.updateapp_btn.connect("clicked", self.updateapp_pressed)
        #self.removeapp_btn.connect("clicked", self.removeapp_pressed)
        #self.cancelapp_btn.connect("clicked", self.cancelapp_pressed)

        #For sources
        self.source_ids = []
        self.subsource_ids = []

        pass




####AppView
class PageArea(Gtk.Stack):

    def __init__(self, guimain):
        Gtk.Stack.__init__(self)
        self.guimain = guimain


        #Main Page
        self.mainpage = Gtk.ScrolledWindow()
        self.mainpage.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        mainpagesub = Gtk.VBox(spacing=8)

        #Main Page: Application Listings
        appslabel_box = Gtk.Box()
        appslabel = Gtk.Label(label="Application Listings:")
        appslabel_box.pack_start(appslabel, False, False, 0)

        self.appsitems = Gtk.FlowBox()
        self.appsitems.set_min_children_per_line(3)
        self.appsitems.set_margin_top(4)
        self.appsitems.set_margin_bottom(4)
        self.appsitems.set_row_spacing(4)
        self.appsitems.set_homogeneous(True)
        self.appsitems.set_valign(Gtk.Align.START)


        #Main Page: Games Listings
        gameslabel_box = Gtk.Box()
        gameslabel = Gtk.Label(label="Games Listings:")
        gameslabel_box.pack_start(gameslabel, False, False, 0)

        self.gamesitems = Gtk.FlowBox()
        self.gamesitems.set_min_children_per_line(3)
        self.gamesitems.set_margin_top(4)
        self.gamesitems.set_margin_bottom(4)
        self.gamesitems.set_row_spacing(4)
        self.gamesitems.set_homogeneous(True)
        self.gamesitems.set_valign(Gtk.Align.START)


        #Main Page: Themes Listings
        themeslabel_box = Gtk.Box()
        themeslabel = Gtk.Label(label="Themes Listings:")
        themeslabel_box.pack_start(themeslabel, False, False, 0)

        self.themesitems = Gtk.FlowBox()
        self.themesitems.set_min_children_per_line(3)
        self.themesitems.set_margin_top(4)
        self.themesitems.set_margin_bottom(4)
        self.themesitems.set_row_spacing(4)
        self.themesitems.set_homogeneous(True)
        self.themesitems.set_valign(Gtk.Align.START)


        #Main Page: Websites Listings
        websiteslabel_box = Gtk.Box()
        websiteslabel = Gtk.Label(label="Websites Listings:")
        websiteslabel_box.pack_start(websiteslabel, False, False, 0)

        self.websitesitems = Gtk.FlowBox()
        self.websitesitems.set_min_children_per_line(3)
        self.websitesitems.set_margin_top(4)
        self.websitesitems.set_margin_bottom(4)
        self.websitesitems.set_row_spacing(4)
        self.websitesitems.set_homogeneous(True)
        self.websitesitems.set_valign(Gtk.Align.START)


        #Assemble the main page
        mainpagesub.pack_start(appslabel_box, False, True, 0)
        mainpagesub.pack_start(self.appsitems, False, True, 0)
        mainpagesub.pack_start(gameslabel_box, False, True, 0)
        mainpagesub.pack_start(self.gamesitems, False, True, 0)
        mainpagesub.pack_start(themeslabel_box, False, True, 0)
        mainpagesub.pack_start(self.themesitems, False, True, 0)
        mainpagesub.pack_start(websiteslabel_box, False, True, 0)
        mainpagesub.pack_start(self.websitesitems, False, True, 0)

        mainpagesub.set_margin_bottom(8)
        mainpagesub.set_margin_top(8)
        mainpagesub.set_margin_left(10)
        mainpagesub.set_margin_right(10)

        self.mainpage.add(mainpagesub)

        #Add the main page to the page control
        self.add_named(self.mainpage, "home")


        #Tasks Page
        self.taskspage = Gtk.ScrolledWindow()
        self.taskspage.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        taskspagesub = Gtk.VBox(spacing=8)

        #Tasks Page: Tasks in progress
        taskslabel_box = Gtk.Box()
        taskslabel = Gtk.Label(label="Currently working on these tasks:")
        taskslabel_box.pack_start(taskslabel, False, False, 0)

        self.tasksitemscontainer = Gtk.Box()
        self.tasksitemscontainer.set_margin_top(4)
        self.tasksitemscontainer.set_margin_bottom(4)
        self.tasksitemscontainer.set_valign(Gtk.Align.START)
        self.tasksitems = None


        #Tasks Page: Updates available
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


        #Tasks Page: Installed items
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


        #Assemble the tasks page
        taskspagesub.pack_start(taskslabel_box, False, True, 0)
        taskspagesub.pack_start(self.tasksitemscontainer, False, True, 0)
        taskspagesub.pack_start(updateslabel_box, False, True, 0)
        taskspagesub.pack_start(self.updatesitems, False, True, 0)
        taskspagesub.pack_start(installedlabel_box, False, True, 0)
        taskspagesub.pack_start(self.installeditems, False, True, 0)

        taskspagesub.set_margin_bottom(8)
        taskspagesub.set_margin_top(8)
        taskspagesub.set_margin_left(10)
        taskspagesub.set_margin_right(10)

        self.taskspage.add(taskspagesub)

        #Add the tasks page to the main control
        self.add_named(self.taskspage, "tasks")



        #Search Page
        self.searchpage = Gtk.ScrolledWindow()
        self.searchpage.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        searchpagesub = Gtk.VBox(spacing=8)

        #Search Page: Main Searchbar
        self.searchbar = Gtk.Entry()
        #self.searchbar.connect("changed", self.searchbar_search)


        #Search Page: Search Results
        self.searchresultscontainer = Gtk.Box()
        self.searchresultscontainer.set_margin_top(4)
        self.searchresultscontainer.set_margin_bottom(4)
        self.searchresults = None


        #Assemble the search page
        searchpagesub.pack_start(self.searchbar, False, True, 4)
        searchpagesub.pack_start(self.searchresultscontainer, False, True, 4)

        searchpagesub.set_margin_bottom(8)
        searchpagesub.set_margin_top(8)
        searchpagesub.set_margin_left(10)
        searchpagesub.set_margin_right(10)

        self.searchpage.add(searchpagesub)


        #Add the search page to the main control
        self.add_named(self.searchpage, "search")


        #Item's page
        self.itempage = Gtk.ScrolledWindow()
        self.itempage.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.itempagestack = Gtk.Stack()
        self.itempagesub = Gtk.VBox(spacing=8)
        self.itempageloading = Gtk.Label(label=_("Loading..."))


        #Item's Page: Information container
        self.itempagecontents = Gtk.FlowBox()
        self.itempagecontents.set_min_children_per_line(1)
        self.itempagecontents.set_max_children_per_line(1)

        self.itempagesub.pack_start(self.itempagecontents, True, True, 8)

        #Images list; NOTE: Boxes are used to left-align the labels
        images_box = Gtk.Box()
        self.pkgpage_images = Gtk.Label(label="Images: ")
        images_box.pack_start(self.pkgpage_images, False, False, 0)

        self.itempagecontents.insert(images_box, -1)

        #Description
        description_box = Gtk.Box()
        self.pkgpage_description = Gtk.Label(label="Description: ")
        description_box.pack_start(self.pkgpage_description, False, False, 0)

        self.itempagecontents.insert(description_box, -1)

        #Category
        category_box = Gtk.Box()
        self.pkgpage_category = Gtk.Label(label="Category: ")
        category_box.pack_start(self.pkgpage_category, False, False, 0)

        self.itempagecontents.insert(category_box, -1)

        #Website
        website_box = Gtk.Box()
        self.pkgpage_website = Gtk.Label(label="Website: ")
        website_box.pack_start(self.pkgpage_website, False, False, 0)

        self.itempagecontents.insert(website_box, -1)

        #Author
        author_box = Gtk.Box()
        self.pkgpage_author = Gtk.Label(label="Author: ")
        author_box.pack_start(self.pkgpage_author, False, False, 0)

        self.itempagecontents.insert(author_box, -1)

        #URL for Donations
        donateurl_box = Gtk.Box()
        self.pkgpage_donateurl = Gtk.Label(label="Donate URL: ")
        donateurl_box.pack_start(self.pkgpage_donateurl, False, False, 0)

        self.itempagecontents.insert(donateurl_box, -1)

        #URL for Bugs
        bugsurl_box = Gtk.Box()
        self.pkgpage_bugsurl = Gtk.Label(label="Bugs URL: ")
        bugsurl_box.pack_start(self.pkgpage_bugsurl, False, False, 0)

        self.itempagecontents.insert(bugsurl_box, -1)

        #URL for Terms of Service
        tosurl_box = Gtk.Box()
        self.pkgpage_tosurl = Gtk.Label(label="TOS URL: ")
        tosurl_box.pack_start(self.pkgpage_tosurl, False, False, 0)

        self.itempagecontents.insert(tosurl_box, -1)

        #URL for Privacy Policy
        privpolurl_box = Gtk.Box()
        self.pkgpage_privpolurl = Gtk.Label(label="Privacy Policy URL: ")
        privpolurl_box.pack_start(self.pkgpage_privpolurl, False, False, 0)

        self.itempagecontents.insert(privpolurl_box, -1)

        # build another scrolled window widget and add our package view

        self.itempagesub.set_margin_bottom(8)
        self.itempagesub.set_margin_top(8)
        self.itempagesub.set_margin_left(10)
        self.itempagesub.set_margin_right(10)

        self.itempage.add(self.itempagestack)
        self.itempagestack.add_named(self.itempagesub, "page")
        self.itempagestack.add_named(self.itempageloading, "loading")


        self.add_named(self.itempage, "itempage")


    #Main page
    def populate_mainpage(self):
        thread = Thread(target=self._populate_mainpage,
                            args=())
        thread.start()

    def _populate_mainpage(self):
        #TODO: Split into sections
        data = self.guimain.storeapi.getItemIDs(["all"])
        for category in data:
            for pkgname in data[category]:
                btn = Gtk.Button(label=(pkgname))
                btn.connect("clicked", self.btn_goto_itempage, pkgname)
                if category.startswith("ice-"):
                    GLib.idle_add(self.websitesitems.insert, btn, -1)
                elif category.startswith("themes-"):
                    GLib.idle_add(self.themesitems.insert, btn, -1)
                elif category.startswith("games-"):
                    GLib.idle_add(self.themesitems.insert, btn, -1)
                else:
                    GLib.idle_add(self.appsitems.insert, btn, -1)
        GLib.idle_add(self.show_all)


    def btn_goto_itempage(self, btn, itemid, sourceid=""):
        self.gotoID(itemid, sourceid)

    def gotoID(self, itemid, sourceid=""): #API call
        print(itemid, sourceid)

        thread = Thread(target=self._gotoID,
                            args=(itemid, sourceid))
        thread.start()

    def _gotoID(self, itemid, sourceid=""):
        #Go to Item Page, with the loading screen for now
        GLib.idle_add(self.itempagestack.set_visible_child, self.itempageloading)
        GLib.idle_add(self.set_visible_child, self.itempage)
        self.guimain.current_itemid = itemid

        #Get available sources
        availablesources = self.guimain.storeapi.getAvailableSources(itemid)
        print(availablesources)

        #Feed the information to the header to get it loading
        #TODO: self.guimain.detailsheader.load_data(itemid, availablesources, sourceid)

        #TODO: Move the below code to call made by Header from changing the source (and make said call change to loading again every time)
        #Get information from default source
        pkginfo = None #TODO

        #Switch from loading screen to page now the loading's done
        GLib.idle_add(self.itempagestack.set_visible_child, self.itempagesub)
        pass #TODO




####Store Window
class module(object):
    def __init__(self, storeapi):
        self.storeapi = storeapi

        #To determine whether or not to run refresh tasks and so on
        self.current_itemid = ""
        self.current_sourceid = ""
        self.current_subsourceid = ""
        #TODO: Consider divulging this into module-source-subsource IDs?


    def _gohome_pressed(self, gtk_widget):
        self.pagearea.set_visible_child(self.pagearea.mainpage)

    def _search_pressed(self, gtk_widget):
        self.pagearea.set_visible_child(self.pagearea.searchpage)

    def _status_pressed(self, gtk_widget):
        self.pagearea.set_visible_child(self.pagearea.taskspage)

    def pagearea_pagechanged(self, gtk_widget, value):
        #Toggle block buttons first
        self.gohome_btn.handler_block(self.gohome_handle_id)
        self.status_btn.handler_block(self.status_handle_id)
        self.search_btn.handler_block(self.search_handle_id)

        #Empty button presseds
        self.gohome_btn.set_active(False)
        self.status_btn.set_active(False)
        self.search_btn.set_active(False)

        #Assign the right button pressed
        if self.pagearea.get_visible_child() == self.pagearea.taskspage:
            self.status_btn.set_active(True)
        elif self.pagearea.get_visible_child() == self.pagearea.searchpage:
            self.search_btn.set_active(True)
            self.pagearea.searchbar.grab_focus()
        elif self.pagearea.get_visible_child() == self.pagearea.itempage:
            pass
        elif self.pagearea.get_visible_child() == self.pagearea.mainpage:
            self.gohome_btn.set_active(True)

        #Now unblock the signals
        self.gohome_btn.handler_unblock(self.gohome_handle_id)
        self.status_btn.handler_unblock(self.status_handle_id)
        self.search_btn.handler_unblock(self.search_handle_id)

        #Hide details header outside of Item Page
        if self.pagearea.get_visible_child() != self.pagearea.itempage:
            GLib.idle_add(self.detailsheader.set_visible, False)


    def close(self, p1 = None, p2 = None):
        try:
            os.file.remove(pidfile)
        except:
            pass
        Gtk.main_quit(p1, p2)


    def prepareGUI(self):
        GObject.threads_init()

        #Program identification for the Desktop Environment
        GLib.set_prgname('/usr/bin/feren-storium')


        # Main window
        self.storewnd = Gtk.Window()
        self.storewnd.set_position(Gtk.WindowPosition.CENTER)
        self.storewnd.set_title("Storium Demo - GUI Module")
        self.storewnd.set_default_size(850, 640)
        self.storewnd.set_size_request(850, 540)
        self.windowcontents = Gtk.VBox()
        self.windowcontents.set_spacing(0)


        #Top toolbar buttons
        status_img = Gtk.Image()
        status_img.set_from_icon_name("folder-download-symbolic", Gtk.IconSize.BUTTON);
        self.status_btn = Gtk.ToggleButton(image=status_img)
        self.status_btn.set_name("status-btn")
        self.status_btn.set_always_show_image(True)
        self.status_handle_id = self.status_btn.connect("clicked", self._status_pressed)
        self.status_btn.set_tooltip_text("See tasks and updates...")

        search_img = Gtk.Image()
        search_img.set_from_icon_name("edit-find-symbolic", Gtk.IconSize.BUTTON);
        self.search_btn = Gtk.ToggleButton(image=search_img)
        self.search_btn.set_name("search-btn")
        self.search_handle_id = self.search_btn.connect("clicked", self._search_pressed)
        self.search_btn.set_tooltip_text("Search for applications...")

        mainmenu = Gio.Menu()
        mainmenu.append("Settings... (TBD)")
        mainmenu.append("Export Application Playlist... (TBD)")
        mainmenu.append("Import Application Playlist... (TBD)")
        mainmenu.append("About Feren Storium (TBD)")
        menu_btn_img = Gtk.Image()
        menu_btn_img.set_from_icon_name("open-menu-symbolic", Gtk.IconSize.BUTTON);
        menu_btn = Gtk.MenuButton(image=menu_btn_img)
        menu_btn.set_use_popover(False)
        menu_btn.set_menu_model(mainmenu)
        menu_btn.set_tooltip_text("More options...")

        self.gohome_btn = Gtk.ToggleButton(label=("Items Page"))
        self.gohome_btn.set_name("gohome-btn")
        self.gohome_handle_id = self.gohome_btn.connect("clicked", self._gohome_pressed)


        #Top toolbar
        self.maintoolbar = Gtk.Box()
        self.maintoolbar.get_style_context().add_class(Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)
        toolbarspacer=Gtk.Alignment()
        self.maintoolbar.pack_start(toolbarspacer, True, True, 0)
        self.maintoolbar.pack_end(menu_btn, False, True, 0)
        self.maintoolbar.pack_end(self.search_btn, False, True, 0)
        self.maintoolbar.pack_end(self.status_btn, False, True, 0)
        self.maintoolbar.pack_end(self.gohome_btn, False, True, 0)


        #Assemble window so far
        self.storewnd.add(self.windowcontents)
        self.storewnd.connect('delete-event', self.close)
        self.storewnd.show_all()


    def GUILoadingFinished(self):
        thread = Thread(target=self._GUILoadingFinished,
                        args=())
        thread.daemon = True
        thread.start()

    def _GUILoadingFinished(self):
        GLib.idle_add(self.__GUILoadingFinished)

    def __GUILoadingFinished(self):
        #Details header
        self.detailsheader = AppDetailsHeader(self)

        #Pages area
        self.pagearea = PageArea(self)
        self.pagearea.get_style_context().add_class(Gtk.STYLE_CLASS_VIEW)
        self.pagearea.connect("notify::visible-child", self.pagearea_pagechanged)

        #Assemble everything in the window
        self.windowcontents.pack_start(self.maintoolbar, False, True, 0)
        self.windowcontents.pack_start(self.detailsheader, False, True, 0)
        self.windowcontents.pack_end(self.pagearea, True, True, 0)
        GLib.idle_add(self.storewnd.show_all)

        self.pagearea.populate_mainpage()


    def showGUIHold(self):
        Gtk.main()

    def refresh_memory(self):
        pass





    # API CALLS FOR CLASSES
    def gotoID(self, itemid):
        self.pagearea.gotoID(itemid)
