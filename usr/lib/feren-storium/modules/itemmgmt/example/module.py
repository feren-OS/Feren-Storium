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
        
        #Item Storage will store the data of opened packages this instance, to make future loads faster
        self.items = {}
        self.redirects = {}
        self.sources = {}

        #Refresh memory for the first time
        self.refreshMemory()

        #Test value for demonstrating item source adding
        self.obtainablesourceinstalled = False

        
    def refreshMemory(self): # Function to refresh some memory values
        #self.memory_refreshing = True

        self.items = {}
        with open("/usr/share/feren-storium/itemmgmtexample/items.json", 'r') as fp:
            self.items = json.loads(fp.read())
        with open("/usr/share/feren-storium/itemmgmtexample/redirects.json", 'r') as fp:
            self.redirects = json.loads(fp.read())
        with open("/usr/share/feren-storium/itemmgmtexample/sources.json", 'r') as fp:
            self.sources = json.loads(fp.read())
        
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
        for i in self.items:
            if "all" in self.items[i]:
                if "category" in self.items[i]["all"]:
                    if self.items[i]["all"]["category"] == category:
                        #category is always determined by the module's default source, so just store it in 'all' to prevent inconsistencies
                        result.append(i)

        return result


    def getItemInformation(self, itemid, sourceid):
        result = {}
        if sourceid not in self.items[itemid] and "all" not in self.items[itemid]:
            raise ExampleModuleException(_("%s does not exist in source %s") % (itemid, sourceid))
        #Append generic item information first
        if "all" in self.items[itemid]:
            result = self.api.dictMerge(result, self.items[itemid]["all"])
        #Then overwrite with any source-specific item information
        if sourceid in self.items[itemid]:
            result = self.api.dictMerge(result, self.items[itemid][sourceid])
        return result


    def getAvailableSources(self, itemid):
        result = {}
        for i in self.items[itemid]["sources"]:
            #Add empty values for normal sources so Brain can fill them in, saving
            # time and referencing source-managing Tasks if they currently exist.
            result[i] = {}
            if itemid in self.redirects:
                #As for redirection sources, pre-fill these in to prevent an exception as they aren't *real* sources
                if i in self.redirects[itemid]:
                    sourceinfo = self.redirects[itemid][i]
                    result[i] = {"redirectitemid": sourceinfo["redirectitemid"], \
                        "redirectmoduleid": sourceinfo["redirectmoduleid"], \
                        "redirectsourceid": sourceinfo["redirectsourceid"], \
                        "redirectmessage": sourceinfo["redirectmessage"], \
                        "priority": 0}
        return result

        #Current redirection sources plan:
        #   - minimum item information required for item blocks is given by getItemInformation, and NOT the redirection itself's info
        #   - upon choosing the source the Store redirects to the new item INSTEAD of loading item information/status - this, in turn, results in the item info/status of the post-redirect being loaded automatically
        #   - redirection items shall not appear in Store outside of Library, nor have subsources
        #       TODO: Make modules delist items without a category from search
        #   - when getting the sources, if a redirect source is found check its redirect exists (if not, remove said source)
        #   - if a redirect source is valid, change its name to "*NAME HERE* (*SOURCE HERE*)"

        #   - To appear in Library, the module must report an item is installed from the redirection source's ID in said module (this ID can be entirely custom)
        #   - TODO: Should the module just list all installed IDs and then we query for attributes afterwards like up-to-date or redirection source, or should that befall the module's own duty?


    def getSourceExists(self, sourceid):
        if sourceid == "main":
            return True #'main' is the header source
        return sourceid in self.sources


    def getRequiredCrossSources(self, itemid, sourceid):
        #TODO: Should there be an example of this added?
        return []


    def getSourceInformation(self, sourceid):
        #no more itemid
        #moved redirects to getAvailableSources
        #elevated, defereasymode, and priority are now filled in by Brain, as well as the new sourceElevated value
        if sourceid in self.sources:
            return self.sources[sourceid]
        else:
            raise ExampleModuleException(_("The sourceid %s does not exist") % sourceid)


    ############################################
    # Item Management
    ############################################

    def getItemStatus(self, itemid, sourceid):
        #This is just so the functionality can be shown off - in an actual module, you should query your chosen backend for installation status and respond appropriately.
        # NOTE: Only 0, 1, and 2 are accepted status values for a module to return.

        #Normal items
        if itemid not in self.items:
            if itemid in self.redirects:
                if sourceid in self.redirects[itemid]["sources"]:
                    return 1, "" #Return installed for our redirection test(s)
                else:
                    raise ExampleModuleException(_("%s is not a valid redirection source for %s") % (sourceid, itemid))
            else:
                raise ExampleModuleException(_("The itemid %s does not exist") % itemid)
        else:
            installed = self.items[itemid][sourceid]["testinstalledstatus"]
            subsource = self.items[itemid][sourceid]["testinstalledsubsource"]
            if installed == "no":
                return 0, ""
            elif installed == "updateavailable":
                return 2, subsource
            elif installed == "yes":
                return 1, subsource
        #TODO: Make examplenosource also fail the source installed check, and add a check for this separately


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


    ############################################
    # Source Information
    ############################################

    def getSourceStatus(self, sourceid):
        #This is just so the functionality can be shown off - in an actual module, you should query your chosen backend for installation status and respond appropriately.
        # NOTE: Only 0, 1, and 2 are accepted status values for a module to return.
        if sourceid == "itemsource": #Main item source is mandatory
            return 2
        if sourceid == "exampleobtainable":
            if self.obtainablesourceinstalled == False:
                return 0 #Unlike all other sources, this one should be uninstalled initially
        return 1
