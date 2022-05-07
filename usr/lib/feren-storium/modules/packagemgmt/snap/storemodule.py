import configparser
import os
import subprocess
import gettext
import gi


#Dependencies
import gi
gi.require_version('Snapd', '1')
from gi.repository import Snapd



class SnapModuleException(Exception): # Name this according to the module to allow easier debugging
    pass



class module():

    def __init__(self, storeapi):
        #Gettext Translator
        gettext.install("feren-storium", "/usr/share/locale", names="ngettext")

        #Store APIs
        self.storeapi = storeapi

        #Name to be used in Debugging output
        self.title = _("Snap Package Management Module")
        #Name to be shown in the GUI
        self.humanreadabletitle = _("Snap Applications Management")
        #Name to be shown in sources
        self.sourcesmodulename = _("Snap Store")

        #Package Storage will store the data of opened packages this instance, to make future loads faster
        self.packagestorage = {}

        #Configs (obtained by get_configs)
        self.moduleconfigs={}
        self.get_configs()
        
        #Lock to keep stuff from happening while memory is refreshing
        self.memory_refreshing = False

        #What package types does this module work with?
        self.types_supported = ["snap"]

        #////Package Management:////
        #Can manage Application Sources?
        self.canmanagesources = True
        #Snap Client
        self.snapclient = Snapd.Client()
        #Current name being managed
        self.busywithpackage = ""
        #Do subsources require an information change?
        self.subsourceschangeinfo = False #False because no subsources

        
    def refresh_memory(self): # Function to refresh some memory values
        self.memory_refreshing = True
        
        #Refresh package listings
        self.json_storage = {}
        for i in ["package-info/snap", "package-info/generic"]:
            with open("/usr/share/feren-storium/curated/" + i + "/data.json", 'r') as fp:
                self.json_storage[i] = json.loads(fp.read())
        
        self.memory_refreshing = False



    #////Package Management////
    def getSources(self, pkgid):
        #Get a list of sources available for use via this module, for each pkgtype {pkgtype: [sources]}
        # sources = [subsources]
        return {"snap": {}} #Snap only has one source - the Snap Store


    def getAvailable(self, pkgid, sourceid):
        #Check if package even exists in the first place
        #Return values:
        #0: Available
        #1: Unavailable
        #2: Repository requires being added first

        return 0 #TODO

        
    def pkgstorage_add(self, packagename):
        #Not needed as we just consult the JSON data variable for information anyway

        #If it was, this'd be the intended structure?:
        # [pkgtype][all][packagename] for the package information on all sources
        # [pkgtype][x][packagename] for the package information on x source
        #we need pkgtype to determine the right section to store it in

        pass
        

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
            return 0
        else:
            return 1

    
    def progress_snap_cb(self, client, change, _, user_data):
        # Interate over tasks to determine the aggregate tasks for completion.
        total = 0
        done = 0
        for task in change.get_tasks():
            total += task.get_progress_total()
            done += task.get_progress_done()
        percent = round((done/total)*100)
        self.progress_callback(percent)


    def cleanupModule(self):
        #Cleanup after package operations
        self.currentpackagename = ""
        self.packagemgmtbusy = False


    def get_package_changes(self, packagename, operationtype, pkgtype, source, subsource):
        #Examine the package changes
        return {"install": [], "update": [], "remove": [], "sourceadd": [], "sourceremove": []} #TODO
        
    
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




    #////Package Information////
    def internalToPkgName(self, internalname, packagetype):
        #Translate internal Store name to the appropriate package name
        #e.g.: mozilla-firefox + Flatpak = org.mozilla.firefox

        #internalname: Internal in-Store name
        #packagetype: apt
        try:
            return self.json_storage["package-info/"+packagetype][internalname][packagetype + "-name"]
        except:
            raise SnapInfoModuleException(packagename, _("could not be found in the Store's package names data. If you are getting an exception throw, it means you have not used a Try to respond to the package not being in the Store."))

    def pkgNameToInternal(self, packagename, packagetype):
        #Translate package name to internal Store name
        #e.g.: org.mozilla.firefox + Flatpak = mozilla-firefox

        #packagename: Package name
        #packagetype: apt
        try:
            if self.json_storage["package-info/"+packagetype][pkg][packagetype + "-name"] == packagename:
                return pkg
            raise SnapInfoModuleException(packagename, _("is not associated with any Store internal name. If you are getting an exception throw, it means you have not used a Try to respond to the package not being in the Store."))
        except:
            raise SnapInfoModuleException(packagename, _("is not associated with any Store internal name. If you are getting an exception throw, it means you have not used a Try to respond to the package not being in the Store."))


    def getInfo(self, packagename, packagetype, sourcename=""):
        #Get information on a package using the JSON data
        if packagetype not in self.types_supported:
            raise SnapInfoModuleException(packagetype, _("is not supported by this information module. If you are getting an exception throw, it means you have not used a Try to respond to the module not supporting this type of package."))
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


    def getAuthor(self, packagename, packagetype):
        try:
            author = self.json_storage["package-info/" + packagetype][packagename]["author"]
        except:
            author = _("Unknown Author")
        return author

    def getBugsURL(self, packagename, packagetype):
        try:
            bugreporturl = self.json_storage["package-info/" + packagetype][packagename]["bugreporturl"]
        except:
            bugreporturl = ""
        return bugreporturl

    def getTOSURL(self, packagename, packagetype):
        try:
            tosurl = self.json_storage["package-info/" + packagetype][packagename]["tosurl"]
        except:
            tosurl = ""
        return tosurl

    def getPrivPolURL(self, packagename, packagetype):
        try:
            privpolurl = self.json_storage["package-info/" + packagetype][packagename]["privpolurl"]
        except:
            privpolurl = ""
        return privpolurl

    def getCanTheme(self, packagename, packagetype):
        # Return values:
        # 0: No
        # 1: Yes
        # 2: Yes, but manually enabled
        # 3: Yes, except for Feren OS's style
        # 4: Has own themes system
        # 5: No because LibAdwaita
        # 6: No because LibGranite

        try:
            canusethemes = self.json_storage["package-info/" + packagetype][packagename]["canusethemes"]
        except:
            canusethemes = 1 # Use fallback of Yes when unknown to hide the message
        return canusethemes

    def getCanTouchScreen(self, packagename, packagetype):
        # Return values:
        # 0: No
        # 1: Yes
        # 2: Partially

        try:
            canusetouchscreen = self.json_storage["package-info/" + packagetype][packagename]["canusetouchscreen"]
        except:
            canusetouchscreen = 1 # Use fallback of Yes when unknown to hide the message
        return canusetouchscreen

    def getCanUseAccessibility(self, packagename, packagetype):
        try:
            canuseaccessibility = self.json_storage["package-info/" + packagetype][packagename]["canuseaccessibility"]
        except:
            canuseaccessibility = True # Use fallback of True when unknown to hide the message
        return canuseaccessibility

    def getCanUseDPI(self, packagename, packagetype):
        try:
            canusedpiscaling = self.json_storage["package-info/" + packagetype][packagename]["canusedpiscaling"]
        except:
            canusedpiscaling = True # Use fallback of True when unknown to hide the message
        return canusedpiscaling

    def getCanUseOnPhone(self, packagename, packagetype):
        try:
            canuseonphone = self.json_storage["package-info/" + packagetype][packagename]["canuseonphone"]
        except:
            canuseonphone = True # Use fallback of True when unknown to hide the message
        return canuseonphone

    def getIsOfficial(self, packagename, packagetype):
        try:
            isofficial = self.json_storage["package-info/" + packagetype][packagename]["isofficial"]
        except:
            isofficial = True # Use fallback of True when unknown to hide the message
        return isofficial

    def getSnapName(self, packagename, packagetype):
        try:
            snapname = self.json_storage["package-info/" + packagetype][packagename]["snap-name"]
        except:
            raise GenericInfoModuleException(packagename, _("has no, or an invalid, snap-name value in the package metadata. Snap Packages MUST have an snap-name value when curated."))
            return
        return snapname

    def getSnapSource(self, packagename, packagetype):
        try:
            snapsource = self.json_storage["package-info/" + packagetype][packagename]["snap-source"]
        except:
            raise GenericInfoModuleException(packagename, _("has no, or an invalid, snap-source value in the package metadata. Snap Packages MUST have an snap-source value when curated."))
            return
        return snapsource



if __name__ == "__main__":
    module = PackageMgmtModule()
