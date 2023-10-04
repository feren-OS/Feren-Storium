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
        with open("/usr/share/feren-storium/itemmgmtexample/items.json", 'r') as fp:
            self.itemcache = json.loads(fp.read())
        with open("/usr/share/feren-storium/itemmgmtexample/sourceitems.json", 'r') as fp:
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
        #Check the item's in redirects only, and if so get placeholder item information
        if itemid not in self.itemcache:
            if itemid in self.redirectscache:
                if sourceid in self.redirectscache[itemid]["sources"]:
                    sourceinfo = self.redirectscache[itemid][sourceid]
                    return {"fullname": sourceinfo["fullname"], \
                        "summary": sourceinfo["summary"], \
                        "iconid": sourceinfo["iconid"], \
                        "iconurl": self.redirectscache[itemid]["iconurl"]}
                else:
                    raise ExampleModuleException(_("%s is not a valid redirection source for %s") % (sourceid, itemid))
            else:
                raise ExampleModuleException(_("The itemid %s does not exist") % itemid)
        #Else fall back to normal item information
        result = {}
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
            result[i] = self.getSourceInformation(itemid, i)
        return result


    def getSourceInformation(self, itemid, sourceid):
        #Current redirection sources plan:
        #   - minimum item information required for item blocks is given by getItemInformation, and NOT the redirection itself's info
        #   - upon choosing the source the Store redirects to the new item INSTEAD of loading item information/status - this, in turn, results in the item info/status of the post-redirect being loaded automatically
        #   - redirection items shall not appear in Store outside of Library, nor have subsources
        #       TODO: Make modules delist items without a category from search
        #   - when getting the sources, if a redirect source is found check its redirect exists (if not, remove said source)
        #   - if a redirect source is valid, change its name to "*NAME HERE* (*SOURCE HERE*)"

        #   - To appear in Library, the module must report an item is installed from the redirection source's ID in said module (this ID can be entirely custom)
        #   - TODO: Should the module just list all installed IDs and then we query for attributes afterwards like up-to-date or redirection source, or should that befall the module's own duty?
        # TODO: redirections.json for the IDs that redirect to other IDs in this module

        #Check the item's in redirects only, and if so if the source exists in said redirects information
        if itemid not in self.itemcache:
            if itemid in self.redirectscache:
                if sourceid in self.redirectscache[itemid]["sources"]:
                    sourceinfo = self.redirectscache[itemid][sourceid]
                    return {"redirectitemid": sourceinfo["redirectitemid"], \
                        "redirectmoduleid": sourceinfo["redirectmoduleid"], \
                        "redirectsourceid": sourceinfo["redirectsourceid"], \
                        "redirectmessage": self.redirectscache[itemid]["redirectmessage"], \
                        "priority": 0}
                    #NOTE: Priority = Priority - 900 after being sent to Storium
                else:
                    raise ExampleModuleException(_("%s is not a valid redirection source for %s") % (sourceid, itemid))
            else:
                raise ExampleModuleException(_("The itemid %s does not exist") % itemid)
        #Otherwise fall back to getting source information as expected
        if "defereasymode" in self.sourcescache[sourceid]:
            defereasymode = self.sourcescache[sourceid]["defereasymode"]
        else:
            defereasymode = False
        if "elevated" in self.sourcescache[sourceid]:
            elevated = self.sourcescache[sourceid]["elevated"]
        else:
            elevated = False
        return {"fullname": self.sourcescache[sourceid]["fullname"], \
            "subsources": self.sourcescache[sourceid]["subsources"], \
            "defereasymode": defereasymode, \
            "elevated": elevated}
        #NOTE: Priority falls back to 50


    ############################################
    # Item Management
    ############################################

    def getItemStatus(self, itemid, sourceid):
        #This is just so the functionality can be shown off - in an actual module, you should query your chosen backend for installation status and respond appropriately.
        # NOTE: Only 0, 1, and 2 are accepted status values for a module to return.

        if itemid not in self.itemcache:
            if itemid in self.redirectscache:
                if sourceid in self.redirectscache[itemid]["sources"]:
                    return 1, "" #Return installed for our redirection test(s)
                else:
                    raise ExampleModuleException(_("%s is not a valid redirection source for %s") % (sourceid, itemid))
            else:
                raise ExampleModuleException(_("The itemid %s does not exist") % itemid)
        else:
            installed = self.itemcache[itemid][sourceid]["testinstalledstatus"]
            subsource = self.itemcache[itemid][sourceid]["testinstalledsubsource"]
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
