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


def should_load(): #Should this module be loaded?
    return os.path.isfile("/usr/bin/apt")



class APTModuleException(Exception): # Name this according to the module to allow easier debugging
    pass



class main():

    def __init__(self, storebrain):

        gettext.install("feren-storium", "/usr/share/locale", names="ngettext")

        #Name to be used in Debugging output
        self.title = _("APT Package Management Module")
        #Name to be shown in the GUI
        self.humanreadabletitle = _("Standard Applications Management")
        
        #Can manage Application Sources?
        self.canmanagesources = True
        
        #Store Brain
        self.storebrain = storebrain
        
        #What package types does this manage?
        self.types_supported = ["apt"]
        
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
        
                
    def sourceQuery(self, packagename, pkgtype, sourcelist):
        #TODO: Remove sources whenever they're enabled and the package isn't available
        
        return sourcelist #TEMPORARY
    
    
    def get_subsources(self, packagename, pkgtype, source):
        #Leave empty as apt has no subsources
        return []
    
        
    def pkgstorage_add(self, packagename, pkgtype):
        #Not needed as we just consult the package information modules for information anyway
        
        #If it was, this'd be the intended structure:
        # [pkgtype][all] for ALL sources information
        # [pkgtype][x] where x is a source, for each source, with their specific information
        #we need pkgtype to determine the right section to store it in
        
        #Additionally, if this was needed, it would be triggered via the get_generic_information and get_information calls below.
        
        pass

    def get_generic_information(self, packagename, pkgtype):
        if pkgtype not in self.types_supported:
            raise APTModuleException(_("Items of type %s are not supported by this module.") % packagename)
        
        # Return generic package information via Brain API
        try:
            return self.storebrain.get_generic_item_info(packagename, pkgtype)
        except:
            raise APTModuleException(e)

    def get_information(self, packagename, pkgtype, source):
        if pkgtype not in self.types_supported:
            raise APTModuleException(_("Items of type %s are not supported by this module.") % packagename)
        
        # Return package information via Brain API
        try:
            return self.storebrain.get_item_info_specific(packagename, pkgtype, source)
        except Exception as e:
            raise APTModuleException(e)
        

    def get_status(self, packagename, pkgtype, source):
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
        
    #Add to Tasks
    def install_package(self, packagename, pkgtype, source, subsource):
        bonuses = [] #TODO: Add confirmation prompt showing changes, and also allowing bonus selection
        
        self.storebrain.tasks.add_task(packagename, pkgtype, self, 0, self.storebrain.get_item_info_specific(packagename, pkgtype, source, True), source, subsource, bonuses)
    
    def update_package(self, packagename, pkgtype, source, subsource):
        #TODO: Add confirmation prompt showing changes
        
        self.storebrain.tasks.add_task(packagename, pkgtype, self, 1, self.storebrain.get_item_info_specific(packagename, pkgtype, source, True), source, subsource)
    
    def remove_package(self, packagename, pkgtype, source, subsource):
        #TODO: Add confirmation prompt showing changes
        
        self.storebrain.tasks.add_task(packagename, pkgtype, self, 2, self.storebrain.get_item_info_specific(packagename, pkgtype, source, True), source, subsource)
        
    
    #Actual management TODO: Progress callback
    def task_install_package(self, taskdata):
        #Install package and return exit code
        self.packagemgmtbusy = True
        
        #Remove package and return exit code
        self.currentpackagename = taskdata["packagename"]
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
    
    def task_remove_package(self, taskdata):
        self.packagemgmtbusy = True
        
        #Remove package and return exit code
        self.currentpackagename = taskdata["packagename"]
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
    
    def task_update_package(self, taskdata):
        self.packagemgmtbusy = True
        
        #Update package and return exit code
        self.currentpackagename = taskdata["packagename"]
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