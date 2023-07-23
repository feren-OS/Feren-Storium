import configparser
import os
import subprocess
import gettext
import gi


#Dependencies
from solstice import utils, variables
import json
import shutil
import ast
import signal
import time
from gi.repository import GLib
import colorsys
from urllib import parse
from xdg.DesktopEntry import DesktopEntry
import magic
from PIL import Image


class SolsticeModuleException(Exception): # Name this according to the module to allow easier debugging
    pass


class module():

    def __init__(self, storeapi):
        #Gettext Translator
        gettext.install("feren-solstice-storium", "/usr/share/locale", names="ngettext")
        
        #Store APIs
        self.storeapi = storeapi

        #Name to be used in Debugging output
        self.title = _("Solstice Management Module")
        #Name to be shown in the GUI
        self.humanreadabletitle = _("Solstice Application Management")
        #Name to be shown in sources
        self.sourcesmodulename = _("Website Application")
        
        #Package Storage will store the data of opened packages this instance, to make future loads faster
        self.packagestorage = {}
        
        #Configs (obtained by get_configs)
        self.moduleconfigs={}
        self.get_configs()
        
        #Lock to keep stuff from happening while memory is refreshing
        self.memory_refreshing = False
        
        #What package types does this module work with?
        self.types_supported = ["solstice"]
        
        #////Package Management:////
        #Can manage Application Sources?
        self.canmanagesources = False
        #Current name being managed
        self.busywithpackage = ""
        #Do subsources require an information change?
        self.subsourceschangeinfo = False #False because no subsources

        
    def refresh_memory(self): # Function to refresh some memory values
        self.memory_refreshing = True

        self.packagestorage = {}
        with open("/usr/share/feren-storium/curated/package-info/solstice/data.json", 'r') as fp:
            self.packagestorage = json.loads(fp.read())
        if os.path.isfile("/usr/share/feren-storium/curated/" + locale.getlocale()[0] + "/package-info/solstice/data.json"):
            with open("/usr/share/feren-storium/curated/" + locale.getlocale()[0] + "/package-info/solstice/data.json", 'r') as fp: #Also overwrite with language-specifics if they exist
                self.packagestorage = self.dict_recurupdate(self.packagestorage, json.loads(fp.read()))
        
        self.memory_refreshing = False
        
        
    #////Package Management////
    def getCategoryIDs(self, categoryid):
        #Get list of itemids in the category of categoryid and return that list
        result = []
        for itemid in self.packagestorage:
            if self.packagestorage[itemid]["category"] == categoryid or "all" == categoryid:
                result.append(itemid)
        return result


    def getSources(self, pkgid):
        #TODO: Check package even has a Website Application source in the first place


        #Construct subsources for the only source
        subsources = {}
        for browsertype in variables.sources:
            for browser in variables.sources[browsertype]:
                if "required-file" not in variables.sources[browsertype][browser]:
                    continue #Skip evidently unavailable browsers
                for candidate in variables.sources[browsertype][browser]["required-file"]:
                    if os.path.isfile(candidate):
                        subsources[browsertype+"?"+browser] = {"name": variables.sources[browsertype][browser]["name"]}
                        break #Don't need to check more candidates
        
        #Return complete sources value
        return {"solstice": {"subsources": subsources, "name": _("Website Application")}}
    
    
    def getAvailable(self, pkgid, sourceid):
        #Check if package even exists in the first place
        #Return values:
        #0: Available
        #1: Unavailable
        #2: Repository requires being added first
        #FIXME: We don't need this, given self.get_status

        if pkgid in self.packagestorage:
            return 0 #of course Website Applications are available.
        else:
            return 1

    
        
    def pkgstorage_add(self, packagename):
        #Not needed as this module just pre-stores all the information
        #FIXME: Does Brain call this? This isn't needed, otherwise.
        pass
    
    
    def get_status(self, pkgid, pkgtype, sourceid):
        #FIXME: Ditch pkgtype and figure out how we want to handle local package files (albeit unused for Solstice)
        # Return package installation status
        # 0 - Uninstalled
        # 1 - Installed
        # 2 - Updatable
        # 3 - Available in a disabled source (unused here)
        # 403 - Not Available (unused here)

        #NOTE: sourceid is always 'solstice' due to self.getSources
        currentsubsource = None
        desktopfile = ""

        #First, look for all possible cases of the .desktop file, to see if it exists
        entry=DesktopEntry()
        for browsertype in variables.sources:
            for browser in variables.sources[browsertype]: #NOTE: We don't know the subsource, so we just
                if "classprefix" not in variables.sources[browsertype][browser]:
                    continue #Skip evidently unavailable browsers
                classprefix = variables.sources[browsertype][browser]["classprefix"]
                if os.path.isfile(variables.applications_directory + "/" + classprefix + pkgid + ".desktop"):
                    #Open the .desktop file, and check its lastupdated
                    try:
                        entry.parse(variables.applications_directory + "/" + classprefix + pkgid + ".desktop")
                        lastupdated = entry.get("X-Solstice-LastUpdate")
                    except:
                        continue
                    try:
                        currentsubsource = entry.get("X-Solstice-BrowserType") + "?" + entry.get("X-Solstice-Browser")
                    except:
                        currentsubsource = browsertype + "?" + browser #Consistent ID with self.getSources
                    if lastupdated == "":
                        return 2, currentsubsource #Lacking a lastupdated value immediately means it needs an update
                    if lastupdated != self.packagestorage[pkgid]["lastupdate"]:
                        return 2, currentsubsource #Non-matching lastupdate means it needs updating

                    return 1, currentsubsource #If code reaches this line, it means the shortcut exists and is up-to-date

        return 0, None #Couldn't find a valid .desktop file - it is not installed.
    
    
    def cleanupModule(self):
        #Cleanup after package operations
        self.currentpackagename = ""
        self.packagemgmtbusy = False


    def getTaskChanges(self, itemid, operation, sourceid, subsourceid):
        #Return empty values as there is no extra items being added... only bonuses being added.
        return [], [], [], [], []
        #install, update, remove, sourceadd, sourceremove

    def getBonuses(self, itemid, sourceid, subsourceid):
        #TODO: Website-specific bonuses, and website-specific bonus-priorities
        browsertype, browser = subsourceid.split("?")
        #Check the browser for bonuses support in Solstice
        bonusesavailable = False
        if "bonusesavailable" in variables.sources[browsertype][browser]:
            bonusesavailable = variables.sources[browsertype][browser]["bonusesavailable"]
        if bonusesavailable == False:
            return [] #Return no bonuses on no-bonuses browsers

        #Now get the list of bonuses from Solstice for the respective browser
        if browsertype == "chromium":
            result = []
            with open("/usr/share/solstice/chromium/bonuses.json", 'r') as fp:
                for i in json.loads(fp.read()):
                    result.append(i)
            return result

        return [] #Fallback value

    
    #Application management
    def increment_progress(self, tasksdone, tobedone, progress_callback):
        tasksdone += 1
        progress_callback((tasksdone / tobedone) * 100)
        return tasksdone
    def task_install_package(self, taskdata, progress_callback, forupdate=False):
        #Install package and return exit code
        if forupdate == False:
            self.packagemgmtbusy = True
            self.currentpackagename = taskdata.itemid #FIXME: Do we need this?

        #Take note of package information so we can reuse its information
        pkginfo = self.getInfo(taskdata.itemid, "", "") #TODO: Replace this with a call to complete information
        #package_information = self.getInfo(taskdata.itemid, taskdata.sourceid, taskdata.subsourceid)

        #{'type-importance': ['solstice'], 'realname': 'BBC News', 'iconname': 'bbc-news', 'iconlocal': '', 'iconuri': 'http://m.files.bbci.co.uk/modules/bbc-morph-news-waf-page-meta/5.2.0/apple-touch-icon.png', 'shortdescription': '', 'description': 'TODO', 'website': 'https://www.bbc.co.uk/news', 'donateurl': '', 'category': 'ice-internet', 'images': [''], 'sources-available': ['all'], 'all': {'keywords': 'BBC;News;UK;World;Africa;Asia;Australia;Europe;America;Canada;', 'author': 'BBC', 'bugreporturl': '', 'tosurl': '', 'privpolurl': '', 'icecolor': '#FFFFFF', 'icecolordark': '#000000', 'icecolorhighlight': '#bb1919', 'icelastupdated': '20211210'}, 'keywords': 'BBC;News;UK;World;Africa;Asia;Australia;Europe;America;Canada;', 'author': 'BBC', 'bugreporturl': '', 'tosurl': '', 'privpolurl': '', 'icecolor': '#FFFFFF', 'icecolordark': '#000000', 'icecolorhighlight': '#bb1919', 'icelastupdated': '20211210'}

        #First remove the files just in case there's a partial installation
        #TODO self.task_remove_package(taskdata, None, True)

        if not forupdate:
            tasksdone = 0
            #Calculate tasks to do
            tobedone = 1 + len(pkginfo["childids"]) #.desktop files
            tobedone = tobedone * 2 #icon files - the number of .desktop files = the number of icon IDs created NOTE: This only works due to the code's current order

        #Save main icon to local hicolor icon set
        iconsource = None
        try:
            iconsource = self.storeapi.getFallbackIconLocation("", pkginfo["iconuri"], taskdata.itemid)
        except Exception as e:
            print(e) #TODO: Fail here
        if iconsource != None:
            self.export_icon_file(taskdata.itemid, iconsource)
        if not forupdate:
            tasksdone = self.increment_progress(tasksdone, tobedone, progress_callback)
        #...and repeat for the extra icons
        for childsuffix in pkginfo["childids"]:
            iconsource = None
            childid = taskdata.itemid + "-" + childsuffix
            try:
                childinfo = self.getInfo(childid, "", "") #TODO: Replace this with a call to complete information
                iconsource = self.storeapi.getFallbackIconLocation("", childinfo["iconuri"], taskdata.itemid + "-" + childsuffix)
            except Exception as e:
                print(e) #TODO: Fail here
            if iconsource != None:
                self.export_icon_file(childid, iconsource)
            if not forupdate:
                tasksdone = self.increment_progress(tasksdone, tobedone, progress_callback)


        #Now, create the .desktop file
        browsertype, browser = taskdata.subsourceid.split("?")
        classprefix = variables.sources[browsertype][browser]["classprefix"]
        desktopfile = variables.applications_directory + "/" + classprefix + taskdata.itemid + ".desktop"
        with open(desktopfile, 'w') as fp:
            fp.write("[Desktop Entry]\n")
            fp.write("Version=1.0\n")
            fp.write("Name={0}\n".format(pkginfo["realname"]))
            fp.write("Comment={0}\n".format(pkginfo["shortdescription"]))
            fp.write("Icon={0}\n".format("solstice-" + taskdata.itemid))

            fp.write("Exec=/usr/bin/solstice {0}\n".format('"' + desktopfile + '"'))

            #Convert the special categories Solstice applications have to the XDG format
            if pkginfo["category"] == "solstice-accessories":
                location = "Utility;"
            elif pkginfo["category"] == "solstice-games":
                location = "Game;"
            elif pkginfo["category"] == "solstice-graphics":
                location = "Graphics;"
            elif pkginfo["category"] == "solstice-internet":
                location = "Network;"
            elif pkginfo["category"] == "solstice-office":
                location = "Office;"
            elif pkginfo["category"] == "solstice-programming":
                location = "Development;"
            elif pkginfo["category"] == "solstice-education":
                location = "Education;"
            elif pkginfo["category"] == "solstice-multimedia":
                location = "AudioVideo;"
            elif pkginfo["category"] == "solstice-system":
                location = "System;"
            fp.write("Categories=GTK;Qt;{0}\n".format(location))

            fp.write("Keywords=%s\n" % pkginfo["keywords"])

            fp.write("Terminal=false\n")
            fp.write("X-MultipleArgs=false\n")
            fp.write("Type=Application\n")
            fp.write("StartupWMClass={0}\n".format(classprefix + taskdata.itemid))
            fp.write("StartupNotify=true\n")

            #Now to write the information for ICE to use
            fp.write("X-Solstice-Browser=%s\n" % browser)
            fp.write("X-Solstice-BrowserType=%s\n" % browsertype)
            fp.write("X-Solstice-ID=%s\n" % taskdata.itemid)
            fp.write("X-Solstice-Website=%s\n" % pkginfo["solwebsite"])
            fp.write("X-Solstice-Children=%s\n" % pkginfo["childids"])
            if "solnohistory" in pkginfo: #these are optional
                fp.write("X-Solstice-NoHistory=%s\n" % utils.boolean_to_jsonbool(pkginfo["solnohistory"]))
            if "solgooglehangouts" in pkginfo:
                fp.write("X-Solstice-GoogleHangouts=%s\n" % utils.boolean_to_jsonbool(pkginfo["solgooglehangouts"]))
            if "solworkspaces" in pkginfo:
                fp.write("X-Solstice-Workspaces=%s\n" % utils.boolean_to_jsonbool(pkginfo["solworkspaces"]))
            fp.write("X-Solstice-BonusIDs=%s\n" % str(taskdata.bonusids)) #TODO: Callback in Solstice to change Bonuses
            fp.write("X-Solstice-BG=%s\n" % pkginfo["solbackground"])
            fp.write("X-Solstice-BG-Dark=%s\n" % pkginfo["solbackground-dark"])
            fp.write("X-Solstice-Accent=%s\n" % pkginfo["solaccent"])
            fp.write("X-Solstice-Accent-Dark=%s\n" % pkginfo["solaccent-dark"])
            fp.write("X-Solstice-Color=%s\n" % pkginfo["solcolor"])
            if "solcolor-dark" in pkginfo: #color-dark's optional
                fp.write("X-Solstice-Color-Dark=%s\n" % pkginfo["solcolor-dark"])
            if "solaccentwindow" in pkginfo: #FIXME: Remove all these optionals, instead making them be filled in by self.getInfo
                fp.write("X-Solstice-AccentWindow=%s\n" % utils.boolean_to_jsonbool(pkginfo["solaccentwindow"]))
            if "solchromicolor" in pkginfo: #chromicolor's optional
                fp.write("X-Solstice-ChromiColor=%s\n" % pkginfo["solchromicolor"])
            fp.write("X-Solstice-LastUpdate=%s\n" % pkginfo["lastupdate"])

            #Now write the force-manager action
            fp.write("\n")
            fp.write("Actions=force-manager;\n")
            fp.write("\n")
            fp.write("[Desktop Action force-manager]\n")
            fp.write("Name=Manage Profiles...\n")
            fp.write("Icon=solstice\n")
            fp.write("Exec=/usr/bin/solstice {0} --force-manager\n".format('"' + desktopfile + '"'))
        #Make the shortcut executable
        os.system("chmod +x " + desktopfile)
        if not forupdate:
            tasksdone = self.increment_progress(tasksdone, tobedone, progress_callback) #Update progress

        #Then, create the childrens' .desktop files
        for childsuffix in pkginfo["childids"]:
            childid = taskdata.itemid + "-" + childsuffix
            childinfo = self.getInfo(childid, "", "") #TODO: Replace this with a call to complete information
            desktopfile = variables.applications_directory + "/" + classprefix + childid + ".desktop"
            with open(desktopfile, 'w') as fp:
                fp.write("[Desktop Entry]\n")
                fp.write("Version=1.0\n")
                fp.write("Name={0}\n".format(childinfo["realname"]))
                fp.write("Comment={0}\n".format(childinfo["shortdescription"] if "shortdescription" in childinfo else pkginfo["shortdescription"])) #FIXME
                fp.write("Icon={0}\n".format("solstice-" + childid))

                fp.write("Exec=/usr/bin/solstice {0}\n".format('"' + desktopfile + '"'))

                #Convert the special categories Solstice applications have to the XDG format
                if childinfo["category"] == "solstice-accessories":
                    location = "Utility;"
                elif childinfo["category"] == "solstice-games":
                    location = "Game;"
                elif childinfo["category"] == "solstice-graphics":
                    location = "Graphics;"
                elif childinfo["category"] == "solstice-internet":
                    location = "Network;"
                elif childinfo["category"] == "solstice-office":
                    location = "Office;"
                elif childinfo["category"] == "solstice-programming":
                    location = "Development;"
                elif childinfo["category"] == "solstice-education":
                    location = "Education;"
                elif childinfo["category"] == "solstice-multimedia":
                    location = "AudioVideo;"
                elif childinfo["category"] == "solstice-system":
                    location = "System;"
                fp.write("Categories=GTK;Qt;{0}\n".format(location))

                fp.write("Keywords=%s\n" % childinfo["keywords"])

                fp.write("Terminal=false\n")
                fp.write("X-MultipleArgs=false\n")
                fp.write("Type=Application\n")
                fp.write("StartupWMClass={0}\n".format(classprefix + childid))
                fp.write("StartupNotify=true\n")

                #Now to write the information for ICE to use
                fp.write("X-Solstice-ID=%s\n" % childid)
                fp.write("X-Solstice-ParentID=%s\n" % taskdata.itemid)
                fp.write("X-Solstice-Website=%s\n" % childinfo["solwebsite"])

                #Now write the force-manager action
                fp.write("\n")
                fp.write("Actions=force-manager;\n")
                fp.write("\n")
                fp.write("[Desktop Action force-manager]\n")
                fp.write("Name=Manage Profiles...\n")
                fp.write("Icon=solstice\n")
                fp.write("Exec=/usr/bin/solstice {0} --force-manager\n".format('"' + desktopfile + '"'))
            #Make the shortcut executable
            os.system("chmod +x " + desktopfile)
            if not forupdate:
                tasksdone = self.increment_progress(tasksdone, tobedone, progress_callback)

        return True
    
    
    def task_remove_package(self, taskdata, progress_callback, forupdate=False):
        #Remove package and return exit code
        if forupdate == False:
            self.packagemgmtbusy = True
            self.currentpackagename = taskdata.itemid #FIXME: Do we need this?

        #Take note of package information so we can reuse its information
        pkginfo = self.getInfo(taskdata.itemid, "", "") #TODO: Replace this with a call to complete information

        profilesdir = "{0}/{1}".format(variables.solstice_profiles_directory, taskdata.itemid)
        childids = []
        itemnames = []

        #Store all existing desktopfiles for this item, including unused ones, to fully delete the shortcuts later
        parentdesktopfiles = []
        childdesktopfiles = []

        #Get all .desktop files
        for browsertype in variables.sources:
            for browser in variables.sources[browsertype]: #Make sure unwanted .desktop files get nuked too, in case they somehow exist
                if "classprefix" not in variables.sources[browsertype][browser]:
                    continue #Skip evidently unavailable browsers
                classprefix = variables.sources[browsertype][browser]["classprefix"]
                desktopfile = variables.applications_directory + "/" + classprefix + taskdata.itemid + ".desktop"
                if os.path.isfile(desktopfile):
                    if desktopfile not in parentdesktopfiles:
                        parentdesktopfiles.append(desktopfile)

        #Get childids, and human-readable names, from the .desktop files
        entry=DesktopEntry()
        for i in parentdesktopfiles:
            try:
                entry.parse(i)
                for childid in ast.literal_eval(entry.get("X-Solstice-Children")):
                    if childid not in childids:
                        childids.append(childid)
                itemname = entry.getName()
                if itemname not in itemnames:
                    itemnames.append(itemname)
            except:
                continue
        for childid in pkginfo["childids"]: #Fallback just in case, TODO: Replace this with a call to complete information
            if childid not in childids:
                childids.append(childid)

        #Get all .desktop files for each children ID, too
        for childid in childids:
            for browsertype in variables.sources:
                for browser in variables.sources[browsertype]: #Same strategy as earlier of ensuring unwanted .desktop files are also nuked
                    if "classprefix" not in variables.sources[browsertype][browser]:
                        continue #Skip evidently unavailable browsers
                    classprefix = variables.sources[browsertype][browser]["classprefix"]
                    desktopfile = variables.applications_directory + "/" + classprefix + taskdata.itemid + "-" + childid + ".desktop"
                    if os.path.isfile(desktopfile):
                        if desktopfile not in childdesktopfiles:
                            childdesktopfiles.append(desktopfile)

        #Calculate stuff to be done
        if not forupdate:
            tasksdone = 0
            tobedone = 1 + len(childids) #icons
            tobedone += len(parentdesktopfiles) #.desktop
            tobedone += len(childdesktopfiles) # files
            if os.path.isdir(profilesdir):
                for i in os.listdir(profilesdir):
                    if os.path.isdir(profilesdir + "/" + i):
                        tobedone += 1 #profiles
            tobedone += 1 #Flatpak permissions-revoking

        #Remove all icons, first
        for size in ["512x512", "256x256", "128x128", "64x64", "48x48", "32x32", "24x24", "16x16"]:
            if os.path.isfile(os.path.expanduser("~") + "/.local/share/icons/hicolor/" + size + "/apps/solstice-" + taskdata.itemid + ".png"):
                os.remove(os.path.expanduser("~") + "/.local/share/icons/hicolor/" + size + "/apps/solstice-" + taskdata.itemid + ".png")
        if os.path.isfile(os.path.expanduser("~") + "/.local/share/icons/hicolor/scalable/apps/solstice-" + taskdata.itemid + ".svg"):
            os.remove(os.path.expanduser("~") + "/.local/share/icons/hicolor/scalable/apps/solstice-" + taskdata.itemid + ".svg")
        if not forupdate:
            tasksdone = self.increment_progress(tasksdone, tobedone, progress_callback)
        #...and repeat for the extra icons
        for childsuffix in childids:
            childid = taskdata.itemid + "-" + childsuffix
            for size in ["512x512", "256x256", "128x128", "64x64", "48x48", "32x32", "24x24", "16x16"]:
                if os.path.isfile(os.path.expanduser("~") + "/.local/share/icons/hicolor/" + size + "/apps/solstice-" + childid + ".png"):
                    os.remove(os.path.expanduser("~") + "/.local/share/icons/hicolor/" + size + "/apps/solstice-" + childid + ".png")
            if os.path.isfile(os.path.expanduser("~") + "/.local/share/icons/hicolor/scalable/apps/solstice-" + childid + ".svg"):
                os.remove(os.path.expanduser("~") + "/.local/share/icons/hicolor/scalable/apps/solstice-" + childid + ".svg")
            if not forupdate:
                tasksdone = self.increment_progress(tasksdone, tobedone, progress_callback)

        if not forupdate: #Unless we're updating,
            #then delete the profiles
            if os.path.isdir(profilesdir):
                for i in os.listdir(profilesdir):
                    if os.path.isdir(profilesdir + "/" + i):
                        utils.delete_profilefolder(profilesdir + "/" + i)
                        tasksdone = self.increment_progress(tasksdone, tobedone, progress_callback)
                shutil.rmtree(profilesdir)

            #and revoke Flatpak permissions
            for browsertype in variables.sources: #Iterate through all possible Flatpaks
                for browser in variables.sources[browsertype]:
                    if "flatpak" not in variables.sources[browsertype][browser]:
                        continue
                    for name in itemnames:
                        utils.remove_flatpak_permissions(taskdata.itemid, name, browsertype, browser)
            tasksdone = self.increment_progress(tasksdone, tobedone, progress_callback)

        #Finally, delete all the .desktop files, to finish the job
        for i in childdesktopfiles:
            try:
                os.remove(i)
                if not forupdate:
                    tasksdone = self.increment_progress(tasksdone, tobedone, progress_callback)
            except Exception as e:
                raise SolsticeModuleException(_("Failed to uninstall child shortcuts: %s") % e)
        for i in parentdesktopfiles:
            try:
                os.remove(i)
                if not forupdate:
                    tasksdone = self.increment_progress(tasksdone, tobedone, progress_callback)
            except Exception as e:
                raise SolsticeModuleException(_("Failed to uninstall shortcuts: %s") % e)

        if not forupdate:
            progress_callback(100)
        
        return True
    
    
    def task_update_package(self, taskdata, progress_callback):
        #Update package and return exit code
        self.packagemgmtbusy = True
        self.currentpackagename = taskdata.itemid #FIXME: Do we need this?

        #Remove most of the website application files first
        self.task_remove_package(taskdata, progress_callback, True)

        progress_callback(50)

        #Now re-run the installation process, so that newer files are used
        self.task_install_package(taskdata, progress_callback, True)

        progress_callback(100)
        
        return True

    def export_icon_file(self, itemid, iconsource):
        try:
            #Make sure necessary directories exist
            for i in [os.path.expanduser("~") + "/.local", os.path.expanduser("~") + "/.local/share", os.path.expanduser("~") + "/.local/share/icons", os.path.expanduser("~") + "/.local/share/icons/hicolor"]:
                if not os.path.isdir(i):
                    os.mkdir(i)

            mimetype = magic.Magic(mime=True).from_file(iconsource)
            if mimetype == "image/png" or mimetype == "image/vnd.microsoft.icon" or mimetype == "image/jpeg" or mimetype == "image/bmp": #PNG, JPG, BMP or ICO
                iconfile = Image.open(iconsource)
                #Get and store the image's size, first
                imagesize = iconfile.size[1]

                #Now downsize the icon to each size:
                for i in [[512, "512x512"], [256, "256x256"], [128, "128x128"], [64, "64x64"], [48, "48x48"], [32, "32x32"], [24, "24x24"], [16, "16x16"]]:
                    #...if it is large enough
                    if imagesize < i[0]:
                        continue

                    #Create the directory if it doesn't exist
                    for ii in [os.path.expanduser("~") + "/.local/share/icons/hicolor/" + i[1], os.path.expanduser("~") + "/.local/share/icons/hicolor/" + i[1] + "/apps"]:
                        if not os.path.isdir(ii):
                            os.mkdir(ii)

                    targetpath = os.path.expanduser("~") + "/.local/share/icons/hicolor/" + i[1] + "/apps/solstice-" + itemid + ".png"
                    if imagesize != i[0]:
                        iconfile.resize((i[0], i[0]))
                        iconfile.save(targetpath, "PNG")
                    else:
                        shutil.copy(iconsource, targetpath)
            elif mimetype == "image/svg+xml": #SVG
                #Create the directory if it doesn't exist
                for ii in [os.path.expanduser("~") + "/.local/share/icons/hicolor/scalable", os.path.expanduser("~") + "/.local/share/icons/hicolor/scalable/apps"]:
                    if not os.path.isdir(ii):
                        os.mkdir(ii)

                #Copy the SVG over
                targetpath = os.path.expanduser("~") + "/.local/share/icons/hicolor/scalable/apps/solstice-" + itemid + ".svg"
                shutil.copy(iconsource, targetpath)

        except Exception as e:
            raise SolsticeModuleException(_("Exporting icon failed: %s") % e)
    
    def get_configs(self):
        #Get configs and their current gsettings/file values and return them as a dictionary
        gsettingsschemas={} # e.g.: {org.cinnamon.theme: [name]}
        configfiles={} # {config file: [config names]}
        
        for schema in gsettingsschemas:
            for configname in gsettingsschemas[schema]:
                pass
        for configfile in configfiles:
            for configname in configfiles[configname]:
                pass
        
        #{value: [type (gsettings/file), schema (gsettings schema/file path), current value]}
        pass

    def enable_appsource(self, appsource):
        #You SHOULD NOT be able to manage Application Sources for websites anyway, so raise an error
        raise SolsticeModuleException(_("You cannot manage sources when the 'sources' are just web browsers."))
    
    def disable_appsource(self, appsource):
        #You SHOULD NOT be able to manage Application Sources for websites anyway, so raise an error
        raise SolsticeModuleException(_("You cannot manage sources when the 'sources' are just web browsers."))




    #////Package Information////
    def build_ids_list(self): #Build list of package IDs
        self.pkg_ids = []
        for i in [self.packagestorage]:
            try:
                for package in i:
                    if package not in self.pkg_ids:
                        self.pkg_ids.append(package)
            except:
                pass
        
    def build_categories_ids(self): #Build categories list for package IDs
        self.pkg_categoryids = {}
        #Do nothing else as this isn't a generic module
                
        
    def getPackageJSON(self):
        #Return a json of all package names
        packagejson = {}
        for i in [self.packagestorage]:
            try:
                packagejson.update(i)
            except:
                pass
        return packagejson


    def getInfo(self, itemid, sourceid, subsourceid):
        #Get information on a package using the JSON data
        result = self.packagestorage[itemid]

        if "parentitemid" in result: #If this is a child item, just ensure the child item requirements are met
            defaultvalues = {"iconuri": "", "images": "", "keywords": ""}
            valuesrequired = ["realname", "category", "solwebsite"]
        else:
            defaultvalues = {"childids": [],
                            "iconuri": "",
                            "shortdescription": _("Website Application"),
                            "description": "",
                            "images": [],
                            "keywords": "",
                            "website": "",
                            "donateurl": "",
                            "bugreporturl": "",
                            "tosurl": "",
                            "privpolurl": "",
                            "solnohistory": False,
                            "solgooglehangouts": False,
                            "solworkspaces": False,
                            "solaccentwindow": True}
            valuesrequired = ["realname", "category", "author", "solbackground", "solbackground-dark", "solaccent", "solaccent-dark", "solcolor", "solwebsite", "lastupdate"]
        for item in valuesrequired:
            if item not in result or result[item] == "":
                raise SolsticeModuleException(_("Invalid item information for {0} - {1} is missing").format(itemid, item))
        for item in defaultvalues:
            if item not in result or result[item] == "":
                result[item] = defaultvalues[item]
        result["iconlocal"] = ""
        return result
        
        
    def getSourceList(self, packagename, packagetype):
        #Get list of source order
        
        #Not needed since 'all'
        #if packagetype not in self.types_supported:
            #raise GenericInfoModuleException(packagetype, _("is not supported by this information module. If you are getting an exception throw, it means you have not used a Try to respond to the module not supporting this type of package."))
            #return
            
        return [] #FIXME: Remove, as we have self.getSources
        
    #TODO: Do we need these? I think they are kinda pointless now.
    def getShortDescription(self, packagename):
        try:
            shortdescription = self.packagestorage[packagename]["shortdescription"]
        except:
            shortdescription = _("Website Application")
        return shortdescription
    
    def getKeywords(self, packagename):
        try:
            keywords = self.packagestorage[packagename]["keywords"]
        except:
            raise IceInfoModuleException(packagename, _("has no keywords value in the package metadata. Websites MUST have keywords values when curated."))
            return
        return keywords
    
    def getAuthor(self, packagename):
        try:
            author = self.packagestorage[packagename]["author"]
        except:
            author = _("Unknown Author")
        return author
      
    def getBugsURL(self, packagename):
        try:
            bugsurl = self.packagestorage[packagename]["bugreporturl"]
        except:
            bugsurl = ""
        return bugsurl
      
    def getTOSURL(self, packagename):
        try:
            tosurl = self.packagestorage[packagename]["tos"]
        except:
            tosurl = ""
        return tosurl
      
    def getPrivPolURL(self, packagename):
        try:
            privpolurl = self.packagestorage[packagename]["privpol"]
        except:
            privpolurl = ""
        return privpolurl
      
    def getExtrasIDs(self, packagename):
        try:
            extrasids = self.packagestorage[packagename]["extrasids"]
        except:
            extrasids = []
        return extrasids
      
    def getExtraRealNames(self, packagename):
        try:
            realnameextras = self.packagestorage[packagename]["realnameextras"]
        except:
            realnameextras = []
        return realnameextras
      
    def getIconURIExtras(self, packagename):
        try:
            iconuriextras = self.packagestorage[packagename]["iconuriextras"]
        except:
            iconuriextras = []
        return iconuriextras
      
    def getWebsiteExtras(self, packagename):
        try:
            websiteextras = self.packagestorage[packagename]["websiteextras"]
        except:
            websiteextras = []
        return websiteextras
      
    def getKeywordsExtras(self, packagename):
        try:
            keywordsextras = self.packagestorage[packagename]["keywordsextras"]
        except:
            keywordsextras = []
        return keywordsextras
    
    
    def getCanTheme(self, packagename, packagetype):
        # Return values:
        # 0: No
        # 1: Yes
        # 2: Yes, but manually enabled
        # 3: Yes, except for Feren OS's style
        # 4: Has own themes system
        # 5: No because LibAdwaita
        # 6: No because LibGranite
        
        canusethemes = 1 #Disable warning for Website Applications      
        try:
            if self.packagestorage[packagename]["hasownthemes"] == True:
                canusethemes = 4 #...unless a website has themes of its own
        except:
            pass
        return canusethemes
    
      
    def getCanTouchScreen(self, packagename, packagetype):
        # Return values:
        # 0: No
        # 1: Yes
        # 2: Partially
        
        return 1 #Disable warning for Website Applications
    
    
    def getCanUseAccessibility(self, packagename, packagetype):
        try:
            canuseaccessibility = self.packagestorage[packagename]["canuseaccessibility"]
        except:
            canuseaccessibility = True # Use fallback of True when unknown to hide the message
        return canuseaccessibility
    
    
    def getCanUseDPI(self, packagename, packagetype):
        return True #Disable warning for Website Applications
    
    
    def getCanUseOnPhone(self, packagename, packagetype):
        try:
            canuseonphone = self.packagestorage[packagename]["canuseonphone"]
        except:
            canuseonphone = True # Use fallback of True when unknown to hide the message
        return canuseonphone
    
    
    def getIsOfficial(self, packagename, packagetype):
        return True #Disable warning for Website Applications
    
    

if __name__ == "__main__":
    module = PackageMgmtModule()
