import configparser
import os
import subprocess
import gettext
import gi


#Dependencies



class ICEModuleException(Exception): # Name this according to the module to allow easier debugging
    pass



class PackageMgmtModule():

    def __init__(self, storegui):

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
        
    def refresh_sources(self): # Function to refresh sources list - just return if your module doesn't need this
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
            #TODO: Get from Store Brain's Info Module
            
            #Get the values
            #try:
                #pkgdesc = debpackage["Description"].splitlines()
            #except:
                #pkgdesc = [self.storemain.uistrings.nodesc]
            #try:
                #pkgauthor = debpackage["Maintainer"]
            #except:
                #pkgauthor = self.storemain.uistrings.unknownauthor
            #try:
                #pkginstalledsize = debpackage["Installed-Size"]
            #except:
                #pkginstalledsize = self.storemain.uistrings.unknownsize
            #try:
                #pkgsection = debpackage["Section"]
            #except:
                #pkgsection = self.storemain.uistrings.nosection
            #try:
                #pkghomepage = debpackage["Homepage"]
            #except:
                #pkghomepage = ""
            
                        
            #self.packagestorage(packagename) = PackageStore(packagename, debpackage.pkgname, debpackage["Version"], pkgauthor, pkginstalledsize, pkgsection, pkghomepage, pkgdesc)
            pass
            
    def get_headerdescription(self, packagename):
        return self.genericheader

    def get_description(self, packagename):
        # Return description for package
        if packagename in packagestorage:
            return packagestorage[packagename].description
        else:
            raise ICEModuleException(packagename, _("is not in the Package Storage (packagestorage) yet - make sure it's in the packagestorage variable before obtaining package information."))

    def get_status(self, packagename):
        # Return package installation status
        # 0 - Uninstalled
        # 1 - Installed
        pass
    
    def install_package(self, packagename):
        #Install package and return exit code
        self.packagemgmtbusy = True
        
        packagename = self.packagestorage[packagename].name
        
        #Remove package and return exit code
        self.currentpackagename = packagename
        try:
            
            #TODO
            
        except:
            return False
        
        #Clean up after management
        self.currentpackagename = ""
        self.packagemgmtbusy = False
        return outcome.get_exit_code() == PackageKitGlib.ExitEnum.SUCCESS
    
    def remove_package(self, packagename):
        self.packagemgmtbusy = True
        
        #Remove package and return exit code
        self.currentpackagename = packagename
        try:
            res=pk_client.resolve(PackageKitGlib.FilterEnum.NONE, [packagename], None, lambda p, t, d: True, None)
            package_ids=res.get_package_array()
            if not len(package_ids) > 0:
                return False
            
            outcome = self.pk_client.remove_packages(0, [package_ids[0].get_id()], True, True, None, self.progress_callback, None)
        except:
            return False
        
        #Clean up after management
        self.currentpackagename = ""
        self.packagemgmtbusy = False
        return outcome.get_exit_code() == PackageKitGlib.ExitEnum.SUCCESS
    
    def update_package(self, packagename):
        #You SHOULD NOT be able to hit Update for websites anyway, so raise an error
        raise ICEModuleException(_("You wouldn't update a website."))
    
    def get_package_changes(self, pkgsinstalled, pkgsupdated, pkgsremoved):
        #Examine the package changes - pkgsinstalled, pkgsupdated and pkgsremoved are lists
        # Just skip it by having empty returns
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
        raise ICEModuleException(_("You can't go and manage sources when the 'sources' are just web browsers."))
    
    def disable_appsource(self, appsource):
        #You SHOULD NOT be able to manage Application Sources for websites anyway, so raise an error
        raise ICEModuleException(_("You can't go and manage sources when the 'sources' are just web browsers."))

if __name__ == "__main__":
    module = PackageMgmtModule()