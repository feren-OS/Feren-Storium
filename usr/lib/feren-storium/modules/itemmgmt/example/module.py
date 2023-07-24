#Dependencies
import time
import gettext


class ExampleModuleException(Exception): # Name this according to the module to allow easier debugging
    pass


class module():

    def __init__(self, genericapi, itemapi):
        #Gettext Translator
        gettext.install("feren-solstice-exampleitemmgmt", "/usr/share/locale", names="ngettext")
        
        #Storium APIs
        self.api = genericapi
        self.itemapi = itemapi
        
        #Package Storage will store the data of opened packages this instance, to make future loads faster
        self.packagestorage = {}

        
    def refresh_memory(self): # Function to refresh some memory values
        #self.memory_refreshing = True

        pass #TODO
        
        #self.memory_refreshing = False
        

    
    
