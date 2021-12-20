#!/usr/bin/python3

import gi

gi.require_version('WebKit2', '4.0')
gi.require_version('Gtk', '3.0')

import sys
import locale #Translations go brrr
import gettext #Translations go brrr
import getpass #Used for finding username

import os

from gi.repository import Gtk, Gio, Gdk, GLib, Pango, GObject, GdkPixbuf
from threading import Thread
from queue import Queue, Empty


def should_load(): #Should this module be loaded?
    return True


####Application icon
class AppItemIcon(Gtk.Stack):
    
    def __init__(self, get_icon_callback):
        Gtk.Stack.__init__(self)
        GObject.threads_init()
        
        
        self.get_icon_callback = get_icon_callback
        
        self.app_iconimg = Gtk.Image()
        self.app_iconimg_loading = Gtk.Spinner()
        self.app_iconimg_loading_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.app_iconimg_loading_box.set_center_widget(self.app_iconimg_loading)
        
        self.add_named(self.app_iconimg_loading_box, "load")
        self.add_named(self.app_iconimg, "icon")
        
        self.desired_size = 48
        self.set_icon("file:///usr/share/feren-os/logos/blank.png", "")
        
        self.show_all()
        
    
    def set_icon(self, iconuri, packagename):
        thread = Thread(target=self._set_icon,
                        args=(iconuri, packagename))
        thread.daemon = True
        thread.start()
        
    def _set_icon(self, iconuri, packagename):
        GLib.idle_add(self.set_visible_child, self.app_iconimg_loading_box)
        GLib.idle_add(self.app_iconimg_loading.start,)
        
        try:
            iconurilocat = self.get_icon_callback(iconuri, packagename)
        except:
            #TODO: Change to store-missing-icon
            iconurilocat = "/usr/share/icons/Inspire/256/apps/feren-store.png"
        
        icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file(iconurilocat)
        icon_pixbuf = icon_pixbuf.scale_simple(self.desired_size, self.desired_size, GdkPixbuf.InterpType.BILINEAR)
        
        GLib.idle_add(self.app_iconimg.set_from_pixbuf, icon_pixbuf)
        GLib.idle_add(self.app_iconimg_loading.stop,)
        GLib.idle_add(self.set_visible_child, self.app_iconimg)


####Item button
class AppItemButton(Gtk.Button):
    
    def __init__(self, packagename, storebrain, showwarns=True, packageinfo={}):
        
        Gtk.Button.__init__(self)
        self.storebrain = storebrain
        
        self.child_items = []
        
        if packageinfo == {}:
            packageinfo = self.storebrain.get_item_info_default(packagename)
        
        app_icon = AppItemIcon(self.storebrain.get_icon)
        app_icon.set_icon(packageinfo["iconuri"], packagename)
        
        label_name = Gtk.Label(label=packageinfo["realname"])
        
        label_summary = Gtk.Label(label=packageinfo["shortdescription"])
        label_summary.set_ellipsize(True)
        label_summary.set_ellipsize(Pango.EllipsizeMode.END)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        #Make sure application name and short descriptions are left-aligned in there
        app_title_box = Gtk.Box()
        app_desc_box = Gtk.Box()
        app_title_box.pack_start(label_name, False, False, 0)
        app_desc_box.pack_start(label_summary, False, False, 0)
        

        #Make the column for application name and short description
        vbox.pack_start(app_title_box, False, False, 0)
        vbox.pack_end(app_desc_box, False, False, 0)

        hbox = Gtk.Box()
        hbox.pack_start(app_icon, False, False, 4)
        hbox.pack_start(vbox, False, False, 8)

        self.add(hbox)
        
        self.child_items = [app_icon, label_name, label_summary, vbox, app_title_box, app_desc_box, hbox]
        
        if showwarns == True:
            self.add_warnings(packageinfo)
        
        self.show_all()
                
    def add_warnings(self, packageinfo):
        #TODO
        pass
    
    def destroy_everything(self):
        for item in self.child_items:
            for child in item.get_children():
                child.destroy()
            item.destroy()
        self.destroy()
        
    
####Task Item button
class TaskItemButton(Gtk.Button):
    
    def __init__(self, taskid, storebrain, taskinfo={}):
        
        Gtk.Button.__init__(self)
        self.storebrain = storebrain
        
        #Get task information split up
        modulename, packagetype, packagename = taskid.split(":")[0:3] #Refer to comment on _refresh_tasks
        
        
        self.child_items = []
        
        packageinfo = {}
        
        if taskinfo == {}:
            packageinfo = self.storebrain.get_item_info_default(packagename)
        else:
            packageinfo = taskinfo["pkginfo"]
            
        #TODO: Get default module's item info
        
        app_icon = AppItemIcon(self.storebrain.get_icon)
        app_icon.set_icon(packageinfo["iconuri"], packagename)
        
        label_name = Gtk.Label(label=packageinfo["realname"])
        
        label_summary = Gtk.Label(label=packageinfo["shortdescription"])
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)

        #Make sure application name and short descriptions are left-aligned in there
        app_title_box = Gtk.Box()
        app_desc_box = Gtk.Box()
        app_title_box.pack_start(label_name, False, False, 0)
        app_desc_box.pack_start(label_summary, False, False, 0)
        

        #Make the column for application name and short description
        vbox.pack_start(app_title_box, False, False, 0)
        vbox.pack_end(app_desc_box, False, False, 0)

        hbox = Gtk.Box()
        hbox.pack_start(app_icon, False, False, 4)
        hbox.pack_start(vbox, False, False, 8)

        self.add(hbox)
        
        self.child_items = [app_icon, label_name, label_summary, vbox, app_title_box, app_desc_box, hbox]
        
        self.show_all()
                
    def add_warnings(self, packageinfo):
        #TODO
        pass
    
    def destroy_everything(self):
        for item in self.child_items:
            for child in item.get_children():
                child.destroy()
            item.destroy()
        self.destroy()


####Application Details Header
class AppDetailsHeader(Gtk.VBox):

    def __init__(self, storebrain):
        
        Gtk.Box.__init__(self)
        self.storebrain = storebrain
        
        self.app_icon = AppItemIcon(self.storebrain.get_icon)
        
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
        self.installappnosource_btn.connect("clicked", self.installappnosource_pressed)
        self.updateapp_btn.connect("clicked", self.updateapp_pressed)
        self.removeapp_btn.connect("clicked", self.removeapp_pressed)
        self.cancelapp_btn.connect("clicked", self.cancelapp_pressed)
        
        #For sources
        self.source_ids = []
        self.subsource_ids = []
        
        pass
    
    
    def populate(self, packageinfo, currentpackage):
        thread = Thread(target=self._populate,
                            args=(packageinfo, currentpackage))
        thread.start()
    
    def _populate(self, packageinfo, currentpackage):
        GLib.idle_add(self.app_title.set_label, packageinfo["realname"])
        GLib.idle_add(self.app_icon.set_icon, packageinfo["iconuri"], currentpackage)
        GLib.idle_add(self.app_shortdesc.set_label, packageinfo["shortdescription"]) #Some sources like ICE have their own descriptions
        pass #TODO
    
    
    def populate_sources(self, currentpackage):
        thread = Thread(target=self._populate_sources,
                            args=(currentpackage,))
        thread.start()
    
    def _populate_sources(self, currentpackage):
        self.source_ids, sourcenames = self.storebrain.get_sources(currentpackage)
        
        iface_list_store = Gtk.ListStore(GObject.TYPE_STRING)
        
        n = 0
        for item in self.source_ids:
            iface_list_store.append([sourcenames[n]])
            n += 1
            
        GLib.idle_add(self.app_source_dropdown.set_model, iface_list_store)
        GLib.idle_add(self.app_source_dropdown.set_active, 0)
        if len(self.source_ids) <= 1:
            GLib.idle_add(self.app_source_dropdown.set_sensitive, False)
        else:
            GLib.idle_add(self.app_source_dropdown.set_sensitive, True)
    
    
    def populate_subsources(self, currentpackage, sourceid):
        thread = Thread(target=self._populate_subsources,
                            args=(currentpackage, sourceid))
        thread.start()
    
    def _populate_subsources(self, currentpackage, sourceid):
        self.subsource_ids, subsourcenames = self.storebrain.get_subsources(sourceid, currentpackage)
        
        iface_list_store = Gtk.ListStore(GObject.TYPE_STRING)
        
        n = 0
        for item in self.subsource_ids:
            iface_list_store.append([subsourcenames[n]])
            n += 1
            
        GLib.idle_add(self.app_subsource_dropdown.set_model, iface_list_store)
        GLib.idle_add(self.app_subsource_dropdown.set_active, 0)
        
        if self.installapp_btn.get_sensitive() == True and len(self.subsource_ids) > 1:
            GLib.idle_add(self.app_subsource_dropdown.set_visible, True)
        else:
            GLib.idle_add(self.app_subsource_dropdown.set_visible, False)
            
    
    def on_source_dropdown_changed(self, combobox):
        thread = Thread(target=self._on_source_dropdown_changed,
                            args=(combobox,))
        thread.start()
        
    def on_source_dropdown_changed(self, combobox):
        if combobox.get_active() == -1:
            return
        print("DEBUG: Source changed to", self.source_ids[combobox.get_active()])
        self.mv.current_subsource_viewed = ""
        
        self.mv.current_module_viewed, self.mv.current_type_viewed, self.mv.current_source_viewed = self.source_ids[combobox.get_active()].split(":")
        
        self.mv.change_source(self.mv.current_item_viewed, self.source_ids[combobox.get_active()])
        
    
    def on_subsource_dropdown_changed(self, combobox):
        thread = Thread(target=self._on_subsource_dropdown_changed,
                            args=(combobox,))
        thread.start()
        
    def _on_subsource_dropdown_changed(self, combobox):
        if combobox.get_active() == -1:
            self.mv.current_subsource_viewed = ""
            return
        print("DEBUG: Sub-Source changed to", self.subsource_ids[combobox.get_active()])
        self.mv.current_subsource_viewed = self.subsource_ids[combobox.get_active()]
    

    def set_progress(self, value):
        self.app_mgmt_progress.set_fraction(value / 100)

    def installapp_pressed(self, gtk_widget):
        #TODO: Confirmation and whatnot, let's just get the main event working first
        subsource = self.mv.current_subsource_viewed
        self.storebrain.pkgmgmt_modules[self.mv.current_module_viewed].install_package(self.mv.current_item_viewed, self.mv.current_type_viewed, self.mv.current_source_viewed, self.mv.current_subsource_viewed)

    def installappnosource_pressed(self, gtk_widget):
        #TODO
        pass

    def updateapp_pressed(self, gtk_widget):
        #TODO: Confirmation and whatnot, let's just get the main event working first
        self.storebrain.pkgmgmt_modules[self.mv.current_module_viewed].update_package(self.mv.current_item_viewed, self.mv.current_type_viewed, self.mv.current_source_viewed, self.mv.current_subsource_viewed)

    def removeapp_pressed(self, gtk_widget):
        source = ""
        #TODO: Confirmation and whatnot, let's just get the main event working first
        self.storebrain.pkgmgmt_modules[self.mv.current_module_viewed].remove_package(self.mv.current_item_viewed, self.mv.current_type_viewed, self.mv.current_source_viewed, self.mv.current_subsource_viewed)


    def cancelapp_pressed(self, gtk_widget):
        thread = Thread(target=self._cancelapp_pressed,
                            args=(gtk_widget,))
        thread.start()
        
    def _cancelapp_pressed(self, gtk_widget):
        GLib.idle_add(self.cancelapp_btn.set_sensitive, False)
        self.storebrain.tasks.cancel_task(self.mv.current_module_viewed, self.mv.current_type_viewed, self.mv.current_item_viewed)
    
        
    def update_buttons(self, status):
        thread = Thread(target=self._update_buttons,
                            args=(status,))
        thread.start()
        
    def _update_buttons(self, status):
        #Update buttons according to status
        if status == 0: #Uninstalled
            GLib.idle_add(self.installapp_btn.set_sensitive, True)
        else:
            GLib.idle_add(self.installapp_btn.set_sensitive, False)
        if status == 3: #Available in disabled source
            GLib.idle_add(self.installappnosource_btn.set_sensitive, True)
        else:
            GLib.idle_add(self.installappnosource_btn.set_sensitive, False)
        if status == 2: #Updatable
            GLib.idle_add(self.updateapp_btn.set_sensitive, True)
        else:
            GLib.idle_add(self.updateapp_btn.set_sensitive, False)
        if status == 1 or status == 2: #Installed or updatable
            GLib.idle_add(self.removeapp_btn.set_sensitive, True)
        else:
            GLib.idle_add(self.removeapp_btn.set_sensitive, False)
        if status == 900: #Queued
            GLib.idle_add(self.cancelapp_btn.set_sensitive, True)
        else:
            GLib.idle_add(self.cancelapp_btn.set_sensitive, False)
        #901 - Working on item
        
    
    def tasks_refresh_pkgpage(self):
        thread = Thread(target=self._tasks_refresh_pkgpage,
                            args=())
        thread.start()
        
    def _tasks_refresh_pkgpage(self):
        self.mv.change_source(self.mv.current_item_viewed, self.source_ids[self.app_source_dropdown.get_active()])
        #TODO
        


####AppView
class AppMainView(Gtk.Stack):

    def __init__(self):
        Gtk.Stack.__init__(self)
        
        self.current_item_viewed = ""
        self.current_module_viewed = ""
        self.current_type_viewed = ""
        self.current_source_viewed = ""
        self.current_subsource_viewed = ""
        
        self.sw = Gtk.ScrolledWindow()
        self.sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        mainpage = Gtk.VBox(spacing=8)
        
        mainlabel_box = Gtk.Box()
        mainlabel = Gtk.Label(label="Application Listings:")
        mainlabel_box.pack_start(mainlabel, False, False, 0)
        
        self.appsitems = Gtk.FlowBox()
        self.appsitems.set_min_children_per_line(3)
        self.appsitems.set_margin_top(4)
        self.appsitems.set_margin_bottom(4)
        #self.appsitems.set_min_children_per_line(1)
        #self.appsitems.set_max_children_per_line(1)
        self.appsitems.set_row_spacing(4)
        self.appsitems.set_homogeneous(True)
        self.appsitems.set_valign(Gtk.Align.START)
        
        themeslabel_box = Gtk.Box()
        themeslabel = Gtk.Label(label="Themes Listings:")
        themeslabel_box.pack_start(themeslabel, False, False, 0)
        
        self.themesitems = Gtk.FlowBox()
        self.themesitems.set_min_children_per_line(3)
        self.themesitems.set_margin_top(4)
        self.themesitems.set_margin_bottom(4)
        #self.themesitems.set_min_children_per_line(1)
        #self.themesitems.set_max_children_per_line(1)
        self.themesitems.set_row_spacing(4)
        self.themesitems.set_homogeneous(True)
        self.themesitems.set_valign(Gtk.Align.START)
        
        websiteslabel_box = Gtk.Box()
        websiteslabel = Gtk.Label(label="Websites Listings:")
        websiteslabel_box.pack_start(websiteslabel, False, False, 0)
        
        self.websitesitems = Gtk.FlowBox()
        self.websitesitems.set_min_children_per_line(3)
        self.websitesitems.set_margin_top(4)
        self.websitesitems.set_margin_bottom(4)
        #self.websitesitems.set_min_children_per_line(1)
        #self.websitesitems.set_max_children_per_line(1)
        self.websitesitems.set_row_spacing(4)
        self.websitesitems.set_homogeneous(True)
        self.websitesitems.set_valign(Gtk.Align.START)
                
        mainpage.pack_start(mainlabel_box, False, True, 0)
        mainpage.pack_start(self.appsitems, False, True, 0)
        mainpage.pack_start(themeslabel_box, False, True, 0)
        mainpage.pack_start(self.themesitems, False, True, 0)
        mainpage.pack_start(websiteslabel_box, False, True, 0)
        mainpage.pack_start(self.websitesitems, False, True, 0)
        
        mainpage.set_margin_bottom(8)
        mainpage.set_margin_top(8)
        mainpage.set_margin_left(10)
        mainpage.set_margin_right(10)
        
        self.sw.add(mainpage)
        
        
        self.add_named(self.sw, "home")
        
        
        # build tasks page
        taskspage = Gtk.VBox(spacing=8)
        
        taskslabel_box = Gtk.Box()
        taskslabel = Gtk.Label(label="Currently working on these tasks:")
        taskslabel_box.pack_start(taskslabel, False, False, 0)
        
        self.tasksitemscontainer = Gtk.Box()
        self.tasksitemscontainer.set_margin_top(4)
        self.tasksitemscontainer.set_margin_bottom(4)
        self.tasksitemscontainer.set_valign(Gtk.Align.START)
        self.tasksitems = None
        
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
        taskspage.pack_start(self.tasksitemscontainer, False, True, 0)
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
        
        self.searchbar = Gtk.Entry()
        self.searchbar.connect("changed", self.searchbar_search)
        
        self.searchresultscontainer = Gtk.Box()
        self.searchresultscontainer.set_margin_top(4)
        self.searchresultscontainer.set_margin_bottom(4)
        self.searchresults = None
        
        searchpage.pack_start(self.searchbar, False, True, 4)
        searchpage.pack_start(self.searchresultscontainer, False, True, 4)
        
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
        
        self.packagepagecontents = Gtk.FlowBox()
        self.packagepagecontents.set_min_children_per_line(1)
        self.packagepagecontents.set_max_children_per_line(1)
        
        self.packagepagemessages = [] #Storage for package page messages
        
        packagepage.pack_start(self.packagepagecontents, True, True, 8)
        
        images_box = Gtk.Box()
        self.pkgpage_images = Gtk.Label(label="Images: ")
        images_box.pack_start(self.pkgpage_images, False, False, 0)
        
        self.packagepagecontents.insert(images_box, -1)
        
        description_box = Gtk.Box()
        self.pkgpage_description = Gtk.Label(label="Description: ")
        description_box.pack_start(self.pkgpage_description, False, False, 0)
        
        self.packagepagecontents.insert(description_box, -1)
        
        category_box = Gtk.Box()
        self.pkgpage_category = Gtk.Label(label="Category: ")
        category_box.pack_start(self.pkgpage_category, False, False, 0)
        
        self.packagepagecontents.insert(category_box, -1)
        
        website_box = Gtk.Box()
        self.pkgpage_website = Gtk.Label(label="Website: ")
        website_box.pack_start(self.pkgpage_website, False, False, 0)
        
        self.packagepagecontents.insert(website_box, -1)
        
        author_box = Gtk.Box()
        self.pkgpage_author = Gtk.Label(label="Author: ")
        author_box.pack_start(self.pkgpage_author, False, False, 0)
        
        self.packagepagecontents.insert(author_box, -1)
        
        donateurl_box = Gtk.Box()
        self.pkgpage_donateurl = Gtk.Label(label="Donate URL: ")
        donateurl_box.pack_start(self.pkgpage_donateurl, False, False, 0)
        
        self.packagepagecontents.insert(donateurl_box, -1)
        
        bugsurl_box = Gtk.Box()
        self.pkgpage_bugsurl = Gtk.Label(label="Bugs URL: ")
        bugsurl_box.pack_start(self.pkgpage_bugsurl, False, False, 0)
        
        self.packagepagecontents.insert(bugsurl_box, -1)
        
        tosurl_box = Gtk.Box()
        self.pkgpage_tosurl = Gtk.Label(label="TOS URL: ")
        tosurl_box.pack_start(self.pkgpage_tosurl, False, False, 0)
        
        self.packagepagecontents.insert(tosurl_box, -1)
        
        privpolurl_box = Gtk.Box()
        self.pkgpage_privpolurl = Gtk.Label(label="Privacy Policy URL: ")
        privpolurl_box.pack_start(self.pkgpage_privpolurl, False, False, 0)
        
        self.packagepagecontents.insert(privpolurl_box, -1)
        
        # build another scrolled window widget and add our package view
        self.sw4 = Gtk.ScrolledWindow()
        self.sw4.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        
        packagepage.set_margin_bottom(8)
        packagepage.set_margin_top(8)
        packagepage.set_margin_left(10)
        packagepage.set_margin_right(10)
        
        self.sw4.add(packagepage)
        
        
        self.add_named(self.sw4, "packagepage")
        
    
    def add_message(self, messagetype, messagecontents, button_callback=None, button_text=""):
        thread = Thread(target=self._add_message,
                            args=(messagetype, messagecontents, button_callback, button_text))
        thread.start()
        
    def _add_message(self, messagetype, messagecontents, button_callback=None, button_text=""):
        #TODO: Message types
        message_box = Gtk.Box()
        message_text = Gtk.Label()
        message_text.set_label(messagetype+": "+messagecontents)
        message_box.pack_start(message_text, False, False, 0)
        if button_callback != None:
            message_button = Gtk.Button()
            message_button.set_label(button_text)
            message_button.connect('clicked', button_callback)
            message_box.pack_end(message_button, False, False, 0)
        GLib.idle_add(self.packagepagecontents.insert, message_box, 0)
        
        GLib.idle_add(self.packagepagemessages.append, message_box)
        
        GLib.idle_add(message_box.show_all,)
    
        
    def add_warnings(self, packageinfo, currentpackage):        
        #TODO: Allow configuring which of these show and don't
        
        #Can be themed?
        if "canusethemes" in packageinfo:
            if packageinfo["canusethemes"] == 0: #No
                self.add_message("minorwarn", "This application will not follow your appearance settings and cannot be themed", self.temp_dummy_pressed, "Learn more")
            elif packageinfo["canusethemes"] == 2: #Yes, but manually enabled
                self.add_message("info", "This application can follow your appearance settings but does not by default", self.temp_dummy_pressed, "Learn more")
            elif packageinfo["canusethemes"] == 3: #Yes, except Feren OS's style
                #TODO: Appearance check for Feren OS style
                self.add_message("minorwarn", "This application will not follow your current appearance settings", self.temp_dummy_pressed, "Learn more")
            elif packageinfo["canusethemes"] == 4: #Yes, but manually enabled
                self.add_message("info", "This application uses its own themes, and therefore will not follow your appearance settings", self.temp_dummy_pressed, "Learn more")
            elif packageinfo["canusethemes"] == 5: #LibAdwaita, so no TODO: Have explanation button take to explanation on LibAdwaita
                self.add_message("minorwarn", "This application forces its own theme, so will not follow your appearance settings", self.temp_dummy_pressed, "Learn more")
            elif packageinfo["canusethemes"] == 6: #LibGranite, so no TODO: Have explanation button take to explanation on LibGranite
                self.add_message("minorwarn", "This application forces its own theme, so will not follow your appearance settings", self.temp_dummy_pressed, "Learn more")
                
        #Can be used on touchscreens?
        if "canusetouchscreen" in packageinfo:
            if packageinfo["canusetouchscreen"] == 0: #No
                self.add_message("warn", "This application does not currently support touchscreens") #TODO: Add button once standards checks system is implemented
            elif packageinfo["canusetouchscreen"] == 2: #Yes, but partially
                self.add_message("minorwarn", "This application partially supports touchscreens")
                
        #Can use accessibility?
        if "canuseaccessibility" in packageinfo:
            if packageinfo["canuseaccessibility"] == False: #No
                self.add_message("warn", "You may run into issues with this application if you use Accessibility features") #TODO: Add button once standards checks system is implemented
                
        #Can use DPI scaling?
        if "canusedpiscaling" in packageinfo:
            if packageinfo["canusedpiscaling"] == False: #No
                self.add_message("warn", "This application does not scale to your screen resolution") #TODO: Add button once standards checks system is implemented
                
        #Can use on Phone?
        if "canuseonphone" in packageinfo: #TODO: Phone check
            if packageinfo["canuseonphone"] == False: #No
                self.add_message("warn", "This application is not designed for use on phones") #TODO: Add button once standards checks system is implemented
                
        #Official application?
        if "isofficial" in packageinfo:
            if packageinfo["isofficial"] == False: #No
                self.add_message("warn", "This application is not officially published from this source", self.temp_dummy_pressed, "Learn more")
    
    def temp_dummy_pressed(self, gtk_widget): #TODO: Remove once there's Learn more windows
        print("DEBUG: Dummy press event")
    
        
    def add_source_information(self, modulename, currentpackage):
        thread = Thread(target=self._add_source_information,
                            args=(modulename, currentpackage))
        thread.start()
    
    def _add_source_information(self, packageinfo, currentpackage): #TODO: Move this into using the package store data from the package management module
        GLib.idle_add(self.pkgpage_images.set_label, "Images: " + str(packageinfo["images"]))
        GLib.idle_add(self.pkgpage_description.set_label, "Description: " + str(packageinfo["description"]))
        GLib.idle_add(self.pkgpage_category.set_label, "Category: " + str(packageinfo["category"]))
        GLib.idle_add(self.pkgpage_website.set_label, "Website: " + str(packageinfo["website"]))
        GLib.idle_add(self.pkgpage_donateurl.set_label, "Donate URL: " + str(packageinfo["donateurl"]))
        
        GLib.idle_add(self.pkgpage_author.set_label, "Author: " + str(packageinfo["author"]))
        GLib.idle_add(self.pkgpage_bugsurl.set_label, "Bugs URL: " + str(packageinfo["bugreporturl"]))
        GLib.idle_add(self.pkgpage_tosurl.set_label, "TOS URL: " + str(packageinfo["tosurl"]))
        GLib.idle_add(self.pkgpage_privpolurl.set_label, "Privacy Policy URL: " + str(packageinfo["privpolurl"]))
        
        GLib.idle_add(self.add_warnings, packageinfo, currentpackage)
        
    
    def change_source(self, currentpackage, source):
        thread = Thread(target=self._change_source,
                            args=(currentpackage, source))
        thread.start()
        
    def _change_source(self, currentpackage, source):        
        while self.packagepagemessages != []: #Tried using the conventional for items in list method, but it kept skipping loads of them
            for subitem in self.packagepagemessages[0].get_children():
                GLib.idle_add(subitem.destroy,)
            GLib.idle_add(self.packagepagemessages[0].get_parent().destroy,)
            GLib.idle_add(self.packagepagemessages[0].destroy,)
            self.packagepagemessages.pop(0)
            
        currentmodule, currenttype, currentsource = self.AppDetailsHeader.source_ids[self.AppDetailsHeader.app_source_dropdown.get_active()].split(":")
            
        packageinfo = self.storebrain.get_generic_item_info(currentpackage, currenttype)
        packageinfo = self.storebrain.dict_recurupdate(packageinfo, self.storebrain.get_item_info_specific(currentpackage, currenttype, currentsource))
        
        self.add_source_information(packageinfo, currentpackage)
        self.AppDetailsHeader.populate(packageinfo, currentpackage)
        
        currentstatus = None
        if currentstatus == None and currentmodule in self.storebrain.tasks.currenttasks and self.storebrain.tasks.currenttasks[currentmodule] != {}: #Check 1 for Status: If package is current item in queue
            if self.storebrain.tasks.currenttask[currentmodule] != {} and self.storebrain.tasks.currenttask[currentmodule]["packagename"] == currentpackage:
                currentstatus = 901
        if currentstatus == None and currentmodule in self.storebrain.tasks.currenttasks: #Check 2 for Status: If package is in queue
            for item in self.storebrain.tasks.currenttasks[currentmodule]:
                if item.split(":")[2] == currentpackage:
                    currentstatus = 900
        if currentstatus == None:
            currentstatus = self.storebrain.pkgmgmt_modules[currentmodule].get_status(currentpackage, currenttype, currentsource)
        
        self.AppDetailsHeader.update_buttons(currentstatus)
        
        self.AppDetailsHeader.populate_subsources(currentpackage, source)
    
    
    def goto_packagepage(self, packagename):
        thread = Thread(target=self._goto_packagepage,
                            args=(packagename,))
        thread.start()
        
    def _goto_packagepage(self, packagename):
        self.current_item_viewed = packagename       
        GLib.idle_add(self.set_visible_child, self.sw4)
    
    
    def on_packagepage(self):
        thread = Thread(target=self._on_packagepage,
                            args=())
        thread.start()
    
    def on_packagepage(self):
        self.AppDetailsHeader.populate_sources(self.current_item_viewed)
    
    
    def populate_mainpage(self):
        thread = Thread(target=self._populate_mainpage,
                            args=())
        thread.start()
    
    def _populate_mainpage(self):
        #TODO: Split into sections
        data = self.storebrain.pkginfo_modules[self.storebrain.generic_module].pkg_categoryids
        for category in data:
            for pkgname in data[category]:
                btn = AppItemButton(pkgname, self.storebrain, False)
                btn.connect("clicked", self._btn_goto_packageview, pkgname)
                if category.startswith("ice-"):
                    GLib.idle_add(self.websitesitems.insert, btn, -1)
                elif category.startswith("themes-"):
                    GLib.idle_add(self.themesitems.insert, btn, -1)
                else:
                    GLib.idle_add(self.appsitems.insert, btn, -1)
    
    
    def populate_searchpage(self, searchresults):
        thread = Thread(target=self._populate_searchpage,
                            args=(searchresults,))
        thread.start()
    
    def _populate_searchpage(self, searchresults):
        #Destroy the children first (no actual children were harmed in the making of this program) (according to doc, destroying containers destroys children recursively)
        if self.searchresults != None:
            GLib.idle_add(self.searchresults.destroy,)
        self.searchresults = Gtk.FlowBox()
        GLib.idle_add(self.searchresults.set_min_children_per_line, 1)
        GLib.idle_add(self.searchresults.set_max_children_per_line, 1)
        GLib.idle_add(self.searchresults.set_row_spacing, 4)
        GLib.idle_add(self.searchresults.set_homogeneous, True)
        GLib.idle_add(self.searchresultscontainer.pack_start, self.searchresults, True, True, 0)
        
        for resulttype in searchresults:
            for item in searchresults[resulttype]:
                if "searchlabel" in searchresults[resulttype][item]:
                    lbl = Gtk.Label(searchresults[resulttype][item]["searchlabel"])
                    GLib.idle_add(self.searchresults.insert, lbl, 0) #Insert at top
                    
                    
                else:                    
                    btn = AppItemButton(item, self.storebrain, False)
                    btn.connect("clicked", self._btn_goto_packageview, item)
                    GLib.idle_add(self.searchresults.insert, btn, -1)
            
        GLib.idle_add(self.searchresultscontainer.show_all,)
    
            
    def refresh_tasks(self):
        thread = Thread(target=self._refresh_tasks,
                            args=())
        thread.start()
        
    def _refresh_tasks(self):
        print("DEBUG: GUI Refreshing Tasks")
        #Destroy the children first (no actual children were harmed in the making of this program) (according to doc, destroying containers destroys children recursively)
        if self.tasksitems != None:
            GLib.idle_add(self.tasksitems.destroy,)
        self.tasksitems = Gtk.FlowBox()
        GLib.idle_add(self.tasksitems.set_min_children_per_line, 1)
        GLib.idle_add(self.tasksitems.set_max_children_per_line, 1)
        GLib.idle_add(self.tasksitems.set_row_spacing, 4)
        GLib.idle_add(self.tasksitems.set_homogeneous, True)
        GLib.idle_add(self.tasksitemscontainer.pack_start, self.tasksitems, True, True, 0)
        
        itemsdone = 0
        if len(self.storebrain.tasks.overalltasksorder) == 0:
            return #Don't continue if empty
        while itemsdone < len(self.storebrain.tasks.overalltasksorder): #We can't use python3's normal iteration as the dict size changes causing a SizeChanged exception
            if len(self.storebrain.tasks.overalltasksorder) == 0:
                self._refresh_tasks() #Run again, as tasks have finished during this
                return
            
            taskname = list(self.storebrain.tasks.overalltasksorder.keys())[itemsdone]
            task = self.storebrain.tasks.overalltasksorder[taskname]
        
            module, pkgtype, itemname = taskname.split(":")[0:3] #I guess python3 just omits the maximum ID, so 3 is used instead of 1 here (3 = operation id)
            btn = TaskItemButton(taskname, self.storebrain, task)
            btn.connect("clicked", self._btn_goto_packageview, itemname) #TODO: Teleportation to specific module
            GLib.idle_add(self.tasksitems.insert, btn, -1)
            
            itemsdone += 1
            
        GLib.idle_add(self.tasksitemscontainer.show_all,)
        
        GLib.idle_add(self.AppDetailsHeader.tasks_refresh_pkgpage,)
    
        
    def goto_page(self, page):
        thread = Thread(target=self._goto_page,
                            args=(page,))
        thread.start()
        
    def _goto_page(self, page):
        GLib.idle_add(self.set_visible_child, page)
    

    def _btn_goto_packageview(self, btn, packagename):
        GLib.idle_add(self.goto_packagepage, packagename)
    
        
    def searchbar_search(self, btn):
        thread = Thread(target=self._searchbar_search,
                            args=(btn,))
        thread.start()

    def _searchbar_search(self, btn):
        if self.searchbar.get_text() == "":
            self._populate_searchpage({'exactmatch': {}, 'begins': {}, 'contains': {}, 'ends': {}})
        else:
            results = self.storebrain.item_search(self.searchbar.get_text())
            self._populate_searchpage(results)



####Store Window
class main(object):    
    def __init__(self, storebrain):
        self.storebrain = storebrain

        #systemstate.first_run = self._check_first_run()
        #systemstate.first_run = True

        self._start_page = 'home.html'

    def build_app_post_splashscreen(self, mainwindow, maintoolbar, mv):
        GLib.idle_add(self._build_app_post_splashscreen, mainwindow, maintoolbar, mv)
        
        
        
        mv.populate_mainpage()

    def _build_app_post_splashscreen(self, mainwindow, maintoolbar, mv):
        # build rest of window
        box_application_header = AppDetailsHeader(self.storebrain)
        #box_application_header.set_visible(False)
        box_application_header.parent_window = self.w
        # add the box to the parent window and show
        mainwindow.pack_start(maintoolbar, False, True, 0)
        mainwindow.pack_start(box_application_header, False, True, 0)
        mainwindow.pack_end(mv, True, True, 0)
        mv.AppDetailsHeader = box_application_header
        mv.AppDetailsHeader.mv = mv
        self.w.show_all()

    def _build_app(self):        
        # build window
        self.w = Gtk.Window()
        self.w.set_position(Gtk.WindowPosition.CENTER)
        self.w.set_title("Storium Demo - GUI Module")
        self.w.set_default_size(850, 640)
        self.w.set_size_request(850, 540)
        #self.w.set_resizable(False)

        #This allows Store to be natively recognised as an application associated with its .desktop file
        GLib.set_prgname('/usr/bin/feren-storium')
        
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
        
        mv.header = header
        
        mv.storebrain = self.storebrain
        mv.modulebrain = self
        
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

    def init(self):
        GObject.threads_init()
        
        self._build_app()
        Gtk.main()
        
    def refresh_tasks(self):
        self.mainpage.refresh_tasks()

    def _gohome_pressed(self, gtk_widget):
        self.mainpage.goto_page(self.mainpage.sw)

    def _search_pressed(self, gtk_widget):
        self.mainpage.goto_page(self.mainpage.sw3)

    def _status_pressed(self, gtk_widget):
        self.mainpage.goto_page(self.mainpage.sw2)

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
            self.mainpage.searchbar.grab_focus()
        elif self.mainpage.get_visible_child() == self.mainpage.sw4: # Package Page
            self.mainpage.on_packagepage()
        else:
            self.gohome_btn.set_active(True)
            
        #Now unblock the signals
        self.gohome_btn.handler_unblock(self.gohome_handle_id)
        self.status_btn.handler_unblock(self.status_handle_id)
        self.search_btn.handler_unblock(self.search_handle_id)
        
        self.mainpage.AppDetailsHeader.set_visible(self.mainpage.get_visible_child() == self.mainpage.sw4)
        #if self.mainpage.get_visible_child() != self.mainpage.sw4:
            #self.mainpage.current_item_viewed = ""
            #self.mainpage.current_source_viewed = ""
        
    def set_progress(self, packagename, packagetype, value):
        if self.mainpage.current_item_viewed == packagename and self.mainpage.current_source_viewed == packagetype:
            self.mainpage.AppDetailsHeader.set_progress(value)
        
    

    def _check_first_run(self):
        pass