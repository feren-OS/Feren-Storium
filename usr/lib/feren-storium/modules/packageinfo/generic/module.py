import configparser
import os
import subprocess
import gettext
import gi


#Dependencies
import json
import locale


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
        
    def refresh_memory(self): # Function to refresh some memory values
        self.memory_refreshing = True
        
        self.json_storage = {}
        
        for i in ["package-info/generic"]:
            with open("/usr/share/feren-storium/curated/" + i + "/data.json", 'r') as fp:            
                self.json_storage[i] = json.loads(fp.read())
        
        self.memory_refreshing = False
      
    
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
        
        
        #Return values
        return {"realname": realname, "iconuri": iconuri, "shortdescription": shortdescription, "description": description, "category": category, "images": images, "website": website, "donateurl": donateurl, "packagetype": packagetype}
        
      
    def getRealName(self, packagename, packagetype):
        try:
            realname = self.json_storage["package-info/generic"][packagename]["realname"]
        except:
            realname = packagename
            #TODO: For stuff not curated, have 'packagename' just be the package's actual name
        return realname
      
    def getIconURI(self, packagename, packagetype):
        try:
            iconuri = self.json_storage["package-info/generic"][packagename]["iconurl"]
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
        images = ["", "", ""]
        try:
            images[0] = self.json_storage["package-info/generic"][packagename]["image1"]
            images[1] = self.json_storage["package-info/generic"][packagename]["image2"]
            images[2] = self.json_storage["package-info/generic"][packagename]["image3"]
        except:
            return images
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


if __name__ == "__main__":
    module = PackageInfoModule()