import configparser
import os
import subprocess
import gettext
import gi


#Dependencies
import json
import locale


class GenericSourceInfoModuleException(Exception): # Name this according to the module to allow easier debugging
    pass



class main():

    def __init__(self, storebrain):

        gettext.install("feren-storium", "/usr/share/locale", names="ngettext")

        #Name to be used in Debugging output
        self.title = _("Generic Source Information Module")
        #Name to be shown in the GUI
        self.humanreadabletitle = _("Generic Source Information")
        
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
        
        for i in ["package-sources-info"]:
            with open("/usr/share/feren-storium/curated/" + i + "/data.json", 'r') as fp:            
                self.json_storage[i] = json.loads(fp.read())
        
        self.memory_refreshing = False
        
        
    def getSourceJSON(self):
        #Return a json of all package names
        sourcejson = {}
        for i in [self.json_storage["package-sources-info"]]:
            try:
                sourcejson.update(i)
            except:
                pass
        return sourcejson
      
    def getTypeInfo(self, sourcetype):
        #Get information on a source type (e.g.: 'apt', 'flatpak'...) using the JSON data
        
        #Not needed since 'all'
        #if packagetype not in self.types_provided:
            #raise GenericInfoModuleException(packagetype, _("is not supported by this source information module. If you are getting an exception throw, it means you have not used a Try to respond to the module not supporting this type of package."))
            #return
            
        guiname = self.getSettingsTypeName(sourcetype)
        guimanagable = self.getManagedByGUI(sourcetype)
        guitogglable = self.getCanBeToggled(sourcetype)
        guihideunavailable = self.getHideUnavailableSources(sourcetype)
        
        return {"name": guiname, "managed-via-gui": guimanagable, "can-be-toggled": guitogglable, "hide-unavailable-sources": guihideunavailable}
        
    
    def getInfo(self, sourcename, sourcetype, isSubsource = False):
        #Get information on a source using the JSON data
        
        #Not needed since 'all'
        #if sourcetype not in self.types_provided:
            #raise GenericInfoModuleException(sourcetype, _("is not supported by this source information module. If you are getting an exception throw, it means you have not used a Try to respond to the module not supporting this type of package."))
            #return
        
        #General stuff
        guiname = self.getSettingsName(sourcename, sourcetype)
        sourcename = self.getSourceSelectName(sourcename, sourcetype)
        repository = self.getRepository(sourcename, sourcetype)
        repofile = self.getRepositoryFile(sourcename, sourcetype)
        repopackage = self.getRepositoryPackage(sourcename, sourcetype)
        forced = self.getForced(sourcename, sourcetype)
        arch = self.getArchitecture(sourcename, sourcetype)
        if isSubsource:
            subsources = []
        else:
            subsources = self.getSubSources(sourcename, sourcetype)
        
        
        #Return values
        return {"name": guiname, "sourcename": sourcename, "repovalue": repository, "repofile": repofile, "repopackage": repopackage, "forced": forced, "arch": arch, "subsources": subsources}
        
      
    def getSettingsTypeName(self, sourcetype):
        try:
            name = self.json_storage["package-sources-info"][sourcetype]["name"]
        except:
            name = sourcetype
        return name
      
    def getManagedByGUI(self, sourcetype):
        try:
            managedbygui = self.json_storage["package-sources-info"][sourcetype]["managed-via-gui"]
        except:
            raise GenericSourceInfoModuleException(sourcetype, _("has incomplete or no source type data (missing 'managed-via-gui')."))
        return managedbygui
      
    def getCanBeToggled(self, sourcetype):
        try:
            canbetoggled = self.json_storage["package-sources-info"][sourcetype]["can-be-toggled"]
        except:
            raise GenericSourceInfoModuleException(sourcetype, _("has incomplete or no source type data (missing 'can-be-toggled')."))
        return canbetoggled
      
    def getHideUnavailableSources(self, sourcetype):
        try:
            hideunavailable = self.json_storage["package-sources-info"][sourcetype]["hide-unavailable-sources"]
        except:
            raise GenericSourceInfoModuleException(sourcetype, _("has incomplete or no source type data (missing 'hide-unavailable-sources')."))
        return hideunavailable
      
    def getSettingsName(self, sourcename, sourcetype):
        try:
            name = self.json_storage["package-sources-info"][sourcetype][sourcename]["category"]
        except:
            name = sourcename
        return category
      
    def getSourceSelectName(self, sourcename, sourcetype, subsourcename=""):
        try:
            if subsourcename == "":
                sourceselectname = self.json_storage["package-sources-info"][sourcetype][sourcename]["sourcename"]
            else:
                sourceselectname = self.json_storage["package-sources-info"][sourcetype][sourcename]["subsources"][subsourcename]["sourcename"]
        except:
            sourceselectname = _("{0} ({1})").format(sourcename, sourcetype)
        return sourceselectname
      
    def getRepository(self, sourcename, sourcetype):
        try:
            repository = self.json_storage["package-sources-info"][sourcetype][sourcename]["repository"]
        except:
            raise GenericSourceInfoModuleException(sourcename, _("has incomplete or no source type data (missing 'repository')."))
        return repository
      
    def getRepositoryFile(self, sourcename, sourcetype):
        try:
            repositoryfile = self.json_storage["package-sources-info"][sourcetype][sourcename]["repository-file"]
        except:
            raise GenericSourceInfoModuleException(sourcename, _("has incomplete or no source type data (missing 'repository-file')."))
        return repositoryfile
      
    def getRepositoryPackage(self, sourcename, sourcetype):
        try:
            repositorypackage = self.json_storage["package-sources-info"][sourcetype][sourcename]["repository-package"]
        except:
            raise GenericSourceInfoModuleException(sourcename, _("has incomplete or no source type data (missing 'repository-package')."))
        return repositorypackage
      
    def getForced(self, sourcename, sourcetype):
        try:
            forced = self.json_storage["package-sources-info"][sourcetype][sourcename]["forced"]
        except:
            raise GenericSourceInfoModuleException(sourcename, _("has incomplete or no source type data (missing 'forced')."))
        return forced
      
    def getArchitecture(self, sourcename, sourcetype):
        try:
            arch = self.json_storage["package-sources-info"][sourcetype][sourcename]["arch"]
        except:
            raise GenericSourceInfoModuleException(sourcename, _("has incomplete or no source type data (missing 'arch')."))
        return arch
      
    def getSubSources(self, sourcename, sourcetype):
        subsources = []
        try:
            for subsource in self.json_storage["package-sources-info"][sourcetype][sourcename]["subsources"]:
                subsources.append(subsource)
        except:
            raise GenericSourceInfoModuleException(sourcename, _("has incomplete or no source type data (missing or faulty 'subsources')."))
        return subsources


if __name__ == "__main__":
    module = PackageInfoModule()