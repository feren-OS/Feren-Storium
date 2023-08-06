#Dependencies
import time
import gettext
import json


class ExampleModuleException(Exception): # Name this according to the module to allow easier debugging
    pass


class module():

    def __init__(self, genericapi, itemapi):
        #Gettext Translator
        gettext.install("feren-storium-exampleitemmgmt", "/usr/share/locale", names="ngettext")
        
        #Storium APIs
        self.api = genericapi
        self.itemapi = itemapi

        self.test = "example"
        
        #Package Storage will store the data of opened packages this instance, to make future loads faster
        self.itemcache = {}

        #Refresh memory for the first time
        self.refreshMemory()

        
    def refreshMemory(self): # Function to refresh some memory values
        #self.memory_refreshing = True

        self.itemcache = {}
        with open("/usr/share/feren-storium/curated/itemmgmtexample/items.json", 'r') as fp:
            self.itemcache = json.loads(fp.read())
        
        #self.memory_refreshing = False


    ############################################
    # Item Information
    ############################################
        
    def getCustomCategories(self):
        return {"applications-example": ["applications-profiling", _("Example (Applications)")], \
            "websites-example": ["applications-profiling", _("Example (Websites)")], \
            "example": ["applications-profiling", _("Example Category")]}
    
    def getItemsFromCategory(self, category):
        result = []
        for i in self.itemcache:
            if self.itemcache[i]["category"] == category:
                result.append(i)

        return result
