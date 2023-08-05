#!/usr/bin/python3

import gi

gi.require_version('Gtk', '3.0')

import sys
import locale #Translations go brrr
import gettext #Translations go brrr
import getpass #Used for finding username
from functools import partial

import os
import time

from gi.repository import Gtk, Gio, Gdk, GLib, Pango, GObject, GdkPixbuf
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from threading import Thread, Event
from queue import Queue, Empty

#Settings storage for the GUI
class settings():
    def __init__(self):
        pass #This GUI uses gsettings, TODO: check for changes and reload on the fly?

    def getPreferSystemWideInstalls(self):
        #Returns True if system-wide installs are preferred over user-wide installs
        #TODO
        return True

    def getDebugOutput(self):
        #Returns True if debug output is desired
        #TODO
        return True




####Changes confirming dialog
class changesBonusesDialog(Gtk.Window):
    def __init__(self, parent):
        #TODO: Check if api is even needed - likely will for icons if nothing else
        Gtk.Window.__init__(self)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_title("Preliminary confirmation/bonus-select dialog")

    def prepare(self, api, taskbody, idsadded, idsupdated, idsremoved, bonusavailability):
        self.wndcontents = Gtk.VBox()

        self.bonuses = []
        self.response = False

        headerlabel = Gtk.Label(label=_("Personalise your %s experience") % taskbody.itemid)
        self.wndcontents.pack_start(headerlabel, False, False, 0)
        subheaderlabel = Gtk.Label(label=_("Select the extra items that you would like to add to %s:") % taskbody.itemid)
        self.wndcontents.pack_start(subheaderlabel, False, False, 0)

        installsheader = Gtk.Label(label=_("The following will also be installed:"))
        self.wndcontents.pack_start(installsheader, False, False, 0)
        for i in idsadded:
            addition = Gtk.Label(label=i)
            self.wndcontents.pack_start(addition, False, False, 0)

        updatesheader = Gtk.Label(label=_("The following will also be updated:"))
        self.wndcontents.pack_start(updatesheader, False, False, 0)
        for i in idsupdated:
            update = Gtk.Label(label=i)
            self.wndcontents.pack_start(update, False, False, 0)

        removalsheader = Gtk.Label(label=_("The following will also be removed:"))
        self.wndcontents.pack_start(removalsheader, False, False, 0)
        for i in idsremoved:
            removal = Gtk.Label(label=i)
            self.wndcontents.pack_start(removal, False, False, 0)

        bonusesheader = Gtk.Label(label=_("Choose extra items to add to this application:"))
        self.wndcontents.pack_start(bonusesheader, False, False, 0)

        for i in bonusavailability:
            bonusoption = Gtk.CheckButton(label=i)
            bonusoption.connect('toggled', partial(self.set_bonus_selected, i))
            self.wndcontents.pack_start(bonusoption, False, False, 0)

        okbutton = Gtk.Button(label="Proceed")
        okbutton.connect('clicked', self.ok_clicked)
        cancelbutton = Gtk.Button(label="Cancel")
        cancelbutton.connect('clicked', self.cancel_clicked)
        self.wndcontents.pack_start(okbutton, False, False, 0)
        self.wndcontents.pack_start(cancelbutton, False, False, 0)

        self.add(self.wndcontents)
        self.connect('delete-event', self.cancel_clicked)

        self.show_all()

        if len(idsadded) > 0 or len(idsupdated) > 0 or len(idsremoved) > 0:
            headerlabel.set_text(_("The following changes will be made"))
            if taskbody.operation == 0:
                subheaderlabel.set_text(_("Installing this software will result in the following other changes being made to this computer, would you like to continue?"))
            elif taskbody.operation == 1:
                subheaderlabel.set_text(_("Removing this software will result in the following other changes being made to this computer, would you like to continue?"))
            elif taskbody.operation == 2:
                subheaderlabel.set_text(_("Updating this software will result in the following other changes being made to this computer, would you like to continue?"))
            bonusesheader.set_visible(len(bonusavailability) > 0)
        else:
            bonusesheader.set_visible(False) #No changes means this is only for bonus selection
        installsheader.set_visible(len(idsadded) > 0)
        updatesheader.set_visible(len(idsupdated) > 0)
        removalsheader.set_visible(len(idsremoved) > 0)

    def set_bonus_selected(self, bonusid, widget, data=None):
        if widget.get_active() == True:
            self.bonuses.append(bonusid)
            print("Added " + bonusid)
        else:
            self.bonuses.remove(bonusid)
            print("Removed " + bonusid)

    def exit_dialog(self):
        GLib.idle_add(self.hide,)
        GLib.idle_add(self.wndcontents.destroy,)

    def cancel_clicked(self, button, data=None):
        self.responded.set() #Ends hold

    def ok_clicked(self, button, data=None):
        self.response = True
        self.responded.set()

    def run(self):
        self.responded = Event() #Because GTK is a big dumdum we can't just have nice things so have to fall back to using threading events to hold code until the user's response happens
        self.responded.wait()
        self.exit_dialog()
        return self.response, self.bonuses


############################################
# Errors window
############################################
class errorWindow(Gtk.Window):
    def __init__(self, parent):
        Gtk.Window.__init__(self)

        #TODO: Move everything window-related into here


############################################
# Settings window
############################################
class configWindow(Gtk.Window):
    def __init__(self, parent):
        Gtk.Window.__init__(self)

        #TODO: Move everything window-related into here











####Application icon (used for application details page, and tasks buttons)
class AppItemIcon(Gtk.Stack):

    def __init__(self, api):
        Gtk.Stack.__init__(self)
        GObject.threads_init()


        self.api = api

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

        iconlocat = None
        #TODO: Try to get from icon set first
        try:
            raise
        except: #Get it from fallback location
            try: #TODO: Try to get from icon set
                iconlocat = self.api.getFallbackIconLocation(iconlocal, iconuri, itemid)
            except:
                pass

        if iconlocat == None:
            #TODO: Change to store-missing-icon
            #TODO: iconurilocat = "icon:store-missing-icon"
            iconlocat = "/usr/share/icons/Inspire/256/apps/feren-store.png"

        if iconlocat.startswith("icon:"):
            #TODO
            pass
        else:
            icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file(iconlocat)
            icon_pixbuf = icon_pixbuf.scale_simple(self.desired_size, self.desired_size, GdkPixbuf.InterpType.BILINEAR)


        GLib.idle_add(self.app_iconimg.set_from_pixbuf, icon_pixbuf)
        GLib.idle_add(self.app_iconimg_loading.stop,)
        GLib.idle_add(self.set_visible_child, self.app_iconimg)






####Application Details Header
class AppDetailsHeader(Gtk.VBox):

    def __init__(self, guimain):
        Gtk.Box.__init__(self)
        self.guimain = guimain




        self.app_icon = AppItemIcon(guimain.api)

        self.app_title = Gtk.Label()
        self.app_title.set_label("APPLICATION TITLE")

        self.app_shortdesc = Gtk.Label()
        self.app_shortdesc.set_label("APPLICATION SHORT DESCRIPTION")

        self.app_source_dropdown = Gtk.ComboBox()
        #NOTE TO SELF: NEVER put this in the dropdown refreshing code - it'll cause duplicated labels
        cell = Gtk.CellRendererText()
        self.app_source_dropdown.pack_start(cell, True)
        self.app_source_dropdown.add_attribute(cell, "text", 0)
        self.app_source_dropdown.connect("changed", self.on_source_dropdown_changed)

        self.app_subsource_dropdown = Gtk.ComboBox()
        cell2 = Gtk.CellRendererText()
        self.app_subsource_dropdown.pack_start(cell2, True)
        self.app_subsource_dropdown.add_attribute(cell2, "text", 0)
        self.app_subsource_dropdown.connect("changed", self.on_subsource_dropdown_changed)

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


        self.installapp_btn.connect("clicked", self.installapp_pressed)
        #self.installappnosource_btn.connect("clicked", self.installappnosource_pressed)
        self.updateapp_btn.connect("clicked", self.updateapp_pressed)
        self.removeapp_btn.connect("clicked", self.removeapp_pressed)
        #self.cancelapp_btn.connect("clicked", self.cancelapp_pressed)

        #For sources
        self.current_sourcelist = {}
        self.current_subsources = [] #Makes accessing them way easier

        pass


    def load_sources(self, availablesources, itemid, sourceid=""):
        if itemid != self.guimain.current_itemid:
            return

        self.current_sourcelist = {} #Reset

        iface_list_store = Gtk.ListStore(GObject.TYPE_STRING)

        for item in availablesources["recommended"]:
            iface_list_store.append([availablesources["recommended"][item]['name']])
            self.current_sourcelist[item] = availablesources["recommended"][item]
        #TODO: Stop here on Simple Mode
        for item in availablesources["normal"]:
            iface_list_store.append([availablesources["normal"][item]['name']])
            self.current_sourcelist[item] = availablesources["normal"][item]
        for item in availablesources["nonrecommended"]:
            iface_list_store.append([availablesources["nonrecommended"][item]['name']])
            self.current_sourcelist[item] = availablesources["nonrecommended"][item]

        GLib.idle_add(self.app_source_dropdown.set_model, iface_list_store)
        GLib.idle_add(self.app_source_dropdown.set_active, 0)
        if len(iface_list_store) == 0:
            #If there are no sources, show the unavailable screen and stop
            GLib.idle_add(self.guimain.pagearea.itempagestack.set_visible_child, self.guimain.pagearea.itempageunavailable)
            GLib.idle_add(self.set_visible, False)
            return
        elif len(iface_list_store) <= 1:
            GLib.idle_add(self.app_source_dropdown.set_sensitive, False)
        else:
            GLib.idle_add(self.app_source_dropdown.set_sensitive, True)


        thread = None
        #If sourceid isn't "", switch source over automatically
        if sourceid != "":
            #Find the appropriate source first, and then set it
            n = 0
            for item in self.current_sourcelist:
                if item == sourceid:
                    GLib.idle_add(self.app_source_dropdown.set_active, n)
                    break
                n += 1


    def on_source_dropdown_changed(self, combobox):
        if combobox.get_active() == -1:
            return

        self.guimain.current_sourceid = list(self.current_sourcelist.keys())[combobox.get_active()] #Convert to list of keys, so we can use the combobox.get_active() index on it to get the currently selected source's ID

        thread = Thread(target=self.guimain.pagearea._sourceChange,
                            args=( self.guimain.current_itemid, self.current_sourcelist[self.guimain.current_sourceid] ) )
        thread.start()

        print("TEMPDEBUG SOURCE_DROPDOWN_CHANGED - source changed to " + self.guimain.current_sourceid)

        thread = Thread(target=self.load_sourcedata,
                            args=(self.guimain.current_sourceid, self.guimain.current_itemid) )
        thread.start()


    def load_sourcedata(self, sourceid, itemid):
        if itemid != self.guimain.current_itemid:
            return

        GLib.idle_add(self.app_subsource_dropdown.set_visible, False) #Temporarily hide the subsource selector while loading
        self.load_subsources(sourceid, itemid)

        if itemid != self.guimain.current_itemid:
            return

        self.load_item_status(sourceid, itemid)

        if itemid != self.guimain.current_itemid:
            return


    def load_subsources(self, sourceid, itemid):
        if itemid != self.guimain.current_itemid:
            return

        self.current_subsources = [] #Reset

        iface_list_store = Gtk.ListStore(GObject.TYPE_STRING)

        if "subsources" in self.current_sourcelist[sourceid]:
            #Add subsources if there are actually subsources
            for item in self.current_sourcelist[sourceid]["subsources"]:
                iface_list_store.append([self.current_sourcelist[sourceid]["subsources"][item]["name"]])
                self.current_subsources.append(item) #Add the subsource IDs to a list so we
                    #have an easier time accessing them than the chaotic code that'd
                    #otherwise be needed to access them

        GLib.idle_add(self.app_subsource_dropdown.set_model, iface_list_store)
        GLib.idle_add(self.app_subsource_dropdown.set_active, 0)
        if len(iface_list_store) <= 1:
            GLib.idle_add(self.app_subsource_dropdown.set_sensitive, False)
        else:
            GLib.idle_add(self.app_subsource_dropdown.set_sensitive, True)


    def on_subsource_dropdown_changed(self, combobox):
        if combobox.get_active() == -1:
            self.guimain.current_subsourceid = ""
        else:
            self.guimain.current_subsourceid = self.current_subsources[combobox.get_active()] #This code would be chaos if it wasn't for self.current_subsources

        print("TEMPDEBUG SUBSOURCE_DROPDOWN_CHANGED - subsource changed to " + self.guimain.current_subsourceid)


    def load_item_status(self, sourceid, itemid):
        if itemid != self.guimain.current_itemid:
            return

        #Disable all buttons, and hide subsource selection
        GLib.idle_add(self.installapp_btn.set_sensitive, False)
        GLib.idle_add(self.installappnosource_btn.set_sensitive, False)
        GLib.idle_add(self.updateapp_btn.set_sensitive, False)
        GLib.idle_add(self.removeapp_btn.set_sensitive, False)
        GLib.idle_add(self.cancelapp_btn.set_sensitive, False)
        GLib.idle_add(self.app_subsource_dropdown.set_visible, False)

        result, subsource = self.guimain.api.getAppStatus(self.guimain.current_itemid, self.guimain.current_sourceid)

        if subsource != None: #If a subsource was provided, switch to it
            n = 0
            for item in self.current_subsources:
                if item == subsource:
                    GLib.idle_add(self.app_subsource_dropdown.set_active, n)
                    break
                n += 1

        if result >= 20 and result <= 22: #Currently being worked on
            pass #TODO
        elif result >= 10 and result <= 12: #Waiting in tasks queue
            pass #TODO
        else:
            if result == 0: #Not installed
                GLib.idle_add(self.installapp_btn.set_sensitive, True)
                GLib.idle_add(self.app_subsource_dropdown.set_visible, True)
            elif result == 1: #Installed
                GLib.idle_add(self.removeapp_btn.set_sensitive, True)
            elif result == 2: #Updatable
                GLib.idle_add(self.updateapp_btn.set_sensitive, True)
            elif result == 3: #Available in disabled source
                GLib.idle_add(self.installappnosource_btn.set_sensitive, True)
                GLib.idle_add(self.app_subsource_dropdown.set_visible, True)

        print("TEMPDEBUG LOAD_ITEM_STATUS - result is {0}, subsource is {1}".format(str(result), subsource))


    def load_data(self, itemid, pkginfo):
        if self.guimain.current_itemid != itemid:
            return

        thread = Thread(target=self._load_data,
                            args=(itemid, pkginfo))
        thread.start()

    def _load_data(self, itemid, pkginfo):
        #Update icons and information according to the pkginfo
        self.app_icon.set_icon(pkginfo["iconname"], pkginfo["iconlocal"], pkginfo["iconuri"], itemid)
        self.app_title.set_label(pkginfo["realname"])
        self.app_shortdesc.set_label(pkginfo["shortdescription"])

        if self.guimain.current_itemid == itemid:
            GLib.idle_add(self.set_visible, True)



    def installapp_pressed(self, btn):
        self.guimain.api.installApp(self.guimain.current_itemid, self.guimain.current_sourceid, self.guimain.current_subsourceid)

    def updateapp_pressed(self, btn):
        self.guimain.api.updateApp(self.guimain.current_itemid, self.guimain.current_sourceid, self.guimain.current_subsourceid)

    def removeapp_pressed(self, btn):
        self.guimain.api.removeApp(self.guimain.current_itemid, self.guimain.current_sourceid, self.guimain.current_subsourceid)




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
        self.itempageunavailable = Gtk.Label(label=_("This item is not available."))


        #Item's Page: Information container
        self.itempagecontents = Gtk.FlowBox()
        self.itempagecontents.set_min_children_per_line(1)
        self.itempagecontents.set_max_children_per_line(1)

        self.itempagesub.pack_start(self.itempagecontents, True, True, 8)

        # build another scrolled window widget and add our package view

        self.itempagesub.set_margin_bottom(8)
        self.itempagesub.set_margin_top(8)
        self.itempagesub.set_margin_left(10)
        self.itempagesub.set_margin_right(10)

        self.itempage.add(self.itempagestack)
        self.itempagestack.add_named(self.itempagesub, "page")
        self.itempagestack.add_named(self.itempageloading, "loading")
        self.itempagestack.add_named(self.itempageunavailable, "unavailable")


        self.add_named(self.itempage, "itempage")


    #Main page
    def populate_mainpage(self):
        thread = Thread(target=self._populate_mainpage,
                            args=())
        thread.start()

    def _populate_mainpage(self):
        #TODO: Split into sections
        data = self.guimain.api.getItemIDs(["all"])
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
        thread = Thread(target=self._gotoID,
                            args=(itemid, sourceid))
        thread.start()

    def _gotoID(self, itemid, sourceid=""):
        #Go to Item Page, with the loading screen for now
        GLib.idle_add(self.itempagestack.set_visible_child, self.itempageloading)
        GLib.idle_add(self.set_visible_child, self.itempage)
        self.guimain.current_itemid = itemid

        #Get available sources
        availablesources = self.guimain.api.getAvailableSources(itemid)

        #Feed the information to the header to get it loading
        self.guimain.detailsheader.load_sources(availablesources, itemid, sourceid)


    #### ITEM INFORMATION ####
    def sourceChange(self, itemid, sourceid):
        thread = Thread(target=self._sourceChange,
                            args=(itemid, sourceid))
        thread.start()

    def _sourceChange(self, itemid, sourceid):
        #Go to loading screen
        GLib.idle_add(self.itempagestack.set_visible_child, self.itempageloading)

        #Get information from default source
        pkginfo = self.guimain.api.getItemInformation(itemid, sourceid["id"].split(":")[0], sourceid["id"].split(":")[1], "") #TODO: subsourceid, and make this trigger when subsource is changed instead, with this call here only serving to change source and subsource and then call subsource changed

        #Pass information to header to load into the information there
        self.guimain.detailsheader._load_data(itemid, pkginfo)

        self._loadItemInformation(pkginfo, itemid)

        #Switch from loading screen to page now the loading's done
        GLib.idle_add(self.itempagestack.set_visible_child, self.itempagesub)
        pass #TODO


    def loadItemInformation(self, pkginfo, itemid):
        thread = Thread(target=self._loadItemInformation,
                            args=(pkginfo, itemid))
        thread.start()

    def _loadItemInformation(self, pkginfo, itemid):
        itemstoadd = []

        #Now provide the information: NOTE Boxes are used to left-align the labels
        #Warnings
        #TODO: Retrieve warnings outta pkginfo


        #Images
        images_box = Gtk.Box()
        self.pkgpage_images = Gtk.Label(label=_("Images: %s") % pkginfo["images"])
        GLib.idle_add(images_box.pack_start, self.pkgpage_images, False, False, 0)
        itemstoadd.append(images_box)

        #Description
        description_box = Gtk.Box()
        self.pkgpage_description = Gtk.Label(label=_("Description: %s") % pkginfo["description"])
        GLib.idle_add(description_box.pack_start, self.pkgpage_description, False, False, 0)
        itemstoadd.append(description_box)

        #Category
        category_box = Gtk.Box()
        self.pkgpage_category = Gtk.Label(label=_("Category: %s") % pkginfo["category"])
        GLib.idle_add(category_box.pack_start, self.pkgpage_category, False, False, 0)

        itemstoadd.append(category_box)

        #Website
        website_box = Gtk.Box()
        self.pkgpage_website = Gtk.Label(label=_("Website: %s") % pkginfo["website"])
        GLib.idle_add(website_box.pack_start, self.pkgpage_website, False, False, 0)

        itemstoadd.append(website_box)

        #Author
        author_box = Gtk.Box()
        self.pkgpage_author = Gtk.Label(label=_("Author: %s") % pkginfo["author"])
        GLib.idle_add(author_box.pack_start, self.pkgpage_author, False, False, 0)

        itemstoadd.append(author_box)

        #URL for Donations
        donateurl_box = Gtk.Box()
        self.pkgpage_donateurl = Gtk.Label(label=_("Donate URL: %s") % pkginfo["donateurl"])
        GLib.idle_add(donateurl_box.pack_start, self.pkgpage_donateurl, False, False, 0)

        itemstoadd.append(donateurl_box)

        #URL for Bugs
        bugsurl_box = Gtk.Box()
        self.pkgpage_bugsurl = Gtk.Label(label=_("Bugs URL: %s") % pkginfo["bugreporturl"])
        GLib.idle_add(bugsurl_box.pack_start, self.pkgpage_bugsurl, False, False, 0)

        itemstoadd.append(bugsurl_box)

        #URL for Terms of Service
        tosurl_box = Gtk.Box()
        self.pkgpage_tosurl = Gtk.Label(label=_("Terms of Service URL: %s") % pkginfo["tosurl"])
        GLib.idle_add(tosurl_box.pack_start, self.pkgpage_tosurl, False, False, 0)

        itemstoadd.append(tosurl_box)

        #URL for Privacy Policy
        privpolurl_box = Gtk.Box()
        self.pkgpage_privpolurl = Gtk.Label(label=_("Privacy Policy URL: %s") % pkginfo["privpolurl"])
        GLib.idle_add(privpolurl_box.pack_start, self.pkgpage_privpolurl, False, False, 0)

        itemstoadd.append(privpolurl_box)

        GLib.idle_add(self.placeItemInformation, itemid, itemstoadd)


    def placeItemInformation(self, itemid, itemstoadd):
        #First, delete all children on the item information page
        for child in self.itempagecontents.get_children():
            GLib.idle_add(child.destroy)

        #Now add the new children to the item information page in order
        for item in itemstoadd:
            self.itempagecontents.insert(item, -1)

        #Finally, show them all
        self.itempagecontents.show_all()

############################################
# Notifications
############################################
class notifications():
    def __init__(self, parent):
        self.parent = parent
        self.toaststorage = {}
        mainloop = DBusGMainLoop()
        self.interface = dbus.SessionBus(mainloop=mainloop).get_object("org.freedesktop.Notifications", "/org/freedesktop/Notifications")
        self.interface = dbus.Interface(self.interface, "org.freedesktop.Notifications")
        self.interface.connect_to_signal('ActionInvoked', self.toastAction)
        self.interface.connect_to_signal('NotificationClosed', self.toastExpired)

        #Test notifications
        self.updatesAvailable()


    def newToast(self, icon, title, text, actions={}, subtitle="", replacenid=0, context="", permanent=False):
        nid = None
        dbusactions = []
        for i in actions:
            dbusactions.append(i)
            dbusactions.append(actions[i][0])
        dbustimeout = -1 if permanent == False else 0
        #Create and send the toast
        try:
            nid = self.interface.Notify("", replacenid, icon, title, text, dbusactions, \
                        {"urgency": 1, \
                            "desktop-entry": "feren-storium", \
                            "x-kde-origin-name": subtitle}, dbustimeout)
                    #Substitute application name ("" uses the name from the proce/info)
                    #Replace notification of this nid with this notification
                    #Icon name (can be file path)
                    #Header
                    #Text
                    #Actions (default maps to clicking the notification)
                    #   The cool part
                    #   .desktop mapping
                    #The timeout in milliseconds (-1 means use default)
        except Exception as e:
            if nid == None: #Notifications get created fine for some reason half the time despite 'too many notifications'
                if self.parent.configs != None and self.parent.configs.getDebugOutput() == True:
                    print(_("GUI DEBUG: Could not create toast '%s': %s") % (title, e))
                    #TODO: Global debug call instead
                return
        #Then add the toast to notification storage
        for i in actions:
            actions[i] = actions[i][1]
        self.toaststorage[str(nid)] = {"type": context, "actions": actions}


    def toastExpired(self, nid, reason):
        if nid not in self.toaststorage:
            return #Not our notification, so we shouldn't deal with it
        #Removes expired toast from notification storage
        try:
            self.toaststorage.pop(str(nid))
        except Exception as e:
            if self.parent.configs != None and self.parent.configs.getDebugOutput() == True:
                print(_("GUI DEBUG: Could not close toast %s: %s") % (str(nid), e))
                #TODO: Global debug call instead

    def toastAction(self, nid, action):
        nid, action = str(nid), str(action)
        if nid not in self.toaststorage:
            return #Not our notification, so we shouldn't deal with it
        #Executes the action specified in the notification storage
        if nid not in self.toaststorage:
            return
        if action not in self.toaststorage[nid]["actions"]:
            return
        #Execute the stored callback
        self.toaststorage[nid]["actions"][action]()

    def getToastTypeNID(self, ttype):
        for i in self.toaststorage:
            if self.toaststorage[i]["type"] == ttype:
                return i
        return 0


    def callbackTest(self):
        print("おはよー！")


    def updatesAvailable(self):
        #Shows an Updates Available notification
        self.newToast("mintupdate-updates-available", \
            _("Updates are available"), \
            _("""Open Store to view or install pending updates."""), \
            {"default": [_("View updates"), self.callbackTest]}, \
            "", self.getToastTypeNID("update"), "update")


    def updatesComplete(self):
        #Shows an Updates Complete notification
        self.newToast("mintupdate-up-to-date", \
            _("Your system is up to date"), \
            _("""Your system has successfully installed all of its available updates."""), \
            {}, \
            "", self.getToastTypeNID("update"), "update")



############################################
# Main window
############################################
class window(Gtk.Window):
    def __init__(self, parent):
        Gtk.Window.__init__(self)
        self.parent = parent
        self.connect('delete-event', partial(parent.windowClosed, "wnd"))

        #These three are used to skip page updating code whenever otherwise inappropriate to continue execution of, such as dropdown changes and so on.
        self.current_itemid = ""
        self.current_sourceid = ""
        self.current_subsourceid = ""

        #TODO: Move everything window-related into here
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_title(_("Feren Storium API Demo - GUI Module"))
        self.set_default_size(850, 640)
        self.set_size_request(850, 540)


    def spawn(self):
        #When using spawn, it means the window hasn't been opened yet, so we need to initialise it first, thus a splash screen is used
        GLib.idle_add(self.initSplash)
        GLib.idle_add(self.show_all)
        #Fully load the GUI if the Backend has already finished initialising.
        if self.parent.api.isInitialised() == True:
            GLib.idle_add(self.initComplete)


    def initSplash(self):
        #For the splash screen
        self.wndstack = Gtk.Stack() #Needs accessing later
        self.wndstack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.add(self.wndstack)

        #Splash screen
        self.splashscr = Gtk.VBox()
        self.splashscr.pack_start(Gtk.Box(), True, False, 0)
        splashimg = Gtk.Image()
        splashimg.set_from_icon_name("softwarecenter", Gtk.IconSize.DND)
        self.splashscr.pack_start(splashimg, False, False, 0)
        self.splashtext = Gtk.Label(label=_("Initialising Storium API Demo..."))
        self.splashscr.pack_start(self.splashtext, False, False, 0)
        self.splashscr.pack_start(Gtk.Box(), True, False, 0)
        self.wndstack.add_named(self.splashscr, "splash")


    def initComplete(self):
        if self.get_realized == False:
            return #Do not run this if the window is not currently opened.

        self.wndcontents = Gtk.VBox()

        self.body, self.pages = self.createBody()
        self.maintoolbar = self.createToolbar()

        self.wndcontents.pack_start(self.maintoolbar, False, False, 0)
        self.wndcontents.pack_start(self.body, True, True, 0)

        #Assemble window so far
        self.wndstack.add_named(self.wndcontents, "body")

        self.wndcontents.show_all()
        self.splashscr.destroy() #We don't need it any longer
        self.wndstack.set_visible_child(self.wndcontents)

        #TODO: Start thread to load all pages initially loaded



    ############################################
    # Toolbar
    ############################################

    def createToolbar(self):
        #Left stuff
        backbuttonImg = Gtk.Image()
        backbuttonImg.set_from_icon_name("go-previous-symbolic", Gtk.IconSize.BUTTON)
        self.backbutton = Gtk.Button(image=backbuttonImg)
        self.backbutton.set_sensitive(False)
        self.backbutton.connect("clicked", self.returnToMainView)

        header = Gtk.Box()
        header.set_spacing(6)
        logoimageandbox = Gtk.Box(spacing=8)
        logotypebox = Gtk.VBox(spacing=0)
        logoimg = Gtk.Image()
        logoimg.set_from_icon_name("softwarecenter", Gtk.IconSize.DND);

        logotype1 = Gtk.Label(label=("Storium API"))
        logotype2 = Gtk.Label(label=("Demonstration"))

        logotype1_box = Gtk.Box()
        logotype2_box = Gtk.Box()
        logotype1_box.pack_start(logotype1, False, False, 0)
        logotype2_box.pack_start(logotype2, False, False, 0)

        logotypebox.pack_start(logotype1_box, False, False, 0)
        logotypebox.pack_end(logotype2_box, False, False, 0)
        logoimageandbox.pack_start(logoimg, False, False, 0)
        logoimageandbox.pack_end(logotypebox, False, False, 0)

        header.pack_start(self.backbutton, False, False, 0)
        header.pack_start(logoimageandbox, False, True, 0)

        #Separation of both sides
        toolbarspacer=Gtk.Alignment()

        #Right stuff
        self.pageswitcher = Gtk.StackSwitcher()
        self.pageswitcher.set_stack(self.pages)

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

        #Top toolbar
        result = Gtk.Box()
        result.get_style_context().add_class(Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)
        result.pack_start(header, False, False, 0)
        result.pack_start(toolbarspacer, True, True, 0)
        result.pack_end(menu_btn, False, True, 0)

        funnibutton = Gtk.Button()
        funnibutton.connect("clicked", self.test)
        result.pack_end(funnibutton, False, True, 0)

        result.pack_end(self.pageswitcher, False, True, 0)

        return result

    def test(self, button):
        self.body.set_visible_child(self.itempage)

    def GUIViewChanged(self, stckswch, idk):
        self.pageswitcher.set_visible(self.body.get_visible_child() == self.pages)
        self.backbutton.set_sensitive(self.body.get_visible_child() != self.pages)


    ############################################
    # The window body (the pages)
    ############################################

    def createBody(self):
        result = Gtk.Stack()
        result.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        result.connect("notify::visible-child", self.GUIViewChanged)
        self.homepage = Gtk.FlowBox()
        self.appspage = self.categoricalPage()
        self.gamespage = self.categoricalPage()
        self.themespage = self.categoricalPage()
        self.websitespage = self.categoricalPage()
        self.taskspage = Gtk.VBox()
        self.searchpage = Gtk.VBox()
        self.itempage = Gtk.VBox()
        #TODO: Get all categories from all modules, and, atop our own categories, and collect them here, followed by sorting them into each page's body
        # TODO: Add 'categories' dictionary argument to self.categoricalPage()
        # TODO: Add an 'Extras' page, if there are OOB categories, to house those categories in
        # TODO: Callback to GUI, during module reinitialisation, to do tasks including refreshing the categories shown in the pages of the GUI
        self.extraspage = None

        subresult = Gtk.Stack()
        subresult.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        subresult.get_style_context().add_class(Gtk.STYLE_CLASS_VIEW)

        for i in [self.homepage, self.taskspage, self.searchpage, self.itempage]:
            i.set_margin_top(4)
            i.set_margin_bottom(4)

        subresult.add_titled(self.homepage, "home", _("Home"))
        subresult.add_titled(self.appspage, "apps", _("Applications"))
        subresult.add_titled(self.gamespage, "games", _("Games"))
        subresult.add_titled(self.themespage, "themes", _("Themes"))
        subresult.add_titled(self.websitespage, "websites", _("Websites"))
        subresult.add_named(self.taskspage, "tasks")
        subresult.child_set_property(self.taskspage, "icon-name", "folder-download-symbolic")
        subresult.add_named(self.searchpage, "search")
        subresult.child_set_property(self.searchpage, "icon-name", "edit-find-symbolic")

        result.add_named(subresult, "store")
        result.add_named(self.itempage, "itempage")

        #Spawn categories in the background
        thread = Thread(target=self.parent.refreshCategories,
                        args=())
        thread.daemon = True
        thread.start()

        return result, subresult

    def returnToMainView(self, button):
        self.body.set_visible_child(self.pages)

    def categoricalPage(self):
        result = Gtk.Box()
        categoriesScroll = Gtk.ScrolledWindow()
        categoriesScroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        categoriesPane = Gtk.ListBox()
        categoriesScroll.add(categoriesPane)
        categoriesPane.set_size_request(270, -1)
        result.pack_start(categoriesScroll, False, True, 0)
        result.pack_start(Gtk.Separator(), False, True, 0)
        listingsPane = Gtk.FlowBox()
        listingsPane.set_margin_top(4)
        listingsPane.set_margin_bottom(4)
        result.pack_end(listingsPane, True, True, 0)

        result.categoriesPane = categoriesPane
        result.listingsPane = listingsPane

        categoriesPane.connect('row-activated', self.onCategoryChanged, result)

        return result

        #TODO: For All, do a search on nothing (kinda like with the application sources dialog) with no filter, and give it no limit - afterwards, rid of duplicate IDs, put all the IDs in a list, and get up to (depends on results quantity) 200 random indexes - then, sort these index numbers, and return the list values corresponding to that index, before showing them as results



    def generateCategoryItem(self, categoryid, categoryinfo):
        result = Gtk.ListBoxRow()
        box = Gtk.Box(spacing=7, margin=7)
        icon = Gtk.Image()
        icon.set_from_icon_name(categoryinfo[0]+"-symbolic", Gtk.IconSize.MENU)
        box.pack_start(icon, False, False, 0)
        box.pack_start(Gtk.Label(label=categoryinfo[1], xalign=0), False, False, 0)
        result.add(box)
        result.category = categoryid
        return result

    def onCategoryChanged(self, listbox, row, listingsPane):
        print(row.category, listingsPane)



############################################
# Module initialisation and Brain responder
############################################
class module():
    def __init__(self, genericapi, guiapi):
        self.api = genericapi
        self.guiapi = guiapi
        self.configs = None #Filled by Brain
        self.desktoasts = None #Initialised by initGUI

        self.test = "guitesT"

        # Program identification
        GLib.set_prgname('/usr/bin/feren-storium')

        # Required by GTK for some reason
        GObject.threads_init()

        #Open, but never show, all windows in the background
        self.changeswnd = changesBonusesDialog(self)
        self.errorwnd = errorWindow(self)
        self.configwnd = configWindow(self)
        self.wnd = window(self)
        thread = Thread(target=self.initGTK,
                        args=())
        thread.daemon = True
        thread.start()
        time.sleep(0.1) #Give GTK time to launch as rushed launches lead to an X Window Error when spawning the windows

        #Initialise notifications and such for tasks support
        self.desktoasts = notifications(self)

        #CATEGORIES
        self.defaultcategories = {"applications-webbrowsers": ["applications-internet", _("Web Browsers")],
            "applications-development": ["applications-development", _("Development")],
            "applications-education": ["applications-engineering", _("Education")],
            "applications-electronics": ["applications-electronics", _("Electronics Education")],
            "applications-math": ["applications-mathematics", _("Maths")],
            "applications-science": ["applications-science", _("Science")],
            "applications-3dgraphics": ["applications-3D", _("3D Graphics")],
            "applications-drawing": ["applications-drawing", _("Drawing")],
            "applications-photography": ["applications-photography", _("Photography")],
            "applications-publishing": ["applications-publishing", _("Scanning and Publishing")],
            "applications-viewers": ["applications-viewers", _("Document Viewers")],
            "applications-internet": ["applications-internet", _("Internet")],
            "applications-mail": ["applications-mail", _("Email")],
            "applications-chat": ["applications-chat", _("Chat")],
            "applications-filesharing": ["applications-filesharing", _("File sharing")],
            "applications-office": ["applications-office", _("Office")],
            "applications-development": ["applications-development", _("Programming")],
            "applications-multimedia": ["applications-multimedia", _("Sound and Video")],
            "applications-system": ["applications-system", _("System Tools")],
            "applications-utilities": ["applications-utilities", _("Utilities")],
            "games-stores": ["applications-games", _("Game Stores")],
            "games-launchers": ["applications-games", _("Game Launchers")],
            "games-board": ["applications-boardgames", _("Board Games")],
            "games-1stperson": ["applications-games", _("First-person")],
            "games-realtime": ["applications-games", _("Real-time")],
            "games-turnbased": ["applications-games", _("Turn-based")],
            "games-simracing": ["applications-simulation", _("Simulators and Racing")],
            "games-emulators": ["applications-arcade", _("Hardware Emulation")],
            "themes-styles": ["preferences-desktop-theme", _("Styles")],
            "themes-appstyles": ["preferences-desktop-theme-applications", _("Application Styles")],
            "themes-icons": ["preferences-desktop-icons", _("Icon Sets")],
            "themes-cursors": ["preferences-desktop-cursors", _("Cursors")],
            "themes-wallpapers": ["preferences-desktop-background", _("Wallpapers")],
            "themes-fonts": ["preferences-desktop-fonts", _("Fonts")],
            "themes-bootscreens": ["preferences-system-startup", _("Boot Screens")],
            "websites-development": ["applications-development", _("Development")],
            "websites-education": ["applications-engineering", _("Education")],
            "websites-games": ["applications-games", _("Games")],
            "websites-graphics": ["applications-graphics", _("Graphics")],
            "websites-social": ["applications-internet", _("Social Media")],
            "websites-news": ["applications-internet-news", _("News")],
            "websites-multimedia": ["applications-multimedia", _("Multimedia")],
            "websites-office": ["applications-office", _("Office")],
            "websites-utilities": ["applications-utilities", _("Utilities")],
            "websites-more": ["applications-other", _("More")]}


    def windowClosed(self, target, p1 = None, p2 = None):
        #Reopen the windows in the background, after closing, for their next use
        if target == "wnd" and self.wnd != None:
            self.wnd.destroy()
            self.wnd = window(self)
        elif target == "changes" and self.changeswnd != None:
            self.changeswnd.destroy()
            self.changeswnd = changesBonusesDialog(self)
        elif target == "error" and self.errorwnd != None:
            self.errorwnd.destroy()
            self.errorwnd = errorWindow(self)
        elif target == "config" and self.configwnd != None:
            self.configwnd.destroy()
            self.configwnd = configWindow(self)
        else:
            return
        #TODO: Move this to onExit call of some sort for when quitting Storium:
        #*destroy all 3 windows*
            #Gtk.main_quit(p1, p2)
            #self.gtkrunning = False

    def initGTK(self):
        Gtk.main()


    def spawnGUI(self, command="", targetid="", moduleid="", sourceid="", subsourceid=""):
        #Open main window and direct it with arguments
        # If the window is already loaded, focus it first
        if self.wnd.get_realized() == True: #realized is False until the window's shown
            GLib.idle_add(self.wnd.present)
        else: #If not loaded, it has to spawn first
            self.wnd.spawn()

        #TODO: Once loaded, respond to arguments
        pass

    def updateInitStatus(self, value):
        if self.wnd is None:
            return
        if self.wnd.splashtext is None:
            return
        GLib.idle_add(self.wnd.splashtext.set_label, value)


    def finishInitGUI(self):
        #Proceed to the main page from the splash screen, before loading all content
        GLib.idle_add(self.wnd.initComplete)

    def refreshCategories(self):
        #TODO: Query modules for extra categories
        modulecategories = {}
        categories = {}
        for i in self.defaultcategories:
            categories[i] = self.defaultcategories[i]
        for module in modulecategories:
            for i in modulecategories[module]:
                #Skip category IDs that already exist
                if i in categories:
                    continue
                else:
                    #TODO: Syntax checks
                    categories[i] = modulecategories[module][i]

        #Split categories into pages
        toadd = {"apps": {}, "games": {}, "themes": {}, "websites": {}, "extras": {}}
        for i in categories:
            if i.startswith("applications-"):
                toadd["apps"][i] = categories[i]
            elif i.startswith("games-"):
                toadd["games"][i] = categories[i]
            elif i.startswith("themes-"):
                toadd["themes"][i] = categories[i]
            elif i.startswith("websites-"):
                toadd["websites"][i] = categories[i]
            else:
                toadd["extras"][i] = categories[i]
        del categories

        #Destroy all current categories on all pages
        targets = [self.wnd.appspage, self.wnd.gamespage, self.wnd.themespage, self.wnd.websitespage]
        if self.wnd.extraspage != None: #Account for extras page if used already
            targets.append(self.wnd.extraspage)
        for i in targets:
            for child in i.categoriesPane.get_children():
                GLib.idle_add(child.destroy)

        #Add categories to all pages
        for i in toadd["apps"]:
            GLib.idle_add(self.wnd.appspage.categoriesPane.add, self.wnd.generateCategoryItem(i, toadd["apps"][i]))
        GLib.idle_add(self.wnd.appspage.show_all)
        for i in toadd["games"]:
            GLib.idle_add(self.wnd.gamespage.categoriesPane.add, self.wnd.generateCategoryItem(i, toadd["games"][i]))
        GLib.idle_add(self.wnd.gamespage.show_all)
        for i in toadd["themes"]:
            GLib.idle_add(self.wnd.themespage.categoriesPane.add, self.wnd.generateCategoryItem(i, toadd["themes"][i]))
        GLib.idle_add(self.wnd.themespage.show_all)
        for i in toadd["websites"]:
            GLib.idle_add(self.wnd.websitespage.categoriesPane.add, self.wnd.generateCategoryItem(i, toadd["websites"][i]))
        GLib.idle_add(self.wnd.websitespage.show_all)
        #Destroy extras if unused
        if toadd["extras"] == {}:
            if self.wnd.extraspage != None:
                GLib.idle_add(self.wnd.pages.remove, self.wnd.extraspage)
                GLib.idle_add(self.wnd.extraspage.destroy)
                self.wnd.extraspage = None
        else:
            if self.wnd.extraspage == None: #Create extras if currently non-existant
                self.wnd.extraspage = self.wnd.categoricalPage()
                GLib.idle_add(self.wnd.pages.add_titled, self.wnd.extraspage, "extras", _("Extras"))
            for i in toadd["extras"]: #Irregardless, add categories to Extras page
                GLib.idle_add(self.wnd.extraspage.categoriesPane.add, self.wnd.generateCategoryItem(i, toadd["extras"][i]))
            GLib.idle_add(self.wnd.extraspage.show_all)

        #Fixes for button placement
        if self.wnd.extraspage != None:
            GLib.idle_add(self.wnd.pages.child_set_property, self.wnd.taskspage, "position", 9)
            GLib.idle_add(self.wnd.pages.child_set_property, self.wnd.searchpage, "position", 10)



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
        self.wndcontents.pack_start(self.maintoolbar, False, True, 0)
        self.wndcontents.pack_start(self.detailsheader, False, True, 0)
        self.wndcontents.pack_end(self.pagearea, True, True, 0)
        GLib.idle_add(self.show_all)

        self.pagearea.populate_mainpage()



    def refresh_memory(self):
        pass





    # API CALLS FOR CLASSES
    def gotoID(self, itemid):
        self.pagearea.gotoID(itemid)

    def showTaskConfirmation(self, taskbody, idsadded, idsupdated, idsremoved, bonusavailability):
        #TODO: Make an actual GUI for this
        print("Opened dialog to confirm pending operation of " + str(taskbody.operation) + " to " + taskbody.itemid + " of module" + taskbody.moduleid + " in source " + taskbody.sourceid + ", " + taskbody.subsourceid)

        if len(idsadded) == 0 and len(idsupdated) == 0 and len(idsremoved) == 0 and len(bonusavailability) == 0:
            return True, [] #Skip the confirmation if there is nothing extra to confirm

        GLib.idle_add(self.changeswnd.prepare, self.api, taskbody, idsadded, idsupdated, idsremoved, bonusavailability)
        return self.changeswnd.run()

