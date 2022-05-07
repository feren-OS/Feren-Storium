import configparser
import os
import subprocess
import gettext
import gi


#Dependencies
import json
import shutil
import ast
import signal
import time
from gi.repository import GLib
import colorsys
from urllib import parse
sys.path.insert(0, "/usr/lib/feren-storium/modules/packagemgmt/peppermint-ice")
import moduleshared


class ICEModuleException(Exception): # Name this according to the module to allow easier debugging
    pass


class module():

    def __init__(self, storeapi):
        #Gettext Translator
        gettext.install("feren-storium", "/usr/share/locale", names="ngettext")
        
        #Store APIs
        self.storebrain = storebrain

        #Name to be used in Debugging output
        self.title = _("Ice Management Module")
        #Name to be shown in the GUI
        self.humanreadabletitle = _("Ice Application Management")
        #Name to be shown in sources
        self.sourcesmodulename = _("Website Application")
        
        #Package Storage will store the data of opened packages this instance, to make future loads faster
        self.packagestorage = {}
        
        #Configs (obtained by get_configs)
        self.moduleconfigs={}
        self.get_configs()
        
        #Lock to keep stuff from happening while memory is refreshing
        self.memory_refreshing = False
        
        #What package types does this module work with?
        self.types_supported = ["peppermint-ice"]
        
        #////Package Management:////
        #Can manage Application Sources?
        self.canmanagesources = False
        #Current name being managed
        self.busywithpackage = ""
        #Do subsources require an information change?
        self.subsourceschangeinfo = False #False because no subsources
        
        #Application Sources (for ICE let's have the sources be the browsers that're supported)
        # Empty here, will be appended to with self.refresh_memory()
        self.applicationsources = []        
        
        #Global Ice last updated date (so that all shortcuts can be updated if a major change occurs)
        self.icelastupdated = "20220329"
        
        #Module shared parts
        self.moduleshared = moduleshared.main()
        
    def refresh_memory(self): # Function to refresh some memory values
        self.memory_refreshing = True

        self.json_storage = {}

        for i in ["package-info/peppermint-ice", "package-info/generic"]:
            with open("/usr/share/feren-storium/curated/" + i + "/data.json", 'r') as fp:
                self.json_storage[i] = json.loads(fp.read())
        
        self.sources_storage = {}
            
        for i in ["package-sources-info/generic"]:
            with open("/usr/share/feren-storium/curated/" + i + "/data.json", 'r') as fp:            
                self.sources_storage[i] = json.loads(fp.read())["peppermint-ice"]
        
        self.memory_refreshing = False
        
        
    #////Package Management////
    def getSources(self, pkgid):
        #TODO: Check package even has a Website Application source in the first place
        
        #Construct subsources for the only source
        subsources = []
        for browser in self.sources_storage["package-sources-info/generic"]["sources"]:
            if os.path.isfile(self.sources_storage["package-sources-info/generic"]["sources"][browser]["repository-file"]):
                subsources.append(browser)
        
        #Return complete sources value
        return {"peppermint-ice": {"peppermint-ice": subsources}}
    
    
    def getAvailable(self, pkgid, sourceid):
        #Check if package even exists in the first place
        #Return values:
        #0: Available
        #1: Unavailable
        #2: Repository requires being added first
        
        return 0 #of course Website Applications are available.
    
        
    def pkgstorage_add(self, packagename):
        #Not needed as we just consult the package information modules for information anyway
        
        #If it was, this'd be the intended structure?:
        # [pkgtype][all][packagename] for the package information on all sources
        # [pkgtype][x][packagename] for the package information on x source
        #we need pkgtype to determine the right section to store it in
        
        pass
    
    
    def get_status(self, pkgid, pkgtype, sourceid):
        # Return package installation status
        # 0 - Uninstalled
        # 1 - Installed
        # 2 - Updatable
        # 3 - Available in a disabled source
        # 403 - Not in repositories
        
        if os.path.isfile(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-last-updated" % pkgid):
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-last-updated" % pkgid, 'r') as fp:
                lastupdated = fp.readline()
        else:
            lastupdated = "19700101" #Fallback date, and yes it's beginning of UNIX time - why not
        
        if os.path.isdir(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s" % pkgid):
            #TODO: Change this to use own item information obtaining
            if self.storebrain.get_item_info_specific(pkgid, pkgtype, sourceid, True)["icelastupdated"] > lastupdated or self.icelastupdated > lastupdated:
                return 2
            else:
                return 1
        else:
            return 0
    
    
    def cleanupModule(self):
        #Cleanup after package operations
        self.currentpackagename = ""
        self.packagemgmtbusy = False
        
    
    def get_package_changes(self, pkgid, operationtype, pkgtype, sourceid, subsourceid):
        #Return empty values as there is no extra items being added... only bonuses being added.
        return {"install": [], "update": [], "remove": [], "sourceadd": [], "sourceremove": []}
        
    
    #Application management
    def task_install_package(self, taskdata, progress_callback):
        #Install package and return exit code
        self.packagemgmtbusy = True
        self.currentpackagename = taskdata["packagename"]
        
        windowclassid = taskdata["packagename"]
        if taskdata["source"] == "vivaldi": #FIXME: Temporary until Vivaldi adds proper shadows support
            windowclassid = "vivaldi-" + taskdata["packagename"]
        
        #TODO: Refactor this after Tasks are refactored
        icepackageinfo = taskdata["pkginfo"]
        if "extrasids" in icepackageinfo:
            iceextrasids = icepackageinfo["extrasids"]
        else:
            iceextrasids = []
        if "bonuses" in taskdata:
            icebonuses = taskdata["bonuses"]
        else:
            icebonuses = []
        
        #First remove the files just in case there's a partial installation
        self.task_remove_package(taskdata, None, True)
        
        #Create the .desktop file's home if it doesn't exist
        if not os.path.isdir(os.path.expanduser("~") + "/.local/share/applications"):
            try:
                os.mkdir(os.path.expanduser("~") + "/.local/share/applications")
            except Exception as exceptionstr:
                raise ICEModuleException(_("Failed to install {0}: {1} was encountered when trying to create the shortcut's location").format(taskdata["packagename"], exceptionstr))
            
            
        progress_callback(12)        
        #Titlebar branding
        #if "icecolor" in icepackageinfo:
            #TODO
            #os.system("qdbus org.kde.KWin /KWin reconfigure")
            
            
        #Create the Chromium profile
        if not os.path.isdir(os.path.expanduser("~") + "/.local/share/feren-storium-ice"):
            try:
                os.mkdir(os.path.expanduser("~") + "/.local/share/feren-storium-ice")
            except Exception as exceptionstr:
                raise ICEModuleException(_("Failed to install {0}: {1} was encountered when trying to create the profiles location").format(taskdata["packagename"], exceptionstr))
        if not os.path.isdir(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s" % taskdata["packagename"]):
            try:
                os.mkdir(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s" % taskdata["packagename"])
            except Exception as exceptionstr:
                raise ICEModuleException(_("Failed to install {0}: {1} was encountered when trying to create the profile's folder").format(taskdata["packagename"], exceptionstr))
            
            
        progress_callback(24)
            
        
        try:
            os.mkdir(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/Default" % taskdata["packagename"])
        except Exception as exceptionstr:
            self.task_remove_package(taskdata, None, True) #Remove profile's files/folders on failure
            raise ICEModuleException(_("Failed to install {0}: {1} was encountered when making the Chromium-based profile").format(taskdata["packagename"], exceptionstr))
        
        
        progress_callback(36)
            
        
        usefallbackicon = False
        #Copy icon for package
        try:
            shutil.copy(self.storebrain.tempdir + "/icons/" + taskdata["packagename"], os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/icon" % taskdata["packagename"])
        except Exception as exceptionstr:
            usefallbackicon = True
            
            
        progress_callback(48)
            
        
        
        #Now to make the JSON file
        profiletomake = self.moduleshared.set_default_settings_chromi({}, icepackageinfo["website"], icepackageinfo["realname"], icepackageinfo["iconuri"])
        
        profiletomake = self.moduleshared.append_default_extras_settings_chromi(profiletomake, iceextrasids, icepackageinfo["websiteextras"], icepackageinfo["realnameextras"])
            
        profiletomake = self.moduleshared.set_ice_privacy_chromi(profiletomake, not icepackageinfo["icenohistory"], icepackageinfo["icegoogleinteg"], icepackageinfo["icegooglehangouts"])
        
        profiletomake = self.moduleshared.append_ice_extras_chromi(profiletomake, taskdata["bonuses"])
        
        profiletomake = self.moduleshared.append_theme_colours(profiletomake, not icepackageinfo["icecolor"], icepackageinfo["icecolorhighlight"], icepackageinfo["icecolordark"])
        
        progress_callback(60)
        
        #Write profile
        try:
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/Default/Preferences" % taskdata["packagename"], 'w') as fp:
                fp.write(json.dumps(profiletomake, separators=(',', ':'))) # This dumps minified json (how convenient), which is EXACTLY what Chrome uses for Preferences, so it's literally pre-readied
        except Exception as exceptionstr:
            self.task_remove_package(taskdata, None, True) #Remove profile's files/folders on failure
            raise ICEModuleException(_("Failed to install {0}: {1} was encountered when writing the Chromium-based profile").format(taskdata["packagename"], exceptionstr))
        
        
        profiletomake = self.moduleshared.set_local_state({})
        
        #Write Local State
        try:
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/Local State" % taskdata["packagename"], 'w') as fp:
                fp.write(json.dumps(profiletomake, separators=(',', ':'))) # This dumps minified json (how convenient), which is EXACTLY what Chrome uses for Preferences, so it's literally pre-readied
        except Exception as exceptionstr:
            self.task_remove_package(taskdata, None, True) #Remove profile's files/folders on failure
            raise ICEModuleException(_("Failed to install {0}: {1} was encountered when writing the Chromium-based profile").format(taskdata["packagename"], exceptionstr))
        
        
        self.moduleshared.profile_finishing_touches(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s" % taskdata["packagename"], taskdata["source"], not icepackageinfo["icenohistory"], taskdata["bonuses"])
            
        progress_callback(72)
        
        
        self.moduleshared.create_shortcuts(icepackageinfo["realname"], taskdata["packagename"], True, taskdata["source"], icepackageinfo["website"], icepackageinfo["category"], icepackageinfo["keywords"], windowclassid)
        self.moduleshared.create_extra_shortcuts(icepackageinfo["realname"], taskdata["packagename"], taskdata["source"], icepackageinfo["category"], iceextrasids, icepackageinfo["websiteextras"], icepackageinfo["realnameextras"], icepackageinfo["iconuriextras"], icepackageinfo["keywordsextras"], windowclassid)
            
        progress_callback(100)
        
        return True
    
    
    def task_remove_package(self, taskdata, progress_callback, forinstall=False):
        if os.path.isfile(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-active-pid" % taskdata["packagename"]):
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-active-pid" % taskdata["packagename"], 'r') as pidfile:
                currentpid = pidfile.readline()
                try:
                    currentpid = int(currentpid)
                    os.kill(currentpid, signal.SIGKILL) #Kill the process immediately, so we can remove it
                    time.sleep(0.4) #Should give enough time for everything to clear out process-wise
                except:
                    pass
        
        if not forinstall: # We call this in the install process to clear out partial installs, so for those times we want to skip THIS code to not confuse Store's Brain or anything that could get confused from this module 'unlocking' temporarily
            self.packagemgmtbusy = True
            self.currentpackagename = taskdata["packagename"]
        
        icepackageinfo = taskdata["pkginfo"]
        if "extrasids" in icepackageinfo:
            iceextrasids = iceextrasids
        else:
            iceextrasids = []
        
        #Delete the files and the folders and done
        if os.path.isfile(os.path.expanduser("~") + "/.local/share/color-schemes/%s.colors" % taskdata["packagename"]):
            try:
                os.remove(os.path.expanduser("~") + "/.local/share/color-schemes/%s.colors" % taskdata["packagename"])
                #TODO: Remove window rule
            except Exception as exceptionstr:
                if not forinstall:
                    raise ICEModuleException(_("Failed to uninstall {0}: {1} was encountered when removing the colour scheme").format(taskdata["packagename"], exceptionstr))
            #os.system("qdbus org.kde.KWin /KWin reconfigure")
        
        
        
        
        try:
            if os.path.isfile(os.path.expanduser("~") + "/.local/share/applications/%s.desktop" % taskdata["packagename"]):
                os.remove(os.path.expanduser("~") + "/.local/share/applications/%s.desktop" % taskdata["packagename"])
            if os.path.isfile(os.path.expanduser("~") + "/.local/share/applications/vivaldi-%s.desktop" % taskdata["packagename"]):
                os.remove(os.path.expanduser("~") + "/.local/share/applications/vivaldi-%s.desktop" % taskdata["packagename"])
        except Exception as exceptionstr:
            if not forinstall:
                raise ICEModuleException(_("Failed to uninstall {0}: {1} was encountered when removing the shortcut from the Applications Menu").format(taskdata["packagename"], exceptionstr))
        
        #Now repeat for extras, if appropriate
        extrascount = 0 #Classic strat for iteration
        for extraid in iceextrasids:
            try:
                if os.path.isfile(os.path.expanduser("~") + "/.local/share/applications/{0}-{1}.desktop".format(taskdata["packagename"], extraid)):
                    os.remove(os.path.expanduser("~") + "/.local/share/applications/{0}-{1}.desktop".format(taskdata["packagename"], extraid))
            except Exception as exceptionstr:
                self.task_remove_package(taskdata, None, True) #Remove profile's files/folders on failure
                raise ICEModuleException(_("Failed to uninstall {0}: {1} was encountered when removing extra shortcuts from the Applications Menu").format(taskdata["packagename"], exceptionstr))
            extrascount += 1
            
        if not forinstall:
            progress_callback(50)
        
        try:
            shutil.rmtree(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s" % taskdata["packagename"])
        except Exception as exceptionstr:
            if not forinstall:
                raise ICEModuleException(_("Failed to uninstall {0}: {1} was encountered when deleting the Chromium-based profile").format(taskdata["packagename"], exceptionstr))
        
        if not forinstall:
            progress_callback(100)
        
        return True
    
    
    def task_update_package(self, taskdata, progress_callback):
        
        #Update package and return exit code
        self.packagemgmtbusy = True
        self.currentpackagename = taskdata["packagename"]
        
        windowclassid = taskdata["packagename"]
        if taskdata["source"] == "vivaldi": #FIXME: Temporary until Vivaldi adds proper shadows support
            windowclassid = "vivaldi-" + taskdata["packagename"]
            try:
                if os.path.isfile(os.path.expanduser("~") + "/.local/share/applications/%s.desktop" % taskdata["packagename"]):
                    os.remove(os.path.expanduser("~") + "/.local/share/applications/%s.desktop" % taskdata["packagename"])
            except Exception as exceptionstr:
                raise ICEModuleException(_("Failed to update {0}: {1} was encountered when switching the shortcut in the Applications Menu").format(taskdata["packagename"], exceptionstr))
        else:
            try:
                if os.path.isfile(os.path.expanduser("~") + "/.local/share/applications/vivaldi-%s.desktop" % taskdata["packagename"]):
                    os.remove(os.path.expanduser("~") + "/.local/share/applications/vivaldi-%s.desktop" % taskdata["packagename"])
            except Exception as exceptionstr:
                raise ICEModuleException(_("Failed to update {0}: {1} was encountered when switching the shortcut in the Applications Menu").format(taskdata["packagename"], exceptionstr))
        
        icepackageinfo = taskdata["pkginfo"]
        if "extrasids" in icepackageinfo:
            iceextrasids = iceextrasids
        else:
            iceextrasids = []
        
        if os.path.isfile(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-active-pid" % taskdata["packagename"]):
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-active-pid" % taskdata["packagename"], 'r') as pidfile:
                currentpid = pidfile.readline()
            pidisrunning = False
            try:
                currentpid = int(currentpid)
                try:
                    os.kill(currentpid, 0) #Send a You There? to the PID identified
                    pidisrunning = True #If we didn't just cause an exception by doing that, the PID exists
                except:
                    pass
            except:
                try:
                    os.kill(currentpid, signal.SIGTERM) #Fallback since we don't know if it's running or not
                    time.sleep(0.4)
                except:
                    pass
            if pidisrunning == True:
                raise ICEModuleException(_("Failed to update {0}: Running Website Applications cannot be updated until they are closed").format(taskdata["packagename"]))
        
        #Create the .desktop file's home if it doesn't exist
        if not os.path.isdir(os.path.expanduser("~") + "/.local/share/applications"):
            try:
                os.mkdir(os.path.expanduser("~") + "/.local/share/applications")
            except Exception as exceptionstr:
                raise ICEModuleException(_("Failed to update {0}: {1} was encountered when trying to create the shortcut's location").format(taskdata["packagename"], exceptionstr))
        
        
        #Titlebar branding
        #if "icecolor" in icepackageinfo:
            #self.color_scheme_iding(icepackageinfo["icecolor"], taskdata, icepackageinfo["icecolorhighlight"])
            #os.system("qdbus org.kde.KWin /KWin reconfigure")
            
            
        progress_callback(12)
            
        #Get some data from the files
        #if os.path.isfile(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-default-browser" % taskdata["packagename"]):
            #with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-default-browser" % taskdata["packagename"], 'r') as fp:
                #currenticebrowser = fp.readline()
        #else:
            #currenticebrowser = taskdata["source"] #Fallback
        #TODO: Move above to determining current subsource
        if os.path.isfile(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-extra-ids" % taskdata["packagename"]):
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-extra-ids" % taskdata["packagename"], 'r') as fp:
                currenticeextraids = ast.literal_eval(fp.readline())
        else:
            currenticeextraids = [] #Fallback
        if os.path.isfile(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-bonuses" % taskdata["packagename"]):
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-bonuses" % taskdata["packagename"], 'r') as fp:
                currenticebonuses = ast.literal_eval(fp.readline())
        else:
            currenticebonuses = [] #Fallback
        if "bonuses" in taskdata:
            currenticebonuses.extend(taskdata["bonuses"])
            
            
        progress_callback(24)
            
        try:
            if not os.path.isfile(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/First Run" % taskdata["packagename"]):
                with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/First Run" % taskdata["packagename"], 'w') as fp:
                    pass
        except Exception as exceptionstr:
            raise ICEModuleException(_("Failed to update {0}: {1} was encountered when updating the Chromium-based profile").format(taskdata["packagename"], exceptionstr))
        try:
            if not os.path.isdir(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/Default" % taskdata["packagename"]):
                os.mkdir(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/Default" % taskdata["packagename"])
        except Exception as exceptionstr:
            raise ICEModuleException(_("Failed to update {0}: {1} was encountered when updating the Chromium-based profile").format(taskdata["packagename"], exceptionstr))
        
        progress_callback(36)
            
        
        usefallbackicon = False
        #Copy icon for package
        try:
            if os.path.isfile(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/icon" % taskdata["packagename"]):
                os.remove(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/icon" % taskdata["packagename"])
        except Exception as exceptionstr:
            raise ICEModuleException(_("Failed to update {0}: {1} was encountered when updating the application icon").format(taskdata["packagename"], exceptionstr))
        try:
            shutil.copy(self.storebrain.tempdir + "/icons/" + taskdata["packagename"], os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/icon" % taskdata["packagename"])
        except Exception as exceptionstr:
            usefallbackicon = True
            
            
        progress_callback(48)
            
        
        
        #Now to update the JSON file
        with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/Preferences", 'r') as fp:
            profiledefaults = json.loads(fp.read())
            
        try:
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/Default/Preferences" % taskdata["packagename"], 'r') as fp:
                profiletoupdate = json.loads(fp.read())
        except Exception as exceptionstr:
            raise ICEModuleException(_("Failed to update {0}: {1} was encountered when reading the browser profile (is the profile corrupt?)").format(taskdata["packagename"], exceptionstr))
        
        #Remove the custom links (Chromiums) before adding default shortcut back in and updating it again
        profiletoupdate["custom_links"] = {}
        
        profiletoupdate = self.storebrain.dict_recurupdate(profiletoupdate, profiledefaults)
        
        
        #Update extensions permissions too
        with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/and-plasmaintegration", 'r') as fp:
            profiletoupdateextra = json.loads(fp.read())
            for item in profiletoupdateextra["extensions"]["settings"]:
                if item in profiletoupdate["extensions"]["settings"]:
                    profiletoupdateextra["extensions"]["settings"][item].pop("path", None)
                    profiletoupdateextra["extensions"]["settings"][item]["manifest"].pop("name", None)
                    profiletoupdateextra["extensions"]["settings"][item]["manifest"].pop("version", None) #Prevent the extension version and name from reverting
        profiletoupdate = self.storebrain.dict_recurupdate(profiletoupdate, profiletoupdateextra)
        if "nekocap" in currenticebonuses:
            with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/and-nekocap", 'r') as fp:
                profiletoupdateextra = json.loads(fp.read()) #This is how you make json.load work with file paths, I guess
                for item in profiletoupdateextra["extensions"]["settings"]:
                    if item in profiletoupdate["extensions"]["settings"]:
                        profiletoupdateextra["extensions"]["settings"][item].pop("path", None)
                        profiletoupdateextra["extensions"]["settings"][item]["manifest"].pop("name", None)
                        profiletoupdateextra["extensions"]["settings"][item]["manifest"].pop("version", None)
            profiletoupdate = self.storebrain.dict_recurupdate(profiletoupdate, profiletoupdateextra)
        if "ublock" in currenticebonuses:
            with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/and-ublock", 'r') as fp:
                profiletoupdateextra = json.loads(fp.read())
                for item in profiletoupdateextra["extensions"]["settings"]:
                    if item in profiletoupdate["extensions"]["settings"]:
                        profiletoupdateextra["extensions"]["settings"][item].pop("path", None)
                        profiletoupdateextra["extensions"]["settings"][item]["manifest"].pop("name", None)
                        profiletoupdateextra["extensions"]["settings"][item]["manifest"].pop("version", None)
            profiletoupdate = self.storebrain.dict_recurupdate(profiletoupdate, profiletoupdateextra)
        if "darkreader" in currenticebonuses:
            with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/and-darkreader", 'r') as fp:
                profiletoupdateextra = json.loads(fp.read())
                for item in profiletoupdateextra["extensions"]["settings"]:
                    if item in profiletoupdate["extensions"]["settings"]:
                        profiletoupdateextra["extensions"]["settings"][item].pop("path", None)
                        profiletoupdateextra["extensions"]["settings"][item]["manifest"].pop("name", None)
                        profiletoupdateextra["extensions"]["settings"][item]["manifest"].pop("version", None)
            profiletoupdate = self.storebrain.dict_recurupdate(profiletoupdate, profiletoupdateextra)
        if "imagus" in currenticebonuses:
            with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/and-imagus", 'r') as fp:
                profiletoupdateextra = json.loads(fp.read())
                for item in profiletoupdateextra["extensions"]["settings"]:
                    if item in profiletoupdate["extensions"]["settings"]:
                        profiletoupdateextra["extensions"]["settings"][item].pop("path", None)
                        profiletoupdateextra["extensions"]["settings"][item]["manifest"].pop("name", None)
                        profiletoupdateextra["extensions"]["settings"][item]["manifest"].pop("version", None)
            profiletoupdate = self.storebrain.dict_recurupdate(profiletoupdate, profiletoupdateextra)
        if "googleytdislikes" in currenticebonuses:
            with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/and-googleytdislikes", 'r') as fp:
                profiletoupdateextra = json.loads(fp.read())
                for item in profiletoupdateextra["extensions"]["settings"]:
                    if item in profiletoupdate["extensions"]["settings"]:
                        profiletoupdateextra["extensions"]["settings"][item].pop("path", None)
                        profiletoupdateextra["extensions"]["settings"][item]["manifest"].pop("name", None)
                        profiletoupdateextra["extensions"]["settings"][item]["manifest"].pop("version", None)
            profiletoupdate = self.storebrain.dict_recurupdate(profiletoupdate, profiletoupdateextra)
        
        
        #Extra site-specific tweaks
        profiletoupdate["homepage"] = icepackageinfo["website"]
        profiletoupdate["custom_links"]["list"][0]["title"] = icepackageinfo["realname"]
        profiletoupdate["custom_links"]["list"][0]["url"] = icepackageinfo["website"]
        profiletoupdate["session"]["startup_urls"] = [icepackageinfo["website"]]
        profiletoupdate["download"]["default_directory"] = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD) + "/" + _("{0} Downloads").format(icepackageinfo["realname"])
        profiletoupdate["profile"]["name"] = _("Ice - {0}").format(icepackageinfo["realname"])
        profiletoupdate["ntp"]["custom_background_dict"]["attribution_line_1"] = _("Feren OS Ice Website Application - {0}").format(icepackageinfo["realname"])
        profiletoupdate["vivaldi"]["tabs"]["new_page"]["custom_url"] = "https://feren-os.github.io/start-page/ice?ice-text="+(_("Feren OS Ice Website Application - {0}").format(icepackageinfo["realname"]))+"&home-url={0}".format(parse.quote(icepackageinfo["website"], safe=""))+"&home-icon={0}".format(parse.quote(icepackageinfo["iconuri"], safe=""))
        profiletoupdate["vivaldi"]["homepage"] = icepackageinfo["website"]
        profiletoupdate["vivaldi"]["homepage_cache"] = icepackageinfo["website"]
        
        
        #Update these as well
        if "icegoogleinteg" in icepackageinfo and icepackageinfo["icegoogleinteg"] == True:
            pass
        else:
            with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/disable-google", 'r') as fp:
                profiletoupdateextra = json.loads(fp.read())
            profiletoupdate = self.storebrain.dict_recurupdate(profiletoupdate, profiletoupdateextra)
        if "icegooglehangouts" in icepackageinfo and icepackageinfo["icegooglehangouts"] == True:
            profiletoupdate["vivaldi"]["privacy"]["google_component_extensions"]["hangout_services"] = True
        else:
            profiletoupdate["vivaldi"]["privacy"]["google_component_extensions"]["hangout_services"] = False
        
        if "icenohistory" in icepackageinfo and icepackageinfo["icenohistory"] == True:
            with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/disable-browsehistory", 'r') as fp:
                profiletoupdateextra = json.loads(fp.read())
                profiletoupdate = self.storebrain.dict_recurupdate(profiletoupdate, profiletoupdateextra)
            
            try:
                with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-nohistory" % taskdata["packagename"], 'w') as fp:
                    pass
            except Exception as exceptionstr:
                raise ICEModuleException(_("Failed to install {0}: {1} was encountered when setting up automatic history deletion").format(taskdata["packagename"], exceptionstr))
            
        #Background Sync, Clipboard, Notifications and Payment Handler ONLY for SSB's websites
        for permtype in ["ar", "autoplay", "automatic_downloads", "background_sync", "clipboard", "file_handling", "font_access", "midi_sysex", "notifications", "payment_handler", "sensors", "sound", "sleeping-tabs", "window_placement", "vr"]:
            profiletoupdate["profile"]["content_settings"]["exceptions"][permtype] = {}
            if "icedomain" in icepackageinfo:
                try:
                    shortenedurl = icepackageinfo["icedomain"].split("://")[1:]
                    shortenedurl = ''.join(shortenedurl)
                except:
                    shortenedurl = icepackageinfo["icedomain"]
            else:
                try:
                    shortenedurl = icepackageinfo["website"].split("://")[1:]
                    shortenedurl = ''.join(shortenedurl)
                except:
                    shortenedurl = icepackageinfo["website"]
            try:
                shortenedurl = shortenedurl.split("/")[0]
            except:
                pass
            profiletoupdate["profile"]["content_settings"]["exceptions"][permtype]["[*.]"+shortenedurl+",*"] = {"expiration": "0", "model": 0, "setting": 1}
            profiletoupdate["profile"]["content_settings"]["exceptions"][permtype][shortenedurl+",*"] = {"expiration": "0", "model": 0, "setting": 1}
            #Repeat for extra shortcuts' URLs
            extrascount = 0
            for extraid in iceextrasids:
                try:
                    shortenedurl = icepackageinfo["websiteextras"][extrascount].split("://")[1:]
                    shortenedurl = ''.join(shortenedurl)
                except:
                    shortenedurl = icepackageinfo["websiteextras"][extrascount]
                try:
                    shortenedurl = shortenedurl.split("/")[0]
                except:
                    pass
                profiletoupdate["profile"]["content_settings"]["exceptions"][permtype]["[*.]"+shortenedurl+",*"] = {"expiration": "0", "model": 0, "setting": 1}
                profiletoupdate["profile"]["content_settings"]["exceptions"][permtype][shortenedurl+",*"] = {"expiration": "0", "model": 0, "setting": 1}
                extrascount += 1
        
        
        #Update Vivaldi colour changes
        #   Vivaldi colour changes
        if "icecolor" in icepackageinfo and "icecolorhighlight" in icepackageinfo and "icecolordark" in icepackageinfo:
            vivaldihighlightcol = icepackageinfo["icecolorhighlight"]
            vivaldihighlightcoldark = self.colourFilter(icepackageinfo["icecolorhighlight"], 0.7, True, True)
            if self.get_are_colours_different(icepackageinfo["icecolor"], icepackageinfo["icecolorhighlight"]) and self.get_colour_bg_suitable(icepackageinfo["icecolor"]): #Suitable background colour used
                vivaldiaccentcol = icepackageinfo["icecolorhighlight"]
                vivaldiaccentcoldark = icepackageinfo["icecolorhighlight"]
                vivaldiwinbgcol = icepackageinfo["icecolor"]
                vivaldiwinbgcoldark = icepackageinfo["icecolordark"]
                vivaldiaccentinchrome = False
                
            else: #Otherwise use fallback colours
                vivaldiaccentcol = icepackageinfo["icecolor"]
                vivaldiwinbgcol = ""
                vivaldiaccentcoldark = self.colourFilter(icepackageinfo["icecolordark"], 0.7, True, True)
                vivaldiwinbgcoldark = ""
                vivaldiaccentinchrome = True
                
                
            #Now to make the Private theme    
            vivaldiaccentcolprivate = self.colourFilter(icepackageinfo["icecolorhighlight"], 46.0, True)
            vivaldiwinbgcolprivate = self.colourFilter(icepackageinfo["icecolorhighlight"], 70.0, True)
            
                
            profiletoupdate["vivaldi"]["themes"]["system"][0]["accentOnWindow"] = vivaldiaccentinchrome
            profiletoupdate["vivaldi"]["themes"]["system"][1]["accentOnWindow"] = vivaldiaccentinchrome
            profiletoupdate["vivaldi"]["themes"]["system"][2]["accentOnWindow"] = False
            profiletoupdate["vivaldi"]["themes"]["system"][0]["colorAccentBg"] = vivaldiaccentcol
            profiletoupdate["vivaldi"]["themes"]["system"][1]["colorAccentBg"] = vivaldiaccentcoldark
            profiletoupdate["vivaldi"]["themes"]["system"][2]["colorAccentBg"] = vivaldiaccentcolprivate
            profiletoupdate["vivaldi"]["themes"]["system"][0]["colorHighlightBg"] = vivaldihighlightcol
            profiletoupdate["vivaldi"]["themes"]["system"][1]["colorHighlightBg"] = vivaldihighlightcoldark
            profiletoupdate["vivaldi"]["themes"]["system"][2]["colorHighlightBg"] = vivaldihighlightcol
            if vivaldiwinbgcol != "":
                if self.get_luminant(vivaldiwinbgcol) == False: #Dark BG (in-Preferences default is Light, so no need for Light BG else)
                    profiletoupdate["vivaldi"]["themes"]["system"][0]["colorFg"] = "#FFFFFF"
                profiletoupdate["vivaldi"]["themes"]["system"][0]["colorBg"] = vivaldiwinbgcol
            if vivaldiwinbgcoldark != "":
                if self.get_luminant(vivaldiwinbgcoldark) == True: #Light BG (in-Preferences default is Dark, so no need for Dark BG else)
                    profiletoupdate["vivaldi"]["themes"]["system"][1]["colorFg"] = "#000000"
                profiletoupdate["vivaldi"]["themes"]["system"][1]["colorBg"] = vivaldiwinbgcoldark
            #Private foreground
            if self.get_luminant(vivaldiwinbgcolprivate) == True: #Light BG (in-Preferences default is Dark, so no need for Dark BG else)
                profiletoupdate["vivaldi"]["themes"]["system"][2]["colorFg"] = "#000000"
            profiletoupdate["vivaldi"]["themes"]["system"][2]["colorBg"] = vivaldiwinbgcolprivate
        
        
        
        #Write last updated date to be used in update checks
        try:
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-last-updated" % taskdata["packagename"], 'w') as fp:
                fp.write(datetime.today().strftime('%Y%m%d'))
        except Exception as exceptionstr:
            raise ICEModuleException(_("Failed to update {0}: {1} was encountered when writing the last updated date").format(taskdata["packagename"], exceptionstr))
        
        #Write default browser value to be used for the update process
        try:
            if not os.path.isfile(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-default-browser" % taskdata["packagename"]):
                with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-default-browser" % taskdata["packagename"], 'w') as fp:
                    fp.write(taskdata["source"]) # Used by module during updating to determine your browser
        except Exception as exceptionstr:
            self.task_remove_package(taskdata, None, True) #Remove profile's files/folders on failure
            raise ICEModuleException(_("Failed to update {0}: {1} was encountered when noting the browser selection value").format(taskdata["packagename"], exceptionstr))
        
        
        #Write profile
        try:
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/Default/Preferences" % taskdata["packagename"], 'w') as fp:
                fp.write(json.dumps(profiletoupdate, separators=(',', ':')))
        except Exception as exceptionstr:
            raise ICEModuleException(_("Failed to update {0}: {1} was encountered when writing the Chromium-based profile").format(taskdata["packagename"], exceptionstr))
            
        
        #Update Local State too
        with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/Local State", 'r') as fp:
            profiledefaults = json.loads(fp.read())
        try:
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/Local State" % taskdata["packagename"], 'r') as fp:
                profiletoupdate = json.loads(fp.read())
        except Exception as exceptionstr:
            raise ICEModuleException(_("Failed to update {0}: {1} was encountered when reading the browser's local state (is the local state corrupt?)").format(taskdata["packagename"], exceptionstr))
        try:
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/Local State" % taskdata["packagename"], 'w') as fp:
                fp.write(json.dumps(self.storebrain.dict_recurupdate(profiletoupdate, profiledefaults), separators=(',', ':')))
        except Exception as exceptionstr:
            raise ICEModuleException(_("Failed to update {0}: {1} was encountered when writing the Local State").format(taskdata["packagename"], exceptionstr))
        
            
        progress_callback(72)            
            
            
        try:
            with open(os.path.expanduser("~") + "/.local/share/applications/%s.desktop" % windowclassid, 'w') as fp:
                # I mean, this needs no explanation, it's a .desktop file
                fp.write("[Desktop Entry]\n")
                fp.write("Version=1.0\n")
                fp.write("Name={0}\n".format(icepackageinfo["realname"]))
                fp.write("Comment={0}\n".format(_("Website (obtained from Store)")))
                
                fp.write("Exec=/usr/bin/feren-storium-icelaunch {0} {1} {2} {3}\n".format(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s" % taskdata["packagename"], taskdata["source"], '"' + icepackageinfo["website"] + '"', windowclassid))

                fp.write("Terminal=false\n")
                fp.write("X-MultipleArgs=false\n")
                fp.write("Type=Application\n")
                
                if usefallbackicon == True:
                    fp.write("Icon=text-html\n")
                else:
                    fp.write("Icon={0}\n".format(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/icon" % taskdata["packagename"]))

                #Ice stuff will have their own categories to allow for easier sectioning of items in Store overall
                if icepackageinfo["category"] == "ice-accessories":
                    location = "Utility;"
                elif icepackageinfo["category"] == "ice-games":
                    location = "Game;"
                elif icepackageinfo["category"] == "ice-graphics":
                    location = "Graphics;"
                elif icepackageinfo["category"] == "ice-internet":
                    location = "Network;"
                elif icepackageinfo["category"] == "ice-office":
                    location = "Office;"
                elif icepackageinfo["category"] == "ice-programming":
                    location = "Development;"
                elif icepackageinfo["category"] == "ice-multimedia":
                    location = "AudioVideo;"
                elif icepackageinfo["category"] == "ice-system":
                    location = "System;"
                
                fp.write("Categories=GTK;Qt;{0}\n".format(location))
                fp.write("MimeType=text/html;text/xml;application/xhtml_xml;\n")

                fp.write("Keywords=%s\n" % icepackageinfo["keywords"])

                fp.write("StartupWMClass=%s\n" % windowclassid)
                fp.write("StartupNotify=true\n")
        except Exception as exceptionstr:
            raise ICEModuleException(_("Failed to update {0}: {1} was encountered when updating the shortcut in the Applications Menu").format(taskdata["packagename"], exceptionstr))
        
        
        #Remove old extra shortcuts
        for extraid in currenticeextraids:
            try:
                if os.path.isfile(os.path.expanduser("~") + "/.local/share/applications/{0}-{1}.desktop".format(taskdata["packagename"], extraid)):
                    os.remove(os.path.expanduser("~") + "/.local/share/applications/{0}-{1}.desktop".format(taskdata["packagename"], extraid))
            except Exception as exceptionstr:
                raise ICEModuleException(_("Failed to update {0}: {1} was encountered when removing extra shortcuts to replace with new ones").format(taskdata["packagename"], exceptionstr))
            try:
                if os.path.isfile(os.path.expanduser("~") + "/.local/share/feren-storium-ice/{0}/icon-{1}".format(taskdata["packagename"], extraid)):
                    os.remove(os.path.expanduser("~") + "/.local/share/feren-storium-ice/{0}/icon-{1}".format(taskdata["packagename"], extraid))
            except Exception as exceptionstr:
                raise ICEModuleException(_("Failed to update {0}: {1} was encountered when removing extra icons to replace with new ones").format(taskdata["packagename"], exceptionstr))
        
        #Write the new Extra IDs to be used as a backup
        try:
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-extra-ids" % taskdata["packagename"], 'w') as fp:
                fp.write(str(iceextrasids)) # This means that Storium can manage extras later on in time
        except Exception as exceptionstr:
            raise ICEModuleException(_("Failed to update {0}: {1} was encountered when making a note of the SSB's extra shortcuts").format(taskdata["packagename"], exceptionstr))
        
        #Now repeat for extras, if appropriate
        extrascount = 0 #Classic strat for iteration
        if iceextrasids != []:
            import urllib.request #Grabbing files from internet
            import urllib.error
        for extraid in iceextrasids:
            try:
                with open(os.path.expanduser("~") + "/.local/share/applications/{0}-{1}.desktop".format(taskdata["packagename"], extraid), 'w') as fp:
                    # I mean, this needs no explanation, it's a .desktop file
                    fp.write("[Desktop Entry]\n")
                    fp.write("Version=1.0\n")
                    fp.write("Name={0}\n".format(icepackageinfo["realnameextras"][extrascount]))
                    fp.write("Comment={0}\n".format(_("Website (part of %s)" % icepackageinfo["realname"])))
                    
                    fp.write("Exec=/usr/bin/feren-storium-icelaunch {0} {1} {2} {3}\n".format(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s" % taskdata["packagename"], taskdata["source"], '"' + icepackageinfo["websiteextras"][extrascount] + '"', windowclassid))

                    fp.write("Terminal=false\n")
                    fp.write("X-MultipleArgs=false\n")
                    fp.write("Type=Application\n")
                    
                    try:
                        urllib.request.urlretrieve(icepackageinfo["iconuriextras"][extrascount], (os.path.expanduser("~") + "/.local/share/feren-storium-ice/{0}/icon-{1}".format(taskdata["packagename"], extraid)))
                        fp.write("Icon=%s\n" % (os.path.expanduser("~") + "/.local/share/feren-storium-ice/{0}/icon-{1}".format(taskdata["packagename"], extraid)))
                    except:
                        fp.write("Icon=text-html\n")

                    if icepackageinfo["category"] == "ice-accessories":
                        location = "Utility;"
                    elif icepackageinfo["category"] == "ice-games":
                        location = "Game;"
                    elif icepackageinfo["category"] == "ice-graphics":
                        location = "Graphics;"
                    elif icepackageinfo["category"] == "ice-internet":
                        location = "Network;"
                    elif icepackageinfo["category"] == "ice-office":
                        location = "Office;"
                    elif icepackageinfo["category"] == "ice-programming":
                        location = "Development;"
                    elif icepackageinfo["category"] == "ice-multimedia":
                        location = "AudioVideo;"
                    elif icepackageinfo["category"] == "ice-system":
                        location = "System;"
                    
                    fp.write("Categories=GTK;Qt;{0}\n".format(location))
                    fp.write("MimeType=text/html;text/xml;application/xhtml_xml;\n")

                    fp.write("Keywords=%s\n" % icepackageinfo["keywordsextras"][extrascount])

                    fp.write("StartupNotify=true\n")
            except Exception as exceptionstr:
                raise ICEModuleException(_("Failed to update {0}: {1} was encountered when updating extra shortcuts in the Applications Menu").format(taskdata["packagename"], exceptionstr))
            os.system("chmod +x " + os.path.expanduser("~") + "/.local/share/applications/{0}-{1}.desktop".format(taskdata["packagename"], extraid))
            extrascount += 1
            
        progress_callback(99)
        
        #Otherwise they'll refuse to launch from the Applications Menu (bug seen in Mint's own Ice code fork)
        os.system("chmod +x " + os.path.expanduser("~") + "/.local/share/applications/%s.desktop" % windowclassid)
            
        progress_callback(100)
        
        return True
    
    def get_configs(self):
        #Get configs and their current gsettings/file values and return them as a dictionary
        gsettingsschemas={} # e.g.: {org.cinnamon.theme: [name]}
        configfiles={} # {config file: [config names]}
        
        for schema in gsettingsschemas:
            for configname in gsettingsschemas[schema]:
                pass
        for configfile in configfiles:
            for configname in configfiles[configname]:
                pass
        
        #{value: [type (gsettings/file), schema (gsettings schema/file path), current value]}
        pass

    def enable_appsource(self, appsource):
        #You SHOULD NOT be able to manage Application Sources for websites anyway, so raise an error
        raise ICEModuleException(_("You cannot manage sources when the 'sources' are just web browsers."))
    
    def disable_appsource(self, appsource):
        #You SHOULD NOT be able to manage Application Sources for websites anyway, so raise an error
        raise ICEModuleException(_("You cannot manage sources when the 'sources' are just web browsers."))




    #////Package Information////
    def build_ids_list(self): #Build list of package IDs
        self.pkg_ids = []
        for i in [self.json_storage["package-info/peppermint-ice"]]:
            try:
                for package in i:
                    if package not in self.pkg_ids:
                        self.pkg_ids.append(package)
            except:
                pass
        
    def build_categories_ids(self): #Build categories list for package IDs
        self.pkg_categoryids = {}
        #Do nothing else as this isn't a generic module
        
    def refresh_memory(self): # Function to refresh some memory values
        self.memory_refreshing = True
        
        self.json_storage = {}
        
        for i in ["package-info/peppermint-ice"]:
            with open("/usr/share/feren-storium/curated/" + i + "/data.json", 'r') as fp:            
                self.json_storage[i] = json.loads(fp.read())
        
        self.memory_refreshing = False
                
        
    def getPackageJSON(self):
        #Return a json of all package names
        packagejson = {}
        for i in [self.json_storage["package-info/peppermint-ice"]]:
            try:
                packagejson.update(i)
            except:
                pass
        return packagejson
      
    
    def getInfo(self, packagename, packagetype, sourcename=""):
        #Get information on a package using the JSON data
        
        if packagetype not in self.types_supported:
            raise IceInfoModuleException(packagetype, _("is not supported by this information module. If you are getting an exception throw, it means you have not used a Try to respond to the module not supporting this type of package."))
            return
        
        if sourcename == "":
            return self.json_storage["package-info/" + packagetype][packagename]
        else:
            overallinfo = {}
            try:
                overallinfo = self.json_storage["package-info/" + packagetype][packagename]["all"]
            except:
                pass
            try:
                overallinfo = self.storebrain.dict_recurupdate(overallinfo, self.json_storage["package-info/" + packagetype][packagename][sourcename])
            except:
                pass
            return overallinfo
        
        
    def getSourceList(self, packagename, packagetype):
        #Get list of source order
        
        #Not needed since 'all'
        #if packagetype not in self.types_supported:
            #raise GenericInfoModuleException(packagetype, _("is not supported by this information module. If you are getting an exception throw, it means you have not used a Try to respond to the module not supporting this type of package."))
            #return
            
        return self.json_storage["package-info/" + packagetype][packagename]["sources-available"]
        

    def getShortDescription(self, packagename):
        try:
            shortdescription = self.json_storage["package-info/peppermint-ice"][packagename]["shortdescription"]
        except:
            shortdescription = _("Website Application")
        return shortdescription
    
    def getKeywords(self, packagename):
        try:
            keywords = self.json_storage["package-info/peppermint-ice"][packagename]["keywords"]
        except:
            raise IceInfoModuleException(packagename, _("has no keywords value in the package metadata. Websites MUST have keywords values when curated."))
            return
        return keywords
    
    def getAuthor(self, packagename):
        try:
            author = self.json_storage["package-info/peppermint-ice"][packagename]["author"]
        except:
            author = _("Unknown Author")
        return author
      
    def getBugsURL(self, packagename):
        try:
            bugsurl = self.json_storage["package-info/peppermint-ice"][packagename]["bugreporturl"]
        except:
            bugsurl = ""
        return bugsurl
      
    def getTOSURL(self, packagename):
        try:
            tosurl = self.json_storage["package-info/peppermint-ice"][packagename]["tos"]
        except:
            tosurl = ""
        return tosurl
      
    def getPrivPolURL(self, packagename):
        try:
            privpolurl = self.json_storage["package-info/peppermint-ice"][packagename]["privpol"]
        except:
            privpolurl = ""
        return privpolurl
      
    def getExtrasIDs(self, packagename):
        try:
            extrasids = self.json_storage["package-info/peppermint-ice"][packagename]["extrasids"]
        except:
            extrasids = []
        return extrasids
      
    def getExtraRealNames(self, packagename):
        try:
            realnameextras = self.json_storage["package-info/peppermint-ice"][packagename]["realnameextras"]
        except:
            realnameextras = []
        return realnameextras
      
    def getIconURIExtras(self, packagename):
        try:
            iconuriextras = self.json_storage["package-info/peppermint-ice"][packagename]["iconuriextras"]
        except:
            iconuriextras = []
        return iconuriextras
      
    def getWebsiteExtras(self, packagename):
        try:
            websiteextras = self.json_storage["package-info/peppermint-ice"][packagename]["websiteextras"]
        except:
            websiteextras = []
        return websiteextras
      
    def getKeywordsExtras(self, packagename):
        try:
            keywordsextras = self.json_storage["package-info/peppermint-ice"][packagename]["keywordsextras"]
        except:
            keywordsextras = []
        return keywordsextras
    
    
    def getCanTheme(self, packagename, packagetype):
        # Return values:
        # 0: No
        # 1: Yes
        # 2: Yes, but manually enabled
        # 3: Yes, except for Feren OS's style
        # 4: Has own themes system
        # 5: No because LibAdwaita
        # 6: No because LibGranite
        
        canusethemes = 1 #Disable warning for Website Applications      
        try:
            if self.json_storage["package-info/peppermint-ice"][packagename]["hasownthemes"] == True:
                canusethemes = 4 #...unless a website has themes of its own
        except:
            pass
        return canusethemes
    
      
    def getCanTouchScreen(self, packagename, packagetype):
        # Return values:
        # 0: No
        # 1: Yes
        # 2: Partially
        
        return 1 #Disable warning for Website Applications
    
    
    def getCanUseAccessibility(self, packagename, packagetype):
        try:
            canuseaccessibility = self.json_storage["package-info/peppermint-ice"][packagename]["canuseaccessibility"]
        except:
            canuseaccessibility = True # Use fallback of True when unknown to hide the message
        return canuseaccessibility
    
    
    def getCanUseDPI(self, packagename, packagetype):
        return True #Disable warning for Website Applications
    
    
    def getCanUseOnPhone(self, packagename, packagetype):
        try:
            canuseonphone = self.json_storage["package-info/peppermint-ice"][packagename]["canuseonphone"]
        except:
            canuseonphone = True # Use fallback of True when unknown to hide the message
        return canuseonphone
    
    
    def getIsOfficial(self, packagename, packagetype):
        return True #Disable warning for Website Applications
    
    

if __name__ == "__main__":
    module = PackageMgmtModule()
