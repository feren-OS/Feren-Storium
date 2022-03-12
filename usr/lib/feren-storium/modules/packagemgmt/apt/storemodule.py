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



class module():

    def __init__(self, storeapi):
        #Gettext Translator
        gettext.install("feren-storium", "/usr/share/locale", names="ngettext")
        
        #Store Brain
        self.storeapi = storeapi

        #Name to be used in Debugging output
        self.title = _("APT Packages Module")
        #Name to be shown in the GUI
        self.humanreadabletitle = _("Standard Applications")
        #Name to be shown in sources
        self.sourcesmodulename = _("Standard Install")
        
        #Package Storage will store the data of opened packages this instance, to make future loads faster
        self.packagestorage = {}
        
        #Configs (obtained by get_configs)
        self.moduleconfigs={}
        self.get_configs()
        
        #Lock to keep stuff from happening while memory is refreshing
        self.memory_refreshing = False
        
        #What package types does this module work with?
        self.types_supported = ["apt"]
        
        #////Package Management:////
        # Can manage Application Sources?
        self.canmanagesources = True
        #APT Cache for memory
        self.apt_cache = apt.Cache()
        self.pk_client = PackageKitGlib.Client()
        #Current name being managed
        self.busywithpackage = ""
        #Do subsources require an information change?
        self.subsourceschangeinfo = False #False because no subsources
        
        #Package IDs Dictionary
        self.pkg_ids = {}
    

    def refresh_memory(self): # Function to refresh some memory values
        self.memory_refreshing = True
        
        #Refresh APT cache
        self.apt_cache = apt.Cache()
        #Refresh package listings
        self.json_storage = {}
        for i in ["package-info/apt"]:       
            self.json_storage[i] = storeapi.getCuratedJSON(i)
        
        self.memory_refreshing = False
    


    #////Package Management////
    def getSources(self, pkgid):
        #Get a list of sources available for use via this module, for each pkgtype {pkgtype: [sources]}
        # sources = [subsources]
        sourceslist = {"apt": {}}
        for source in self.json_storage["package-info/apt"][pkgid]["sources-available"]:
            result = getAvailable(pkgid, source)
            if result == 0 or result == 2:
                #Leave the subsources empty as apt has none
                sourceslist["apt"][source] = []
            
        return sourceslist
    
    
    def getAvailable(self, pkgid, sourceid):
        #Check if package even exists in the first place
        #Return values:
        #0: Available
        #1: Unavailable
        #2: Repository requires being added first
        
        return 0 #TODO 'cos I'm too lazy rn to read that damn documentation to figure out how to check package existing
        
    
    def pkgstorage_add(self, packagename, pkgtype):
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
        
        #package_ids=res.get_package_array() -> .get_id()
        #['feren-backgrounds-erbium;2021.04.0.0.0;all;installed:feren_os-stable-main']
        
        res=self.pk_client.resolve(PackageKitGlib.FilterEnum.NONE, [self.storebrain.get_item_info_specific(packagename, pkgtype, source, True)["apt-name"]], None, lambda p, t, d: True, None)
        package_ids=res.get_package_array()
        
        for item in package_ids:
            if item.get_data().startswith("installed:"):
                return 1
            #TODO: Update check, Available in disabled source check using package_id, etc.
            else:
                return 0
        
        
        return 403
        
    
    def progress_cb(self, progress, progresstype, user_data):
        self.progress_callback(progress.get_percentage())
    
    
    def task_cleanup(self, packagename):
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
        
    
    #Actual management TODO: Progress callback
    def task_install_package(self, taskdata, progress_callback):
        import traceback
        #Install package and return exit code
        self.packagemgmtbusy = True
        
        self.progress_callback = progress_callback
        
        #Remove package and return exit code
        self.currentpackagename = taskdata["pkginfo"]["apt-name"]
        try:
            res=self.pk_client.resolve(PackageKitGlib.FilterEnum.NONE, [self.currentpackagename], None, lambda p, t, d: True, None)
            package_ids=res.get_package_array()
            if not len(package_ids) > 0:
                return False
            
            outcome = self.pk_client.install_packages(0, [package_ids[0].get_id()], None, self.progress_cb, None)
        except:
            return False
        
        return outcome.get_exit_code() == PackageKitGlib.ExitEnum.SUCCESS
    
    def task_remove_package(self, taskdata, progress_callback):
        self.packagemgmtbusy = True
        
        self.progress_callback = progress_callback
        
        #Remove package and return exit code
        self.currentpackagename = taskdata["pkginfo"]["apt-name"]
        try:
            res=self.pk_client.resolve(PackageKitGlib.FilterEnum.NONE, [self.currentpackagename], None, lambda p, t, d: True, None)
            package_ids=res.get_package_array()
            if not len(package_ids) > 0:
                return False
            
            outcome = self.pk_client.remove_packages(0, [package_ids[0].get_id()], True, True, None, self.progress_cb, None)
        except:
            return False
        
        return outcome.get_exit_code() == PackageKitGlib.ExitEnum.SUCCESS
    
    def task_update_package(self, taskdata, progress_callback):
        self.packagemgmtbusy = True
        
        self.progress_callback = progress_callback
        
        #Update package and return exit code
        self.currentpackagename = taskdata["pkginfo"]["apt-name"]
        try:
            res=self.pk_client.resolve(PackageKitGlib.FilterEnum.NONE, [self.currentpackagename], None, lambda p, t, d: True, None)
            package_ids=res.get_package_array()
            if not len(package_ids) > 0:
                return False
            
            outcome = self.pk_client.update_packages(0, [package_ids[0].get_id()], True, True, None, self.progress_cb, None)
        except:
            return False
        
        return outcome.get_exit_code() == PackageKitGlib.ExitEnum.SUCCESS
    
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
            raise APTInfoModuleException(packagename, _("could not be found in the Store's package names data. If you are getting an exception throw, it means you have not used a Try to respond to the package not being in the Store."))
      
    def pkgNameToInternal(self, packagename, packagetype):
        #Translate package name to internal Store name
        #e.g.: org.mozilla.firefox + Flatpak = mozilla-firefox
        
        #packagename: Package name
        #packagetype: apt
        try:
            if self.json_storage["package-info/"+packagetype][pkg][packagetype + "-name"] == packagename:
                return pkg
            raise APTInfoModuleException(packagename, _("is not associated with any Store internal name. If you are getting an exception throw, it means you have not used a Try to respond to the package not being in the Store."))
        except:
            raise APTInfoModuleException(packagename, _("is not associated with any Store internal name. If you are getting an exception throw, it means you have not used a Try to respond to the package not being in the Store."))
        
        
    def build_ids_list(self): #Build list of package IDs
        self.pkg_ids = {}
        for i in [self.json_storage["package-info/apt"]]:
            try:
                for package in i:
                    if package not in self.pkg_ids:
                        self.pkg_ids[package] = self.json_storage["package-info/apt"][package]["category"]
            except:
                pass
        #self.pkg_ids.sort() TODO: Alphabetical sorting of IDs
    
    
    def getInfo(self, packagename, packagetype, sourcename=""):
        #Get information on a package using the JSON data        
        if packagetype not in self.types_supported:
            raise APTInfoModuleException(packagetype, _("is not supported by this information module. If you are getting an exception throw, it means you have not used a Try to respond to the module not supporting this type of package."))
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
            canusetouchscreen = self.json_storage["package-info/" + packagetype][packagename]["canihastouch"]
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

    def getAPTName(self, packagename, packagetype):
        try:
            aptname = self.json_storage["package-info/" + packagetype][packagename]["apt-name"]
        except:
            raise GenericInfoModuleException(packagename, _("has no, or an invalid, apt-name value in the package metadata. APT Packages MUST have an apt-name value when curated."))
            return
        return aptname
      
    def getAPTSource(self, packagename, packagetype):
        try:
            aptsource = self.json_storage["package-info/" + packagetype][packagename]["apt-source"]
        except:
            raise GenericInfoModuleException(packagename, _("has no, or an invalid, apt-source value in the package metadata. APT Packages MUST have an apt-source value when curated."))
            return
        return aptsource
        
    

if __name__ == "__main__":
    module = PackageMgmtModule()
