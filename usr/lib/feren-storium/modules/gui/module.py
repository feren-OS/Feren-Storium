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

from gi.repository import Gtk, Gio, Gdk, GLib, Pango, GObject, GdkPixbuf, Pango
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from threading import Thread, Event
from queue import Queue, Empty

class DemoGUIException(Exception):
    pass


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


############################################
# Item Block
############################################
class itemBlockButton(Gtk.Box):
    def __init__(self, module, itemid, manage=True, moduleid=None, sourceid=None):
        self.module = module
        self.itemid = itemid
        self.sourceid = sourceid
        self.moduleid = moduleid
        self.manage = manage
        #TODO: Support subsource direction
        #Check criteria is met, first
        # Does itemid have any available sources?
        availsources = self.module.guiapi.getAvailableSources(self.itemid)
        if availsources == {}:
            raise DemoGUIException(_("%s has no available sources so cannot be added as an item button") % self.itemid)
        # If a moduleid, or even a moduleid-sourceid combo, were specified, are there available sources within their criteria?
        if self.moduleid != None:
            if self.sourceid != None: # check if this module-source combo exists as an available source
                if self.moduleid + "/" + self.sourceid not in availsources:
                    raise DemoGUIException(_("%s has no available source %s in module %s so cannot be added as an item button") % (self.itemid, self.sourceid, self.moduleid))
            else: # check if the module has any available sources - if so, use the first one from the module
                for i in availsources:
                    if i.startswith(self.moduleid + "/"):
                        self.sourceid = i[len(self.moduleid + "/"):] #Trim out moduleid portion
                        break
                if self.sourceid == None:
                    raise DemoGUIException(_("%s has no available sources in module %s so cannot be added as an item button") % (self.itemid, self.moduleid))
        else: #Otherwise use the first available source
            self.moduleid, self.sourceid = list(availsources.keys())[0].split("/")
            #FIXME: We'd need to change this to only split the final / and not precursor ones

        Gtk.Box.__init__(self)

        #Add the main body
        self.itemicon = itemIcon(self, module)
        self.fullname = Gtk.Label()
        self.fullname.set_ellipsize(Pango.EllipsizeMode.END)
        self.summary = Gtk.Label()
        self.summary.set_ellipsize(Pango.EllipsizeMode.END)

        fullnameBox = Gtk.Box()
        summaryBox = Gtk.Box()
        fullnameBox.pack_start(self.fullname, False, False, 0)
        summaryBox.pack_start(self.summary, False, False, 0)
        fullnameSummaryBox = Gtk.VBox()
        fullnameSummaryBox.pack_start(Gtk.Box(), True, True, 0) #Spacing
        fullnameSummaryBox.pack_end(Gtk.Box(), True, True, 0)
        fullnameSummaryBox.pack_start(fullnameBox, False, False, 0)
        fullnameSummaryBox.pack_end(summaryBox, False, False, 0)

        #TODO: Add Warnings summary
        #TODO: Do as shown in diagram before returning one self

        if manage == True:
            self.body = Gtk.Button()
            infobox = Gtk.Box()
            #Swapped the element with spacing here as they look better with the icon not having padding here,
            # while the text having it instead maintains the existing status-quo of the space between icon and text:
            infobox.pack_start(self.itemicon, False, False, 0)
            infobox.pack_start(fullnameSummaryBox, True, True, 8)
            self.body.add(infobox)
            self.body.connect('clicked', self.goto)
        else:
            self.body = Gtk.Box()
            self.body.pack_start(self.itemicon, False, False, 0)
            self.body.pack_start(fullnameSummaryBox, True, True, 8)

        self.set_size_request(320, 52)
        self.pack_start(self.body, True, True, 0)

        #Get item's information
        self.loadItemInformation()

        #Add the button if manage is on
        if manage == True:
            #NOTE: Due to a design issue in GTK, this button is not inside the button, but rather next to it, to prevent the hitbox of the parent button overriding that of the itemmgmt button
            self.buttonsstack = Gtk.Stack()
            self.buttonsstack.connect("notify::visible-child", self.onStatusChanged)

            # Buttons (not queued)
            #  Install
            self.install = Gtk.Button(label=_("Install"))
            self.install.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
            #self.install.connect('clicked', self.onInstall)
            self.buttonsstack.add_named(self.install, "install")
            #  Install (requires adding application source)
            self.installsource = Gtk.Button(label=_("Install..."))
            self.installsource.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
            #self.installsource.connect('clicked', self.onInstallSource)
            self.buttonsstack.add_named(self.installsource, "installsource")
            #  Update
            self.update = Gtk.Button(label=_("Update"))
            self.update.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
            #self.update.connect('clicked', self.onUpdate)
            self.buttonsstack.add_named(self.update, "update")
            #  Remove
            self.remove = Gtk.Button(label=_("Remove"))
            self.remove.get_style_context().add_class(Gtk.STYLE_CLASS_DESTRUCTIVE_ACTION)
            #self.remove.connect('clicked', self.onRemove)
            self.buttonsstack.add_named(self.remove, "remove")

            # Buttons (Queued/Pending)
            self.cancelqueuebtn = Gtk.Button(label=_("Cancel"))
            #cancelqueuebtn.connect('clicked', self.onCancelQueue)
            self.buttonsstack.add_named(self.cancelqueuebtn, "cancelqueue")

            # Buttons (In Progress)
            self.cancelbtn = Gtk.Button(label=_("Cancel"))
            #self.cancelbtn.connect('clicked', self.onCancel)
            self.buttonsstack.add_named(self.cancelbtn, "cancel")

            # Loading status
            self.statusunknown = Gtk.Box()
            self.statusunknown.set_size_request(self.install.get_allocation().width, -1)
            self.statusloading = Gtk.Spinner()
            self.statusunknown.pack_start(Gtk.Box(), True, True, 0)
            self.statusunknown.pack_end(Gtk.Box(), True, True, 0)
            self.statusunknown.pack_start(self.statusloading, False, False, 0)
            self.buttonsstack.add_named(self.statusunknown, "loading")


            #Add buttons to the right of the block, and get the current status
            self.pack_end(self.buttonsstack, False, False, 0)
            if self.moduleid != None and self.sourceid != None:
                thread = Thread(target=self.loadStatus,
                            args=())
            else:
                thread = Thread(target=self.loadStatus,
                            args=())
            thread.daemon = True
            thread.start()
        #TODO: Figure out how we'll get item information - do we just add a clause to getItemInformation in the API where it obtains it from the task if there's a task?

        self.show_all()


    def loadItemInformation(self):
        iteminfo = self.module.api.getItemInformation(self.itemid, self.moduleid, self.sourceid)

        thread = Thread(target=self.itemicon.setIcon,
                        args=(iteminfo["iconid"], iteminfo["iconurl"], self.itemid, self.moduleid, self.sourceid))
        thread.daemon = True
        thread.start()

        #There are only two labels left in the header to change:
        GLib.idle_add(self.fullname.set_label, iteminfo["fullname"])
        GLib.idle_add(self.summary.set_label, iteminfo["summary"])


    def onStatusChanged(self, stckswch, idk):
        #TODO: Make all stacks with loading spinners start/stop depending on their loading stack being visible
        a = stckswch.get_visible_child()
        if a == self.statusunknown:
            self.statusloading.start()
        else:
            self.statusloading.stop()

    def loadStatus(self):
        #TODO: When entering in progress state, change subtitle to "Installing...", "Updating...", "Removing..." and so on, with their progress marked on them 'cos too lazy to implement a label-progressbar-combo in this block in demoGUI.
        #Just in case
        GLib.idle_add(self.buttonsstack.set_visible_child, self.statusunknown)

        status, irrelevant = self.module.guiapi.getItemStatus(self.itemid, self.moduleid, self.sourceid)

        #Switch to appropriate button
        if status == 0:
            #Check if the necessary source is installed if not installed
            sourceavailable = True #TODO
            if sourceavailable == True:
                GLib.idle_add(self.buttonsstack.set_visible_child, self.install)
            else:
                GLib.idle_add(self.buttonsstack.set_visible_child, self.installsource)
        elif status == 1:
            GLib.idle_add(self.buttonsstack.set_visible_child, self.remove)
        elif status == 2:
            GLib.idle_add(self.buttonsstack.set_visible_child, self.update)
        elif status >= 3 and status <= 6: #Queued
            GLib.idle_add(self.buttonsstack.set_visible_child, self.cancelqueuebtn)
        elif status >= 7 and status <= 10:
            GLib.idle_add(self.buttonsstack.set_visible_child, self.cancelbtn)

        #TODO: to check for "Install...", before checking this item's status query getItemStatus on the source ID itself to check if the source is installed


    def goto(self, button):
        if self.moduleid != None and self.sourceid != None:
            thread = Thread(target=self.module.gotoID,
                            args=(self.itemid, self.moduleid, self.sourceid))
        else:
            thread = Thread(target=self.module.gotoID,
                            args=(self.itemid,))
        thread.start()


############################################
# Item Icon
############################################
class itemIcon(Gtk.Stack):
    def __init__(self, parent, module):
        Gtk.Stack.__init__(self)
        self.connect("notify::visible-child", self.stateChanged)
        self.parent = parent
        self.module = module
        self.size = 48
        self.set_size_request(self.size, self.size)
        self.icontheme = Gtk.IconTheme.get_default() #Used in isIconInIcons

        self.icon = Gtk.Image()
        self.loading = Gtk.Spinner()
        self.add_named(self.loading, "loading")
        self.add_named(self.icon, "icon")
        self.set_visible_child(self.icon)
        self.set_no_show_all(True) #Don't show when auto-shown post-summoning

        #Show children so that when show'd the icon and loading indicator are visible
        self.icon.show_all()
        self.loading.show_all()

    def isIconInIcons(self, iconid):
        return self.icontheme.has_icon(iconid)

    def getIconIDLocation(self, iconid):
        if self.isIconInIcons(iconid) == False:
            raise DemoGUIException(_("%s is not in this icon set") % iconid)
        return self.icontheme.lookup_icon_for_scale(iconid, self.size, Gtk.Image().get_scale_factor(), Gtk.IconLookupFlags.FORCE_SIZE).get_filename()

    def iconPixbuf(self, filepath):
        size = self.size * Gtk.Image().get_scale_factor()
        result = GdkPixbuf.Pixbuf.new_from_file(filepath)
        result = result.scale_simple(size, size, GdkPixbuf.InterpType.BILINEAR)
        return result

    def setIcon(self, iconid, iconurl, itemid, moduleid, sourceid):
        #Just in case
        GLib.idle_add(self.set_visible_child, self.loading)
        #Try using icon from icon set first
        if self.isIconInIcons(iconid):
            try:
                GLib.idle_add(self.icon.set_from_pixbuf, self.iconPixbuf(self.getIconIDLocation(iconid)))
                GLib.idle_add(self.set_visible_child, self.icon)
                return
            except:
                pass
        #If not in the icon set, grab its icon from the internet
        try:
            cachepath = self.module.api.getIcon(itemid, moduleid, sourceid, iconurl)
            GLib.idle_add(self.icon.set_from_pixbuf, self.iconPixbuf(cachepath))
            GLib.idle_add(self.set_visible_child, self.icon)
            return
        except Exception as e:
            #TODO: Debug check
            print(_("DEBUG: Could not download icon for %s: %s") % (itemid, e))
        #Fall back to missing icon if all else fails
        try:
            GLib.idle_add(self.icon.set_from_pixbuf, self.iconPixbuf(self.getIconIDLocation("package-x-generic")))
            GLib.idle_add(self.set_visible_child, self.icon)
            return
        except:
            try: #Fallback of all fallbacks
                GLib.idle_add(self.icon.set_from_pixbuf, self.iconPixbuf(self.getIconIDLocation("image-missing")))
            except:
                GLib.idle_add(self.icon.hide)
                GLib.idle_add(self.set_visible_child, self.icon)
                raise DemoGUIException(_("This icon set has no icons??"))


    def stateChanged(self, stckswch, idk):
        a = stckswch.get_visible_child()
        if a == self.loading:
            self.loading.start()
            self.show()
        else:
            self.loading.stop()








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
# Categories view
############################################

class categoricalPage(Gtk.Box):
    def __init__(self, parent, module):
        Gtk.Box.__init__(self)
        self.parent = parent
        self.module = module

        categoriesScroll = Gtk.ScrolledWindow()
        categoriesScroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.categoriesPane = Gtk.ListBox()
        categoriesScroll.add(self.categoriesPane)
        self.categoriesPane.set_size_request(270, -1)
        self.pack_start(categoriesScroll, False, False, 0)
        self.pack_start(Gtk.Separator(), False, False, 0)
        listingsScroll = Gtk.ScrolledWindow()
        listingsScroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        listingsBox = Gtk.VBox() #Prevent stretching items in non-window-filling results
        self.listingsPane = Gtk.FlowBox()
        self.listingsPane.set_homogeneous(True)
        listingsBox.pack_start(self.listingsPane, False, False, 0)
        listingsBox.pack_end(Gtk.Box(), True, True, 0) #used as filler space.
        listingsScroll.add(listingsBox)
        self.listingsPane.set_margin_top(4)
        self.listingsPane.set_margin_bottom(4)
        self.listingsPane.set_margin_left(4)
        self.listingsPane.set_margin_right(4)
        self.pack_end(listingsScroll, True, True, 0)

        self.categoriesPane.connect('row-activated', self.onCategoryChanged)
        self.show_all()

        #TODO: For All, do a search on nothing (kinda like with the application sources dialog) with no filter, and give it no limit - afterwards, rid of duplicate IDs, put all the IDs in a list, and get up to (depends on results quantity) 200 random indexes - then, sort these index numbers, and return the list values corresponding to that index, before showing them as results

    def setCategories(self, catedict):
        #Destroy prior categories
        for i in self.categoriesPane.get_children():
            GLib.idle_add(i.destroy())
        #Create category items for the target categories
        for i in catedict:
            GLib.idle_add(self.categoriesPane.add, self.generateCategoryItem(i, catedict[i]))
        GLib.idle_add(self.categoriesPane.show_all)

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


    def onCategoryChanged(self, listbox, row):
        items = self.module.guiapi.allItemsFilterCategory(row.category, 200, True, False)
        for i in self.listingsPane.get_children():
            for iblock in i.get_children(): #Get itemblock out of FlowBoxChild
                if iblock in self.parent.known_itemboxes:
                    self.parent.known_itemboxes.pop(self.parent.known_itemboxes.index(iblock))
            GLib.idle_add(i.destroy)
        #TODO: Placeholder screen for no items
        for i in items:
            iblock = itemBlockButton(self.module, i, True)
            self.parent.known_itemboxes.append(iblock)
            GLib.idle_add(self.listingsPane.insert, iblock, -1)
        GLib.idle_add(self.listingsPane.show_all)


############################################
# Tasks/Library view
############################################

class tasksLibraryPage(Gtk.ScrolledWindow):
    def __init__(self, parent, module):
        Gtk.ScrolledWindow.__init__(self)
        self.parent = parent
        self.module = module

        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        listingsBox = Gtk.VBox()
        listingsBox.pack_end(Gtk.Box(), True, True, 0) #prevent stretching in non-filling-outcomes
        listingsBox.set_margin_top(4)
        listingsBox.set_margin_bottom(4)
        listingsBox.set_margin_left(4)
        listingsBox.set_margin_right(4)
        self.add(listingsBox)

        #Tasks in progress
        self.tasksLbl = Gtk.Box()
        tasksLbl = Gtk.Label(label=_("Tasks in progress"))
        self.tasksLbl.pack_start(tasksLbl, False, False, 0)
        self.tasksLbl.pack_end(Gtk.Box(), True, True, 0)
        #self.tasksLbl.set_no_show_all(True)
        self.tasksList = Gtk.FlowBox()
        self.tasksList.set_min_children_per_line(1)
        self.tasksList.set_max_children_per_line(1)
        #self.tasksList.set_no_show_all(True)
        listingsBox.pack_start(self.tasksLbl, False, False, 0)
        listingsBox.pack_start(self.tasksList, False, False, 0)

        #Needs attention
        self.needsAttentionLbl = Gtk.Box()
        needsAttentionLbl = Gtk.Label(label=_("Needs attention"))
        self.needsAttentionLbl.pack_start(needsAttentionLbl, False, False, 0)
        self.needsAttentionLbl.pack_end(Gtk.Box(), True, True, 0)
        #self.needsAttentionLbl.set_no_show_all(True)
        self.needsAttentionList = Gtk.FlowBox()
        self.needsAttentionList.set_min_children_per_line(1)
        self.needsAttentionList.set_max_children_per_line(1)
        #self.needsAttentionList.set_no_show_all(True)
        listingsBox.pack_start(self.needsAttentionLbl, False, False, 0)
        listingsBox.pack_start(self.needsAttentionList, False, False, 0)

        #Pending updates
        self.updatesLbl = Gtk.Box()
        updatesLbl = Gtk.Label(label=_("Pending updates"))
        self.updatesLbl.pack_start(updatesLbl, False, False, 0)
        self.updatesLbl.pack_end(Gtk.Box(), True, True, 0)
        #self.updatesLbl.set_no_show_all(True)
        self.updatesList = Gtk.FlowBox()
        self.updatesList.set_min_children_per_line(1)
        self.updatesList.set_max_children_per_line(1)
        #self.updatesList.set_no_show_all(True)
        listingsBox.pack_start(self.updatesLbl, False, False, 0)
        listingsBox.pack_start(self.updatesList, False, False, 0)

        #Drivers
        self.driversLbl = Gtk.Box()
        driversLbl = Gtk.Label(label=_("Available drivers"))
        self.driversLbl.pack_start(driversLbl, False, False, 0)
        self.driversLbl.pack_end(Gtk.Box(), True, True, 0)
        #self.driversLbl.set_no_show_all(True)
        self.driversList = Gtk.FlowBox()
        self.driversList.set_min_children_per_line(1)
        self.driversList.set_max_children_per_line(1)
        #self.driversList.set_no_show_all(True)
        listingsBox.pack_start(self.driversLbl, False, False, 0)
        listingsBox.pack_start(self.driversList, False, False, 0)

        #Installed
        self.installedLbl = Gtk.Box()
        installedLbl = Gtk.Label(label=_("Installed applications"))
        self.installedLbl.pack_start(installedLbl, False, False, 0)
        self.installedLbl.pack_end(Gtk.Box(), True, True, 0)
        #self.installedLbl.set_no_show_all(True)
        self.installedList = Gtk.FlowBox()
        self.installedList.set_min_children_per_line(1)
        self.installedList.set_max_children_per_line(1)
        #self.installedList.set_no_show_all(True)
        listingsBox.pack_start(self.installedLbl, False, False, 0)
        listingsBox.pack_start(self.installedList, False, False, 0)

        self.show_all()


    def refreshTasksList(self):
        taskslist = self.module.guiapi.getTasks()
        #Remove existing items
        for i in self.tasksList.get_children():
            for iblock in i.get_children(): #Get itemblock out of FlowBoxChild
                if iblock in self.parent.known_itemboxes:
                    self.parent.known_itemboxes.pop(self.parent.known_itemboxes.index(iblock))
            GLib.idle_add(i.destroy)
        #Generate new item blocks for the tasks
        for i in taskslist:
            iblock = itemBlockButton(self.module, taskslist[i]["itemid"], True, taskslist[i]["moduleid"], taskslist[i]["sourceid"])
            self.parent.known_itemboxes.append(iblock)
            GLib.idle_add(self.tasksList.insert, iblock, -1)




############################################
# Item Details header
############################################

class itemDetailsHeader(Gtk.Box):
    def __init__(self, parent, module):
        Gtk.Box.__init__(self)
        self.set_size_request(-1, 52)
        self.parent = parent
        self.module = module
        self.sourcesdata = {}
        self.targetsubsource = None
        self.extrabuttoncallbacks = {}

        #Item icon
        self.itemicon = itemIcon(self, module)

        #Item fullname and summary
        self.fullname = Gtk.Label()
        self.fullname.set_ellipsize(Pango.EllipsizeMode.END)
        self.summary = Gtk.Label()
        self.summary.set_ellipsize(Pango.EllipsizeMode.END)

        fullnameBox = Gtk.Box()
        summaryBox = Gtk.Box()
        fullnameBox.pack_start(self.fullname, False, False, 0)
        summaryBox.pack_start(self.summary, False, False, 0)
        fullnameSummaryBox = Gtk.VBox()
        fullnameSummaryBox.pack_start(Gtk.Box(), True, True, 0) #Spacing
        fullnameSummaryBox.pack_end(Gtk.Box(), True, True, 0)
        fullnameSummaryBox.pack_start(fullnameBox, False, False, 0)
        fullnameSummaryBox.pack_end(summaryBox, False, False, 0)

        #Source dropdowns
        sourceslbl = Gtk.Label(label=_("Source:"))
        sourcesarea = Gtk.VBox()
        sourcesarea.pack_start(Gtk.Box(), True, True, 0)
        sourcesarea.pack_end(Gtk.Box(), True, True, 0)
        self.sources = Gtk.Stack()
        self.source = Gtk.ComboBox()
        self.source.connect("changed", self.onSourceChange)
        cell = Gtk.CellRendererText()
        self.source.pack_start(cell, True)
        self.source.add_attribute(cell, "text", 0) #Otherwise it completely lacks text
        self.sourcelbl = Gtk.Label()
        self.sources.add_named(self.source, "dropdown")
        self.sources.add_named(self.sourcelbl, "label")
        sourcesarea.pack_start(self.sources, False, False, 0)

        #Buttons and status
        actionsarea = Gtk.VBox()
        actionsarea.pack_start(Gtk.Box(), True, True, 0)
        actionsarea.pack_end(Gtk.Box(), True, True, 0)
        self.itemstatus = Gtk.Stack()
        self.itemstatus.connect("notify::visible-child", self.onStatusChanged)

        # Buttons (not queued)
        self.moduleactions = Gtk.Box() #Extra buttons from the current module
        self.actions = Gtk.Box()
        #  Install
        self.install = Gtk.Button(label=_("Install"))
        self.install.set_no_show_all(True) #Prevent being shown on show_all(), thus preventing W I D E  window
        self.install.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        self.install.connect('clicked', self.onInstall)
        #  Install (requires adding application source)
        self.installsource = Gtk.Button(label=_("Install..."))
        self.installsource.set_no_show_all(True)
        self.installsource.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        self.installsource.connect('clicked', self.onInstallSource)
        #  Update
        self.update = Gtk.Button(label=_("Update"))
        self.update.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        self.update.set_no_show_all(True)
        self.update.connect('clicked', self.onUpdate)
        #  Reinstall
        self.reinstall = Gtk.Button(label=_("Reinstall"))
        self.reinstall.set_no_show_all(True)
        self.reinstall.connect('clicked', self.onReinstall)
        #  Remove
        self.remove = Gtk.Button(label=_("Remove"))
        self.remove.set_no_show_all(True)
        self.remove.get_style_context().add_class(Gtk.STYLE_CLASS_DESTRUCTIVE_ACTION)
        self.remove.connect('clicked', self.onRemove)
        #  Assemble them
        self.actions.pack_end(self.remove, False, False, 4)
        self.actions.pack_end(self.update, False, False, 4)
        self.actions.pack_end(self.reinstall, False, False, 4)
        self.actions.pack_end(self.installsource, False, False, 4)
        self.actions.pack_end(self.install, False, False, 4)
        #  Subsources selector
        self.subsource = Gtk.ComboBox()
        self.subsource.connect("changed", self.onSubsourceChange)
        cell2 = Gtk.CellRendererText()
        self.subsource.pack_start(cell2, True)
        self.subsource.add_attribute(cell2, "text", 0)
        #Combine extra buttons and buttons and add
        self.statusunqueued = Gtk.Box()
        self.statusunqueued.pack_start(self.subsource, False, False, 4)
        self.statusunqueued.pack_start(self.moduleactions, False, False, 0)
        self.statusunqueued.pack_start(self.actions, False, False, 0)
        self.itemstatus.add_named(self.statusunqueued, "unqueued")

        # Queued / Pending
        self.statusqueued = Gtk.Box()
        self.queuedlbl = Gtk.Label(label=_("Waiting for OPERATIONHERE"))
        cancelqueuebtn = Gtk.Button(label=_("Cancel"))
        #cancelqueuebtn.connect('clicked', self.onCancelQueue)
        self.statusqueued.pack_start(self.queuedlbl, False, False, 4)
        self.statusqueued.pack_end(cancelqueuebtn, False, False, 4)
        self.itemstatus.add_named(self.statusqueued, "queued")

        # Progress
        self.statusinprogress = Gtk.Box()
        self.itemprogress = Gtk.ProgressBar()
        self.itemprogress.set_size_request(270, -1)
        self.cancelbtn = Gtk.Button(label=_("Cancel"))
        #self.cancelbtn.connect('clicked', self.onCancel)
        self.statusinprogress.pack_start(self.itemprogress, False, False, 4)
        self.statusinprogress.pack_end(self.cancelbtn, False, False, 4)
        self.itemstatus.add_named(self.statusinprogress, "inprogress")

        # Loading status
        self.statusunknown = Gtk.Box()
        self.statusunknown.set_size_request(self.install.get_allocation().width, -1)
        self.statusloading = Gtk.Spinner()
        self.statusunknown.pack_start(Gtk.Box(), True, True, 0)
        self.statusunknown.pack_end(Gtk.Box(), True, True, 0)
        self.statusunknown.pack_start(self.statusloading, False, False, 0)
        self.itemstatus.add_named(self.statusunknown, "loading")

        # Adding it all into the header area
        actionsarea.pack_start(self.itemstatus, False, False, 0)
        self.pack_start(self.itemicon, False, False, 8)
        self.pack_start(fullnameSummaryBox, True, True, 4)
        self.pack_end(actionsarea, False, False, 4)
        self.pack_end(sourcesarea, False, False, 4)
        self.pack_end(sourceslbl, False, False, 4)
        self.show_all()


    def onStatusChanged(self, stckswch, idk):
        #TODO: Make all stacks with loading spinners start/stop depending on their loading stack being visible
        a = stckswch.get_visible_child()
        if a == self.statusunqueued:
            self.install.set_sensitive(True)
        if a == self.statusqueued:
            self.statusqueued.show()
        else:
            self.statusqueued.hide()
        if a == self.statusinprogress:
            self.statusinprogress.show()
        else:
            self.statusinprogress.hide()
        if a == self.statusunknown:
            self.statusunknown.show()
            self.install.set_sensitive(False)
            self.install.show()
        else:
            self.statusunknown.hide()


    def loadSources(self, itemid, targetmodule="", targetsource="", targetsubsource=""):
        if itemid != self.parent.currentItem:
            return #Do not run if the item being viewed is not itemid

        #Show a loading item page
        GLib.idle_add(self.parent.itempage.loadspin.start)
        GLib.idle_add(self.parent.itempage.set_visible_child, self.parent.itempage.loading)

        #Get the sources
        sources = self.module.guiapi.getAvailableSources(itemid)
        if len(sources) == 0:
            pass #TODO: "Not available" page
            return
        self.sourcesdata = sources
        self.targetsubsource = None #Reset if not yet reset

        if len(self.sourcesdata) == 1:
            GLib.idle_add(self.sources.set_visible_child, self.sourcelbl)
            GLib.idle_add(self.source.hide)
        else:
            GLib.idle_add(self.source.show)
            GLib.idle_add(self.sources.set_visible_child, self.source)

        iface_list_store = Gtk.ListStore(GObject.TYPE_STRING)
        for source in self.sourcesdata: #Why did they design it to need to be a list?
            iface_list_store.append([self.sourcesdata[source]["fullname"]])
        GLib.idle_add(self.source.set_model, iface_list_store)

        #Select the appropriate source
        targetindex = 0
        if targetmodule != "" and targetsource != "":
            target = targetmodule + "/" + targetsource
            if target in sources:
                targetindex = list(self.sourcesdata.keys()).index(target)
                if targetsubsource != "": #Store targetsubsource so the subsource automatically switches upon source selection
                    self.targetsubsource = targetsubsource
            else:
                #TODO: Debug output check/@...
                print(_("DEBUG: Could not switch source to %s from %s as it is not available for this item.") % (targetsource, targetmodule))
        #Select a source automatically
        GLib.idle_add(self.source.set_active, targetindex)

        #Show the page to the user
        GLib.idle_add(self.parent.itempage.set_visible_child, self.parent.itempage.loaded)
        GLib.idle_add(self.parent.itempage.loadspin.stop)

        #TODO: Stop on first non-easymode-deferring source when on Simple Mode

    def onSourceChange(self, combobox):
        if combobox.get_active() == -1: #Prevent exceptions on invalid values
            return

        newsourceid = list(self.sourcesdata.keys())[combobox.get_active()]
        self.parent.currentModuleSource = newsourceid
        self.sourcelbl.set_label(self.sourcesdata[newsourceid]["fullname"])

        #Switch item page to loading
        GLib.idle_add(self.parent.itempage.bodyloadspin.start)
        GLib.idle_add(self.parent.itempage.body.set_visible_child, self.parent.itempage.bodyloading)
        GLib.idle_add(self.itemicon.set_visible_child, self.itemicon.loading)
        GLib.idle_add(self.fullname.set_label, "")
        GLib.idle_add(self.summary.set_label, "")

        #Ditto with item status
        GLib.idle_add(self.statusloading.start)
        GLib.idle_add(self.itemstatus.set_visible_child, self.statusunknown)

        #Redirect if this source is a redirection source
        #TODO

        #Load item information from this source
        thread = Thread(target=self.parent.loadItemInformation,
                        args=(newsourceid, self.parent.currentItem))
        thread.daemon = True
        thread.start()

        #Load subsources
        self.loadSubsources(newsourceid, self.parent.currentItem)

        #Load status of the item
        self.loadStatus(newsourceid, self.parent.currentItem)
    def loadSubsources(self, modulesourceid, itemid):
        if itemid != self.parent.currentItem:
            return #Do not run if the item being viewed is not itemid
        if modulesourceid != self.parent.currentModuleSource:
            return #Do not run if the source being viewed is not this
        subsources = self.sourcesdata[modulesourceid]["subsources"]

        if len(subsources) <= 1:
            #TODO: Move this code to loadStatus as it'll toggle dropdown visibility
            GLib.idle_add(self.subsource.hide)
        else:
            GLib.idle_add(self.subsource.show)

        iface_list_store = Gtk.ListStore(GObject.TYPE_STRING)
        for subsource in subsources: #Why did they design it to need to be a list?
            iface_list_store.append([subsources[subsource]["fullname"]])
        GLib.idle_add(self.subsource.set_model, iface_list_store)
        self.changeSubsource(subsources, modulesourceid, itemid, self.targetsubsource)
        self.targetsubsource = None #Reset the value once used

    def changeSubsource(self, subsources, modulesourceid, itemid, targetsubsource):
        if itemid != self.parent.currentItem:
            return #Do not run if the item being viewed is not itemid
        if modulesourceid != self.parent.currentModuleSource:
            return #Do not run if the source being viewed is not this
        #Select the appropriate source
        targetindex = 0
        if targetsubsource != None and not len(subsources) <= 1:
            if targetsubsource in subsources:
                targetindex = list(subsources.keys()).index(targetsubsource)
            else:
                #TODO: Debug output check/@...
                print(_("DEBUG: Could not switch subsource to %s as it is not available for this item.") % targetsubsource)
        #Select a source automatically
        GLib.idle_add(self.subsource.set_active, targetindex)


    def onSubsourceChange(self, combobox):
        self.parent.currentSubsource = list(self.sourcesdata[self.parent.currentModuleSource]["subsources"].keys())[combobox.get_active()]


    def loadStatus(self, modulesourceid, itemid):
        if itemid != self.parent.currentItem:
            return #Do not run if the item being viewed is not itemid
        if modulesourceid != self.parent.currentModuleSource:
            return #Do not run if the source being viewed is not this
        #Run in a thread
        thread = Thread(target=self._loadStatus,
                        args=(modulesourceid, itemid))
        thread.daemon = True
        thread.start()
    def _loadStatus(self, modulesourceid, itemid):
        #Just in case
        GLib.idle_add(self.parent.itempage.header.statusloading.start)
        GLib.idle_add(self.parent.itempage.header.itemstatus.set_visible_child, self.parent.itempage.header.statusunknown)

        #Get split values for source and module IDs
        moduleid, sourceid = modulesourceid.split("/")
        #FIXME: We'd need to change this to only split the final / and not precursor ones

        #Get status, and subsource if relevant via API
        status, installedsubsource = self.module.guiapi.getItemStatus(itemid, moduleid, sourceid)

        #Change visibility of buttons accordingly (alongside subsource selector's visibility)
        GLib.idle_add(self.parent.itempage.header.install.hide)
        GLib.idle_add(self.parent.itempage.header.installsource.hide)
        GLib.idle_add(self.parent.itempage.header.reinstall.hide)
        GLib.idle_add(self.parent.itempage.header.update.hide)
        GLib.idle_add(self.parent.itempage.header.remove.hide)
        GLib.idle_add(self.parent.itempage.header.subsource.hide)
        for i in self.moduleactions.get_children():
            GLib.idle_add(i.destroy)
        self.extrabuttoncallbacks = {} #Erase existing callback values now the buttons are gone
        if status == 0:
            #Check if the necessary source is installed if not installed
            sourceavailable = True #TODO
            if sourceavailable == True:
                GLib.idle_add(self.parent.itempage.header.install.show)
            else:
                GLib.idle_add(self.parent.itempage.header.installsource.show)
            GLib.idle_add(self.parent.itempage.header.subsource.show)
        elif status == 1:
            GLib.idle_add(self.parent.itempage.header.reinstall.show)
            GLib.idle_add(self.parent.itempage.header.remove.show)
            #Change subsource accordingly if installed
            self.changeSubsource(self.sourcesdata[modulesourceid]["subsources"], modulesourceid, itemid, installedsubsource)
        elif status == 2:
            GLib.idle_add(self.parent.itempage.header.update.show)
            GLib.idle_add(self.parent.itempage.header.remove.show)
            self.changeSubsource(self.sourcesdata[modulesourceid]["subsources"], modulesourceid, itemid, installedsubsource)
        elif status == 3: #Queued
            GLib.idle_add(self.parent.itempage.header.queuedlbl.set_label, _("Waiting for installation"))
        elif status == 4:
            GLib.idle_add(self.parent.itempage.header.queuedlbl.set_label, _("Waiting for reinstallation"))
        elif status == 5:
            GLib.idle_add(self.parent.itempage.header.queuedlbl.set_label, _("Waiting for update"))
        elif status == 6:
            GLib.idle_add(self.parent.itempage.header.queuedlbl.set_label, _("Waiting for removal"))
        elif status >= 7 and status <= 10:
            pass #TODO: Get current progress and immediately place it on the in-page progress bar

        #Get extra buttons from the selected module
        for i in self.module.guiapi.getExtraItemButtons(itemid, moduleid, sourceid, status):
            img = Gtk.Image()
            img.set_from_icon_name(i["icon"], Gtk.IconSize.BUTTON);
            ii = Gtk.Button(label=i["text"], image=img)
            ii.set_tooltip_text(i["tooltip"])
            callbackid = 0
            while callbackid in self.extrabuttoncallbacks:
                callbackid += 1
            self.extrabuttoncallbacks[callbackid] = i["callback"]
            ii.connect("clicked", self.extraButtonCallback, callbackid)
            #Add the extra button to the row of 'em
            GLib.idle_add(self.moduleactions.pack_end, ii, False, False, 4) #Prevent showing both the newly spawned buttons and the deleted ones at the same time
            ii.show()

        #Show the appropriate items
        if status >= 0 and status <= 2:
            GLib.idle_add(self.parent.itempage.header.itemstatus.set_visible_child, self.parent.itempage.header.statusunqueued)
        elif status >= 3 and status <= 6:
            GLib.idle_add(self.parent.itempage.header.itemstatus.set_visible_child, self.parent.itempage.header.statusqueued)
        elif status >= 7 and status <= 10:
            GLib.idle_add(self.parent.itempage.header.itemstatus.set_visible_child, self.parent.itempage.header.statusinprogress)

        #TODO: to check for "Install...", before checking this item's status query getItemStatus on the source ID itself to check if the source is installed
        GLib.idle_add(self.parent.itempage.header.statusloading.stop)


    def loadInfo(self, iteminfo, modulesourceid, itemid):
        if itemid != self.parent.currentItem:
            return
        if modulesourceid != self.parent.currentModuleSource:
            return

        #Show the appropriate icon
        moduleid, sourceid = modulesourceid.split("/")
        #FIXME: We'd need to change this to only split the final / and not precursor ones
        thread = Thread(target=self.itemicon.setIcon,
                        args=(iteminfo["iconid"], iteminfo["iconurl"], itemid, moduleid, sourceid))
        thread.daemon = True
        thread.start()

        #There are only two labels left in the header to change:
        GLib.idle_add(self.fullname.set_label, iteminfo["fullname"])
        GLib.idle_add(self.summary.set_label, iteminfo["summary"])


    def extraButtonCallback(self, button, callbackid):
        if callbackid not in self.extrabuttoncallbacks:
            return

        self.extrabuttoncallbacks[callbackid]()


    def onInstall(self, button):
        moduleid, sourceid = self.parent.currentModuleSource.split("/")
        self.module.guiapi.installItem(self.parent.currentItem, moduleid, sourceid, self.parent.currentSubsource)

    def onInstallSource(self, button):
        moduleid, sourceid = self.parent.currentModuleSource.split("/")
        #TODO: Figure out how to do sourceitemid
        #self.module.guiapi.installItem(self.parent.currentItem, moduleid, sourceid, self.parent.currentSubsource)

    def onUpdate(self, button):
        moduleid, sourceid = self.parent.currentModuleSource.split("/")
        self.module.guiapi.updateItem(self.parent.currentItem, moduleid, sourceid, self.parent.currentSubsource)

    def onReinstall(self, button):
        moduleid, sourceid = self.parent.currentModuleSource.split("/")
        self.module.guiapi.reinstallItem(self.parent.currentItem, moduleid, sourceid, self.parent.currentSubsource)

    def onRemove(self, button):
        moduleid, sourceid = self.parent.currentModuleSource.split("/")
        self.module.guiapi.removeItem(self.parent.currentItem, moduleid, sourceid, self.parent.currentSubsource)

    #TODO: Change bonuses button


############################################
# Item Information page
############################################

class itemInfoBody(Gtk.FlowBox):
    def __init__(self, parent, module):
        Gtk.FlowBox.__init__(self)
        self.parent = parent
        self.module = module
        self.set_max_children_per_line(1)
        self.set_margin_top(4)
        self.set_margin_bottom(4)

        #TODO: Remaining contents
        self.show_all()

    def loadInfo(self, iteminfo, modulesourceid, itemid):
        if itemid != self.parent.currentItem:
            return
        if modulesourceid != self.parent.currentModuleSource:
            return

        print(iteminfo)


############################################
# Main window
############################################
class window(Gtk.Window):
    def __init__(self, parent):
        Gtk.Window.__init__(self)
        self.parent = parent
        self.connect('delete-event', partial(parent.windowClosed, "wnd"))
        self.splashtext = None
        self.wndstack = None

        #These three are used to skip page updating code whenever otherwise inappropriate to continue execution of, such as dropdown changes and so on.
        self.currentItem = ""
        self.currentModuleSource = ""
        self.currentSubsource = ""

        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_title(_("Feren Storium API Demo - GUI Module"))
        self.set_default_size(850, 640)
        self.set_size_request(850, 540)
        self.known_itemboxes = [] #Current known item boxes in the GUI


    def spawn(self, eventtrigger=None):
        #When using spawn, it means the window hasn't been opened yet, so we need to initialise it first, thus a splash screen is used
        GLib.idle_add(self.initSplash, eventtrigger)
        #Fully load the GUI if the Backend has already finished initialising.
        if self.parent.api.isInitialised() == True:
            GLib.idle_add(self.initComplete)


    def initSplash(self, eventtrigger):
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
        self.show_all()
        if eventtrigger != None: #Initial spawnGUI() blocks until now so that spawn() does not run twice during init
            eventtrigger.set()


    def initComplete(self):
        if self.get_realized() == False:
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
        header.pack_start(logoimageandbox, False, False, 0)

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
        result.pack_end(menu_btn, False, False, 0)

        result.pack_end(self.pageswitcher, False, False, 0)

        return result

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
        self.appspage = categoricalPage(self, self.parent)
        self.gamespage = categoricalPage(self, self.parent)
        self.themespage = categoricalPage(self, self.parent)
        self.websitespage = categoricalPage(self, self.parent)
        self.taskspage = tasksLibraryPage(self, self.parent)
        self.searchpage = Gtk.VBox()
        self.itempage = self.itemPage()
        # TODO: Callback to GUI, during module reinitialisation, to do tasks including refreshing the categories shown in the pages of the GUI
        self.extraspage = None

        subresult = Gtk.Stack()
        subresult.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        subresult.get_style_context().add_class(Gtk.STYLE_CLASS_VIEW)

        for i in [self.homepage, self.taskspage, self.searchpage]:
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

    def gotoID(self, itemid, moduleid="", sourceid="", subsourceid=""):
        GLib.idle_add(self.body.set_visible_child, self.itempage)

        #Get the available sources of the item, and switch to the appropriate source
        self.currentItem = itemid
        thread = Thread(target=self.itempage.header.loadSources,
                        args=(itemid, moduleid, sourceid, subsourceid))
        thread.daemon = True
        thread.start()

        #TODO: Tell header to load available sources
        # Then the header can tell itself and body to load the item information of the default source
        #TODO: Any way to prevent source changing twice technically if we supply a command to open Storium immediately to an item with a source override and module override?


    ############################################
    # Item page
    ############################################

    def itemPage(self):
        result = Gtk.Stack()
        result.loading = Gtk.VBox()
        result.loading.get_style_context().add_class(Gtk.STYLE_CLASS_VIEW)
        result.loaded = Gtk.VBox()
        result.loadspin = Gtk.Spinner()

        #Item information header
        itemdetailsheader = itemDetailsHeader(self, self.parent)
        result.header = itemdetailsheader

        #Item information area
        result.bodyloaded = Gtk.ScrolledWindow()
        result.bodyloaded.get_style_context().add_class(Gtk.STYLE_CLASS_VIEW)
        result.bodyloaded.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        result.iteminfo = itemInfoBody(self, self.parent)
        result.bodyloaded.add(result.iteminfo)

        result.body = Gtk.Stack()
        result.body.get_style_context().add_class(Gtk.STYLE_CLASS_VIEW)
        result.bodyloading = Gtk.VBox()
        result.bodyloadspin = Gtk.Spinner()

        #Putting it all together
        result.loading.pack_start(Gtk.Box(), True, True, 0)
        result.loading.pack_end(Gtk.Box(), True, True, 0)
        result.loading.pack_start(result.loadspin, False, False, 0)
        result.add_named(result.loading, "loading")
        result.add_named(result.loaded, "loaded")

        result.bodyloading.pack_start(Gtk.Box(), True, True, 0)
        result.bodyloading.pack_end(Gtk.Box(), True, True, 0)
        result.bodyloading.pack_start(result.bodyloadspin, False, False, 0)
        result.body.add_named(result.bodyloading, "loading")
        result.body.add_named(result.bodyloaded, "loaded")

        result.loaded.pack_start(itemdetailsheader, False, False, 0)
        result.loaded.pack_start(Gtk.Separator(), False, False, 0)
        result.loaded.pack_end(result.body, True, True, 0)
        return result


    def loadItemInformation(self, modulesourceid, itemid):
        if itemid != self.currentItem:
            return #Do not run if the item being viewed is not itemid
        if modulesourceid != self.currentModuleSource:
            return #Do not run if the source being viewed is not this

        #Just in case
        GLib.idle_add(self.itempage.bodyloadspin.start)
        GLib.idle_add(self.itempage.body.set_visible_child, self.itempage.bodyloading)
        GLib.idle_add(self.itempage.header.itemicon.set_visible_child, self.itempage.header.itemicon.loading)
        GLib.idle_add(self.itempage.header.fullname.set_label, "")
        GLib.idle_add(self.itempage.header.summary.set_label, "")

        #Get split values for source and module IDs
        moduleid, sourceid = modulesourceid.split("/")
        #FIXME: We'd need to change this to only split the final / and not precursor ones

        iteminfo = self.parent.api.getItemInformation(itemid, moduleid, sourceid)
        self.itempage.header.loadInfo(iteminfo, modulesourceid, itemid)
        self.itempage.iteminfo.loadInfo(iteminfo, modulesourceid, itemid)

        GLib.idle_add(self.itempage.body.set_visible_child, self.itempage.bodyloaded)
        GLib.idle_add(self.itempage.bodyloadspin.stop)


############################################
# Module initialisation and Brain responder
############################################
class module():
    def __init__(self, genericapi, guiapi, unused):
        self.api = genericapi
        self.guiapi = guiapi
        self.configs = None #Filled by Brain
        #Initialised by initGUI
        self.desktoasts = None
        self.changeswnd = None
        self.errorwnd = None
        self.configwnd = None
        self.wnd = None

    def initGUI(self):
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
        time.sleep(0.4) #Give GTK time to launch as rushed launches lead to an X Window Error when spawning the windows

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


    def spawnGUI(self, command="", targetid="", moduleid="", sourceid="", subsourceid="", wait=False):
        #Open main window and direct it with arguments
        # If the window is already loaded, focus it first
        if self.wnd.get_realized() == True: #realized is False until the window's shown
            GLib.idle_add(self.wnd.present)
        else: #If not loaded, it has to spawn first
            if wait == True:
                event = Event()
                self.wnd.spawn(event)
                event.wait()
            else:
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
        modulecategories = self.guiapi.getCustomCategories()
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
        self.wnd.appspage.setCategories(toadd["apps"])
        self.wnd.gamespage.setCategories(toadd["games"])
        self.wnd.themespage.setCategories(toadd["themes"])
        self.wnd.websitespage.setCategories(toadd["websites"])
        #Destroy extras if unused
        if toadd["extras"] == {}:
            if self.wnd.extraspage != None:
                GLib.idle_add(self.wnd.pages.remove, self.wnd.extraspage)
                GLib.idle_add(self.wnd.extraspage.destroy)
                self.wnd.extraspage = None
        else:
            if self.wnd.extraspage == None: #Create extras if currently non-existant
                self.wnd.extraspage = categoricalPage(self.wnd, self)
                GLib.idle_add(self.wnd.pages.add_titled, self.wnd.extraspage, "extras", _("Extras"))
                GLib.idle_add(self.wnd.extraspage.show_all)
            #Irregardless, add categories to Extras page
            self.wnd.extraspage.setCategories(toadd["extras"])

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
        self.wndcontents.pack_start(self.maintoolbar, False, False, 0)
        self.wndcontents.pack_start(self.detailsheader, False, False, 0)
        self.wndcontents.pack_end(self.pagearea, True, True, 0)
        GLib.idle_add(self.show_all)

        self.pagearea.populate_mainpage()



    def refresh_memory(self):
        pass





    # API CALLS FOR CLASSES
    #TODO: Update these
    def gotoID(self, itemid, moduleid="", sourceid="", subsourceid=""):
        thread = Thread(target=self.wnd.gotoID,
                            args=(itemid, moduleid, sourceid, subsourceid))
        thread.start()

    def showTaskConfirmation(self, taskbody, idsadded, idsupdated, idsremoved, bonusavailability):
        #TODO: Make an actual GUI for this
        print("Opened dialog to confirm pending operation of " + str(taskbody.operation) + " to " + taskbody.itemid + " of module" + taskbody.moduleid + " in source " + taskbody.sourceid + ", " + taskbody.subsourceid)

        if len(idsadded) == 0 and len(idsupdated) == 0 and len(idsremoved) == 0 and len(bonusavailability) == 0:
            return True, [] #Skip the confirmation if there is nothing extra to confirm

        GLib.idle_add(self.changeswnd.prepare, self.api, taskbody, idsadded, idsupdated, idsremoved, bonusavailability)
        return self.changeswnd.run()

    def refreshTasksPage(self):
        if self.wnd is None:
            return
        self.wnd.taskspage.refreshTasksList()

    def refreshItemStatus(self, itemid, moduleid, sourceid):
        modulesourceid = moduleid + "/" + sourceid
        #TODO: Exception catcher for if blocks are changed during this signal
        for i in self.wnd.known_itemboxes:
            if i.itemid == itemid and i.moduleid == moduleid and i.sourceid == sourceid:
                #Reload status on existing itemboxes
                thread = Thread(target=i.loadStatus,
                                args=())
                thread.daemon = True
                thread.start()
        self.wnd.itempage.header.loadStatus(modulesourceid, itemid)
