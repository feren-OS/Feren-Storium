import configparser
import os
import subprocess
import gettext
import gi


#Dependencies
import apt
import gi
gi.require_version('PackageKitGlib', '1.0')
from gi.repository import PackageKitGlib



class APTModuleException(Exception): # Name this according to the module to allow easier debugging
    pass



class PackageMgmtModule():

    def __init__(self, storegui):

        gettext.install("feren-storium", "/usr/share/locale", names="ngettext")

        #Name to be used in Debugging output
        self.title = _("APT Package Management Module")
        #Name to be shown in the GUI
        self.humanreadabletitle = _("Standard Applications Management")
        
        #Can manage Application Sources?
        self.canmanagesources = True
        
        #Application Sources (leave at {} if canmanagesources is False I guess)
        # internal name: Human-readable name
        self.applicationsources = {"standard": [_("Standard Installation")], /
                                   "google-chrome": [_("Google (Official)")], /
                                   "google-earth": [_("Google (Official)")], /
                                   "vivaldi": [_("Vivaldi (Official)")], /
                                   "microsoft-edge": [_("Microsoft (Official)")], /
                                   "visual-studio": [_("Microsoft (Official)")], /
                                   "opera": [_("Opera (Official)")], /
                                   "waterfox": [_("hawkeye116477")]}
        
        #Configs (obtained by get_configs)
        self.moduleconfigs={}
        self.get_configs()
        
        #Package Storage will store the data of opened packages this instance
        self.packagestorage = {}
        
        #Last package viewed
        self.lastpkgviewed = ""
        
        #APT Cache for memory
        self.apt_cache = apt.Cache()
        self.pk_client = PackageKitGlib.Client()
        
        #Lock to keep stuff from happening while memory is refreshing
        self.memory_refreshing = False
        
        #Is the package management busy?
        self.packagemgmtbusy = False
        
        #Current name being managed
        self.currentpackagename = ""
        
    def refresh_memory(self): # Function to refresh some memory values
        self.memory_refreshing = True
        
        self.apt_cache = apt.Cache()
        
        self.memory_refreshing = False
        
    def check_package_in_storage(self, packagename):
        if packagename not in self.packagestorage:
            debpackage = apt.debfile.DebPackage(packagename, None)
            
            #Get the values
            try:
                pkgdesc = debpackage["Description"].splitlines()
            except:
                pkgdesc = [self.storemain.uistrings.nodesc]
            try:
                pkgauthor = debpackage["Maintainer"]
            except:
                pkgauthor = self.storemain.uistrings.unknownauthor
            try:
                pkginstalledsize = debpackage["Installed-Size"]
            except:
                pkginstalledsize = self.storemain.uistrings.unknownsize
            try:
                pkgsection = debpackage["Section"]
            except:
                pkgsection = self.storemain.uistrings.nosection
            try:
                pkghomepage = debpackage["Homepage"]
            except:
                pkghomepage = ""
            
                        
            self.packagestorage(packagename) = PackageStore(packagename, debpackage.pkgname, debpackage["Version"], pkgauthor, pkginstalledsize, pkgsection, pkghomepage, pkgdesc)
            
    def get_headerdescription(self, packagename):
        return self.genericheader

    def get_description(self, packagename):
        # Return description for package
        if packagename in packagestorage:
            return packagestorage[packagename].description
        else:
            raise DebModuleException(packagename, _("is not in the Package Storage (packagestorage) yet - make sure it's in the packagestorage variable before obtaining package information."))

    def get_status(self, packagename):
        # Return package installation status
        # 0 - Uninstalled
        # 1 - Installed
        # 2 - Updatable
        # 3 - Available in a disabled source
        # 403 - Not in repositories
        pass
    
    def finishing_cleanup(self, packagename):
        #Cleanup after package operations
        self.currentpackagename = ""
        self.packagemgmtbusy = False
        #TODO: Move this call to Store Brain's Tasks management once implemented
        self.storebrain.gui_module.mainpage._refresh_page(packagename, "apt")
        
    
    def install_package(self, packagename):
        #Install package and return exit code
        self.packagemgmtbusy = True
        
        packagename = self.packagestorage[packagename].name
        
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
        self.finishing_cleanup(packagename)
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
        self.finishing_cleanup(packagename)
        return outcome.get_exit_code() == PackageKitGlib.ExitEnum.SUCCESS
    
    def update_package(self, packagename):
        self.packagemgmtbusy = True
        
        #Update package and return exit code
        self.currentpackagename = packagename
        try:
            res=pk_client.resolve(PackageKitGlib.FilterEnum.NONE, [packagename], None, lambda p, t, d: True, None)
            package_ids=res.get_package_array()
            if not len(package_ids) > 0:
                return False
            
            outcome = self.pk_client.update_packages(0, [package_ids[0].get_id()], True, True, None, self.progress_callback, None)
        except:
            return False
        
        #Clean up after management
        self.finishing_cleanup(packagename)
        return outcome.get_exit_code() == PackageKitGlib.ExitEnum.SUCCESS
    
    def get_package_changes(self, pkgsinstalled, pkgsupdated, pkgsremoved):
        #Examine the package changes - pkgsinstalled, pkgsupdated and pkgsremoved are lists
        pass
    
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
        #Enable an Application Source
        pass
    
    def disable_appsource(self, appsource):
        #Disable an Application Source
        pass

if __name__ == "__main__":
    module = PackageMgmtModule()