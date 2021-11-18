import configparser
import os
import subprocess
import gettext
import gi


#Dependencies
import json
import shutil


def should_load(): #Should this module be loaded?
    return True


class ICEModuleException(Exception): # Name this according to the module to allow easier debugging
    pass


class PackageStore():
    def __init__(self, realname, iconuri, shortdescription, description, author, category, images, website, donateurl, bugreporturl, tosurl, privpolurl, keywords, extrasids, realnameextras, iconuriextras, websiteextras, keywordsextras):
        self.realname = realname
        self.iconuri = iconuri
        self.shortdescription = shortdescription
        self.description = description
        self.author = author
        self.category = category
        self.images = images
        self.website = website
        self.donateurl = donateurl
        self.bugreporturl = bugreporturl
        self.tosurl = tosurl
        self.privpolurl = privpolurl
        self.keywords = keywords
        self.extrasids = extrasids
        self.realnameextras = realnameextras
        self.iconuriextras = iconuriextras
        self.websiteextras = websiteextras
        self.keywordsextras = keywordsextras


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
        self.applicationsources = []
        
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
        
    def refresh_memory(self): # Function to refresh some memory values
        self.memory_refreshing = True
            
        pass #TODO
        
        self.memory_refreshing = False
        
                
    def get_sources(self, packagename):
        sources = ["peppermint-ice"]
        return sources
        
    def get_subsources(self, packagename, source):
        subsources = []
        #Add each browser to applicationsources
        if os.path.isfile("/usr/bin/vivaldi"):
            subsources.append("vivaldi")
        if os.path.isfile("/usr/bin/brave-browser"):
            subsources.append("brave")
        if os.path.isfile("/usr/bin/google-chrome"):
            subsources.append("chrome")
        if os.path.isfile("/usr/bin/microsoft-edge"):
            subsources.append("msedge")
        return subsources
    
        
    def pkgstorage_add(self, packagename):
        if packagename not in self.packagestorage:
            packageinfo = {}
            
            #Get the values
            for packagetype in self.types_managed:
                try:
                    packageinfo = self.storebrain.get_item_info(packagename, packagetype, True)
                    if packageinfo != self.storebrain.get_generic_item_info(packagename): #Check we have full information, not just generic information
                        continue
                except:
                    pass
            
            if packageinfo == {}:
                return
            
            self.packagestorage[packagename] = PackageStore(packageinfo["realname"], packageinfo["iconuri"], packageinfo["shortdescription"], packageinfo["description"], packageinfo["author"], packageinfo["category"], packageinfo["images"], packageinfo["website"], packageinfo["donateurl"], packageinfo["bugreporturl"], packageinfo["tosurl"], packageinfo["privpolurl"], packageinfo["keywords"], packageinfo["extrasids"], packageinfo["realnameextras"], packageinfo["iconuriextras"], packageinfo["websiteextras"], packageinfo["keywordsextras"])

    def get_information(self, packagename):
        # Return description for package
        if packagename in self.packagestorage:
            return self.packagestorage[packagename].realname, self.packagestorage[packagename].iconuri, self.packagestorage[packagename].shortdesc, self.packagestorage[packagename].description, self.packagestorage[packagename].author, self.packagestorage[packagename].category, self.packagestorage[packagename].images, self.packagestorage[packagename].website, self.packagestorage[packagename].donateurl, self.packagestorage[packagename].bugreporturl, self.packagestorage[packagename].tosurl, self.packagestorage[packagename].privpolurl, self.packagestorage[packagename].keywords
        else:
            raise ICEModuleException(_("%s is not in the Package Storage (packagestorage) yet - make sure it's in the packagestorage variable before obtaining package information.") % packagename)

    def get_status(self, packagename):
        # Return package installation status
        # 0 - Uninstalled
        # 1 - Installed
        if os.path.isfile(os.path.expanduser("~") + "/.local/share/applications/%s.desktop" % packagename) and os.path.isdir(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s" % packagename):
            return 1
        else:
            return 0
    
    
    def finishing_cleanup(self, packagename):
        #Cleanup after package operations
        self.currentpackagename = ""
        self.packagemgmtbusy = False
        
    #Add to Tasks
    def install_package(self, packagename, source, subsource):
        bonuses = ["ublock", "nekocap", "imagus"] #TODO: Add confirmation prompt showing changes, and also allowing bonus selection
        
        self.storebrain.tasks.add_task(self.modulename, packagename, 0, self.packagestorage[packagename].realname, source, subsource, bonuses)
    
    def update_package(self, packagename, source, subsource):
        #You SHOULD NOT be able to hit Update for websites anyway, so raise an error
        self.finishing_cleanup(packagename)
        raise ICEModuleException(_("You wouldn't update an Ice Website Application."))
    
    def remove_package(self, packagename, source, subsource):
        #TODO: Add confirmation prompt showing changes, and also allowing bonus selection
        
        self.storebrain.tasks.add_task(self.modulename, packagename, 2, self.packagestorage[packagename].realname, source, subsource)
        
    
    #Actual management TODO: Progress callback
    def task_install_package(self, packagename, source, subsource, bonuses=[]):
        if packagename not in self.packagestorage:
            raise ICEModuleException(_("%s is not in the Package Storage (packagestorage) yet - make sure it's in the packagestorage variable before obtaining package information.") % packagename)
        
        #Install package and return exit code
        self.packagemgmtbusy = True
        self.currentpackagename = packagename
        
        #First remove the files just in case there's a partial installation
        self.task_remove_package(packagename, source, subsource, True)
        
        #Create the .desktop file's home if it doesn't exist
        if not os.path.isdir(os.path.expanduser("~") + "/.local/share/applications"):
            try:
                os.mkdir(os.path.expanduser("~") + "/.local/share/applications")
            except Exception as exceptionstr:
                raise ICEModuleException(_("Failed to install {0}: {1} was encountered when trying to create the shortcut's location").format(packagename, exceptionstr))
            
            
        self.storebrain.set_progress(packagename, "peppermint-ice", 12)
            
            
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
            
            
        self.storebrain.set_progress(packagename, "peppermint-ice", 24)
            
            
        #First Run existing skips the initial Welcome to Google Chrome dialog, which is very useful here to have a skip in place for
        try:
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/First Run" % packagename, 'w') as fp:
                pass
        except Exception as exceptionstr:
            self.task_remove_package(packagename, subsource, True) #Remove profile's files/folders on failure
            raise ICEModuleException(_("Failed to install {0}: {1} was encountered when making the Chromium-based profile").format(packagename, exceptionstr))
        try:
            os.mkdir(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/Default" % packagename)
        except Exception as exceptionstr:
            self.task_remove_package(packagename, subsource, True) #Remove profile's files/folders on failure
            raise ICEModuleException(_("Failed to install {0}: {1} was encountered when making the Chromium-based profile").format(packagename, exceptionstr))
        
        
        self.storebrain.set_progress(packagename, "peppermint-ice", 36)
            
        
        usefallbackicon = False
        #Copy icon for package
        try:
            shutil.copy(self.storebrain.tempdir + "/icons/" + packagename, os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/icon" % packagename)
        except Exception as exceptionstr:
            usefallbackicon = True
            
            
        self.storebrain.set_progress(packagename, "peppermint-ice", 48)
            
        
        
        #Now to make the JSON file
        with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/Preferences", 'r') as fp:
            profiletomake = json.loads(fp.read())
        
        if "nekocap" in bonuses:
            with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/and-nekocap", 'r') as fp:
                profiletomakeextra = json.loads(fp.read()) #This is how you make json.load work with file paths, I guess
            profiletomake = self.storebrain.dict_recurupdate(profiletomake, profiletomakeextra)
        if "ublock" in bonuses:
            with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/and-ublock", 'r') as fp:
                profiletomakeextra = json.loads(fp.read())
            profiletomake = self.storebrain.dict_recurupdate(profiletomake, profiletomakeextra)
        if "darkreader" in bonuses:
            with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/and-darkreader", 'r') as fp:
                profiletomakeextra = json.loads(fp.read())
            profiletomake = self.storebrain.dict_recurupdate(profiletomake, profiletomakeextra)
        if "imagus" in bonuses:
            with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/and-imagus", 'r') as fp:
                profiletomakeextra = json.loads(fp.read())
            profiletomake = self.storebrain.dict_recurupdate(profiletomake, profiletomakeextra)
        
        
        self.storebrain.set_progress(packagename, "peppermint-ice", 60)
        
        
        #Write profile
        try:
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/Default/Preferences" % packagename, 'w') as fp:
                fp.write(json.dumps(profiletomake, separators=(',', ':'))) # This dumps minified json (how convenient), which is EXACTLY what Chrome uses for Preferences, so it's literally pre-readied
        except Exception as exceptionstr:
            self.task_remove_package(packagename, subsource, True) #Remove profile's files/folders on failure
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
            
            
        self.storebrain.set_progress(packagename, "peppermint-ice", 72)            
            
            
        try:

            with open(os.path.expanduser("~") + "/.local/share/applications/%s.desktop" % packagename, 'w') as fp:
                # I mean, this needs no explanation, it's a .desktop file
                fp.write("[Desktop Entry]\n")
                fp.write("Version=1.0\n")
                fp.write("Name={0}\n".format(self.packagestorage[packagename].realname))
                fp.write("Comment={0}\n".format(_("Website (obtained from Store)")))
                
                fp.write("Exec=/usr/bin/feren-storium-icelaunch {0} {1} {2} {3} {4} {5} {6}\n".format(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s" % packagename, subsource, self.packagestorage[packagename].website, packagename, ublockarg, nekocaparg, darkreadarg))

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
            self.task_remove_package(packagename, subsource, True) #Remove profile's files/folders on failure
            raise ICEModuleException(_("Failed to install {0}: {1} was encountered when creating a shortcut in the Applications Menu").format(packagename, exceptionstr))
        
        #Now repeat for extras, if appropriate
        extrascount = 0 #Classic strat for iteration
        if self.packagestorage[packagename].extrasids != []:
            import urllib.request #Grabbing files from internet
            import urllib.error
        for extraid in self.packagestorage[packagename].extrasids:
            try:
                with open(os.path.expanduser("~") + "/.local/share/applications/{0}-{1}.desktop".format(packagename, extraid), 'w') as fp:
                    # I mean, this needs no explanation, it's a .desktop file
                    fp.write("[Desktop Entry]\n")
                    fp.write("Version=1.0\n")
                    fp.write("Name={0}\n".format(self.packagestorage[packagename].realnameextras[extrascount]))
                    fp.write("Comment={0}\n".format(_("Website (obtained from Store)")))
                    
                    fp.write("Exec=/usr/bin/feren-storium-icelaunch {0} {1} {2} {3} {4} {5} {6}\n".format(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s" % packagename, subsource, self.packagestorage[packagename].websiteextras[extrascount], packagename, ublockarg, nekocaparg, darkreadarg))

                    fp.write("Terminal=false\n")
                    fp.write("X-MultipleArgs=false\n")
                    fp.write("Type=Application\n")
                    
                    try:
                        urllib.request.urlretrieve(self.packagestorage[packagename].iconuriextras[extrascount], (os.path.expanduser("~") + "/.local/share/feren-storium-ice/{0}/icon-{1}".format(packagename, extraid)))
                        fp.write("Icon=%s\n" % (os.path.expanduser("~") + "/.local/share/feren-storium-ice/{0}/icon-{1}".format(packagename, extraid)))
                    except:
                        fp.write("Icon=text-html\n")

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

                    fp.write("Keywords=%s\n" % self.packagestorage[packagename].keywordsextras[extrascount])

                    fp.write("StartupNotify=true\n")
            except Exception as exceptionstr:
                self.task_remove_package(packagename, subsource, True) #Remove profile's files/folders on failure
                raise ICEModuleException(_("Failed to install {0}: {1} was encountered when creating extra shortcuts in the Applications Menu").format(packagename, exceptionstr))
            os.system("chmod +x " + os.path.expanduser("~") + "/.local/share/applications/{0}-{1}.desktop".format(packagename, extraid))
            extrascount += 1
            
        self.storebrain.set_progress(packagename, "peppermint-ice", 99)
        
        #Otherwise they'll refuse to launch from the Applications Menu (bug seen in Mint's own Ice code fork)
        os.system("chmod +x " + os.path.expanduser("~") + "/.local/share/applications/%s.desktop" % packagename)
            
        self.storebrain.set_progress(packagename, "peppermint-ice", 100)
        
        #Clean up after management
        self.finishing_cleanup(packagename)
        return True
    
    def task_remove_package(self, packagename, source, subsource, forinstall=False):
        if packagename not in self.packagestorage:
            raise ICEModuleException(_("%s is not in the Package Storage (packagestorage) yet - make sure it's in the packagestorage variable before obtaining package information.") % packagename)
        
        if not forinstall: # We call this in the install process to clear out partial installs, so for those times we want to skip THIS code to not confuse Store's Brain or anything that could get confused from this module 'unlocking' temporarily
            self.packagemgmtbusy = True
            self.currentpackagename = packagename
        
        #Delete the files and the folders and done        
        try:
            if os.path.isfile(os.path.expanduser("~") + "/.local/share/applications/%s.desktop" % packagename):
                os.remove(os.path.expanduser("~") + "/.local/share/applications/%s.desktop" % packagename)
        except Exception as exceptionstr:
            if not forinstall:
                raise ICEModuleException(_("Failed to uninstall {0}: {1} was encountered when removing the shortcut from the Applications Menu").format(packagename, exceptionstr))
        
        #Now repeat for extras, if appropriate
        extrascount = 0 #Classic strat for iteration
        for extraid in self.packagestorage[packagename].extrasids:
            try:
                if os.path.isfile(os.path.expanduser("~") + "/.local/share/applications/{0}-{1}.desktop".format(packagename, extraid)):
                    os.remove(os.path.expanduser("~") + "/.local/share/applications/{0}-{1}.desktop".format(packagename, extraid))
            except Exception as exceptionstr:
                self.task_remove_package(packagename, subsource, True) #Remove profile's files/folders on failure
                raise ICEModuleException(_("Failed to uninstall {0}: {1} was encountered when removing extra shortcuts from the Applications Menu").format(packagename, exceptionstr))
            extrascount += 1
            
        self.storebrain.set_progress(packagename, "peppermint-ice", 50)
        
        try:
            shutil.rmtree(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s" % packagename)
        except Exception as exceptionstr:
            if not forinstall:
                raise ICEModuleException(_("Failed to uninstall {0}: {1} was encountered when deleting the Chromium-based profile").format(packagename, exceptionstr))
            
        #FIXME: All the 'source' values need to point to the browser, once Source dropdown's implemented
        self.storebrain.set_progress(packagename, "peppermint-ice", 100)
        
        #Clean up after management
        if not forinstall:
            self.finishing_cleanup(packagename)
        return True
    
    def task_update_package(self, packagename, source, subsource):
        self.finishing_cleanup(packagename)
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