import configparser
import os
import subprocess
import gettext
import gi

class PackageMgmtModule():

    def __init__(self, storegui):

        gettext.install("feren-storium", "/usr/share/locale", names="ngettext")

        #Name to be used in Debugging output
        self.title = _("APT Package Management Module")
        #Name to be shown in the GUI
        self.humanreadabletitle = _("Standard Applications Management")
        
        #Can manage Application Sources?
        self.canmanagesources = True
        
        #Application Sources (leave at {} if canmanagesources is False I guess)
        # internal name: Human-readable name
        self.applicationsources = {"standard": [_("Standard Installation")], /
                                   "google-chrome": [_("Google (Official)")], /
                                   "google-earth": [_("Google (Official)")], /
                                   "vivaldi": [_("Vivaldi (Official)")], /
                                   "microsoft-edge": [_("Microsoft (Official)")], /
                                   "visual-studio": [_("Microsoft (Official)")], /
                                   "opera": [_("Opera (Official)")], /
                                   "waterfox": [_("hawkeye116477")]}
        
        #Configs (obtained by get_configs)
        self.moduleconfigs={}
        self.get_configs()
        

    def get_descriptions(self, packagename):
        # Return description for package
        pass

    def get_status(self, packagename):
        # Return package installation status
        # 0 - Uninstalled
        # 1 - Installed
        # 2 - Updatable
        pass
    
    def install_package(self, packagename):
        #Install package and return exit code
        pass
    
    def remove_package(self, packagename):
        #Remove package and return exit code
        pass
    
    def update_package(self, packagename):
        #Update package and return exit code
        pass
    
    def get_configs(self):
        #Get configs and their current gsettings/file values and return them as a dictionary
        gsettingsschemas=[]
        configfiles={} # {config file: [config names]}
        
        for schema in gsettingsschemas:
            pass
        for configfile in configfiles:
            for configname in configfiles[configname]:
                pass
        
        #{value: [type (gsettings/file), schema (gsettings schema/file path), current value]}
        pass

    def callback(self, data):
        subprocess.run(["/usr/bin/feren-majorupdate-gui"])
        # reload
        return True

if __name__ == "__main__":
    report = Report()
    print(report.is_pertinent())
