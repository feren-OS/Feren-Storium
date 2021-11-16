import configparser
import os
import subprocess
import gettext
import gi


#Dependencies
import json
import locale


def should_load(): #Should this module be loaded?
    return True


class SnapInfoModuleException(Exception): # Name this according to the module to allow easier debugging
    pass



class main():

    def __init__(self, storegui):

        gettext.install("feren-storium", "/usr/share/locale", names="ngettext")

        #Name to be used in Debugging output
        self.title = _("Snap Application Listing Information Module")
        #Name to be shown in the GUI
        self.humanreadabletitle = _("Snap Application Information")
        
        #Configs (obtained by get_configs)
        self.moduleconfigs={}
        
        #What package types does this provide info for?
        self.types_provided = ["snap"]
        
        #Information Storage to keep it in - modify list as appropriate for files
        self.json_storage = {}
        
        #Lock to keep stuff from happening while memory is refreshing
        self.memory_refreshing = False
        
        #Locale (for info modules)
        self.locale = locale.getlocale()[0]
        
        #Force a memory refresh
        self.refresh_memory()
        
        #Package IDs List
        self.pkg_ids = []
        #Package Categories - IDs List
        self.pkg_categoryids = {}
        
        
    def build_ids_list(self): #Build list of package IDs
        self.pkg_ids = []
        for i in [self.json_storage["package-info/snap"]]:
            try:
                for package in i:
                    if package not in self.pkg_ids:
                        self.pkg_ids.append(package)
            except:
                pass
        self.pkg_ids.sort() #Alphabetical sorting of IDs
        
    def build_categories_ids(self): #Build categories list for package IDs
        self.pkg_categoryids = {}
        #Do nothing else as this isn't a generic module
        
    def refresh_memory(self): # Function to refresh some memory values
        self.memory_refreshing = True
        
        self.json_storage = {}
        
        for i in ["package-info/snap"]:
            with open("/usr/share/feren-storium/curated/" + i + "/data.json", 'r') as fp:            
                self.json_storage[i] = json.loads(fp.read())
        
        self.memory_refreshing = False
        
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
      
    
    def getInfo(self, packagename, packagetype):
        #Get information on a package using the JSON data        
        if packagetype not in self.types_provided:
            raise SnapInfoModuleException(packagetype, _("is not supported by this information module. If you are getting an exception throw, it means you have not used a Try to respond to the module not supporting this type of package."))
            return
        
        #General stuff
        author = self.getAuthor(packagename, packagetype)
        bugreporturl = self.getBugsURL(packagename, packagetype)
        tosurl = self.getTOSURL(packagename, packagetype)
        privpolurl = self.getPrivPolURL(packagename, packagetype)
        
        #Application compatibility
        canusethemes = self.getCanTheme(packagename, packagetype)
        canusetouchscreen = self.getCanTouchScreen(packagename, packagetype)
        canuseaccessibility = self.getCanUseAccessibility(packagename, packagetype)
        canusedpiscaling = self.getCanUseDPI(packagename, packagetype)
        canuseonphone = self.getCanUseOnPhone(packagename, packagetype)
        isofficial = self.getIsOfficial(packagename, packagetype)
        
        #Snap-only stuff
        snapname = self.getSnapName(packagename, packagetype)
        snapsource = self.getSnapSource(packagename, packagetype)
        
        
        #Return values
        return {"author": author, "bugreporturl": bugreporturl, "tosurl": tosurl, "privpolurl": privpolurl, "canusethemes": canusethemes, "canusetouchscreen": canusetouchscreen, "canuseaccessibility": canuseaccessibility, "canusedpiscaling": canusedpiscaling, "canuseonphone": canuseonphone, "isofficial": isofficial, "snapname": snapname, "snapsource": snapsource}
        
    
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
    module = PackageInfoModule()