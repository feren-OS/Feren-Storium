import configparser
import os
import subprocess
import gettext
import gi


#Dependencies
import locale


def should_load(): #Should this module be loaded?
    return True


class GenericSearchModuleException(Exception): # Name this according to the module to allow easier debugging
    pass



class main():

    def __init__(self, storebrain):

        gettext.install("feren-storium", "/usr/share/locale", names="ngettext")
        
        self.storebrain = storebrain

        #Name to be used in Debugging output
        self.title = _("Generic Search Module")
        #Name to be shown in the GUI
        self.humanreadabletitle = _("Generic Search")
        
        #Configs (obtained by get_configs)
        self.moduleconfigs={}
        
        #Lock to keep stuff from happening while memory is refreshing
        self.memory_refreshing = False
        
        #Locale (for info modules)
        self.locale = locale.getlocale()[0]
        
        #Storage for past searches, so we can remember them to make redoes faster
        self.search_results = {}
        #TODO: Put 'current search' variable in GUI
        
        #Force a memory refresh
        self.refresh_memory()
        
    def refresh_memory(self): # Function to refresh some memory values
        self.memory_refreshing = True
        
        try:
            if self.storebrain.current_search != "":
                if self.search_results[self.storebrain.current_search]['status'] != 0:
                    self.search_results = {self.search_results[self.storebrain.current_search]}
                else:
                    self.search_results = {}
            else:
                self.search_results = {}
        except:
            print(self.title + ":", _("Could not obtain storebrain.current_search - make sure current_search is a variable in the Storium Brain."))
            self.search_results = {}
        
        self.memory_refreshing = False
        
    def checkIfInResults(self, item, searchterm): #Check if our result isn't already in the results to prevent duplicates
        if item not in self.search_results[searchterm]['exactmatch'] and item not in self.search_results[searchterm]['begins'] and item not in self.search_results[searchterm]['contains'] and item not in self.search_results[searchterm]['ends']:
            return False
        else:
            return True
        
    def getData(self, item): #Get package data for our search results
        value = self.storebrain.get_generic_item_info(item)
        value = self.storebrain.dict_recurupdate(value, self.storebrain.get_item_info(item, value["packagetype"], False))
            
        return value
    
    def getResults(self, searchterm):
        #If it has already been searched before
        if searchterm in self.search_results:
            while self.search_results[searchterm]['status'] == 1: #If searching already, wait for the current search to complete
                pass
            
            if self.search_results[searchterm]['status'] == 0: #If there's already a completed search, just reuse its results
                return self.search_results[searchterm]
        
        self.search_results[searchterm] = {'status': 1, 'exactmatch': {}, 'begins': {}, 'contains': {}, 'ends': {}}
        package_ids = self.storebrain.pkginfo_modules[self.storebrain.generic_module].pkg_ids
        
        #Get JSON data of each result
        #FIXME: Is there not a more efficient way to do this?
        
        #First check: Is the search term literally the name of the package or the real name?
        for item in package_ids:
            if searchterm not in self.search_results: #Abort search to save resources if it's cancelled
                return {'exactmatch': {}, 'begins': {}, 'contains': {}, 'ends': {}}
            
            if searchterm.lower() == self.storebrain.pkginfo_modules[self.storebrain.generic_module].getRealName(item, "").lower():
                if self.checkIfInResults(item, searchterm) == False:
                    self.search_results[searchterm]['exactmatch'][item] = self.getData(item)
        if searchterm.lower() in package_ids:
            if searchterm not in self.search_results:
                return {'exactmatch': {}, 'begins': {}, 'contains': {}, 'ends': {}}
            
            if self.checkIfInResults(searchterm, searchterm) == False:
                self.search_results[searchterm]['exactmatch'][searchterm] = self.getData(searchterm)
        
        #Second check: Do any names start with the search term?
        for item in package_ids:
            if searchterm not in self.search_results:
                return {'exactmatch': {}, 'begins': {}, 'contains': {}, 'ends': {}}
            
            if item.startswith(searchterm.lower()) or self.storebrain.pkginfo_modules[self.storebrain.generic_module].getRealName(item, "").lower().startswith(searchterm.lower()):
                if self.checkIfInResults(item, searchterm) == False:
                    self.search_results[searchterm]['begins'][item] = self.getData(item)
        
        #Third check: Do any names contain the search term?
        for item in package_ids:
            if searchterm not in self.search_results:
                return {'exactmatch': {}, 'begins': {}, 'contains': {}, 'ends': {}}
            
            if searchterm.lower() in item or searchterm.lower() in self.storebrain.pkginfo_modules[self.storebrain.generic_module].getRealName(item, "").lower():
                if self.checkIfInResults(item, searchterm) == False:
                    self.search_results[searchterm]['contains'][item] = self.getData(item)
        
        #Fourth check: Do any names end with the search term?
        for item in package_ids:
            if searchterm not in self.search_results:
                return {'exactmatch': {}, 'begins': {}, 'contains': {}, 'ends': {}}
            
            if item.endswith(searchterm.lower()) or self.storebrain.pkginfo_modules[self.storebrain.generic_module].getRealName(item, "").lower().endswith(searchterm.lower()):
                if self.checkIfInResults(item, searchterm) == False:
                    self.search_results[searchterm]['ends'][item] = self.getData(item)
        
        self.search_results[searchterm]['status'] = 0 #Mark as completed search
        return self.search_results[searchterm]
        
        
