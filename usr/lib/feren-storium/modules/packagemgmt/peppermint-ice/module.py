import configparser
import os
import subprocess
import gettext
import gi


#Dependencies
import json
import shutil
import collections.abc


class ICEModuleException(Exception): # Name this according to the module to allow easier debugging
    pass


class PackageStore():
    def __init__(self, realname, iconuri, shortdesc, description, author, category, images, website, donateurl, bugsurl, tosurl, privpolurl, keywords):
        self.realname = realname
        self.iconuri = iconuri
        self.shortdesc = shortdesc
        self.description = description
        self.author = author
        self.category = category
        self.images = images
        self.website = website
        self.donateurl = donateurl
        self.bugsurl = bugsurl
        self.tosurl = tosurl
        self.privpolurl = privpolurl
        self.keywords = keywords


class main():

    def __init__(self, storebrain):

        gettext.install("feren-storium", "/usr/share/locale", names="ngettext")

        #Name to be used in Debugging output
        self.title = _("Ice Website Management Module")
        #Name to be shown in the GUI
        self.humanreadabletitle = _("Ice WebApp Management")
        
        #Can manage Application Sources?
        self.canmanagesources = False
        
        #Application Sources (for ICE let's have the sources be the browsers that're supported)
        # Empty here, will be appended to with self.refresh_memory()
        self.applicationsources = {}
        
        #Store Brain
        self.storebrain = storebrain
        
        #What package types does this manage?
        self.types_managed = ["peppermint-ice"]
        
        #Generic Description for header
        self.genericheader = _("Website Application")
        
        #Configs (obtained by get_configs)
        self.moduleconfigs={}
        self.get_configs()
        
        #Package Storage will store the data of opened packages this instance
        self.packagestorage = {}
        
        #Last package viewed
        self.lastpkgviewed = ""
        
        #Lock to keep stuff from happening while memory is refreshing
        self.memory_refreshing = False
        
        #Is the package management busy?
        self.packagemgmtbusy = False
        
        #Current name being managed
        self.currentpackagename = ""
        
        #Force refresh the sources to populate the sources
        self.refresh_sources()
        
    def refresh_sources(self, packagename=""): # Function to refresh sources list - just return if your module doesn't need this
        self.applicationsources = {}
        #Add each browser to applicationsources
        if os.path.isfile("/usr/bin/vivaldi"):
            self.applicationsources["vivaldi"] = [_("Vivaldi")]
        if os.path.isfile("/usr/bin/brave-browser"):
            self.applicationsources["brave"] = [_("Brave")]
        if os.path.isfile("/usr/bin/google-chrome"):
            self.applicationsources["chrome"] = [_("Google Chrome")]
        if os.path.isfile("/usr/bin/microsoft-edge"):
            self.applicationsources["msedge"] = [_("Microsoft Edge")]
        
    def refresh_memory(self): # Function to refresh some memory values
        self.memory_refreshing = True
            
        pass #TODO
        
        self.memory_refreshing = False
        
    def pkgstorage_add(self, packagename):
        if packagename not in self.packagestorage:
            #Get the values
            packageinfo = self.storebrain.get_item_info(packagename, "peppermint-ice")
            
            self.packagestorage[packagename] = PackageStore(packageinfo["realname"], packageinfo["iconuri"], "desc", packageinfo["description"], packageinfo["author"], packageinfo["category"], packageinfo["images"], packageinfo["website"], packageinfo["donateurl"], packageinfo["bugsurl"], packageinfo["tosurl"], packageinfo["privpolurl"], packageinfo["keywords"])

    def get_information(self, packagename):
        # Return description for package
        if packagename in self.packagestorage:
            return self.packagestorage[packagename].realname, self.packagestorage[packagename].iconuri, self.packagestorage[packagename].shortdesc, self.packagestorage[packagename].description, self.packagestorage[packagename].author, self.packagestorage[packagename].category, self.packagestorage[packagename].images, self.packagestorage[packagename].website, self.packagestorage[packagename].donateurl, self.packagestorage[packagename].bugsurl, self.packagestorage[packagename].tosurl, self.packagestorage[packagename].privpolurl, self.packagestorage[packagename].keywords
        else:
            raise ICEModuleException(_("%s is not in the Package Storage (packagestorage) yet - make sure it's in the packagestorage variable before obtaining package information.") % packagename)

    def get_status(self, packagename):
        # Return package installation status
        # 0 - Uninstalled
        # 1 - Installed
        if os.path.isfile(os.path.expanduser("~") + "/.local/share/applications/%s.desktop" % packagename) and os.path.isdir(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/icon" % packagename):
            return 1
        else:
            return 0
        
    def dict_recurupdate(self, d, u): # I'm sure it's a recursive dictionary updater function, from what I can read of this function
        for k, v in u.items():
            if isinstance(v, collections.abc.Mapping):
                d[k] = self.dict_recurupdate(d.get(k, {}), v)
            else:
                d[k] = v
        return d
    
    def install_package(self, packagename, source, bonuses=[]):
        if packagename not in self.packagestorage:
            raise ICEModuleException(_("%s is not in the Package Storage (packagestorage) yet - make sure it's in the packagestorage variable before obtaining package information.") % packagename)
        
        #Install package and return exit code
        self.packagemgmtbusy = True
        self.currentpackagename = packagename
        
        #First remove the files just in case there's a partial installation
        self.remove_package(packagename, source, True)
        
        #Create the .desktop file's home if it doesn't exist
        if not os.path.isdir(os.path.expanduser("~") + "/.local/share/applications"):
            try:
                os.mkdir(os.path.expanduser("~") + "/.local/share/applications")
            except Exception as exceptionstr:
                raise ICEModuleException(_("Failed to install {0}: {1} was encountered when trying to create the shortcut's location").format(packagename, exceptionstr))
            
        #Create the Chromium profile
        if not os.path.isdir(os.path.expanduser("~") + "/.local/share/feren-storium-ice"):
            try:
                os.mkdir(os.path.expanduser("~") + "/.local/share/feren-storium-ice")
            except Exception as exceptionstr:
                raise ICEModuleException(_("Failed to install {0}: {1} was encountered when trying to create the profiles location").format(packagename, exceptionstr))
        if not os.path.isdir(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s" % packagename):
            try:
                os.mkdir(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s" % packagename)
            except Exception as exceptionstr:
                raise ICEModuleException(_("Failed to install {0}: {1} was encountered when trying to create the profile's folder").format(packagename, exceptionstr))
            
        #First Run existing skips the initial Welcome to Google Chrome dialog, which is very useful here to have a skip in place for
        try:
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/First Run" % packagename, 'w') as fp:
                pass
        except Exception as exceptionstr:
            self.remove_package(packagename, source, True) #Remove profile's files/folders on failure
            raise ICEModuleException(_("Failed to install {0}: {1} was encountered when making the Chromium-based profile").format(packagename, exceptionstr))
        try:
            os.mkdir(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/Default" % packagename)
        except Exception as exceptionstr:
            self.remove_package(packagename, source, True) #Remove profile's files/folders on failure
            raise ICEModuleException(_("Failed to install {0}: {1} was encountered when making the Chromium-based profile").format(packagename, exceptionstr))
        
        usefallbackicon = False
        #Copy icon for package
        try:
            shutil.copy(self.storebrain.tempdir + "/icons/" + packagename, os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/icon" % packagename)
        except Exception as exceptionstr:
            usefallbackicon = True
        
        
        #Now to make the JSON file
        with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/Preferences", 'r') as fp:
            profiletomake = json.loads(fp.read())
        
        if "nekocap" in bonuses:
            with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/and-nekocap", 'r') as fp:
                profiletomakeextra = json.loads(fp.read()) #This is how you make json.load work with file paths, I guess
            #FIXME: In python3 you're meant to dict.update(newdict), but the pythonic way gets RID of our other Extensions in the process from the Preferences, hence this in-house function's used instead, here
            profiletomake = self.dict_recurupdate(profiletomake, profiletomakeextra)
        if "ublock" in bonuses:
            with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/and-ublock", 'r') as fp:
                profiletomakeextra = json.loads(fp.read())
            profiletomake = self.dict_recurupdate(profiletomake, profiletomakeextra)
        if "darkreader" in bonuses:
            with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/and-darkreader", 'r') as fp:
                profiletomakeextra = json.loads(fp.read())
            profiletomake = self.dict_recurupdate(profiletomake, profiletomakeextra)
        
        
        #Write profile
        try:
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/Default/Preferences" % packagename, 'w') as fp:
                fp.write(json.dumps(profiletomake, separators=(',', ':'))) # This dumps minified json (how convenient), which is EXACTLY what Chrome uses for Preferences, so it's literally pre-readied
        except Exception as exceptionstr:
            self.remove_package(packagename, source, True) #Remove profile's files/folders on failure
            raise ICEModuleException(_("Failed to install {0}: {1} was encountered when writing the Chromium-based profile").format(packagename, exceptionstr))
        
        
        #Write .desktop file
        if "nekocap" in bonuses:
            nekocaparg = "true"
        else:
            nekocaparg = "false"
        if "ublock" in bonuses:
            ublockarg = "true"
        else:
            ublockarg = "false"
        if "darkreader" in bonuses:
            darkreadarg = "true"
        else:
            darkreadarg = "false"
        try:

            with open(os.path.expanduser("~") + "/.local/share/applications/%s.desktop" % packagename, 'w') as fp:
                # I mean, this needs no explanation, it's a .desktop file
                fp.write("[Desktop Entry]\n")
                fp.write("Version=1.0\n")
                fp.write("Name={0}\n".format(self.packagestorage[packagename].realname))
                fp.write("Comment={0}\n".format(_("Website (obtained from Store)")))
                
                fp.write("Exec=/usr/bin/feren-storium-icelaunch {0} {1} {2} {3} {4} {5} {6}\n".format(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s" % packagename, source, self.packagestorage[packagename].website, packagename, ublockarg, nekocaparg, darkreadarg))

                fp.write("Terminal=false\n")
                fp.write("X-MultipleArgs=false\n")
                fp.write("Type=Application\n")
                
                if usefallbackicon == True:
                    fp.write("Icon=text-html\n")
                else:
                    fp.write("Icon={0}\n".format(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/icon" % packagename))

                #Ice stuff will have their own categories to allow for easier sectioning of items in Store overall
                if self.packagestorage[packagename].category == "ice-accessories":
                    location = "Utility;"
                elif self.packagestorage[packagename].category == "ice-games":
                    location = "Game;"
                elif self.packagestorage[packagename].category == "ice-graphics":
                    location = "Graphics;"
                elif self.packagestorage[packagename].category == "ice-internet":
                    location = "Network;"
                elif self.packagestorage[packagename].category == "ice-office":
                    location = "Office;"
                elif self.packagestorage[packagename].category == "ice-programming":
                    location = "Development;"
                elif self.packagestorage[packagename].category == "ice-multimedia":
                    location = "AudioVideo;"
                elif self.packagestorage[packagename].category == "ice-system":
                    location = "System;"
                
                fp.write("Categories=GTK;Qt;{0}\n".format(location))
                fp.write("MimeType=text/html;text/xml;application/xhtml_xml;\n")

                fp.write("Keywords=%s\n" % self.packagestorage[packagename].keywords)

                fp.write("StartupWMClass=%s\n" % packagename)
                fp.write("StartupNotify=true\n")
        except Exception as exceptionstr:
            self.remove_package(packagename, source, True) #Remove profile's files/folders on failure
            raise ICEModuleException(_("Failed to install {0}: {1} was encountered when creating a shortcut in the Applications Menu").format(packagename, exceptionstr))
        
        #Otherwise they'll refuse to launch from the Applications Menu (bug seen in Mint's own Ice code fork)
        os.system("chmod +x " + os.path.expanduser("~") + "/.local/share/applications/%s.desktop" % packagename)
        
        #Clean up after management
        self.currentpackagename = ""
        self.packagemgmtbusy = False
        return True
    
    def remove_package(self, packagename, source, forinstall=False):
        if packagename not in self.packagestorage:
            raise ICEModuleException(_("%s is not in the Package Storage (packagestorage) yet - make sure it's in the packagestorage variable before obtaining package information.") % packagename)
        
        if not forinstall: # We call this in the install process to clear out partial installs, so for those times we want to skip THIS code to not confuse Store's Brain or anything that could get confused from this module 'unlocking' temporarily
            self.packagemgmtbusy = True
            self.currentpackagename = packagename
        
        #Delete the files and the folders and done        
        try:
            os.remove(os.path.expanduser("~") + "/.local/share/applications/%s.desktop" % packagename)
        except Exception as exceptionstr:
            if not forinstall:
                raise ICEModuleException(_("Failed to uninstall {0}: {1} was encountered when removing the shortcut from the Applications Menu").format(packagename, exceptionstr))
        try:
            shutil.rmtree(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s" % packagename)
        except Exception as exceptionstr:
            if not forinstall:
                raise ICEModuleException(_("Failed to uninstall {0}: {1} was encountered when deleting the Chromium-based profile").format(packagename, exceptionstr))
        
        #Clean up after management
        if not forinstall:
            self.currentpackagename = ""
            self.packagemgmtbusy = False
        return True
    
    def update_package(self, packagename):
        #You SHOULD NOT be able to hit Update for websites anyway, so raise an error
        raise ICEModuleException(_("You wouldn't update an Ice Website Application."))
    
    def get_package_changes(self, pkgsinstalled, pkgsupdated, pkgsremoved):
        #Examine the package changes - pkgsinstalled, pkgsupdated and pkgsremoved are lists
        # Just skip it by having empty returns since Ice is exempt
        return [], [], []
    
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

if __name__ == "__main__":
    module = PackageMgmtModule()