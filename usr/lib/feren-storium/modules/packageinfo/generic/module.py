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


class GenericInfoModuleException(Exception): # Name this according to the module to allow easier debugging
    pass



class main():

    def __init__(self, storebrain):

        gettext.install("feren-storium", "/usr/share/locale", names="ngettext")

        #Name to be used in Debugging output
        self.title = _("Generic Listing Information Module")
        #Name to be shown in the GUI
        self.humanreadabletitle = _("Generic Information")
        
        #Configs (obtained by get_configs)
        self.moduleconfigs={}
        
        #What package types does this provide info for?
        self.types_provided = ["all"]
        
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
        for i in [self.json_storage["package-info/generic"]]:
            try:
                for package in i:
                    if package not in self.pkg_ids:
                        self.pkg_ids.append(package)
            except:
                pass
        self.pkg_ids.sort() #Alphabetical sorting of IDs
        
    def build_categories_ids(self): #Build categories list for package IDs
        self.pkg_categoryids = {}
        for i in [self.json_storage["package-info/generic"]]:
            try:
                for package in i:
                    category = i[package]["category"]
                    if category not in self.pkg_categoryids:
                        self.pkg_categoryids[category] = []
                    if package not in self.pkg_categoryids[category]:
                        self.pkg_categoryids[category].append(package)
            except:
                pass
        for i in self.pkg_categoryids:
            self.pkg_categoryids[i].sort() #Alphabetical sorting of IDs
        
    def refresh_memory(self): # Function to refresh some memory values
        self.memory_refreshing = True
        
        self.json_storage = {}
        
        for i in ["package-info/generic"]:
            with open("/usr/share/feren-storium/curated/" + i + "/data.json", 'r') as fp:            
                self.json_storage[i] = json.loads(fp.read())
        
        self.memory_refreshing = False
        
        
    def getPackageJSON(self):
        #Return a json of all package names
        packagejson = {}
        for i in [self.json_storage["package-info/generic"]]:
            try:
                packagejson.update(i)
            except:
                pass
        return packagejson
      
    
    def getInfo(self, packagename, packagetype):
        #Get information on a package using the JSON data
        
        #Not needed since 'all'
        #if packagetype not in self.types_provided:
            #raise GenericInfoModuleException(packagetype, _("is not supported by this information module. If you are getting an exception throw, it means you have not used a Try to respond to the module not supporting this type of package."))
            #return
        
        #General stuff
        realname = self.getRealName(packagename, packagetype)
        iconuri = self.getIconURI(packagename, packagetype)
        shortdescription = self.getShortDescription(packagename, packagetype)
        description = self.getDescription(packagename, packagetype)
        category = self.getCategory(packagename, packagetype)
        images = self.getImages(packagename, packagetype)
        website = self.getWebsite(packagename, packagetype)
        donateurl = self.getDonateURL(packagename, packagetype)
        pkgtype = self.getPkgType(packagename, packagetype)
        
        
        #Return values
        return {"realname": realname, "iconuri": iconuri, "shortdescription": shortdescription, "description": description, "category": category, "images": images, "website": website, "donateurl": donateurl, "packagetype": pkgtype}
        
      
    def getRealName(self, packagename, packagetype):
        try:
            realname = self.json_storage["package-info/generic"][packagename]["realname"]
        except:
            realname = packagename
            #TODO: For stuff not curated, have 'packagename' just be the package's actual name
        return realname
      
    def getIconURI(self, packagename, packagetype):
        try:
            iconuri = self.json_storage["package-info/generic"][packagename]["iconuri"]
        except:
            iconuri = ""
        return iconuri
      
    def getShortDescription(self, packagename, packagetype):
        try:
            shortdescription = self.json_storage["package-info/generic"][packagename]["shortdescription"]
        except:
            shortdescription = _("Package")
            print(self.title + ":", _("Could not obtain a short description for"), packagename, _("(is it improperly curated, or is it a package file?), falling back to generic short description."))
        return shortdescription
      
    def getDescription(self, packagename, packagetype):
        try:
            description = self.json_storage["package-info/generic"][packagename]["description"]
        except:
            description = _("No description provided.")
            print(self.title + ":", _("Could not obtain a description for"), packagename, _("(is it improperly curated, or is it a package file?), falling back to generic description."))
        return description
      
    def getCategory(self, packagename, packagetype):
        try:
            category = self.json_storage["package-info/generic"][packagename]["category"]
        except:
            raise GenericInfoModuleException(packagename, _("has no category value in the package metadata. Packages MUST have source values when curated."))
            return
        return category
      
    def getImages(self, packagename, packagetype):
        try:
            images = self.json_storage["package-info/generic"][packagename]["images"]
        except:
            images = []
        return images
      
    def getWebsite(self, packagename, packagetype):
        try:
            website = self.json_storage["package-info/generic"][packagename]["website"]
        except:
            website = ""
        return website
      
    def getDonateURL(self, packagename, packagetype):
        try:
            donateurl = self.json_storage["package-info/generic"][packagename]["donation"]
        except:
            donateurl = ""
        return donateurl
      
    def getPkgType(self, packagename, packagetype):
        try:
            pkgtype = self.json_storage["package-info/generic"][packagename]["order-of-module-importance"][0]
        except:
            raise GenericInfoModuleException(packagename, _("has no, or an invalid, order-of-module-importance value in the package metadata. Packages MUST have an order-of-importance value when curated."))
            return
        return pkgtype


if __name__ == "__main__":
    module = PackageInfoModule()