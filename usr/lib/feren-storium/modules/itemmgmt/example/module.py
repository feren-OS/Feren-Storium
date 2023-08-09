#Dependencies
import time
import gettext
import json


class ExampleModuleException(Exception): # Name this according to the module to allow easier debugging
    pass


class module():

    def __init__(self, genericapi, itemapi, systemmode):
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
            if self.itemcache[i]["all"]["category"] == category: #category is always determined by the module's default source, so just store it in 'all' to prevent inconsistencies
                result.append(i)

        return result

    def getItemInformation(self, itemid, sourceid):
        result = {}
        if sourceid not in self.itemcache[itemid] and "all" not in self.itemcache[itemid]:
            raise ExampleModuleException(_("%s does not exist in source %s") % (itemid, sourceid))
        if "all" in self.itemcache[itemid]:
            result = self.api.dictMerge(result, self.itemcache[itemid]["all"])
        if sourceid in self.itemcache[itemid]: #Merge information from specific source over all
            result = self.api.dictMerge(result, self.itemcache[itemid][sourceid])
        return result
