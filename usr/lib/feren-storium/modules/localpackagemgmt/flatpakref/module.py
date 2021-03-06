import configparser
import os
import subprocess
import gettext
import gi


#Dependencies
import apt
import apt.debfile
import gi
gi.require_version('PackageKitGlib', '1.0')
from gi.repository import PackageKitGlib


class DebModuleException(Exception): # Name this according to the module to allow easier debugging
    pass



class PackageStore():

    def __init__(self, pkgname, pkgversion, pkgauthor, pkginstalledsize, pkgsection, pkghomepage, pkgdescription):
        self.name = pkgname
        self.version = pkgversion
        self.author = author
        self.installedsize = pkginstalledsize
        self.section = pkgsection
        self.homepage = pkghomepage
        self.description = pkgdescription


class LocalPackageMgmtModule():

    def __init__(self, storemain):
        
        self.storemain = storemain

        gettext.install("feren-storium", "/usr/share/locale", names="ngettext")

        #Name to be used in Debugging output
        self.title = _("deb Package Management Module")
        #Name to be shown in the GUI
        self.humanreadabletitle = _("Local Package Files Management")
        
        #Mimetypes this works with
        self.mimetypessupported = ["application/vnd.debian.binary-package"]
        
        #Generic header title for when there's no header
        self.genericheader = _("Local Package File")
        
        #Does this manage the application sources of a package management module?
        self.managesmodulesources = False
        #If so, what modules does it manage? (e.g.: [flatpak])
        self.modulessourcemanaged = []
        
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
        
        #Current file being managed
        self.currentpackagefile = ""
        
    def refresh_memory(self): # Function to refresh some memory values
        self.memory_refreshing = True
        
        self.apt_cache = apt.Cache()
        
        self.memory_refreshing = False
        
    def check_package_in_storage(self, packagefile):
        if packagefile not in self.packagestorage:
            debpackage = apt.debfile.DebPackage(packagefile, None)
            
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
            
                        
            self.packagestorage(packagefile) = PackageStore(packagename, debpackage.pkgname, debpackage["Version"], pkgauthor, pkginstalledsize, pkgsection, pkghomepage, pkgdesc)
            
    def get_headerdescription(self, packagefile):
        return self.genericheader

    def get_description(self, packagefile):
        # Return description for package
        if packagefile in packagestorage:
            return packagestorage[packagefile].description
        else:
            raise DebModuleException(packagefile, _("is not in the Package Storage (packagestorage) yet - make sure it's in the packagestorage variable before obtaining package information."))

    def get_status(self, packagename):
        while self.memory_refreshing == True:
            pass
        # Return package installation status
        # 0 - Uninstalled
        # 1 - Installed
        # 2 - Updatable
        
        try:
            pkginfo = self.apt_cache[package]
        except:
            return(0)
        self.apt_cache.upgrade(True) # dist-upgrade

        if (self.apt_cache[pkginfo.name].is_installed and self.apt_cache[pkginfo.name].marked_upgrade and self.apt_cache[pkginfo.name].candidate.version != self.apt_cache[pkginfo.name].installed.version):
            return(2)
        elif self.apt_cache[pkginfo.name].is_installed:
            return(1)
        else:
            return(0)
        
        
    def progress_callback(self, progress, uselesstype, user_data):
        try:
            if progress.props.package_id.split(";")[0] == self.packagestorage[self.currentpackagefile].name:
                print(self.packagestorage[self.currentpackagefile].name, ':', progress.props.percentage, '%')
                #TODO: Pass this to storemain for Store's overall tasks and progress storage
        except:
            pass
    
    
            outcome = self.pk_client.install_files(0, [packagefile], None, self.progress_callback, None)
        except:
            return False
        
        #Clean up after management
        self.currentpackagefile = ""
        self.packagemgmtbusy = False
        return outcome.get_exit_code() == PackageKitGlib.ExitEnum.SUCCESS
    
    def remove_package(self, packagefile):
        self.packagemgmtbusy = True
        
        packagename = self.packagestorage[packagefile].name
        
        #Remove package and return exit code
        self.currentpackagefile = packagefile
        try:
            res=pk_client.resolve(PackageKitGlib.FilterEnum.NONE, [packagename], None, lambda p, t, d: True, None)
            package_ids=res.get_package_array()
            if not len(package_ids) > 0:
                return False
            
            outcome = self.pk_client.remove_packages(0, [package_ids[0].get_id()], True, True, None, self.progress_callback, None)
        except:
            return False
        
        #Clean up after management
        self.currentpackagefile = ""
        self.packagemgmtbusy = False
        return outcome.get_exit_code() == PackageKitGlib.ExitEnum.SUCCESS
    
    def update_package(self, packagefile):
        self.packagemgmtbusy = True
        
        packagename = self.packagestorage[packagefile].name
        
        #Update package and return exit code
        self.currentpackagefile = packagefile
        try:
            res=pk_client.resolve(PackageKitGlib.FilterEnum.NONE, [packagename], None, lambda p, t, d: True, None)
            package_ids=res.get_package_array()
            if not len(package_ids) > 0:
                return False
            
            outcome = self.pk_client.update_packages(0, [package_ids[0].get_id()], True, True, None, self.progress_callback, None)
        except:
            return False
        
        #Clean up after management
        self.currentpackagefile = ""
        self.packagemgmtbusy = False
        return outcome.get_exit_code() == PackageKitGlib.ExitEnum.SUCCESS
    
    def get_package_changes(self, packagefile, operationtype):
        #operationtype must be: 1: Install, 2: Update, 3: Remove
        pkgsinstalled=[]
        pkgsupdated=[]
        pkgsremoved=[]
        #Examine the package changes - pkgsinstalled, pkgsupdated and pkgsremoved are lists
        #TODO: Figure out a means of getting package dependencies of .debs in PackageKit - right now we'll just have to output that the .deb's package name is being installed, removed or updated according to the arguments
        if operationtype == 1:
            pkgsinstalled.append(self.packagestorage[packagefile].name)
        elif operationtype == 2:
            pkgsupdated.append(self.packagestorage[packagefile].name)
        elif operationtype == 3:
            pkgsremoved.append(self.packagestorage[packagefile].name)
        
        return pkgsinstalled, pkgsupdated, pkgsremoved
    
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
        #TODO: Change this for storemain once we have proper storemain module storage var.
        self.storemain.modules_apt.enable_appsource(appsource)
    
    def disable_appsource(self, appsource):
        #Disable an Application Source
        #TODO: Change this for storemain once we have proper storemain module storage var.
        self.storemain.modules_apt.disable_appsource(appsource)

if __name__ == "__main__":
    module = PackageMgmtModule()