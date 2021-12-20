import configparser
import os
import subprocess
import gettext
import gi


#Dependencies
import gi
gi.require_version('Snapd', '1')
from gi.repository import Snapd


def should_load(): #Should this module be loaded?
    return True



class SnapModuleException(Exception): # Name this according to the module to allow easier debugging
    pass



class main():

    def __init__(self, storebrain):

        gettext.install("feren-storium", "/usr/share/locale", names="ngettext")

        #Name to be used in Debugging output
        self.title = _("Snap Package Management Module")
        #Name to be shown in the GUI
        self.humanreadabletitle = _("Snap Applications Management")
        
        #Can manage Application Sources?
        self.canmanagesources = True
        
        #Store Brain
        self.storebrain = storebrain
        
        #What package types does this manage?
        self.types_supported = ["snap"]
        
        #Configs (obtained by get_configs)
        self.moduleconfigs={}
        self.get_configs()
        
        #Package Storage will store the data of opened packages this instance
        self.packagestorage = {}
        
        #Last package viewed
        self.lastpkgviewed = ""
        
        #Snap Client
        self.snapclient = Snapd.Client()
        
        #Lock to keep stuff from happening while memory is refreshing
        self.memory_refreshing = False
        
        #Is the package management busy?
        self.packagemgmtbusy = False
        
        #Current name being managed
        self.currentpackagename = ""
        
        #FIXME: Is there a way to carry progress_callback into progress_snap_cb?
        self.progress_callback = None
        
    def refresh_memory(self): # Function to refresh some memory values
        self.memory_refreshing = True
        
        pass
        
        self.memory_refreshing = False
        
                
    def sourceQuery(self, packagename, packagetype, sourcelist):
        if sourcelist == ['snapstore']:
            return ['snapstore'] #Snap only has one source - the Snap Store
        else:
            raise SnapModuleException(_("Unsupported sources were provided."))
    
    def get_subsources(self, packagename, packagetype, source):
        #Leave empty as snap has no subsources
        return []
    
        
    def pkgstorage_add(self, packagename):
        #Not needed as we just consult the package information modules for information anyway
        pass

    def get_generic_information(self, packagename, packagetype):
        if packagetype not in self.types_supported:
            raise SnapModuleException(_("Items of type %s are not supported by this module.") % packagename)
        
        # Return generic package information via Brain API
        try:
            return self.storebrain.get_generic_item_info(packagename, packagetype)
        except:
            raise SnapModuleException(e)

    def get_information(self, packagename, packagetype, source):
        if packagetype not in self.types_supported:
            raise SnapModuleException(_("Items of type %s are not supported by this module.") % packagename)
        
        # Return package information via Brain API
        try:
            return self.storebrain.get_item_info_specific(packagename, packagetype, source)
        except Exception as e:
            raise SnapModuleException(e)
        

    def get_status(self, packagename, pkgtype, source):
        # Return package installation status
        # 0 - Uninstalled
        # 1 - Installed
        # 2 - Updatable
        # 3 - Available in a disabled source
        # 403 - Not in repositories
        if not os.path.isfile("/usr/bin/snap"):
            return 3
        try:
            snapinfo = self.snapclient.get_snap_sync(self.storebrain.get_item_info_specific(packagename, pkgtype, source)["snap-name"])
        except:
            return(0)
        else:
            return(1)
    
    
    def task_cleanup(self, packagename):
        #Cleanup after package operations
        self.currentpackagename = ""
        self.packagemgmtbusy = False
        self.progress_callback = None
        
    
    def progress_snap_cb(self, client, change, _, user_data):
        # Interate over tasks to determine the aggregate tasks for completion.
        total = 0
        done = 0
        for task in change.get_tasks():
            total += task.get_progress_total()
            done += task.get_progress_done()
        percent = round((done/total)*100)
        self.progress_callback(percent)
        
    
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
        
    
    #Actual management
    def task_install_package(self, taskdata, progress_callback):
        #Install package and return exit code
        self.packagemgmtbusy = True
        
        #FIXME: Is there a way to carry progress_callback into progress_snap_cb?
        self.progress_callback = progress_callback
        
        self.currentpackagename = taskdata["packagename"]
        snapname = taskdata["pkginfo"]["snap-name"]
        
        try:
            outcome = self.snapclient.install2_sync(Snapd.InstallFlags.NONE, snapname, None, None, self.progress_snap_cb, (None,), None)
        except:
            return False
        
        return outcome
    
    def task_remove_package(self, taskdata, progress_callback):
        #Remove package and return exit code
        self.packagemgmtbusy = True
        
        self.progress_callback = progress_callback
        
        self.currentpackagename = taskdata["packagename"]
        snapname = taskdata["pkginfo"]["snap-name"]
        
        try:
            outcome = self.snapclient.remove2_sync(Snapd.InstallFlags.NONE, snapname, self.progress_snap_cb, (None,), None)
        except:
            return False
        
        return outcome
    
    def task_update_package(self, taskdata, progress_callback):
        #You SHOULD NOT be able to hit Update for Snaps anyway, so raise an error
        raise SnapModuleException(_("Snaps update themselves."))
    
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
