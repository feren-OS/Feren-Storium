import configparser
import os
import subprocess
import gettext
import gi


#Dependencies
import json
import locale


class ApplicationInfoModuleException(Exception): # Name this according to the module to allow easier debugging
    pass



class PackageInfoModule():

    def __init__(self, storegui):

        gettext.install("feren-storium", "/usr/share/locale", names="ngettext")

        #Name to be used in Debugging output
        self.title = _("Application Listing Information Module")
        #Name to be shown in the GUI
        self.humanreadabletitle = _("Application Information")
        
        #Configs (obtained by get_configs)
        self.moduleconfigs={}
        
        #What package types does this provide info for?
        self.types_provided = ["apt", "snap", "flatpak"]
        
        #Information Storage to keep it in - modify list as appropriate for files
        self.json_storage = {}
        
        #Lock to keep stuff from happening while memory is refreshing
        self.memory_refreshing = False
        
        #Locale (for info modules)
        self.locale = locale.getlocale()[0]
        
        #Force a memory refresh
        self.refresh_memory()
        
    def refresh_memory(self): # Function to refresh some memory values
        self.memory_refreshing = True
        
        self.json_storage = {}
        
        for i in ["package-sources", "package-sources-info", "package-intnames", "package-info/apt", "package-info/flatpak", "package-info/generic", "package-info/snap"]:
            self.json_storage[i] = json.load("/usr/share/feren-storium/curated/" + i + "/data.json")
        
        self.memory_refreshing = False
      
    
    def internalToPkgName(self, internalname, packagetype):
        #Translate internal Store name to the appropriate package name
        #e.g.: mozilla-firefox + Flatpak = org.mozilla.firefox
        
        #internalname: Internal in-Store name
        #packagetype: apt, flatpak, snap...
        try:
            return self.json_storage["package-intnames"][internalname][packagetype]
        except:
            raise ApplicationInfoModuleException(packagename, _("could not be found in the Store's package names data. If you are getting an exception throw, it means you have not used a Try to respond to the package not being in the Store."))
      
    def pkgNameToInternal(self, packagename, packagetype):
        #Translate package name to internal Store name
        #e.g.: org.mozilla.firefox + Flatpak = mozilla-firefox
        
        #packagename: Package name
        #packagetype: apt, flatpak, snap...
        try:
            for pkg in self.json_storage["package-intnames"]:
                if self.json_storage["package-intnames"][pkg][packagetype] == packagename:
                    return pkg
            raise ApplicationInfoModuleException(packagename, _("is not associated with any Store internal name. If you are getting an exception throw, it means you have not used a Try to respond to the package not being in the Store."))
        except:
            raise ApplicationInfoModuleException(packagename, _("is not associated with any Store internal name. If you are getting an exception throw, it means you have not used a Try to respond to the package not being in the Store."))
      
    
    def getInfo(self, packagename, packagetype):
        #Get information on a package using the JSON data
        translatedpackagename = self.getNameFromInternal(packagename, packagetype)
        
        if packagetype not in self.types_provided:
            raise ApplicationInfoModuleException(packagetype, _("is not supported by this information module. If you are getting an exception throw, it means you have not used a Try to respond to the module not supporting this type of package."))
            return
        
        #General stuff
        author = self.getAuthor(packagename, packagetype, translatedpackagename)
        pkgsource = self.getPkgSource(packagename, packagetype, translatedpackagename)
        bugsurl = self.getBugsURL(packagename, packagetype, translatedpackagename)
        tosurl = self.getTOSURL(packagename, packagetype, translatedpackagename)
        privpolurl = self.getPrivPolURL(packagename, packagetype, translatedpackagename)
        
        #Application compatibility
        canusethemes = self.getCanTheme(packagename, packagetype, translatedpackagename)
        canusetouchscreen = self.getCanTouchScreen(packagename, packagetype, translatedpackagename)
        canuseaccessibility = self.getCanUseAccessibility(packagename, packagetype, translatedpackagename)
        canusedpiscaling = self.getCanUseDPI(packagename, packagetype, translatedpackagename)
        canuseonphone = self.getCanUseOnPhone(packagename, packagetype, translatedpackagename)
        isofficial = self.getIsOfficial(packagename, packagetype, translatedpackagename)
        
        
        #Return values
        return {"author": author, "pkgsource": pkgsource, "bugsurl": bugsurl, "tosurl": tosurl, "privpolurl": privpolurl, "canusethemes": canusethemes, "canusetouchscreen": canusetouchscreen, "canuseaccessibility": canuseaccessibility, "canusedpiscaling": canusedpiscaling, "canuseonphone": canuseonphone, "isofficial": isofficial}
        

    def getAuthor(self, packagename, packagetype, translatedpackagename=self.getNameFromInternal(packagename, packagetype), typejson=self.json_storage["package-info/" + packagetype]):
        try:
            author = typejson[translatedpackagename]["author"]
        except:
            author = _("Unknown Author")
        return author
      
    def getPkgSource(self, packagename, packagetype, translatedpackagename=self.getNameFromInternal(packagename, packagetype), typejson=self.json_storage["package-info/" + packagetype]):
        try:
            pkgsource = typejson[translatedpackagename]["pkgsource"]
        except:
            raise ApplicationInfoModuleException(packagename, _("has no pkgsource value in the package metadata. Packages MUST have source values when curated."))
            return
        return pkgsource
      
    def getBugsURL(self, packagename, packagetype, translatedpackagename=self.getNameFromInternal(packagename, packagetype), typejson=self.json_storage["package-info/" + packagetype]):
        try:
            bugsurl = typejson[translatedpackagename]["bugreporturl"]
        except:
            bugsurl = ""
        return bugsurl
      
    def getTOSURL(self, packagename, packagetype, translatedpackagename=self.getNameFromInternal(packagename, packagetype), typejson=self.json_storage["package-info/" + packagetype]):
        try:
            tosurl = typejson[translatedpackagename]["tos"]
        except:
            tosurl = ""
        return tosurl
      
    def getPrivPolURL(self, packagename, packagetype, translatedpackagename=self.getNameFromInternal(packagename, packagetype), typejson=self.json_storage["package-info/" + packagetype]):
        try:
            privpolurl = typejson[translatedpackagename]["privpol"]
        except:
            privpolurl = ""
        return privpolurl
      
    def getCanTheme(self, packagename, packagetype, translatedpackagename=self.getNameFromInternal(packagename, packagetype), typejson=self.json_storage["package-info/" + packagetype]):
        # Return values:
        # 0: No
        # 1: Yes
        # 2: Yes, but manually enabled
        # 3: Yes, except for Feren OS's style
        # 4: Has own themes system
        # 5: No because LibAdwaita
        # 6: No because LibGranite
        
        try:
            canusethemes = typejson[translatedpackagename]["canihasthemes"]
        except:
            canusethemes = 1 # Use fallback of Yes when unknown to hide the message
        return canusethemes
      
    def getCanTouchScreen(self, packagename, packagetype, translatedpackagename=self.getNameFromInternal(packagename, packagetype), typejson=self.json_storage["package-info/" + packagetype]):
        # Return values:
        # 0: No
        # 1: Yes
        # 2: Partially
        
        try:
            canusetouchscreen = typejson[translatedpackagename]["canihastouch"]
        except:
            canusetouchscreen = 1 # Use fallback of Yes when unknown to hide the message
        return canusetouchscreen
      
    def getCanUseAccessibility(self, packagename, packagetype, translatedpackagename=self.getNameFromInternal(packagename, packagetype), typejson=self.json_storage["package-info/" + packagetype]):
        try:
            canuseaccessibility = typejson[translatedpackagename]["canihasaccessibility"]
        except:
            canuseaccessibility = True # Use fallback of True when unknown to hide the message
        return canuseaccessibility
      
    def getCanUseDPI(self, packagename, packagetype, translatedpackagename=self.getNameFromInternal(packagename, packagetype), typejson=self.json_storage["package-info/" + packagetype]):
        try:
            canusedpiscaling = typejson[translatedpackagename]["canihasdpiscaling"]
        except:
            canusedpiscaling = True # Use fallback of True when unknown to hide the message
        return canusedpiscaling
      
    def getCanUseOnPhone(self, packagename, packagetype, translatedpackagename=self.getNameFromInternal(packagename, packagetype), typejson=self.json_storage["package-info/" + packagetype]):
        try:
            canuseonphone = typejson[translatedpackagename]["canihasphoneadapting"]
        except:
            canuseonphone = True # Use fallback of True when unknown to hide the message
        return canuseonphone
      
    def getIsOfficial(self, packagename, packagetype, translatedpackagename=self.getNameFromInternal(packagename, packagetype), typejson=self.json_storage["package-info/" + packagetype]):
        try:
            isofficial = typejson[translatedpackagename]["officialpackage"]
        except:
            isofficial = True # Use fallback of True when unknown to hide the message
        return isofficial


if __name__ == "__main__":
    module = PackageInfoModule()