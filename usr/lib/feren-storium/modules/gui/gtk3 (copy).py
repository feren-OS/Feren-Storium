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

from gi.repository import WebKit2, Gtk, Gio, Gdk, GLib, Pango, GObject, GdkPixbuf
from threading import Thread
from queue import Queue, Empty
from notify2 import Notification, init as NotifyInit



####Application Details Header
class AppDetailsHeader(Gtk.Box):

    def __init__(self):
        
        Gtk.Box.__init__(self)
        
        self.get_style_context().add_class("only-toolbar")

        self.current_package_type = ""
        
        box_application_namedesc = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        #Application Icon
        self.app_iconimg = Gtk.Image()
        self.app_iconimg_loading = Gtk.Spinner()
        self.app_iconimg_stack = Gtk.Stack()
        self.app_iconimg_loading_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.app_iconimg_loading_box.set_center_widget(self.app_iconimg_loading)
        self.app_iconimg_stack.add_named(self.app_iconimg_loading_box, "Loading")
        self.app_iconimg_stack.add_named(self.app_iconimg, "AppIcon")
        self.app_iconimg_stack.set_visible_child(self.app_iconimg)
        
        #Application Title
        self.app_title = Gtk.Label()
        self.app_title.get_style_context().add_class("14scale")
        
        #Application Description
        self.app_desc = Gtk.Label()

        #Sources labels
        self.sources_label_stack = Gtk.Stack()
        self.sources_label_package = Gtk.Label(label=("Source: "))
        self.sources_label_ice = Gtk.Label(label=("Browser: "))
        self.sources_label_stack.add_named(self.sources_label_package, "PackageSource")
        self.sources_label_stack.add_named(self.sources_label_ice, "IceSource")
        
        #Application Management Buttons
        self.app_mgmt_button = Gtk.Stack()
        self.app_mgmt_installbtn = Gtk.Button(label=("Install"))
        self.app_mgmt_installunavailbtn = Gtk.Button(label=("Install..."))
        self.app_mgmt_removebtn = Gtk.Button(label=("Remove"))
        self.app_mgmt_updatebtn = Gtk.Button(label=("Update"))
        self.app_mgmt_installbtn.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        self.app_mgmt_installunavailbtn.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        self.app_mgmt_updatebtn.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        self.app_mgmt_removebtn.get_style_context().add_class(Gtk.STYLE_CLASS_DESTRUCTIVE_ACTION)
        self.app_mgmt_preparingbtns = Gtk.Spinner()
        self.app_mgmt_button.add_named(self.app_mgmt_preparingbtns, "Preparing")
        self.app_mgmt_button.add_named(self.app_mgmt_installbtn, "Standard")
        self.app_mgmt_button.add_named(self.app_mgmt_installunavailbtn, "InstallRepo")
        self.app_mgmt_button.add_named(self.app_mgmt_removebtn, "Remove")
        self.app_mgmt_button.set_visible_child(self.app_mgmt_preparingbtns)
        #self.app_mgmt_preparingbtns.start()
        
        #Application Source Combobox
        self.app_source_dropdown_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.app_source_dropdown_box.pack_start(self.sources_label_stack, False, False, 0)
        self.app_source_dropdown = Gtk.ComboBox()
        #NOTE TO SELF: NEVER put this in the dropdown refreshing code - it'll cause duplicated labels
        cell = Gtk.CellRendererText()
        self.app_source_dropdown.pack_start(cell, True)
        self.app_source_dropdown.add_attribute(cell, "text", 0)
        self.app_source_dropdown.connect("changed", self.on_source_dropdown_changed)
        self.app_source_dropdown_box.pack_end(self.app_source_dropdown, False, False, 0)
        
        #Progress Bar
        self.app_mgmt_progress = Gtk.ProgressBar()
        self.app_mgmt_progress_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.app_mgmt_progress_box.set_center_widget(self.app_mgmt_progress)
        
        #Pending Status
        self.app_mgmt_pending_box = Gtk.Box(spacing=8)
        app_mgmt_pending_labelbox = Gtk.VBox()
        app_mgmt_pending_label = Gtk.Label(label="Queued")
        app_mgmt_pending_cancel = Gtk.Button(label="Cancel")
        app_mgmt_pending_cancel.connect('clicked', self.cancel_from_queue_pressed)
        app_mgmt_pending_labelbox.set_center_widget(app_mgmt_pending_label)
        self.app_mgmt_pending_box.pack_start(app_mgmt_pending_labelbox, False, False, 0)
        self.app_mgmt_pending_box.pack_end(app_mgmt_pending_cancel, False, False, 0)
        self.app_mgmt_button.add_named(self.app_mgmt_pending_box, "Pending")
        
        #Make sure application name and short descriptions are left-aligned in there
        app_title_box = Gtk.Box()
        app_desc_box = Gtk.Box()
        app_title_box.pack_start(self.app_title, False, False, 0)
        app_desc_box.pack_start(self.app_desc, False, False, 0)
        
        #Make the column for application name and short description
        box_application_namedesc.pack_start(app_title_box, False, False, 0)
        box_application_namedesc.pack_end(app_desc_box, False, False, 0)
        
        #Stuff for centering items vertically
        centering_titledesc_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        centering_titledesc_box.set_center_widget(box_application_namedesc)
        centering_btnactions_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        inside_btnactions_box = Gtk.Box()
        inside_btnactions_box.pack_start(self.app_source_dropdown_box, False, False, 4)
        inside_btnactions_box.pack_start(self.app_mgmt_progress_box, False, False, 4)
        inside_btnactions_box.pack_start(self.app_mgmt_updatebtn, False, False, 4)
        inside_btnactions_box.pack_start(self.app_mgmt_button, False, False, 4)
        
        centering_btnactions_box.set_center_widget(inside_btnactions_box)
        
        #Header building
        self.pack_start(self.app_iconimg_stack, False, False, 8)
        self.pack_start(centering_titledesc_box, False, True, 4)
        self.pack_end(centering_btnactions_box, False, True, 4)
        
        #Margins
        self.app_iconimg.set_margin_top(8)
        self.app_iconimg.set_margin_bottom(8)
        
        #Header image temp
        desired_width = 48
        desired_height = 48
        icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file("/usr/share/feren-os/logos/blank.png")
        icon_pixbuf = icon_pixbuf.scale_simple(desired_width, desired_height, GdkPixbuf.InterpType.BILINEAR)
        self.app_iconimg.set_from_pixbuf(icon_pixbuf)
        
        #Button Assignment
        self.app_mgmt_installbtn.connect('clicked', self.install_pressed)
        self.app_mgmt_installunavailbtn.connect('clicked', self.install_with_source_pressed)
        self.app_mgmt_updatebtn.connect('clicked', self.update_pressed)
        self.app_mgmt_removebtn.connect('clicked', self.remove_pressed)
        
        #Variables
        self.current_package = ""
        self.sources_visible = True
        
        #Initialize Management
        self.APTMgmt = APTMgmt(classnetwork)
        classnetwork.APTMgmt = self.APTMgmt
        self.ICEMgmt = ICEMgmt(classnetwork)
        classnetwork.ICEMgmt = self.ICEMgmt

        self.app_mgmt_button.set_visible_child(self.app_mgmt_preparingbtns)
        self.app_mgmt_updatebtn.set_visible(False)
        
        GObject.threads_init()
        
    def set_current_package(self, packagename):
        self.current_package = packagename

    def show(self):
        self.set_visible(True)
    
    def hide(self):
        self.set_visible(False)
    
    def set_icon(self, iconuri, packagetoview):
        tempdir = classnetwork.GlobalVariables.storagetemplocation
        
        self.app_iconimg_loading.start()
        self.app_iconimg_stack.set_visible_child(self.app_iconimg_loading_box)
        #Set the icon shown on the package header
                
        desired_width = 48
        desired_height = 48
        try:
            if not iconuri.startswith("file://"):
                #Download the application icon
                if not os.path.isfile(tempdir+"/"+packagetoview+"-icon"):
                    urllib.request.urlretrieve(iconuri, tempdir+"/"+packagetoview+"-icon")
                #Set it as the icon in the Store
                icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file(tempdir+"/"+packagetoview+"-icon")
            else:
                #Set it as the icon in the Store
                icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file(iconuri.split('file://')[1])
        except Exception as exceptionstring:
            print("Could not retrieve icon for", packagetoview, "-", exceptionstring)
            #TODO: Change to store-missing-icon
            icon_pixbuf = GdkPixbuf.Pixbuf.new_from_file("/usr/share/icons/Inspire/256/apps/feren-store.png")
        icon_pixbuf = icon_pixbuf.scale_simple(desired_width, desired_height, GdkPixbuf.InterpType.BILINEAR)
        self.app_iconimg.set_from_pixbuf(icon_pixbuf)
        self.app_iconimg_stack.set_visible_child(self.app_iconimg)
        self.app_iconimg_loading.stop()
    
    def set_app_details(self, apprname, appshortdesc):
        #Set the application real name (apprname) and short description (appshortdesc) on the package header
        self.app_title.set_label(apprname)
        self.app_desc.set_label(appshortdesc)
    
    def set_package_type(self, packagesource):
        #Set the application source to the one selected in the source dropdown
        self.current_package_type = packagesource

    def get_package_type(self):
        return self.current_package_type
    
    def get_sources(self, package):
        iface_list_store = Gtk.ListStore(GObject.TYPE_STRING)
        amount_of_sources = 0

        if package.startswith("feren-ice-ssb-"):
            GLib.idle_add(self.sources_label_stack.set_visible_child, self.sources_label_ice)
            #TODO: Put preferred browser at top of list
            if os.path.isfile("/usr/bin/vivaldi-stable"):
                iface_list_store.append(["Vivaldi"])
                amount_of_sources += 1
            if os.path.isfile("/usr/bin/google-chrome"):
                iface_list_store.append(["Google Chrome"])
                amount_of_sources += 1
            if os.path.isfile("/usr/bin/chromium-browser"):
                iface_list_store.append(["Chromium"])
                amount_of_sources += 1
            if os.path.isfile("/usr/bin/firefox"):
                iface_list_store.append(["Mozilla Firefox"])
                amount_of_sources += 1
            if classnetwork.flatpakmgmtimported == True and os.path.isfile("/var/lib/flatpak/overrides/org.mozilla.firefox"):
                iface_list_store.append(["M.Firefox (Flathub)"]) #TODO: Add userland support here
                amount_of_sources += 1
            if os.path.isfile("/usr/bin/brave-browser"):
                iface_list_store.append(["Brave"])
                amount_of_sources += 1
        elif package == "debfile":
            friendlysourcename = ApplicationSourceTranslator().TranslateToHumanReadable("standard")
            if friendlysourcename:
                iface_list_store.append([friendlysourcename])
                amount_of_sources += 1
        else:
            GLib.idle_add(self.sources_label_stack.set_visible_child, self.sources_label_package)
            #Using the JSON Data from sources/packages.json, populate the sources dropdown according to what's available
            sourcenames, orderofsources = [classnetwork.JSONReader.availablesources[package]["apt"], classnetwork.JSONReader.availablesources[package]["flatpak"], classnetwork.JSONReader.availablesources[package]["snap"]], classnetwork.JSONReader.availablesources[package]["order-of-importance"]
            
            for sourcename in orderofsources:
                if sourcename == "apt":
                    #apt source
                    friendlysourcename = ApplicationSourceTranslator().TranslateToHumanReadable(sourcenames[0])
                    if friendlysourcename:
                        iface_list_store.append([friendlysourcename])
                        amount_of_sources += 1
                elif sourcename == "flatpak":
                    #flatpak source
                    friendlysourcename = ApplicationSourceTranslator().TranslateToHumanReadable(sourcenames[1])
                    if friendlysourcename:
                        iface_list_store.append([friendlysourcename])
                        amount_of_sources += 1
                elif sourcename == "snap":
                    #snap source
                    friendlysourcename = ApplicationSourceTranslator().TranslateToHumanReadable(sourcenames[2])
                    if friendlysourcename:
                        iface_list_store.append([friendlysourcename])
                        amount_of_sources += 1
        
        self.app_source_dropdown.set_model(iface_list_store)
        self.app_source_dropdown.set_active(0)
        if amount_of_sources <= 1:
            self.app_source_dropdown_box.set_visible(False)
            self.sources_visible = False
        else:
            self.app_source_dropdown_box.set_visible(True)
            self.sources_visible = True
            
    def change_button_state(self, newstate, disableremove):
        thread = Thread(target=self._change_button_state,
                        args=(newstate, disableremove))
        thread.daemon = True
        thread.start()
        
    def _change_button_state(self, newstate, disableremove):
        GLib.idle_add(self.__change_button_state, newstate, disableremove)
    
    def __change_button_state(self, newstate, disableremove):
        #Change button state between 4 states:
        #uninstalled: Install is visible
        #sourcemissing: Install... is visible
        #installed: Remove is visible
        #updatable: Update and Remove are visible
        
        self.app_mgmt_installbtn.set_sensitive(False)
        self.app_mgmt_installunavailbtn.set_sensitive(False)
        self.app_mgmt_removebtn.set_sensitive(False)
        self.app_mgmt_updatebtn.set_sensitive(False)
        
        if newstate == "loading":
            self.app_mgmt_progress_box.set_visible(False)
            self.app_mgmt_button.set_visible(True)
            self.app_mgmt_preparingbtns.start()
            self.app_mgmt_updatebtn.set_visible(False)
            self.app_mgmt_button.set_visible_child(self.app_mgmt_preparingbtns)
        elif newstate == "queued":
            self.app_mgmt_progress_box.set_visible(False)
            self.app_mgmt_button.set_visible(True)
            self.app_mgmt_preparingbtns.start()
            self.app_mgmt_updatebtn.set_visible(False)
            self.app_mgmt_button.set_visible_child(self.app_mgmt_pending_box)
        elif newstate == "busy":
            #TODO: Add cancel button for non-running tasks once the tasks system is implemented
            self.app_source_dropdown_box.set_visible(False)
            self.app_mgmt_progress_box.set_visible(True)
            self.app_mgmt_button.set_visible(False)
        elif newstate == "uninstalled":
            self.app_mgmt_progress_box.set_visible(False)
            self.app_mgmt_button.set_visible(True)
            self.app_mgmt_installbtn.set_sensitive(True)
            self.app_mgmt_updatebtn.set_visible(False)
            self.app_mgmt_button.set_visible_child(self.app_mgmt_installbtn)
            self.app_mgmt_preparingbtns.stop()
        elif newstate == "sourcemissing":
            self.app_mgmt_progress_box.set_visible(False)
            self.app_mgmt_button.set_visible(True)
            self.app_mgmt_installunavailbtn.set_sensitive(True)
            self.app_mgmt_updatebtn.set_visible(False)
            self.app_mgmt_button.set_visible_child(self.app_mgmt_installunavailbtn)
            self.app_mgmt_preparingbtns.stop()
        elif newstate == "installed":
            self.app_mgmt_progress_box.set_visible(False)
            self.app_mgmt_button.set_visible(True)
            if disableremove == False:
                self.app_mgmt_removebtn.set_sensitive(True)
            self.app_mgmt_updatebtn.set_visible(False)
            self.app_mgmt_button.set_visible_child(self.app_mgmt_removebtn)
            self.app_mgmt_preparingbtns.stop()
        elif newstate == "updatable":
            self.app_mgmt_progress_box.set_visible(False)
            self.app_mgmt_button.set_visible(True)
            if disableremove == False:
                self.app_mgmt_removebtn.set_sensitive(True)
            self.app_mgmt_updatebtn.set_sensitive(True)
            self.app_mgmt_updatebtn.set_visible(True)
            self.app_mgmt_button.set_visible_child(self.app_mgmt_removebtn)
            self.app_mgmt_preparingbtns.stop()

    def switch_source(self, package, packagetype, autosourceswitch=True):
        thread = Thread(target=self._switch_source,
                        args=(package, packagetype, autosourceswitch))
        thread.daemon = True
        thread.start()
        
    def on_source_dropdown_changed(self, combobox):
        if self.current_package == "debfile":
            self.current_package_type = "apt"
        elif self.current_package_type != "ice":
            self.current_package_type = classnetwork.JSONReader.availablesources[self.current_package]["order-of-importance"][combobox.get_active()]
        self.switch_source(self.current_package, self.current_package_type, False)

    def _switch_source(self, package, packagetype, autosourceswitch=True):
        if self.current_package == "":
            return #Don't do anything if we're not currently in the package view area
        print("Switch Source:", packagetype)
        # Don't refresh the source details, etc if we aren't looking at the package - it'll mess up the GUI otherwise as if this was ran for X package while viewing Y package it'd change some of the details shown for Y package to ones for X package on that source
        if self.current_package != package:
            return
        # If it's the current package but the dropdown isn't on this source, let's abort this code after triggering the part of this code that responds to dropdown value changes (thus making this run again) by changing the dropdown value to the right value
        if self.current_package_type != packagetype:
            if autosourceswitch == True:
                GLib.idle_add(self.app_source_dropdown.set_active(classnetwork.JSONReader.availablesources[package]["order-of-importance"].index(packagetype)))
            return

        #Now change the appropriate items of the page
        GLib.idle_add(classnetwork.AppView.update_insite_information, package, packagetype)


        #Get the state of the package for changing the buttons presented to the user accordingly - is it installed? does it need an update?
        #packagetype is whether it's native, snap, ice or flatpak
        if self.current_package_type != "ice" and self.current_package != "debfile":
            mgmtpkgname = classnetwork.JSONReader.getNameFromInternal(package, self.current_package_type)
        GLib.idle_add(self.change_button_state, "loading", False)
        if self.current_package_type == "apt" and self.current_package != "debfile":
            if classnetwork.TasksMgmt.currenttask.startswith("apt:") and classnetwork.TasksMgmt.currenttask.endswith(":"+package):
                GLib.idle_add(self.change_button_state, "busy", False)
                return
            elif ("apt:inst:"+package in classnetwork.TasksMgmt.currenttasks or "apt:upgr:"+package in classnetwork.TasksMgmt.currenttasks or "apt:rm:"+package in classnetwork.TasksMgmt.currenttasks) and not (classnetwork.TasksMgmt.currenttask.startswith("apt:") and classnetwork.TasksMgmt.currenttask.endswith(":"+package)):
                GLib.idle_add(self.change_button_state, "queued", False)
                return
            ifinstalled = APTChecks.checkinstalled(mgmtpkgname)
            if self.current_package == package:
                if ifinstalled == 1: #TODO: Change blacklisting of Remove functionality to if the package is in a list of them
                    GLib.idle_add(self.change_button_state, "installed", mgmtpkgname == "feren-store")
                    return
                elif ifinstalled == 3:
                    GLib.idle_add(self.change_button_state, "updatable", mgmtpkgname == "feren-store")
                    return
                elif ifinstalled == 404: #TODO: Move this to if it can't find any usable sources
                    print("Cannot find", mgmtpkgname)
                    GLib.idle_add(classnetwork.StoreWindow.pages.set_visible_child, classnetwork.StoreWindow.nfpage)
                    GLib.idle_add(self.hide)
                    return
                else:
                    if ifinstalled != 404 and APTChecks.checkneedsrepo(mgmtpkgname) != []:
                        GLib.idle_add(self.change_button_state, "sourcemissing", mgmtpkgname == "feren-store")
                        return
                    else:
                        GLib.idle_add(self.change_button_state, "uninstalled", False)
                        return
        elif self.current_package_type == "apt" and self.current_package == "debfile":
            mgmtpkgname = classnetwork.AppView._deb.pkgname
            if "aptdeb:inst:"+sys.argv[1] == classnetwork.TasksMgmt.currenttask or "apt:upgr:"+mgmtpkgname == classnetwork.TasksMgmt.currenttask or "apt:rm:"+mgmtpkgname == classnetwork.TasksMgmt.currenttask:
                GLib.idle_add(self.change_button_state, "busy", False)
                return
            elif "aptdeb:inst:"+sys.argv[1] in classnetwork.TasksMgmt.currenttasks or "apt:upgr:"+mgmtpkgname in classnetwork.TasksMgmt.currenttasks or "apt:rm:"+mgmtpkgname in classnetwork.TasksMgmt.currenttasks:
                GLib.idle_add(self.change_button_state, "queued", False)
                return
            ifinstalled = APTChecks.checkinstalled(mgmtpkgname)
            if self.current_package == package:
                if ifinstalled == 1: #TODO: Change blacklisting of Remove functionality to if the package is in a list of them
                    GLib.idle_add(self.change_button_state, "installed", mgmtpkgname == "feren-store")
                    return
                elif ifinstalled == 3:
                    GLib.idle_add(self.change_button_state, "updatable", mgmtpkgname == "feren-store")
                    return
                else:
                    if ifinstalled != 404 and APTChecks.checkneedsrepo(mgmtpkgname) != []: #TODO: Make checkneedsrepo support DEBs
                        GLib.idle_add(self.change_button_state, "sourcemissing", mgmtpkgname == "feren-store")
                        return
                    else:
                        GLib.idle_add(self.change_button_state, "uninstalled", False)
                        return
        
        
        elif self.current_package_type == "snap":
            if classnetwork.TasksMgmt.currenttask.startswith("snap:") and classnetwork.TasksMgmt.currenttask.endswith(":"+package):
                GLib.idle_add(self.change_button_state, "busy", False)
                return
            elif ("snap:inst:"+package in classnetwork.TasksMgmt.currenttasks or "snap:upgr:"+package in classnetwork.TasksMgmt.currenttasks or "snap:rm:"+package in classnetwork.TasksMgmt.currenttasks) and not (classnetwork.TasksMgmt.currenttask.startswith("snap:") and classnetwork.TasksMgmt.currenttask.endswith(":"+package)):
                GLib.idle_add(self.change_button_state, "queued", False)
                return
            if classnetwork.snapmgmtimported == True:
                ifinstalled = classnetwork.SnapChecks.checkinstalled(mgmtpkgname)
                if self.current_package == package:
                    if ifinstalled == 1:
                        GLib.idle_add(self.change_button_state, "installed", False)
                        return
                    else:
                        GLib.idle_add(self.change_button_state, "uninstalled", False)
                        return
            else:
                GLib.idle_add(self.change_button_state, "sourcemissing", False)
                return
        
        elif self.current_package_type == "flatpak":
            if classnetwork.TasksMgmt.currenttask.startswith("flatpak:") and classnetwork.TasksMgmt.currenttask.endswith(":"+package):
                GLib.idle_add(self.change_button_state, "busy", False)
                return
            elif ("flatpak:inst:"+package in classnetwork.TasksMgmt.currenttasks or "flatpak:upgr:"+package in classnetwork.TasksMgmt.currenttasks or "flatpak:rm:"+package in classnetwork.TasksMgmt.currenttasks) and not (classnetwork.TasksMgmt.currenttask.startswith("flatpak:") and classnetwork.TasksMgmt.currenttask.endswith(":"+package)):
                GLib.idle_add(self.change_button_state, "queued", False)
                return
            if classnetwork.flatpakmgmtimported == True:
                ifinstalled = classnetwork.FlatpakChecks.checkinstalled(mgmtpkgname, False) #TODO: Add userland Flatpak support (the 'False' = System-wide)
                if self.current_package == package:
                    if ifinstalled == 1 or ifinstalled == 3:
                        GLib.idle_add(self.change_button_state, "installed", False)
                        return
                    else:
                        if classnetwork.FlatpakChecks.checkneedsrepo(mgmtpkgname, classnetwork.JSONReader.availablesources[package]["flatpak"].split("flatpak-")[1], False) != []:
                            GLib.idle_add(self.change_button_state, "sourcemissing", False)
                            return
                        else:
                            GLib.idle_add(self.change_button_state, "uninstalled", False)
                            return
            else:
                GLib.idle_add(self.change_button_state, "sourcemissing", False)
                return

        elif self.current_package_type == "ice":
            GLib.idle_add(self.app_source_dropdown_box.set_visible, False)
            GLib.idle_add(self.change_button_state, "loading", False)
            if os.path.isfile(os.path.expanduser("~")+"/.local/share/applications/feren-ice-ssb-"+package.split("feren-ice-ssb-")[1]+".desktop"):
                GLib.idle_add(self.change_button_state, "installed", False)
                return
            else:
                GLib.idle_add(self.change_button_state, "uninstalled", False)
                if self.sources_visible:
                    GLib.idle_add(self.app_source_dropdown_box.set_visible, True)
                return
                
    def on_installer_finished(self, package):
        #thread = Thread(target=self._on_installer_finished,
        #                args=(package,))
        #thread.daemon = True
        #thread.start()
        pass
    
    def _on_installer_finished(self, package):
        #Tried threads - just crashes
        #GLib.idle_add(self.__on_installer_finished, package)
        pass
            
    def __on_installer_finished(self, package):
        pass
    
    def install_with_source_pressed(self, button):
        #When you press 'Install...'
        pass
    
    def install_pressed(self, button):
        #When you press 'Install'
        self.change_button_state("loading", False)
        if self.current_package_type == "apt":
            if self.current_package == "debfile":
                self.APTMgmt.install_package(sys.argv[1])
            else:
                self.APTMgmt.install_package(self.current_package)
        elif self.current_package_type == "snap":
            classnetwork.SnapMgmt.install_package(self.current_package)
        elif self.current_package_type == "flatpak":
            classnetwork.FlatpakMgmt.install_package(self.current_package, False)
        elif self.current_package_type == "ice":
            tree_iter = self.app_source_dropdown.get_active_iter()
            if tree_iter is not None:
                model = self.app_source_dropdown.get_model()
                active_text = model[tree_iter][0]
                self.ICEMgmt.install(self.current_package, active_text)
    
    def update_pressed(self, button):
        #When you press 'Update'
        self.change_button_state("loading", False)
        if self.current_package_type == "apt":
            self.APTMgmt.upgrade_package(self.current_package)
        elif self.current_package_type == "flatpak":
            classnetwork.FlatpakMgmt.upgrade_package(self.current_package, False)
    
    def remove_pressed(self, button):
        #When you press 'Remove'
        self.change_button_state("loading", False)
        if self.current_package_type == "apt":
            self.APTMgmt.remove_package(self.current_package)
        elif self.current_package_type == "snap":
            classnetwork.SnapMgmt.remove_package(self.current_package)
        elif self.current_package_type == "flatpak":
            classnetwork.FlatpakMgmt.remove_package(self.current_package, False)
        elif self.current_package_type == "ice":
            self.ICEMgmt.remove(self.current_package)

    def cancel_from_queue_pressed(self, button):
        #TODO: Make this work irregardless of package manager
        if not (classnetwork.TasksMgmt.currenttask.startswith(self.current_package_type+":") and classnetwork.TasksMgmt.currenttask.endswith(":"+self.current_package)):
            for taskitem in classnetwork.TasksMgmt.currenttasks[:]:
                if taskitem.startswith(self.current_package_type+":") and taskitem.endswith(":"+self.current_package):
                    classnetwork.TasksMgmt.currenttasks.remove(taskitem)
                    classnetwork.TasksMgmt.gui_refresh_tasks()
                    self.switch_source(self.current_package, self.current_package_type)



####AppView (the website)
class AppView(WebKit2.WebView):

    def __init__(self):
        WebKit2.WebView.__init__(self)
        
        # Set WebKit background to the same as GTK
        #Update: Nevermind it goes black
        #self.set_background_color(Gdk.RGBA(0, 0, 0, 0))

        self.connect('load-changed', self._load_changed_cb)
        self.connect('context-menu', self._context_menu_cb)
        self.connect('notify::status', self.on_load_status_change)

        self.l_uri = None
        self.status_btn = None
        self.back_btn = None
        #self.set_zoom_level(0.90)

        #For the back button
        #TODO: Check this more rigorously
        self.back_button_history = ["home.html"]

        self.back_signal_handler = None
        
        self.current_package = ""
    
        
    def on_load_status_change(download, status):
        print(download, status)
        
        #self._push_config()
        
    def refresh_gtk_colors(self):
        """
        Updates the CSS on the page to use the colours from GTK.
        """
        window = Gtk.Window()
        style_context = window.get_style_context()

        def _rgba_to_hex(color):
           """
           Return hexadecimal string for :class:`Gdk.RGBA` `color`.
           """
           return "#{0:02x}{1:02x}{2:02x}".format(
                                            int(color.red   * 255),
                                            int(color.green * 255),
                                            int(color.blue  * 255))

        def _get_color(style_context, preferred_color, fallback_color):
            color = _rgba_to_hex(style_context.lookup_color(preferred_color)[1])
            if color == "#000000":
                color = _rgba_to_hex(style_context.lookup_color(fallback_color)[1])
            return color

        def _get_hex_variant(string, offset):
            """
            Converts hex input #RRGGBB to RGB and HLS to increase lightness independently
            """
            string = string.lstrip("#")
            rgb = list(int(string[i:i+2], 16) for i in (0, 2 ,4))

            # colorsys module converts to HLS to brighten/darken
            hls = colorsys.rgb_to_hls(rgb[0], rgb[1], rgb[2])
            newbright = hls[1] + offset
            newbright = min([255, max([0, newbright])])
            hls = (hls[0], newbright, hls[2])

            # Re-convert to rgb and hex
            newrgb = colorsys.hls_to_rgb(hls[0], hls[1], hls[2])

            def _validate(value):
                value = int(value)
                if value > 255:
                    return 255
                elif value < 0:
                    return 0
                return value

            newrgb = [_validate(newrgb[0]), _validate(newrgb[1]), _validate(newrgb[2])]
            newhex = '#%02x%02x%02x' % (newrgb[0], newrgb[1], newrgb[2])
            return newhex

        bg_color = _get_color(style_context, "theme_base_color_breeze", "theme_base_color")
        text_color = _get_color(style_context, "theme_fg_color_breeze", "theme_fg_color")
        selected_bg_color = _get_color(style_context, "theme_selected_bg_color_breeze", "theme_selected_bg_color")
        selected_text_color = _get_color(style_context, "theme_selected_fg_color_breeze", "theme_selected_fg_color")
        button_bg_color = _get_color(style_context, "theme_button_background_normal_breeze", "theme_bg_color")

        css = []
        css.append("--bg: " + bg_color)
        css.append("--text: " + text_color)
        css.append("--selected_bg: " + selected_bg_color)
        css.append("--selected_text: " + selected_text_color)
        css.append("--button_bg: linear-gradient(to bottom, {0}, {1})".format(
                                          _get_hex_variant(button_bg_color, 8),
                                          _get_hex_variant(button_bg_color, -8)))

        app.update_page("body", "append", "<style>:root {" + ";".join(css) + "}</style>")

        # For High Contrast theme
        if bg_color in ["#000", "#000000"]:
            app.update_page("body", "addClass", "bg-is-black")

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
        self.run_javascript('gotopage("'+self.back_button_history[-1]+'")')
        
    def _goto_page(self, page):
        #file = os.path.abspath(os.path.join(translations.get_pages_path(), page+".html"))
        file = os.path.abspath(os.path.join("/usr/share/feren-store-new/"+page+".html"))
        uri = 'file://' + urllib.request.pathname2url(file)
        self.load_uri(uri)
        
    def _goto_packageview(self, packagename):
        #file = os.path.abspath(os.path.join(translations.get_pages_path(), "packagepage.html"))
        self.run_javascript('gotopackage("'+packagename+'")')

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

    def _push_config(self):
        # TODO: push notification should be connected to angularjs and use a
        # broadcast event any suitable controllers will be able to listen and
        # respond accordingly, for now we just use jQuery to manually toggle
        current_page = app.current_page
                
        #Toggle block buttons first
        self.StoreGUI.gohome_btn.handler_block(self.StoreGUI.gohome_handle_id)
        self.StoreGUI.goapps_btn.handler_block(self.StoreGUI.goapps_handle_id)
        self.StoreGUI.gothemes_btn.handler_block(self.StoreGUI.gothemes_handle_id)
        self.StoreGUI.gowebsites_btn.handler_block(self.StoreGUI.gowebsites_handle_id)
        self.StoreGUI.status_btn.handler_block(self.StoreGUI.status_handle_id)
        #Do their toggles and then unblock
        self.StoreGUI.gohome_btn.set_active(False)
        self.StoreGUI.goapps_btn.set_active(False)
        self.StoreGUI.gothemes_btn.set_active(False)
        self.StoreGUI.gowebsites_btn.set_active(False)
        self.StoreGUI.status_btn.set_active(False)
        self.StoreGUI.gohome_btn.handler_unblock(self.StoreGUI.gohome_handle_id)
        self.StoreGUI.goapps_btn.handler_unblock(self.StoreGUI.goapps_handle_id)
        self.StoreGUI.gothemes_btn.handler_unblock(self.StoreGUI.gothemes_handle_id)
        self.StoreGUI.gowebsites_btn.handler_unblock(self.StoreGUI.gowebsites_handle_id)
        self.StoreGUI.status_btn.handler_unblock(self.StoreGUI.status_handle_id)

        ### Index Page ###
        if current_page == 'statuspage.html':
            pass

        if current_page.startswith('packagepage.html'):
            pass

    def _load_changed_cb(self, view, frame):
        self.refresh_gtk_colors()
        uri = str(self.get_uri())
        
        #By making this only run on a fully loaded page we prevent this thing running multiple times in one page load
        if self.get_estimated_load_progress() == 1.0:
            self.toggle_back(uri.rsplit('/', 1)[1] != "home.html")
            #Add page to history if it isn't the latest page in history
            if self.back_button_history[-1] != uri.rsplit('/', 1)[1] and uri.rsplit('/', 1)[1] != "splash.html":
                self.back_button_history.append(uri.rsplit('/', 1)[1])
                

            if uri.rsplit('/', 1)[1] == "splash.html":
                self.back_button_history = ["home.html"]
                self.run_javascript('gotopage("'+self.StoreGUI._start_page+'")')
                return
            else:
                self.mainwindowstack.set_visible_child(self.mainwindow)
            app.current_page = uri.rsplit('/', 1)[1]
            self._push_config()

    def _context_menu_cb(self, webview, menu, event, htr, user_data=None):
        # Disable context menu.
        return True
    
    


####Get icon of any size
class RetrieveIconSize():
    #Credits to Linux Mint for this code
    def set_icon_string(icon_string, width):
        theme = Gtk.IconTheme.get_default()
        scalefactor = Gtk.Image().get_scale_factor()

        icon_width = width * scalefactor

        if theme.has_icon(icon_string):
            info = theme.lookup_icon_for_scale(icon_string,
                                               width,
                                               scalefactor,
                                               Gtk.IconLookupFlags.FORCE_SIZE)
            if info:
                return(info.get_filename())
            
            return(RetrieveIconSize().set_icon_string(FALLBACK_PACKAGE_ICON_PATH, self.icon_width, self.icon_width))



####Store Window
class StoreWindow(object):
    def __init__(self):

        self.current_page = ""

        #systemstate.first_run = self._check_first_run()
        #systemstate.first_run = True

        self._start_page = 'home.html'

        self._build_app()

    def build_app_post_splashscreen(self, mainwindow, maintoolbar, mv, b):
        GLib.idle_add(self._build_app_post_splashscreen, mainwindow, maintoolbar, mv, b)

    def _build_app_post_splashscreen(self, mainwindow, maintoolbar, mv, b):
        # build rest of window
        box_application_header = AppDetailsHeader()
        box_application_header.set_visible(False)
        box_application_header.parent_window = self.w
        # add the box to the parent window and show
        mainwindow.pack_start(maintoolbar, False, True, 0)
        mainwindow.pack_start(box_application_header, False, True, 0)
        mainwindow.pack_end(b, True, True, 0)
        file = os.path.abspath(os.path.join("/usr/share/feren-store-new/splash.html"))
        uri = 'file://' + urllib.request.pathname2url(file)
        mv.load_uri(uri)
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
        GLib.set_prgname('/usr/bin/feren-store-new')
        
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
        search_btn = Gtk.ToggleButton(image=search_img)
        search_btn.set_name("search-btn")
        
        mainmenu = Gio.Menu()
        mainmenu.append("hello")
        mainmenu.append("world")
        menu_btn_img = Gtk.Image()
        menu_btn_img.set_from_icon_name("open-menu-symbolic", Gtk.IconSize.BUTTON);
        menu_btn = Gtk.MenuButton(image=menu_btn_img)
        menu_btn.set_use_popover(False)
        menu_btn.set_menu_model(mainmenu)
        
        self.gohome_btn = Gtk.ToggleButton(label=("Home"))
        self.gohome_btn.set_name("gohome-btn")
        self.gohome_handle_id = self.gohome_btn.connect("clicked", self._gohome_pressed)
        
        self.goapps_btn = Gtk.ToggleButton(label=("Applications"))
        self.goapps_btn.set_name("goapps-btn")
        self.goapps_handle_id = self.goapps_btn.connect("clicked", self._goapps_pressed)
        
        self.gothemes_btn = Gtk.ToggleButton(label=("Themes"))
        self.gothemes_btn.set_name("gothemes-btn")
        self.gothemes_handle_id = self.gothemes_btn.connect("clicked", self._gothemes_pressed)
        
        self.gowebsites_btn = Gtk.ToggleButton(label=("Websites"))
        self.gowebsites_btn.set_name("gowebsites-btn")
        self.gowebsites_handle_id = self.gowebsites_btn.connect("clicked", self._gowebsites_pressed)
        
        #For the splash screen
        mainwindowstack = Gtk.Stack()
        mainwindowstack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        #Use a titlebar-toolbar approach
        mainwindow = Gtk.VBox()
        mainwindow.set_spacing(0)
        maintoolbar = Gtk.Toolbar()
        maintoolbar.get_style_context().add_class(Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)
        maintoolbar.get_style_context().add_class("only-toolbar")
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
        
        store_logotype1 = Gtk.Label(label=("Feren OS"))
        store_logotype1.get_style_context().add_class("logotype1")
        store_logotype2 = Gtk.Label(label=("Store"))
        store_logotype2.get_style_context().add_class("logotype2")
        
        store_logotype1_box = Gtk.Box()
        store_logotype2_box = Gtk.Box()
        store_logotype1_box.pack_start(store_logotype1, False, False, 0)
        store_logotype2_box.pack_start(store_logotype2, False, False, 0)
        
        logotypebox.pack_start(store_logotype1_box, False, False, 0)
        logotypebox.pack_end(store_logotype2_box, False, False, 0)
        logoimageandbox.pack_start(store_logoimg, False, False, 0)
        logoimageandbox.pack_end(logotypebox, False, False, 0)
            
        header.pack_start(back_btn, False, True, 0)
        header.pack_start(logoimageandbox, False, True, 0)
        header.pack_start(toolbarspacer, True, True, 0)
        
        buttoncentering = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        buttoncenteringbtns = Gtk.Box(spacing=4)
        buttoncentering.set_center_widget(buttoncenteringbtns)
        
        buttoncenteringbtns.pack_start(self.gohome_btn, False, True, 0)
        buttoncenteringbtns.pack_start(self.goapps_btn, False, True, 0)
        buttoncenteringbtns.pack_start(self.gothemes_btn, False, True, 0)
        buttoncenteringbtns.pack_start(self.gowebsites_btn, False, True, 0)
        buttoncenteringbtns.pack_start(self.status_btn, False, True, 0)
        buttoncenteringbtns.pack_start(search_btn, False, True, 0)
        buttoncenteringbtns.pack_start(menu_btn, False, True, 0)
        
        header.pack_end(buttoncentering, False, False, 0)
        
        css_provider = Gtk.CssProvider()
        #In case this is Feren OS Classic or another non-Plasma-based Desktop running the Feren Store
        css_provider.load_from_path('/usr/share/feren-store-new/css/fallback.css')
        #Add some spizzas to the Feren Store logo too
        css_provider.load_from_path('/usr/share/feren-store-new/css/application.css')
        screen = Gdk.Screen.get_default()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, css_provider,
                                          Gtk.STYLE_PROVIDER_PRIORITY_USER)
        
        # build tasks page
        taskspage = Gtk.VBox(spacing=8)
        
        taskslabel_box = Gtk.Box()
        taskslabel = Gtk.Label(label="Currently working on these tasks:")
        taskslabel.get_style_context().add_class("14scale")
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
        updateslabel.get_style_context().add_class("14scale")
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
        installedlabel.get_style_context().add_class("14scale")
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
        
        
        # build 404 page
        self.nfpage = Gtk.VBox(spacing=8)
        
        nfpage_box = Gtk.VBox()
        nfpagelabel = Gtk.Label(label="Not Available")
        nfpagelabel2 = Gtk.Label(label="This item is currently not available or does not exist.")
        nfpagelabel.get_style_context().add_class("14scale")
        nfpage_box.pack_start(nfpagelabel, False, False, 5)
        nfpage_box.pack_end(nfpagelabel2, False, False, 5)
        self.nfpage.set_center_widget(nfpage_box)

        # build splash screen
        self.splashscreen = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        store_splashimg = Gtk.Image()
        iconpath = RetrieveIconSize.set_icon_string("softwarecenter", 128)
        store_splashimg.set_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file(iconpath))
        store_ferenimg = Gtk.Image()
        store_ferenimgpixbuf = GdkPixbuf.Pixbuf.new_from_file("/usr/share/feren-store-new/splashlogo.png")
        store_ferenimg.set_from_pixbuf(store_ferenimgpixbuf)
        self.splashscreen.pack_start(Gtk.Box(), True, False, 0)
        self.splashscreen.pack_start(store_splashimg, False, False, 0)
        self.splashscreen.pack_start(Gtk.Box(), True, False, 0)
        self.splashscreen.pack_start(store_ferenimg, False, False, 0)
        self.splashscreen.set_margin_bottom(44)
        self.splashscreen.set_margin_top(44)
        
        mainwindowstack.add_named(self.splashscreen, "splashscreen")
        mainwindowstack.add_named(mainwindow, "window")
        
        # build webkit container
        mv = AppView()
        mv.get_style_context().add_class(Gtk.STYLE_CLASS_VIEW)
        mv.set_zoom_level(1.0)

        mv.back_btn = back_btn
        mv.back_signal_handler = mv.back_btn.connect("clicked", mv._back_action)
        mv.header = header
        
        mv.StoreGUI = self
        
        #handle_id is needed to block events as otherwise the button active state changes cause button press events to occur (for whatever stupid reason) which ultimately leads to a Stack Overflow as the event code retriggers the event by triggering the button press yet again looping the cycle indefinitely

        # build scrolled window widget and add our appview stack
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        # build another scrolled window widget and add our tasks view
        sw2 = Gtk.ScrolledWindow()
        sw2.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sw2.get_style_context().add_class(Gtk.STYLE_CLASS_VIEW)
        
        self.pages = Gtk.Stack()
        self.pages.get_style_context().add_class(Gtk.STYLE_CLASS_VIEW)
        self.pages.add_named(sw, "webkit")
        self.pages.add_named(sw2, "tasks")
        self.pages.add_named(self.nfpage, "404")
        taskspage.set_margin_bottom(8)
        taskspage.set_margin_top(8)
        taskspage.set_margin_left(10)
        taskspage.set_margin_right(10)
        
        sw.add(mv)
        sw2.add(taskspage)

        # build a an autoexpanding box and add our scrolled window
        b = Gtk.Box(homogeneous=False, spacing=0)
        b.pack_start(self.pages, expand=True, fill=True, padding=0)
        
        self.w.add(mainwindowstack)
        
        self.w.connect('delete-event', self.close)

        self._window = self.w
        self.webkit = mv

        self.w.show_all()
        
        #Add more variables to mv
        mv.sw = sw
        mv.sw2 = sw2
        mv.pages = self.pages
        mv.mainwindow = mainwindow
        mv.mainwindowstack = mainwindowstack
        
        thread = Thread(target=self.build_app_post_splashscreen,
                        args=(mainwindow, maintoolbar, mv, b))
        thread.daemon = True
        thread.start()

    def run(self):
        Gtk.main()

    def _gohome_pressed(self, gtk_widget):
        self.webkit._goto_page("home")

    def _goapps_pressed(self, gtk_widget):
        self.webkit._goto_page("applicationspage")

    def _gothemes_pressed(self, gtk_widget):
        self.webkit._goto_page("themespage")

    def _gowebsites_pressed(self, gtk_widget):
        self.webkit._goto_page("websitespage")

    def _status_pressed(self, gtk_widget):
        self.webkit._goto_page("statuspage")

    def close(self, p1 = None, p2 = None):
        try:
            os.file.remove(pidfile)
        except:
            pass
        Gtk.main_quit(p1, p2)

    def update_page(self, element, function, parm1=None, parm2=None):
        """ Runs a JavaScript jQuery function on the page,
            ensuring correctly parsed quotes. """
        if parm1 and parm2:
            self.run_javascript('$("' + element + '").' + function + "('" + parm1.replace("'", '\\\'') + "', '" + parm2.replace("'", '\\\'') + "')")
        if parm1:
            if not function == 'src':
                self.run_javascript('$("' + element + '").' + function + "('" + parm1.replace("'", '\\\'') + "')")
            else:
                #Image replacing requires a special code modification
                self.run_javascript('$("' + element + '").attr' + "('src', '" + parm1.replace("'", '\\\'') + "')")
        else:
            self.run_javascript('$("' + element + '").' + function + '()')

    def run_javascript(self, script):
        thread = Thread(target=self._run_javascript,
                        args=(script,))
        thread.start()

    def _run_javascript(self, script):
        """
        Runs a JavaScript function on the page, regardless of which thread it is called from.
        GTK+ operations must be performed on the same thread to prevent crashes.
        """
        GLib.idle_add(self.__run_javascript, script)

    def __run_javascript(self, script):
        """
        Runs a JavaScript script on the page when invoked from run_javascript()
        """
        self.webkit.run_javascript(script)
        return GLib.SOURCE_REMOVE

    def _check_first_run(self):
        pass
    

if __name__ == "__main__":    
    app = StoreWindow()
    app.run()