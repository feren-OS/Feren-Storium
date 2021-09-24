import configparser
import os
import subprocess
import gettext
import gi


#Dependencies
import json
import locale


class IceInfoModuleException(Exception): # Name this according to the module to allow easier debugging
    pass



class PackageInfoModule():

    def __init__(self, storegui):

        gettext.install("feren-storium", "/usr/share/locale", names="ngettext")

        #Name to be used in Debugging output
        self.title = _("Ice Website Information Module")
        #Name to be shown in the GUI
        self.humanreadabletitle = _("Ice Website Information")
        
        #Configs (obtained by get_configs)
        self.moduleconfigs={}
        self.get_configs()
        
        #What package types does this provide info for?
        self.types_provided = ["ice"]
        
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
        
        for i in ["package-info/ice"]:
            self.json_storage[i] = json.load("/usr/share/feren-storium/curated/" + i + "/data.json")
        
        self.memory_refreshing = False
      
    
    def getInfo(self, packagename, packagetype):
        #Get information on a package using the JSON data
        
        if packagetype not in self.types_provided:
            raise IceInfoModuleException(packagetype, _("is not supported by this information module. If you are getting an exception throw, it means you have not used a Try to respond to the module not supporting this type of package."))
            return
        
        #General in-Store stuff
        author = self.getAuthor(packagename)
        bugsurl = self.getBugsURL(packagename)
        tosurl = self.getTOSURL(packagename)
        privpolurl = self.getPrivPolURL(packagename)
        
        #Ice-specific stuff
        keywords = self.getKeywords(packagename)
        
        
        #Return values
        return {"author": author, "bugsurl": bugsurl, "tosurl": tosurl, "privpolurl": privpolurl, "keywords": keywords}
        

    def getKeywords(self, packagename):
        try:
            keywords = self.json_storage["package-info/ice"][packagename]["keywords"]
        except:
            raise IceInfoModuleException(packagename, _("has no keywords value in the package metadata. Websites MUST have keywords values when curated."))
            return
        return keywords
    
    def getAuthor(self, packagename):
        try:
            author = self.json_storage["package-info/ice"][packagename]["author"]
        except:
            author = _("Unknown Author")
        return author
      
    def getBugsURL(self, packagename):
        try:
            bugsurl = self.json_storage["package-info/ice"][packagename]["bugreporturl"]
        except:
            bugsurl = ""
        return bugsurl
      
    def getTOSURL(self, packagename):
        try:
            tosurl = self.json_storage["package-info/ice"][packagename]["tos"]
        except:
            tosurl = ""
        return tosurl
      
    def getPrivPolURL(self, packagename):
        try:
            privpolurl = self.json_storage["package-info/ice"][packagename]["privpol"]
        except:
            privpolurl = ""
        return privpolurl


if __name__ == "__main__":
    module = PackageInfoModule()