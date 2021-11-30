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


class PackageStore():
    def __init__(self, realname, iconuri, shortdesc, description, author, category, images, website, donateurl, bugreporturl, tosurl, privpolurl, canusethemes, canusetouchscreen, canuseaccessibility, canusedpiscaling, canuseonphone, isofficial, snapname, snapsource):
        self.realname = realname
        self.iconuri = iconuri
        self.shortdesc = shortdesc
        self.description = description
        self.author = author
        self.category = category
        self.images = images
        self.website = website
        self.donateurl = donateurl
        self.bugreporturl = bugreporturl
        self.tosurl = tosurl
        self.privpolurl = privpolurl
        self.keywords = ""
        self.isofficial = isofficial
        self.canusethemes = canusethemes
        self.canusetouchscreen = canusetouchscreen
        self.canuseaccessibility = canuseaccessibility
        self.canusedpiscaling = canusedpiscaling
        self.canuseonphone = canuseonphone
        self.snapname = snapname
        self.snapsource = snapsource



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
        self.types_managed = ["snap"]
        
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
        
    def refresh_memory(self): # Function to refresh some memory values
        self.memory_refreshing = True
        
        pass
        
        self.memory_refreshing = False
        
                
    def get_sources(self, packagename):
        return ['snapstore'] #Snap only has one source - the Snap Store
        #if packagename in self.packagestorage:
            #return [self.packagestorage[packagename].aptsource]
        #else:
            #raise SnapModuleException(_("%s is not in the Package Storage (packagestorage) yet - make sure it's in the packagestorage variable before obtaining its sources.") % packagename)
    
    def get_subsources(self, packagename, source):
        #Leave empty as snap has no subsources
        return []
    
        
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
            
            self.packagestorage[packagename] = PackageStore(packageinfo["realname"], packageinfo["iconuri"], packageinfo["shortdescription"], packageinfo["description"], packageinfo["author"], packageinfo["category"], packageinfo["images"], packageinfo["website"], packageinfo["donateurl"], packageinfo["bugreporturl"], packageinfo["tosurl"], packageinfo["privpolurl"], packageinfo["canusethemes"], packageinfo["canusetouchscreen"], packageinfo["canuseaccessibility"], packageinfo["canusedpiscaling"], packageinfo["canuseonphone"], packageinfo["isofficial"], packageinfo["snapname"], packageinfo["snapsource"])

    def get_information(self, packagename):
        # Return description for package
        if packagename in self.packagestorage:
            return self.packagestorage[packagename].realname, self.packagestorage[packagename].iconuri, self.packagestorage[packagename].shortdesc, self.packagestorage[packagename].description, self.packagestorage[packagename].author, self.packagestorage[packagename].category, self.packagestorage[packagename].images, self.packagestorage[packagename].website, self.packagestorage[packagename].donateurl, self.packagestorage[packagename].bugreporturl, self.packagestorage[packagename].tosurl, self.packagestorage[packagename].privpolurl, self.packagestorage[packagename].keywords
        else:
            raise SnapModuleException(_("%s is not in the Package Storage (packagestorage) yet - make sure it's in the packagestorage variable before obtaining package information.") % packagename)

    def get_status(self, packagename):
        # Return package installation status
        # 0 - Uninstalled
        # 1 - Installed
        # 2 - Updatable
        # 3 - Available in a disabled source
        # 403 - Not in repositories
        if not os.path.isfile("/usr/bin/snap"):
            return 3
        try:
            snapinfo = self.snapclient.get_snap_sync(self.packagestorage[packagename].snapname)
        except:
            return(0)
        else:
            return(1)
    
    
    def finishing_cleanup(self, packagename):
        #Cleanup after package operations
        self.currentpackagename = ""
        self.packagemgmtbusy = False
        
    
    def progress_snap_cb(self, client, change, _, user_data):
        # Interate over tasks to determine the aggregate tasks for completion.
        total = 0
        done = 0
        for task in change.get_tasks():
            total += task.get_progress_total()
            done += task.get_progress_done()
        percent = round((done/total)*100)
        self.storebrain.set_progress(self.currentpackagename, "snap", percent)
        
    
    #Add to Tasks
    def install_package(self, packagename, source, subsource):
        bonuses = [] #TODO: Add confirmation prompt showing changes, and also allowing bonus selection
        
        self.storebrain.tasks.add_task(self.modulename, packagename, 0, self.packagestorage[packagename].realname, source, subsource, bonuses)
    
    def update_package(self, packagename, source, subsource):
        #TODO: Add confirmation prompt showing changes, and also allowing bonus selection
        
        self.storebrain.tasks.add_task(self.modulename, packagename, 1, self.packagestorage[packagename].realname, source, subsource)
    
    def remove_package(self, packagename, source, subsource):
        #TODO: Add confirmation prompt showing changes, and also allowing bonus selection
        
        self.storebrain.tasks.add_task(self.modulename, packagename, 2, self.packagestorage[packagename].realname, source, subsource)
        
    
    #Actual management TODO: Progress callback
    def task_install_package(self, packagename, source, subsource, bonuses=[]):
        #Install package and return exit code
        self.packagemgmtbusy = True
        
        snapname = self.packagestorage[packagename].snapname
        self.currentpackagename = packagename
        
        try:
            outcome = self.snapclient.install2_sync(Snapd.InstallFlags.NONE, snapname, None, None, self.progress_snap_cb, (None,), None)
        except:
            return False
        
        #Clean up after management
        self.finishing_cleanup(packagename)
        return outcome
    
    def task_remove_package(self, packagename, source, subsource):
        #Remove package and return exit code
        self.packagemgmtbusy = True
        
        snapname = self.packagestorage[packagename].snapname
        self.currentpackagename = packagename
        
        try:
            outcome = self.snapclient.remove2_sync(Snapd.InstallFlags.NONE, snapname, self.progress_snap_cb, (None,), None)
        except:
            return False
        
        #Clean up after management
        self.finishing_cleanup(packagename)
        return outcome
    
    def task_update_package(self, packagename, source, subsource):
        #You SHOULD NOT be able to hit Update for Snaps anyway, so raise an error
        self.finishing_cleanup(packagename)
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
