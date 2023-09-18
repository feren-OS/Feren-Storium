#Dependencies
import time
import gettext
import json
from functools import partial

class ExampleModuleException(Exception): # Name this according to the module to allow easier debugging
    pass


class module():

    def __init__(self, genericapi, itemapi, systemmode):
        #Gettext Translator
        gettext.install("feren-storium-exampleitemmgmt", "/usr/share/locale", names="ngettext")
        
        #Storium APIs
        self.api = genericapi
        self.itemapi = itemapi
        
        #Package Storage will store the data of opened packages this instance, to make future loads faster
        self.itemcache = {}
        self.sourcescache = {}

        #Refresh memory for the first time
        self.refreshMemory()

        
    def refreshMemory(self): # Function to refresh some memory values
        #self.memory_refreshing = True

        self.itemcache = {}
        with open(self.api.usrdir + "/curated/itemmgmtexample/items.json", 'r') as fp:
            self.itemcache = json.loads(fp.read())
        with open(self.api.usrdir + "/curated/itemmgmtexample/sourceitems.json", 'r') as fp:
            self.sourcescache = json.loads(fp.read())
        
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
        sourceid = sourceid[len(self.moduleid + "-appsource-"):]
        if sourceid not in self.itemcache[itemid] and "all" not in self.itemcache[itemid]:
            raise ExampleModuleException(_("%s does not exist in source %s") % (itemid, sourceid))
        if "all" in self.itemcache[itemid]:
            result = self.api.dictMerge(result, self.itemcache[itemid]["all"])
        if sourceid in self.itemcache[itemid]: #Merge information from specific source over all
            result = self.api.dictMerge(result, self.itemcache[itemid][sourceid])
        return result


    def getAvailableSources(self, itemid):
        result = {}
        for i in self.itemcache[itemid]["sources"]:
            result[self.moduleid + "-appsource-" + i] = self.getSourceInformation(itemid, i)
        return result


    def getSourceInformation(self, itemid, sourceid):
        # TODO: Migrate to using sources information JSON
        if sourceid.startswith(self.moduleid + "-appsource-"):
            sourceid = sourceid[len(self.moduleid + "-appsource-"):]
        if sourceid == "exampleredir": #Pretend this is a check for an item having moved or being replaced by another item on this source
            return {"fullname": self.sourcescache[sourceid]["fullname"], \
                "subsources": {}, \
                "redirectitemid": "mozilla-firefox", \
                "redirectmoduleid": "flatpak", \
                "redirectsourceid": "flathub", \
                "redirectmessage": "This is a test redirect", \
                "priority": 10}
            #NOTE: Priority = Priority - 900 after being sent to Storium
        else:
            elevated = True if sourceid == "example2" else False
            return {"fullname": self.sourcescache[sourceid]["fullname"], \
                "subsources": {"sub1": {"fullname": {"C": "subsource 1"}}, "sub2": {"fullname": {"C": "subsource 2"}}}, \
                "defereasymode": True, "elevated": elevated}
            #NOTE: Priority falls back to 50


    ############################################
    # Item Management
    ############################################

    def getItemStatus(self, itemid, sourceid):
        #This is just so the functionality can be shown off - in an actual module, you should query your chosen backend for installation status and respond appropriately.
        # NOTE: Only 0, 1, and 2 are accepted status values for a module to return.
        if itemid == "exampleinstall":
            return 0, ""
        elif itemid == "examplenosource":
            return 0, "" #TODO: Make this example fail the source installed check, and add a check for this separately
        elif itemid == "exampleupdate":
            return 2, "sub2"
        elif itemid == "exampleinstalled":
            return 1, "sub1"
        else:
            return 0, ""


    def getExtraItemButtons(self, itemid, sourceid, status):
        result = []
        result.append({"text": "Test button", \
                       "tooltip": "A test button!", \
                       "icon": "softwarecenter", \
                       "callback": self.callbackTest})
        if status == 1:
            result.append({"text": "Another", \
                       "tooltip": "Another test button!", \
                       "icon": "dialog-apply", \
                       "callback": partial(self.callbackTest, True)})
        return result
    def callbackTest(self, alt=False):
        if alt == False:
            print("IT WORKS")
        else:
            print("I'll tell you what yo")

    def invalidateItemStatusCache(self, itemids):
        #If we stored the status of items visited in this Store session in memory,
        # this call would be used to erase the remembered statuses, from memory,
        # of items in the list itemids.
        #However, since this example module does not store any caches in memory,
        # besides hardcoded information to allow test-cases to occur, this does
        # nothing.

        #NOTE: If IDs in itemids don't exist in this module, don't throw an exception, just ignore them.
        return
