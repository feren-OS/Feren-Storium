#Dependencies
import time
import gettext
import json
from threading import Thread
import copy
import subprocess
import dbus
from dbus.mainloop.glib import DBusGMainLoop

class FlatpakModuleException(Exception):
    pass


class module():

    def __init__(self, genericapi, itemapi, systemmode):
        #Gettext Translator
        gettext.install("feren-storium-flatpakitemmgmt", "/usr/share/locale", names="ngettext")
        
        #Storium APIs
        self.api = genericapi
        self.itemapi = itemapi
        
        #Package Storage will store the data of opened packages this instance, to make future loads faster
        self.itemcache = {}

        #Refresh memory for the first time
        self.refreshMemory()

        #Manage theme lock on context-appropriate Flatpaks
        if systemmode == True:
            self.addGTKOverrides() #TODO: Also make a thread
        else:
            mainloop = DBusGMainLoop()
            self.interface = dbus.SessionBus(mainloop=mainloop).get_object("org.freedesktop.portal.Desktop", "/org/freedesktop/portal/desktop")
            self.interface = dbus.Interface(self.interface, "org.freedesktop.portal.Settings")
            self.interface.connect_to_signal('SettingChanged', self.themePreferenceChanged)
        self.refreshThemeLock(systemmode) #TODO: Make thread

        
    def refreshMemory(self): # Function to refresh some memory values
        #self.memory_refreshing = True

        self.itemcache = {}
        with open("/usr/share/feren-storium/curated/flatpak/items.json", 'r') as fp:
            self.itemcache = json.loads(fp.read())
        
        #self.memory_refreshing = False


    ############################################
    # Theme Lock
    ############################################

    def refreshThemeLock(self, systemmode=False):
        #TODO: When implementing this module in full, only enact this on the installed Flatpaks
        #TODO: Add 'themelocktype' value to metadata if ever needed
        if systemmode == True: #Change job to do depending on if system mode or userland
            overridesfile = "/var/lib/flatpak/overrides/"
            overridecommand = ["/usr/bin/flatpak", "--system", "override", "--env=GTK_THEME=", ""]
            self.setGTKThemeLock(self, overridesfile, overridecommand, "Adwaita")
        else:
            value = "0" #Assume no preference by default
            try:
                value = self.interface.Read("org.freedesktop.appearance", "color-scheme")
            except Exception as e:
                #TODO: Check for debug preference
                print(_("Could not detect user's theme preference: %s") % e)
            self.themePreferenceChanged("org.freedesktop.appearance", "color-scheme", value)

    def setGTKThemeLock(self, overridesfile, overridecommand, themeid):
        for i in self.itemcache:
            if self.itemcache[i]["all"]["respectsnativetheme"] != "forcedoff":
                continue #Skip Flatpaks that do not have theme lock on them
            #TODO: Store themelocked Flatpaks in a system/user config file for the module, and also add a means to disable theme lock, so that Flatpaks no longer theme locked can be un-themelocked
            fpakid = self.itemcache[i]["all"]["flatpakID"]
            #Check that the Flatpak has the necessary theme set as its override
            with open(overridesfile+fpakid, 'r') as fp:
                environmentreached = False
                gtkthemeline = ""
                for i in fp.readlines(): #Obtain the GTK_THEME line, if there is one
                    if i.startswith("[Environment]"):
                        environmentreached = True
                    elif i.startswith("[") and environmentreached == True:
                        break #Exit the loop after environment settings're read
                    elif i.startswith("GTK_THEME=") and environmentreached == True:
                        gtkthemeline = i
                        break #We have what we came for
            gtkthemeline=gtkthemeline.strip() #Remove \n and such
            if gtkthemeline == "GTK_THEME="+themeid:
                continue #Skip if the theme lock is already set as intended
            shouldthemelock = False
            #Determine if we should apply a theme lock
            themelockrequirements = ["Adwaita", "feren", "feren-dark", "Inspire", "Inspire Dark"]
            for i in themelockrequirements:
                if gtkthemeline == "GTK_THEME="+i or gtkthemeline == "GTK_THEME="+i+":light" or gtkthemeline == "GTK_THEME="+i+":dark":
                    shouldthemelock = True
            if shouldthemelock != True:
                continue #Skip if the user has a custom theme forced.
            #Now requirements are satisfied, apply the requested theme lock
            overridecommand[-1] == fpakid
            overridecommand[-2] == "--env=GTK_THEME="+themeid
            subprocess.Popen(overridecommand)


    def addGTKOverrides(self):
        pass #TODO: Add filesystem path global overrides

    def themePreferenceChanged(self, path, intent, value):
        if path != "org.freedesktop.appearance" or intent != "color-scheme":
            return #Ignore other signals
        overridesfile = os.path.expanduser("~") + "/.local/share/flatpak/overrides/"
        overridecommand = ["/usr/bin/flatpak", "--user", "override", "--env=GTK_THEME=", ""]
        if value == "0" or value == "2": #No preference and light preference are basically the same due to a bug in GTK, so we might as well merge them here.
            self.setGTKThemeLock(overridesfile, overridecommand, "Adwaita:light")
        elif value == "1":
            self.setGTKThemeLock(overridesfile, overridecommand, "Adwaita:dark")




    ############################################
    # Item Information
    ############################################
        
    def getCustomCategories(self):
        return {} #TODO
    
    def getItemsFromCategory(self, category):
        return [] #TODO

    def getItemInformation(self, itemid, sourceid):
        result = {}
        if sourceid not in self.itemcache[itemid] and "all" not in self.itemcache[itemid]:
            raise ExampleModuleException(_("%s does not exist in source %s") % (itemid, sourceid))
        if "all" in self.itemcache[itemid]:
            result = self.api.dictMerge(result, self.itemcache[itemid]["all"])
        if sourceid in self.itemcache[itemid]: #Merge information from specific source over all
            result = self.api.dictMerge(result, self.itemcache[itemid][sourceid])
        return result
