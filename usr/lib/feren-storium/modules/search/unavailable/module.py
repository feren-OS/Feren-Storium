import configparser
import os
import subprocess
import gettext
import gi


#Dependencies
import locale
import json


def should_load(): #Should this module be loaded?
    return True


class GenericSearchModuleException(Exception): # Name this according to the module to allow easier debugging
    pass



class main():

    def __init__(self, storebrain):

        gettext.install("feren-storium", "/usr/share/locale", names="ngettext")
        
        self.storebrain = storebrain

        #Name to be used in Debugging output
        self.title = _("Unavailability Search Module")
        #Name to be shown in the GUI
        self.humanreadabletitle = _("Unavailability Search")
        
        #Configs (obtained by get_configs)
        self.moduleconfigs = {}
        
        #Information Storage to keep it in - modify list as appropriate for files
        self.json_storage = {}
        
        #Lock to keep stuff from happening while memory is refreshing
        self.memory_refreshing = False
        
        #Locale (for info modules)
        self.locale = locale.getlocale()[0]
        
        #Storage for past searches, so we can remember them to make redoes faster
        self.search_results = {}
        
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
            
        self.json_storage = {'packages': {}, 'labels': {}}
        
        with open("/usr/share/feren-storium/curated/package-search-info/data.json", 'r') as fp:
            jsondata = json.loads(fp.read())
            for pkgname in jsondata["unavailable"]:
                self.json_storage["packages"][pkgname] = jsondata["unavailable"][pkgname]
            for labelid in jsondata["unavailable-labels"]:
                self.json_storage["labels"][labelid] = jsondata["unavailable-labels"][labelid]
        
        self.memory_refreshing = False
        
    def checkIfInResults(self, item, searchterm): #Check if our result isn't already in the results to prevent duplicates
        if item not in self.search_results[searchterm]['exactmatch'] and item not in self.search_results[searchterm]['begins'] and item not in self.search_results[searchterm]['contains'] and item not in self.search_results[searchterm]['ends']:
            return False
        else:
            return True
    
    def getResults(self, searchterm):
        #If it has already been searched before
        if searchterm in self.search_results:
            while self.search_results[searchterm]['status'] == 1: #If searching already, wait for the current search to complete
                pass
            
            if self.search_results[searchterm]['status'] == 0: #If there's already a completed search, just reuse its results
                return self.search_results[searchterm]
        
        self.search_results[searchterm] = {'status': 1, 'exactmatch': {}, 'begins': {}, 'contains': {}, 'ends': {}}
        package_ids = list(self.json_storage["packages"].keys())
        
        #Get JSON data of each result
        
        #Is the search term literally the name of the package or the real name?
        for item in package_ids:
            if searchterm not in self.search_results:
                return {'exactmatch': {}, 'begins': {}, 'contains': {}, 'ends': {}}
            
            if searchterm.lower() == item.lower():
                if self.checkIfInResults(item, searchterm) == False:
                    self.search_results[searchterm]['exactmatch'][item] = {'searchlabel': self.json_storage["labels"][self.json_storage["packages"][item]]}
        
        self.search_results[searchterm]['status'] = 0 #Mark as completed search
        return self.search_results[searchterm]
        
        
