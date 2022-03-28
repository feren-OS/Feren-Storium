import configparser
import os
import subprocess
import gettext
import gi


#Dependencies
import json
import shutil
from datetime import datetime
import ast
import signal
import time
import gi
from gi.repository import GLib
import re
import colorsys
from urllib import parse


def should_load(): #Should this module be loaded?
    return True


class ICEModuleException(Exception): # Name this according to the module to allow easier debugging
    pass


class main():

    def __init__(self, storebrain):

        gettext.install("feren-storium", "/usr/share/locale", names="ngettext")

        #Name to be used in Debugging output
        self.title = _("Ice Website Management Module")
        #Name to be shown in the GUI
        self.humanreadabletitle = _("Ice WebApp Management")
        
        #Can manage Application Sources?
        self.canmanagesources = False
        
        #Application Sources (for ICE let's have the sources be the browsers that're supported)
        # Empty here, will be appended to with self.refresh_memory()
        self.applicationsources = []
        
        #Store Brain
        self.storebrain = storebrain
        
        #What package types does this manage?
        self.types_supported = ["peppermint-ice"]
        
        #Generic Description for header
        self.genericheader = _("Website Application")
        
        #Configs (obtained by get_configs)
        self.moduleconfigs={}
        self.get_configs()
        
        #Package Storage will store the data of opened packages this instance
        self.packagestorage = {}
        
        #Last package viewed
        self.lastpkgviewed = ""
        
        #Lock to keep stuff from happening while memory is refreshing
        self.memory_refreshing = False
        
        #Is the package management busy?
        self.packagemgmtbusy = False
        
        #Current name being managed
        self.currentpackagename = ""
        
        #Global Ice last updated date (so that all shortcuts can be updated if a major change occurs)
        self.icelastupdated = "20220329"
        
        #Sources storage
        self.sources_storage = {}
        
    def refresh_memory(self): # Function to refresh some memory values
        self.memory_refreshing = True
        
        self.sources_storage = {}
            
        for i in ["package-sources-info/generic"]:
            with open("/usr/share/feren-storium/curated/" + i + "/data.json", 'r') as fp:            
                self.sources_storage[i] = json.loads(fp.read())["peppermint-ice"]
        
        self.memory_refreshing = False
        
                
    def sourceQuery(self, packagename, packagetype, sourcelist):
        if packagetype not in self.types_supported:
            raise ICEModuleException(_("Items of type %s are not supported by this module.") % packagename)
        sources = []
        
        if sourcelist == ["all"]:
            #Add each browser to sources
            for browser in self.sources_storage["package-sources-info/generic"]["sources"]:
                if os.path.isfile(self.sources_storage["package-sources-info/generic"]["sources"][browser]["repository-file"]):
                    sources.append(browser)
        else:
            #Add each source to sources
            for browser in sourcelist:
                try:
                    if os.path.isfile(self.sources_storage["package-sources-info/generic"]["sources"][browser]["repository-file"]):
                        sources.append(browser)
                except:
                    pass
        
        return sources
        
    
    def get_subsources(self, packagename, packagetype, source):
        if packagetype not in self.types_supported:
            raise ICEModuleException(_("Items of type %s are not supported by this module.") % packagename)
        
        #Leave empty as peppermint-ice has no subsources
        return []
    
        
    def pkgstorage_add(self, packagename):
        #Not needed as we just consult the package information modules for information anyway
        pass

    def get_generic_information(self, packagename, packagetype):
        if packagetype not in self.types_supported:
            raise ICEModuleException(_("Items of type %s are not supported by this module.") % packagename)
        
        # Return generic package information via Brain API
        try:
            return self.storebrain.get_generic_item_info(packagename, packagetype)
        except:
            raise ICEModuleException(e)

    def get_information(self, packagename, packagetype, source):
        if packagetype not in self.types_supported:
            raise ICEModuleException(_("Items of type %s are not supported by this module.") % packagename)
        
        # Return package information via Brain API
        try:
            return self.storebrain.get_item_info_specific(packagename, packagetype, source)
        except Exception as e:
            raise ICEModuleException(e)
        

    def get_status(self, packagename, pkgtype, source):
        # Return package installation status
        # 0 - Uninstalled
        # 1 - Installed
        # 2 - Update available
        
        if os.path.isfile(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-last-updated" % packagename):
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-last-updated" % packagename, 'r') as fp:
                lastupdated = fp.readline()
        else:
            lastupdated = "19700101" #Fallback date, and yes it's beginning of UNIX time - why not
        
        if os.path.isfile(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/Default/Preferences" % packagename) and os.path.isdir(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s" % packagename):
            if self.storebrain.get_item_info_specific(packagename, pkgtype, source, True)["icelastupdated"] > lastupdated or self.icelastupdated > lastupdated:
                return 2
            else:
                return 1
        else:
            return 0
    
    
    def color_scheme_iding(self, colourcode, taskdata, colourcodehighlight="#006aff"):
        #TODO: Add IDs for Feren OS Titlebar Theme, to add titlebar branding colours
        
        redc, greenc, bluec = tuple(int(colourcode[i:i+2], 16) for i in (1, 3, 5)) #Dodge the # character
        
        lumi = colorsys.rgb_to_hls(redc, greenc, bluec)[1]
        
        foregroundc = ""
        if lumi > 127.5:
            foregroundc = "0,0,0"
        else:
            foregroundc = "255,255,255"
        
        redacc, greenacc, blueacc = tuple(int(colourcodehighlight[i:i+2], 16) for i in (1, 3, 5))
        
        #lumiacc = colorsys.rgb_to_hls(redacc, greenacc, blueacc)[1]
        
        #foregroundacc = ""
        #if lumiacc > 127.5:
            #foregroundacc = "0,0,0"
        #else:
        foregroundacc = "255,255,255"
        
        
        
    def get_luminant(self, colourcode):
        #Returns:
        # True: Light
        # False: Dark
        
        redc, greenc, bluec = tuple(int(colourcode[i:i+2], 16) for i in (1, 3, 5)) #Dodge the # character
        
        lumi = colorsys.rgb_to_hls(redc, greenc, bluec)[1]
        
        if lumi > 127.5:
            return True
        else:
            return False
    
    
    def colourFilter(self, colourcode, amount, darken, multiply=False): #hexcode, float, bool, bool
        #Returns:
        # Darkened/Lightened colour
        
        redc, greenc, bluec = tuple(int(colourcode[i:i+2], 16) for i in (1, 3, 5)) #Dodge the # character
        
        hue, lumi, sat = colorsys.rgb_to_hls(redc, greenc, bluec)
        
        if darken == True:
            if multiply == True:
                lumi = lumi * amount
            else:
                if (lumi - amount) < 0.0:
                    lumi = 0.0
                else:
                    lumi -= amount
        else:
            if multiply == True:
                lightner = 1.0 - amount
                lumi = lumi * lightner
            else:
                if (lumi + amount) > 255.0:
                    lumi = 255.0
                else:
                    lumi += amount
            
        redc, greenc, bluec = colorsys.hls_to_rgb(hue, lumi, sat)
        
        redc, greenc, bluec = int(redc), int(greenc), int(bluec) #Convert back to integers
        
        return '#%02x%02x%02x' % (redc, greenc, bluec)
    
    
    def get_are_colours_different(self, colourcode1, colourcode2):
        #Returns:
        # True: Yes
        # False: No
        #    Based on if the r, g, and b values of cc2 aren't matching within 20 above to 20 below cc1's values
        
        red1, green1, blue1 = tuple(int(colourcode1[i:i+2], 16) for i in (1, 3, 5))
        red2, green2, blue2 = tuple(int(colourcode2[i:i+2], 16) for i in (1, 3, 5))
        
        #Red
        redmatches = False
        if red2 > (red1 - 20) and red2 < (red1 + 20):
            redmatches = True
        #Green
        greenmatches = False
        if green2 > (green1 - 20) and green2 < (green1 + 20):
            greenmatches = True
        #Blue
        bluematches = False
        if blue2 > (blue1 - 20) and blue2 < (blue1 + 20):
            bluematches = True
            
        if redmatches and greenmatches and bluematches:
            return False
        else:
            return True
    
    
    def get_colour_bg_suitable(self, colourcode):
        #Returns:
        # True: Yes
        # False: No
        #    Based on if the r, g, and b values of colourcode are matching or very close to each other
        
        red1, green1, blue1 = tuple(int(colourcode[i:i+2], 16) for i in (1, 3, 5))
        
        #Red
        if red1 > (green1 - 20) and red1 < (green1 + 20) and red1 > (blue1 - 20) and red1 < (blue1 + 20) and green1 > (blue1 - 20) and green1 < (blue1 + 20):
            return True
        else:
            return False
    
    
    
    def task_cleanup(self, task):
        #Cleanup after package operations
        self.currentpackagename = ""
        self.packagemgmtbusy = False
        
    #Add to Tasks
    def install_package(self, packagename, pkgtype, source, subsource):
        bonuses = ["ublock", "nekocap", "imagus", "googleytdislikes"] #TODO: Add confirmation prompt showing changes, and also allowing bonus selection
        
        self.storebrain.tasks.add_task(packagename, pkgtype, self, 0, self.storebrain.get_item_info_specific(packagename, pkgtype, source, True), source, subsource, bonuses)
    
    def update_package(self, packagename, pkgtype, source, subsource):
        #TODO: Add confirmation prompt showing changes
        
        self.storebrain.tasks.add_task(packagename, pkgtype, self, 1, self.storebrain.get_item_info_specific(packagename, pkgtype, source, True), source, subsource)
    
    def remove_package(self, packagename, pkgtype, source, subsource):
        #TODO: Add confirmation prompt showing changes
        
        self.storebrain.tasks.add_task(packagename, pkgtype, self, 2, self.storebrain.get_item_info_specific(packagename, pkgtype, source, True), source, subsource)
        
    
    
        
    #Stuff consistent across Install and Update
    def task_shortcut_stuff(self):
        pass
        
    
    #Actual management
    def task_install_package(self, taskdata, progress_callback):
        #Install package and return exit code
        self.packagemgmtbusy = True
        self.currentpackagename = taskdata["packagename"]
        
        windowclassid = taskdata["packagename"]
        if taskdata["source"] == "vivaldi": #FIXME: Temporary until Vivaldi adds proper shadows support
            windowclassid = "vivaldi-" + taskdata["packagename"]
        
        icepackageinfo = taskdata["pkginfo"]
        if "extrasids" in icepackageinfo:
            iceextrasids = icepackageinfo["extrasids"]
        else:
            iceextrasids = []
        if "bonuses" in taskdata:
            icebonuses = taskdata["bonuses"]
        else:
            icebonuses = []
        
        #First remove the files just in case there's a partial installation
        self.task_remove_package(taskdata, None, True)
        
        #Create the .desktop file's home if it doesn't exist
        if not os.path.isdir(os.path.expanduser("~") + "/.local/share/applications"):
            try:
                os.mkdir(os.path.expanduser("~") + "/.local/share/applications")
            except Exception as exceptionstr:
                raise ICEModuleException(_("Failed to install {0}: {1} was encountered when trying to create the shortcut's location").format(taskdata["packagename"], exceptionstr))
            
            
        progress_callback(12)
        
        
        #Titlebar branding (old)
        #if "icecolor" in icepackageinfo:
            #self.color_scheme_iding(icepackageinfo["icecolor"], taskdata, icepackageinfo["icecolorhighlight"])
            #os.system("qdbus org.kde.KWin /KWin reconfigure")
            
            
        #Create the Chromium profile
        if not os.path.isdir(os.path.expanduser("~") + "/.local/share/feren-storium-ice"):
            try:
                os.mkdir(os.path.expanduser("~") + "/.local/share/feren-storium-ice")
            except Exception as exceptionstr:
                raise ICEModuleException(_("Failed to install {0}: {1} was encountered when trying to create the profiles location").format(taskdata["packagename"], exceptionstr))
        if not os.path.isdir(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s" % taskdata["packagename"]):
            try:
                os.mkdir(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s" % taskdata["packagename"])
            except Exception as exceptionstr:
                raise ICEModuleException(_("Failed to install {0}: {1} was encountered when trying to create the profile's folder").format(taskdata["packagename"], exceptionstr))
            
            
        progress_callback(24)
            
            
        #First Run existing skips the initial Welcome to Google Chrome dialog, which is very useful here to have a skip in place for
        try:
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/First Run" % taskdata["packagename"], 'w') as fp:
                pass
        except Exception as exceptionstr:
            self.task_remove_package(taskdata, None, True) #Remove profile's files/folders on failure
            raise ICEModuleException(_("Failed to install {0}: {1} was encountered when making the Chromium-based profile").format(taskdata["packagename"], exceptionstr))
        try:
            os.mkdir(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/Default" % taskdata["packagename"])
        except Exception as exceptionstr:
            self.task_remove_package(taskdata, None, True) #Remove profile's files/folders on failure
            raise ICEModuleException(_("Failed to install {0}: {1} was encountered when making the Chromium-based profile").format(taskdata["packagename"], exceptionstr))
        
        
        progress_callback(36)
            
        
        usefallbackicon = False
        #Copy icon for package
        try:
            shutil.copy(self.storebrain.tempdir + "/icons/" + taskdata["packagename"], os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/icon" % taskdata["packagename"])
        except Exception as exceptionstr:
            usefallbackicon = True
            
            
        progress_callback(48)
            
        
        
        #Now to make the JSON file
        with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/Preferences", 'r') as fp:
            profiletomake = json.loads(fp.read())
            
        with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/and-plasmaintegration", 'r') as fp:
            profiletomakeextra = json.loads(fp.read())
        profiletomake = self.storebrain.dict_recurupdate(profiletomake, profiletomakeextra)
        
        if "icegoogleinteg" in icepackageinfo and icepackageinfo["icegoogleinteg"] == True:
            pass
        else:
            with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/disable-google", 'r') as fp:
                profiletomakeextra = json.loads(fp.read())
            profiletomake = self.storebrain.dict_recurupdate(profiletomake, profiletomakeextra)
        if "icegooglehangouts" in icepackageinfo and icepackageinfo["icegooglehangouts"] == True:
            profiletomake["vivaldi"]["privacy"]["google_component_extensions"]["hangout_services"] = True
        else:
            profiletomake["vivaldi"]["privacy"]["google_component_extensions"]["hangout_services"] = False
        
        if "icenohistory" in icepackageinfo and icepackageinfo["icenohistory"] == True:
            with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/disable-browsehistory", 'r') as fp:
                profiletomakeextra = json.loads(fp.read())
                profiletomake = self.storebrain.dict_recurupdate(profiletomake, profiletomakeextra)
            
            try:
                with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-nohistory" % taskdata["packagename"], 'w') as fp:
                    pass
            except Exception as exceptionstr:
                self.task_remove_package(taskdata, None, True) #Remove profile's files/folders on failure
                raise ICEModuleException(_("Failed to install {0}: {1} was encountered when setting up automatic history deletion").format(taskdata["packagename"], exceptionstr))
        
        
        if "nekocap" in icebonuses:
            with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/and-nekocap", 'r') as fp:
                profiletomakeextra = json.loads(fp.read()) #This is how you make json.load work with file paths, I guess
            profiletomake = self.storebrain.dict_recurupdate(profiletomake, profiletomakeextra)
        if "ublock" in icebonuses:
            with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/and-ublock", 'r') as fp:
                profiletomakeextra = json.loads(fp.read())
            profiletomake = self.storebrain.dict_recurupdate(profiletomake, profiletomakeextra)
        if "darkreader" in icebonuses:
            with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/and-darkreader", 'r') as fp:
                profiletomakeextra = json.loads(fp.read())
            profiletomake = self.storebrain.dict_recurupdate(profiletomake, profiletomakeextra)
        if "imagus" in icebonuses:
            with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/and-imagus", 'r') as fp:
                profiletomakeextra = json.loads(fp.read())
            profiletomake = self.storebrain.dict_recurupdate(profiletomake, profiletomakeextra)
        if "googleytdislikes" in icebonuses:
            with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/and-googleytdislikes", 'r') as fp:
                profiletomakeextra = json.loads(fp.read())
            profiletomake = self.storebrain.dict_recurupdate(profiletomake, profiletomakeextra)
            
            
        #Write Bonuses to be used as a backup
        try:
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-bonuses" % taskdata["packagename"], 'w') as fp:
                fp.write(str(icebonuses)) # This means that Storium can manage bonuses later on in time
        except Exception as exceptionstr:
            self.task_remove_package(taskdata, None, True) #Remove profile's files/folders on failure
            raise ICEModuleException(_("Failed to install {0}: {1} was encountered when making a note of the SSB's bonus additions").format(taskdata["packagename"], exceptionstr))
        
        
        #Extra site-specific tweaks
        profiletomake["homepage"] = icepackageinfo["website"]
        profiletomake["custom_links"]["list"][0]["title"] = icepackageinfo["realname"]
        profiletomake["custom_links"]["list"][0]["url"] = icepackageinfo["website"]
        profiletomake["session"]["startup_urls"] = [icepackageinfo["website"]]
        profiletomake["download"]["default_directory"] = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD) + "/" + _("{0} Downloads").format(icepackageinfo["realname"]) #TODO: Allow configuration of downloads location, whether or not to save to individual folders
        profiletomake["profile"]["name"] = _("Ice - {0}").format(icepackageinfo["realname"])
        profiletomake["ntp"]["custom_background_dict"]["attribution_line_1"] = _("Feren OS Ice Website Application - {0}").format(icepackageinfo["realname"])
        profiletomake["vivaldi"]["tabs"]["new_page"]["custom_url"] = "https://feren-os.github.io/start-page/ice?ice-text="+(_("Feren OS Ice Website Application - {0}").format(icepackageinfo["realname"]))+"&home-url={0}".format(parse.quote(icepackageinfo["website"], safe=""))+"&home-icon={0}".format(parse.quote(icepackageinfo["iconuri"], safe=""))
        profiletomake["vivaldi"]["homepage"] = icepackageinfo["website"]
        profiletomake["vivaldi"]["homepage_cache"] = icepackageinfo["website"]
        
        
        #Background Sync, Clipboard, Notifications and Payment Handler ONLY for SSB's websites
        for permtype in ["ar", "autoplay", "automatic_downloads", "background_sync", "clipboard", "file_handling", "font_access", "midi_sysex", "notifications", "payment_handler", "sensors", "sound", "sleeping-tabs", "window_placement", "vr"]:
            profiletomake["profile"]["content_settings"]["exceptions"][permtype] = {}
            if "icedomain" in icepackageinfo:
                try:
                    shortenedurl = icepackageinfo["icedomain"].split("://")[1:]
                    shortenedurl = ''.join(shortenedurl)
                except:
                    shortenedurl = icepackageinfo["icedomain"]
            else:
                try:
                    shortenedurl = icepackageinfo["website"].split("://")[1:]
                    shortenedurl = ''.join(shortenedurl)
                except:
                    shortenedurl = icepackageinfo["website"]
            try:
                shortenedurl = shortenedurl.split("/")[0]
            except:
                pass
            profiletomake["profile"]["content_settings"]["exceptions"][permtype]["[*.]"+shortenedurl+",*"] = {"expiration": "0", "model": 0, "setting": 1}
            profiletomake["profile"]["content_settings"]["exceptions"][permtype][shortenedurl+",*"] = {"expiration": "0", "model": 0, "setting": 1}
            #Repeat for extra shortcuts' URLs
            extrascount = 0
            for extraid in iceextrasids:
                try:
                    shortenedurl = icepackageinfo["websiteextras"][extrascount].split("://")[1:]
                    shortenedurl = ''.join(shortenedurl)
                except:
                    shortenedurl = icepackageinfo["websiteextras"][extrascount]
                try:
                    shortenedurl = shortenedurl.split("/")[0]
                except:
                    pass
                profiletomake["profile"]["content_settings"]["exceptions"][permtype]["[*.]"+shortenedurl+",*"] = {"expiration": "0", "model": 0, "setting": 1}
                profiletomake["profile"]["content_settings"]["exceptions"][permtype][shortenedurl+",*"] = {"expiration": "0", "model": 0, "setting": 1}
                extrascount += 1
        
        
        #TODO: Figure out doing themes for Chrome to colour the windows by their website colours
        #   Vivaldi colour changes
        if "icecolor" in icepackageinfo and "icecolorhighlight" in icepackageinfo and "icecolordark" in icepackageinfo:
            vivaldihighlightcol = icepackageinfo["icecolorhighlight"]
            vivaldihighlightcoldark = self.colourFilter(icepackageinfo["icecolorhighlight"], 0.7, True, True)
            if self.get_are_colours_different(icepackageinfo["icecolor"], icepackageinfo["icecolorhighlight"]) and self.get_colour_bg_suitable(icepackageinfo["icecolor"]): #Suitable background colour used
                vivaldiaccentcol = icepackageinfo["icecolorhighlight"]
                vivaldiaccentcoldark = icepackageinfo["icecolorhighlight"]
                vivaldiwinbgcol = icepackageinfo["icecolor"]
                vivaldiwinbgcoldark = icepackageinfo["icecolordark"]
                vivaldiaccentinchrome = False
                
            else: #Otherwise use fallback colours
                vivaldiaccentcol = icepackageinfo["icecolor"]
                vivaldiwinbgcol = ""
                vivaldiaccentcoldark = self.colourFilter(icepackageinfo["icecolordark"], 0.7, True, True)
                vivaldiwinbgcoldark = ""
                vivaldiaccentinchrome = True
                
                
            #Now to make the Private theme    
            vivaldiaccentcolprivate = self.colourFilter(icepackageinfo["icecolorhighlight"], 46.0, True)
            vivaldiwinbgcolprivate = self.colourFilter(icepackageinfo["icecolorhighlight"], 70.0, True)
            
                
            profiletomake["vivaldi"]["themes"]["system"][0]["accentOnWindow"] = vivaldiaccentinchrome
            profiletomake["vivaldi"]["themes"]["system"][1]["accentOnWindow"] = vivaldiaccentinchrome
            profiletomake["vivaldi"]["themes"]["system"][2]["accentOnWindow"] = False
            profiletomake["vivaldi"]["themes"]["system"][0]["colorAccentBg"] = vivaldiaccentcol
            profiletomake["vivaldi"]["themes"]["system"][1]["colorAccentBg"] = vivaldiaccentcoldark
            profiletomake["vivaldi"]["themes"]["system"][2]["colorAccentBg"] = vivaldiaccentcolprivate
            profiletomake["vivaldi"]["themes"]["system"][0]["colorHighlightBg"] = vivaldihighlightcol
            profiletomake["vivaldi"]["themes"]["system"][1]["colorHighlightBg"] = vivaldihighlightcoldark
            profiletomake["vivaldi"]["themes"]["system"][2]["colorHighlightBg"] = vivaldihighlightcol
            if vivaldiwinbgcol != "":
                if self.get_luminant(vivaldiwinbgcol) == False: #Dark BG (in-Preferences default is Light, so no need for Light BG else)
                    profiletomake["vivaldi"]["themes"]["system"][0]["colorFg"] = "#FFFFFF"
                profiletomake["vivaldi"]["themes"]["system"][0]["colorBg"] = vivaldiwinbgcol
            if vivaldiwinbgcoldark != "":
                if self.get_luminant(vivaldiwinbgcoldark) == True: #Light BG (in-Preferences default is Dark, so no need for Dark BG else)
                    profiletomake["vivaldi"]["themes"]["system"][1]["colorFg"] = "#000000"
                profiletomake["vivaldi"]["themes"]["system"][1]["colorBg"] = vivaldiwinbgcoldark
            #Private foreground
            if self.get_luminant(vivaldiwinbgcolprivate) == True: #Light BG (in-Preferences default is Dark, so no need for Dark BG else)
                profiletomake["vivaldi"]["themes"]["system"][2]["colorFg"] = "#000000"
            profiletomake["vivaldi"]["themes"]["system"][2]["colorBg"] = vivaldiwinbgcolprivate
            
            
        
        
        #Write last updated date to be used in update checks
        try:
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-last-updated" % taskdata["packagename"], 'w') as fp:
                fp.write(datetime.today().strftime('%Y%m%d')) # This means that Storium can update some parts of it whenever appropriate
        except Exception as exceptionstr:
            self.task_remove_package(taskdata, None, True) #Remove profile's files/folders on failure
            raise ICEModuleException(_("Failed to install {0}: {1} was encountered when writing the last updated date").format(taskdata["packagename"], exceptionstr))
        
        #Write default browser value to be used for the update process
        try:
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-default-browser" % taskdata["packagename"], 'w') as fp:
                fp.write(taskdata["source"]) # Used by module during updating to determine your browser
        except Exception as exceptionstr:
            self.task_remove_package(taskdata, None, True) #Remove profile's files/folders on failure
            raise ICEModuleException(_("Failed to install {0}: {1} was encountered when setting the browser you selected").format(taskdata["packagename"], exceptionstr))
        
        progress_callback(60)
        
        
        #Write profile
        try:
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/Default/Preferences" % taskdata["packagename"], 'w') as fp:
                fp.write(json.dumps(profiletomake, separators=(',', ':'))) # This dumps minified json (how convenient), which is EXACTLY what Chrome uses for Preferences, so it's literally pre-readied
        except Exception as exceptionstr:
            self.task_remove_package(taskdata, None, True) #Remove profile's files/folders on failure
            raise ICEModuleException(_("Failed to install {0}: {1} was encountered when writing the Chromium-based profile").format(taskdata["packagename"], exceptionstr))
        
        #Write Local State
        try:
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/Local State" % taskdata["packagename"], 'w') as fp:
                with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/Local State", 'r') as fp2:
                    fp.write(json.dumps(json.loads(fp2.read()), separators=(',', ':')))
        except Exception as exceptionstr:
            self.task_remove_package(taskdata, None, True) #Remove profile's files/folders on failure
            raise ICEModuleException(_("Failed to install {0}: {1} was encountered when writing the Chromium-based profile").format(taskdata["packagename"], exceptionstr))
        
        
        
        #Write bookmarks
        try:
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/Default/Bookmarks" % taskdata["packagename"], 'w') as fp:
                pass
        except Exception as exceptionstr:
            self.task_remove_package(taskdata, None, True) #Remove profile's files/folders on failure
            raise ICEModuleException(_("Failed to install {0}: {1} was encountered when writing the Bookmarks file").format(taskdata["packagename"], exceptionstr))
            
            
        progress_callback(72)            
            
            
        try:
            with open(os.path.expanduser("~") + "/.local/share/applications/%s.desktop" % windowclassid, 'w') as fp:
                # I mean, this needs no explanation, it's a .desktop file
                fp.write("[Desktop Entry]\n")
                fp.write("Version=1.0\n")
                fp.write("Name={0}\n".format(icepackageinfo["realname"]))
                fp.write("Comment={0}\n".format(_("Website (obtained from Store)")))
                
                fp.write("Exec=/usr/bin/feren-storium-icelaunch {0} {1} {2} {3}\n".format(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s" % taskdata["packagename"], taskdata["source"], '"' + icepackageinfo["website"] + '"', windowclassid))

                fp.write("Terminal=false\n")
                fp.write("X-MultipleArgs=false\n")
                fp.write("Type=Application\n")
                
                if usefallbackicon == True:
                    fp.write("Icon=text-html\n")
                else:
                    fp.write("Icon={0}\n".format(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/icon" % taskdata["packagename"]))

                #Ice stuff will have their own categories to allow for easier sectioning of items in Store overall
                if icepackageinfo["category"] == "ice-accessories":
                    location = "Utility;"
                elif icepackageinfo["category"] == "ice-games":
                    location = "Game;"
                elif icepackageinfo["category"] == "ice-graphics":
                    location = "Graphics;"
                elif icepackageinfo["category"] == "ice-internet":
                    location = "Network;"
                elif icepackageinfo["category"] == "ice-office":
                    location = "Office;"
                elif icepackageinfo["category"] == "ice-programming":
                    location = "Development;"
                elif icepackageinfo["category"] == "ice-multimedia":
                    location = "AudioVideo;"
                elif icepackageinfo["category"] == "ice-system":
                    location = "System;"
                
                fp.write("Categories=GTK;Qt;{0}\n".format(location))
                fp.write("MimeType=text/html;text/xml;application/xhtml_xml;\n")

                fp.write("Keywords=%s\n" % icepackageinfo["keywords"])

                fp.write("StartupWMClass=%s\n" % windowclassid)
                fp.write("StartupNotify=true\n")
        except Exception as exceptionstr:
            self.task_remove_package(taskdata, None, True) #Remove profile's files/folders on failure
            raise ICEModuleException(_("Failed to install {0}: {1} was encountered when creating a shortcut in the Applications Menu").format(taskdata["packagename"], exceptionstr))
        
        
        #Write Extra IDs to be used as a backup
        try:
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-extra-ids" % taskdata["packagename"], 'w') as fp:
                fp.write(str(iceextrasids)) # This means that Storium can manage extras later on in time
        except Exception as exceptionstr:
            self.task_remove_package(taskdata, None, True) #Remove profile's files/folders on failure
            raise ICEModuleException(_("Failed to install {0}: {1} was encountered when making a note of the SSB's extra shortcuts").format(taskdata["packagename"], exceptionstr))
        
        #Now repeat for extras, if appropriate
        extrascount = 0 #Classic strat for iteration
        if iceextrasids != []:
            import urllib.request #Grabbing files from internet
            import urllib.error
        for extraid in iceextrasids:
            try:
                with open(os.path.expanduser("~") + "/.local/share/applications/{0}-{1}.desktop".format(taskdata["packagename"], extraid), 'w') as fp:
                    # I mean, this needs no explanation, it's a .desktop file
                    fp.write("[Desktop Entry]\n")
                    fp.write("Version=1.0\n")
                    fp.write("Name={0}\n".format(icepackageinfo["realnameextras"][extrascount]))
                    fp.write("Comment={0}\n".format(_("Website (part of %s)" % icepackageinfo["realname"])))
                    
                    fp.write("Exec=/usr/bin/feren-storium-icelaunch {0} {1} {2} {3}\n".format(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s" % taskdata["packagename"], taskdata["source"], '"' + icepackageinfo["websiteextras"][extrascount] + '"', windowclassid))

                    fp.write("Terminal=false\n")
                    fp.write("X-MultipleArgs=false\n")
                    fp.write("Type=Application\n")
                    
                    try:
                        urllib.request.urlretrieve(icepackageinfo["iconuriextras"][extrascount], (os.path.expanduser("~") + "/.local/share/feren-storium-ice/{0}/icon-{1}".format(taskdata["packagename"], extraid)))
                        fp.write("Icon=%s\n" % (os.path.expanduser("~") + "/.local/share/feren-storium-ice/{0}/icon-{1}".format(taskdata["packagename"], extraid)))
                    except:
                        fp.write("Icon=text-html\n")

                    if icepackageinfo["category"] == "ice-accessories":
                        location = "Utility;"
                    elif icepackageinfo["category"] == "ice-games":
                        location = "Game;"
                    elif icepackageinfo["category"] == "ice-graphics":
                        location = "Graphics;"
                    elif icepackageinfo["category"] == "ice-internet":
                        location = "Network;"
                    elif icepackageinfo["category"] == "ice-office":
                        location = "Office;"
                    elif icepackageinfo["category"] == "ice-programming":
                        location = "Development;"
                    elif icepackageinfo["category"] == "ice-multimedia":
                        location = "AudioVideo;"
                    elif icepackageinfo["category"] == "ice-system":
                        location = "System;"
                    
                    fp.write("Categories=GTK;Qt;{0}\n".format(location))
                    fp.write("MimeType=text/html;text/xml;application/xhtml_xml;\n")

                    fp.write("Keywords=%s\n" % icepackageinfo["keywordsextras"][extrascount])

                    fp.write("StartupNotify=true\n")
            except Exception as exceptionstr:
                self.task_remove_package(taskdata, None, True) #Remove profile's files/folders on failure
                raise ICEModuleException(_("Failed to install {0}: {1} was encountered when creating extra shortcuts in the Applications Menu").format(taskdata["packagename"], exceptionstr))
            os.system("chmod +x " + os.path.expanduser("~") + "/.local/share/applications/{0}-{1}.desktop".format(taskdata["packagename"], extraid))
            extrascount += 1
            
        progress_callback(99)
        
        #Otherwise they'll refuse to launch from the Applications Menu (bug seen in Mint's own Ice code fork)
        os.system("chmod +x " + os.path.expanduser("~") + "/.local/share/applications/%s.desktop" % windowclassid)
            
        progress_callback(100)
        
        return True
    
    
    def task_remove_package(self, taskdata, progress_callback, forinstall=False):
        if os.path.isfile(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-active-pid" % taskdata["packagename"]):
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-active-pid" % taskdata["packagename"], 'r') as pidfile:
                currentpid = pidfile.readline()
                try:
                    currentpid = int(currentpid)
                    os.kill(currentpid, signal.SIGKILL) #Kill the process immediately, so we can remove it
                    time.sleep(0.4) #Should give enough time for everything to clear out process-wise
                except:
                    pass
        
        if not forinstall: # We call this in the install process to clear out partial installs, so for those times we want to skip THIS code to not confuse Store's Brain or anything that could get confused from this module 'unlocking' temporarily
            self.packagemgmtbusy = True
            self.currentpackagename = taskdata["packagename"]
        
        icepackageinfo = taskdata["pkginfo"]
        if "extrasids" in icepackageinfo:
            iceextrasids = icepackageinfo["extrasids"]
        else:
            iceextrasids = []
        
        #Delete the files and the folders and done
        if os.path.isfile(os.path.expanduser("~") + "/.local/share/color-schemes/%s.colors" % taskdata["packagename"]):
            try:
                os.remove(os.path.expanduser("~") + "/.local/share/color-schemes/%s.colors" % taskdata["packagename"])
                #TODO: Remove window rule
            except Exception as exceptionstr:
                if not forinstall:
                    raise ICEModuleException(_("Failed to uninstall {0}: {1} was encountered when removing the colour scheme").format(taskdata["packagename"], exceptionstr))
            #os.system("qdbus org.kde.KWin /KWin reconfigure")
        
        
        
        
        try:
            if os.path.isfile(os.path.expanduser("~") + "/.local/share/applications/%s.desktop" % taskdata["packagename"]):
                os.remove(os.path.expanduser("~") + "/.local/share/applications/%s.desktop" % taskdata["packagename"])
            if os.path.isfile(os.path.expanduser("~") + "/.local/share/applications/vivaldi-%s.desktop" % taskdata["packagename"]):
                os.remove(os.path.expanduser("~") + "/.local/share/applications/vivaldi-%s.desktop" % taskdata["packagename"])
        except Exception as exceptionstr:
            if not forinstall:
                raise ICEModuleException(_("Failed to uninstall {0}: {1} was encountered when removing the shortcut from the Applications Menu").format(taskdata["packagename"], exceptionstr))
        
        #Now repeat for extras, if appropriate
        extrascount = 0 #Classic strat for iteration
        for extraid in iceextrasids:
            try:
                if os.path.isfile(os.path.expanduser("~") + "/.local/share/applications/{0}-{1}.desktop".format(taskdata["packagename"], extraid)):
                    os.remove(os.path.expanduser("~") + "/.local/share/applications/{0}-{1}.desktop".format(taskdata["packagename"], extraid))
            except Exception as exceptionstr:
                self.task_remove_package(taskdata, None, True) #Remove profile's files/folders on failure
                raise ICEModuleException(_("Failed to uninstall {0}: {1} was encountered when removing extra shortcuts from the Applications Menu").format(taskdata["packagename"], exceptionstr))
            extrascount += 1
            
        if not forinstall:
            progress_callback(50)
        
        try:
            shutil.rmtree(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s" % taskdata["packagename"])
        except Exception as exceptionstr:
            if not forinstall:
                raise ICEModuleException(_("Failed to uninstall {0}: {1} was encountered when deleting the Chromium-based profile").format(taskdata["packagename"], exceptionstr))
        
        if not forinstall:
            progress_callback(100)
        
        return True
    
    
    def task_update_package(self, taskdata, progress_callback):
        
        #Update package and return exit code
        self.packagemgmtbusy = True
        self.currentpackagename = taskdata["packagename"]
        
        windowclassid = taskdata["packagename"]
        if taskdata["source"] == "vivaldi": #FIXME: Temporary until Vivaldi adds proper shadows support
            windowclassid = "vivaldi-" + taskdata["packagename"]
            try:
                if os.path.isfile(os.path.expanduser("~") + "/.local/share/applications/%s.desktop" % taskdata["packagename"]):
                    os.remove(os.path.expanduser("~") + "/.local/share/applications/%s.desktop" % taskdata["packagename"])
            except Exception as exceptionstr:
                raise ICEModuleException(_("Failed to update {0}: {1} was encountered when switching the shortcut in the Applications Menu").format(taskdata["packagename"], exceptionstr))
        else:
            try:
                if os.path.isfile(os.path.expanduser("~") + "/.local/share/applications/vivaldi-%s.desktop" % taskdata["packagename"]):
                    os.remove(os.path.expanduser("~") + "/.local/share/applications/vivaldi-%s.desktop" % taskdata["packagename"])
            except Exception as exceptionstr:
                raise ICEModuleException(_("Failed to update {0}: {1} was encountered when switching the shortcut in the Applications Menu").format(taskdata["packagename"], exceptionstr))
        
        icepackageinfo = taskdata["pkginfo"]
        if "extrasids" in icepackageinfo:
            iceextrasids = icepackageinfo["extrasids"]
        else:
            iceextrasids = []
        
        if os.path.isfile(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-active-pid" % taskdata["packagename"]):
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-active-pid" % taskdata["packagename"], 'r') as pidfile:
                currentpid = pidfile.readline()
            pidisrunning = False
            try:
                currentpid = int(currentpid)
                try:
                    os.kill(currentpid, 0) #Send a You There? to the PID identified
                    pidisrunning = True #If we didn't just cause an exception by doing that, the PID exists
                except:
                    pass
            except:
                try:
                    os.kill(currentpid, signal.SIGTERM) #Fallback since we don't know if it's running or not
                    time.sleep(0.4)
                except:
                    pass
            if pidisrunning == True:
                raise ICEModuleException(_("Failed to update {0}: Running Website Applications cannot be updated until they are closed").format(taskdata["packagename"]))
        
        #Create the .desktop file's home if it doesn't exist
        if not os.path.isdir(os.path.expanduser("~") + "/.local/share/applications"):
            try:
                os.mkdir(os.path.expanduser("~") + "/.local/share/applications")
            except Exception as exceptionstr:
                raise ICEModuleException(_("Failed to update {0}: {1} was encountered when trying to create the shortcut's location").format(taskdata["packagename"], exceptionstr))
        
        
        #Titlebar branding
        #if "icecolor" in icepackageinfo:
            #self.color_scheme_iding(icepackageinfo["icecolor"], taskdata, icepackageinfo["icecolorhighlight"])
            #os.system("qdbus org.kde.KWin /KWin reconfigure")
            
            
        progress_callback(12)
            
        #Get some data from the files
        #if os.path.isfile(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-default-browser" % taskdata["packagename"]):
            #with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-default-browser" % taskdata["packagename"], 'r') as fp:
                #currenticebrowser = fp.readline()
        #else:
            #currenticebrowser = taskdata["source"] #Fallback
        #TODO: Move above to determining current subsource
        if os.path.isfile(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-extra-ids" % taskdata["packagename"]):
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-extra-ids" % taskdata["packagename"], 'r') as fp:
                currenticeextraids = ast.literal_eval(fp.readline())
        else:
            currenticeextraids = [] #Fallback
        if os.path.isfile(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-bonuses" % taskdata["packagename"]):
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-bonuses" % taskdata["packagename"], 'r') as fp:
                currenticebonuses = ast.literal_eval(fp.readline())
        else:
            currenticebonuses = [] #Fallback
        if "bonuses" in taskdata:
            currenticebonuses.extend(taskdata["bonuses"])
            
            
        progress_callback(24)
            
        try:
            if not os.path.isfile(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/First Run" % taskdata["packagename"]):
                with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/First Run" % taskdata["packagename"], 'w') as fp:
                    pass
        except Exception as exceptionstr:
            raise ICEModuleException(_("Failed to update {0}: {1} was encountered when updating the Chromium-based profile").format(taskdata["packagename"], exceptionstr))
        try:
            if not os.path.isdir(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/Default" % taskdata["packagename"]):
                os.mkdir(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/Default" % taskdata["packagename"])
        except Exception as exceptionstr:
            raise ICEModuleException(_("Failed to update {0}: {1} was encountered when updating the Chromium-based profile").format(taskdata["packagename"], exceptionstr))
        
        progress_callback(36)
            
        
        usefallbackicon = False
        #Copy icon for package
        try:
            if os.path.isfile(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/icon" % taskdata["packagename"]):
                os.remove(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/icon" % taskdata["packagename"])
        except Exception as exceptionstr:
            raise ICEModuleException(_("Failed to update {0}: {1} was encountered when updating the application icon").format(taskdata["packagename"], exceptionstr))
        try:
            shutil.copy(self.storebrain.tempdir + "/icons/" + taskdata["packagename"], os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/icon" % taskdata["packagename"])
        except Exception as exceptionstr:
            usefallbackicon = True
            
            
        progress_callback(48)
            
        
        
        #Now to update the JSON file
        with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/Preferences", 'r') as fp:
            profiledefaults = json.loads(fp.read())
            
        try:
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/Default/Preferences" % taskdata["packagename"], 'r') as fp:
                profiletoupdate = json.loads(fp.read())
        except Exception as exceptionstr:
            raise ICEModuleException(_("Failed to update {0}: {1} was encountered when reading the browser profile (is the profile corrupt?)").format(taskdata["packagename"], exceptionstr))
        
        #Remove the custom links (Chromiums) before adding default shortcut back in and updating it again
        profiletoupdate["custom_links"] = {}
        
        profiletoupdate = self.storebrain.dict_recurupdate(profiletoupdate, profiledefaults)
        
        
        #Update extensions permissions too
        with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/and-plasmaintegration", 'r') as fp:
            profiletoupdateextra = json.loads(fp.read())
            for item in profiletoupdateextra["extensions"]["settings"]:
                if item in profiletoupdate["extensions"]["settings"]:
                    profiletoupdateextra["extensions"]["settings"][item].pop("path", None)
                    profiletoupdateextra["extensions"]["settings"][item]["manifest"].pop("name", None)
                    profiletoupdateextra["extensions"]["settings"][item]["manifest"].pop("version", None) #Prevent the extension version and name from reverting
        profiletoupdate = self.storebrain.dict_recurupdate(profiletoupdate, profiletoupdateextra)
        if "nekocap" in currenticebonuses:
            with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/and-nekocap", 'r') as fp:
                profiletoupdateextra = json.loads(fp.read()) #This is how you make json.load work with file paths, I guess
                for item in profiletoupdateextra["extensions"]["settings"]:
                    if item in profiletoupdate["extensions"]["settings"]:
                        profiletoupdateextra["extensions"]["settings"][item].pop("path", None)
                        profiletoupdateextra["extensions"]["settings"][item]["manifest"].pop("name", None)
                        profiletoupdateextra["extensions"]["settings"][item]["manifest"].pop("version", None)
            profiletoupdate = self.storebrain.dict_recurupdate(profiletoupdate, profiletoupdateextra)
        if "ublock" in currenticebonuses:
            with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/and-ublock", 'r') as fp:
                profiletoupdateextra = json.loads(fp.read())
                for item in profiletoupdateextra["extensions"]["settings"]:
                    if item in profiletoupdate["extensions"]["settings"]:
                        profiletoupdateextra["extensions"]["settings"][item].pop("path", None)
                        profiletoupdateextra["extensions"]["settings"][item]["manifest"].pop("name", None)
                        profiletoupdateextra["extensions"]["settings"][item]["manifest"].pop("version", None)
            profiletoupdate = self.storebrain.dict_recurupdate(profiletoupdate, profiletoupdateextra)
        if "darkreader" in currenticebonuses:
            with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/and-darkreader", 'r') as fp:
                profiletoupdateextra = json.loads(fp.read())
                for item in profiletoupdateextra["extensions"]["settings"]:
                    if item in profiletoupdate["extensions"]["settings"]:
                        profiletoupdateextra["extensions"]["settings"][item].pop("path", None)
                        profiletoupdateextra["extensions"]["settings"][item]["manifest"].pop("name", None)
                        profiletoupdateextra["extensions"]["settings"][item]["manifest"].pop("version", None)
            profiletoupdate = self.storebrain.dict_recurupdate(profiletoupdate, profiletoupdateextra)
        if "imagus" in currenticebonuses:
            with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/and-imagus", 'r') as fp:
                profiletoupdateextra = json.loads(fp.read())
                for item in profiletoupdateextra["extensions"]["settings"]:
                    if item in profiletoupdate["extensions"]["settings"]:
                        profiletoupdateextra["extensions"]["settings"][item].pop("path", None)
                        profiletoupdateextra["extensions"]["settings"][item]["manifest"].pop("name", None)
                        profiletoupdateextra["extensions"]["settings"][item]["manifest"].pop("version", None)
            profiletoupdate = self.storebrain.dict_recurupdate(profiletoupdate, profiletoupdateextra)
        if "googleytdislikes" in currenticebonuses:
            with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/and-googleytdislikes", 'r') as fp:
                profiletoupdateextra = json.loads(fp.read())
                for item in profiletoupdateextra["extensions"]["settings"]:
                    if item in profiletoupdate["extensions"]["settings"]:
                        profiletoupdateextra["extensions"]["settings"][item].pop("path", None)
                        profiletoupdateextra["extensions"]["settings"][item]["manifest"].pop("name", None)
                        profiletoupdateextra["extensions"]["settings"][item]["manifest"].pop("version", None)
            profiletoupdate = self.storebrain.dict_recurupdate(profiletoupdate, profiletoupdateextra)
        
        
        #Extra site-specific tweaks
        profiletoupdate["homepage"] = icepackageinfo["website"]
        profiletoupdate["custom_links"]["list"][0]["title"] = icepackageinfo["realname"]
        profiletoupdate["custom_links"]["list"][0]["url"] = icepackageinfo["website"]
        profiletoupdate["session"]["startup_urls"] = [icepackageinfo["website"]]
        profiletoupdate["download"]["default_directory"] = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD) + "/" + _("{0} Downloads").format(icepackageinfo["realname"])
        profiletoupdate["profile"]["name"] = _("Ice - {0}").format(icepackageinfo["realname"])
        profiletoupdate["ntp"]["custom_background_dict"]["attribution_line_1"] = _("Feren OS Ice Website Application - {0}").format(icepackageinfo["realname"])
        profiletoupdate["vivaldi"]["tabs"]["new_page"]["custom_url"] = "https://feren-os.github.io/start-page/ice?ice-text="+(_("Feren OS Ice Website Application - {0}").format(icepackageinfo["realname"]))+"&home-url={0}".format(parse.quote(icepackageinfo["website"], safe=""))+"&home-icon={0}".format(parse.quote(icepackageinfo["iconuri"], safe=""))
        profiletoupdate["vivaldi"]["homepage"] = icepackageinfo["website"]
        profiletoupdate["vivaldi"]["homepage_cache"] = icepackageinfo["website"]
        
        
        #Update these as well
        if "icegoogleinteg" in icepackageinfo and icepackageinfo["icegoogleinteg"] == True:
            pass
        else:
            with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/disable-google", 'r') as fp:
                profiletoupdateextra = json.loads(fp.read())
            profiletoupdate = self.storebrain.dict_recurupdate(profiletoupdate, profiletoupdateextra)
        if "icegooglehangouts" in icepackageinfo and icepackageinfo["icegooglehangouts"] == True:
            profiletoupdate["vivaldi"]["privacy"]["google_component_extensions"]["hangout_services"] = True
        else:
            profiletoupdate["vivaldi"]["privacy"]["google_component_extensions"]["hangout_services"] = False
        
        if "icenohistory" in icepackageinfo and icepackageinfo["icenohistory"] == True:
            with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/disable-browsehistory", 'r') as fp:
                profiletoupdateextra = json.loads(fp.read())
                profiletoupdate = self.storebrain.dict_recurupdate(profiletoupdate, profiletoupdateextra)
            
            try:
                with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-nohistory" % taskdata["packagename"], 'w') as fp:
                    pass
            except Exception as exceptionstr:
                raise ICEModuleException(_("Failed to install {0}: {1} was encountered when setting up automatic history deletion").format(taskdata["packagename"], exceptionstr))
            
        #Background Sync, Clipboard, Notifications and Payment Handler ONLY for SSB's websites
        for permtype in ["ar", "autoplay", "automatic_downloads", "background_sync", "clipboard", "file_handling", "font_access", "midi_sysex", "notifications", "payment_handler", "sensors", "sound", "sleeping-tabs", "window_placement", "vr"]:
            profiletoupdate["profile"]["content_settings"]["exceptions"][permtype] = {}
            if "icedomain" in icepackageinfo:
                try:
                    shortenedurl = icepackageinfo["icedomain"].split("://")[1:]
                    shortenedurl = ''.join(shortenedurl)
                except:
                    shortenedurl = icepackageinfo["icedomain"]
            else:
                try:
                    shortenedurl = icepackageinfo["website"].split("://")[1:]
                    shortenedurl = ''.join(shortenedurl)
                except:
                    shortenedurl = icepackageinfo["website"]
            try:
                shortenedurl = shortenedurl.split("/")[0]
            except:
                pass
            profiletoupdate["profile"]["content_settings"]["exceptions"][permtype]["[*.]"+shortenedurl+",*"] = {"expiration": "0", "model": 0, "setting": 1}
            profiletoupdate["profile"]["content_settings"]["exceptions"][permtype][shortenedurl+",*"] = {"expiration": "0", "model": 0, "setting": 1}
            #Repeat for extra shortcuts' URLs
            extrascount = 0
            for extraid in iceextrasids:
                try:
                    shortenedurl = icepackageinfo["websiteextras"][extrascount].split("://")[1:]
                    shortenedurl = ''.join(shortenedurl)
                except:
                    shortenedurl = icepackageinfo["websiteextras"][extrascount]
                try:
                    shortenedurl = shortenedurl.split("/")[0]
                except:
                    pass
                profiletoupdate["profile"]["content_settings"]["exceptions"][permtype]["[*.]"+shortenedurl+",*"] = {"expiration": "0", "model": 0, "setting": 1}
                profiletoupdate["profile"]["content_settings"]["exceptions"][permtype][shortenedurl+",*"] = {"expiration": "0", "model": 0, "setting": 1}
                extrascount += 1
        
        
        #Update Vivaldi colour changes
        #   Vivaldi colour changes
        if "icecolor" in icepackageinfo and "icecolorhighlight" in icepackageinfo and "icecolordark" in icepackageinfo:
            vivaldihighlightcol = icepackageinfo["icecolorhighlight"]
            vivaldihighlightcoldark = self.colourFilter(icepackageinfo["icecolorhighlight"], 0.7, True, True)
            if self.get_are_colours_different(icepackageinfo["icecolor"], icepackageinfo["icecolorhighlight"]) and self.get_colour_bg_suitable(icepackageinfo["icecolor"]): #Suitable background colour used
                vivaldiaccentcol = icepackageinfo["icecolorhighlight"]
                vivaldiaccentcoldark = icepackageinfo["icecolorhighlight"]
                vivaldiwinbgcol = icepackageinfo["icecolor"]
                vivaldiwinbgcoldark = icepackageinfo["icecolordark"]
                vivaldiaccentinchrome = False
                
            else: #Otherwise use fallback colours
                vivaldiaccentcol = icepackageinfo["icecolor"]
                vivaldiwinbgcol = ""
                vivaldiaccentcoldark = self.colourFilter(icepackageinfo["icecolordark"], 0.7, True, True)
                vivaldiwinbgcoldark = ""
                vivaldiaccentinchrome = True
                
                
            #Now to make the Private theme    
            vivaldiaccentcolprivate = self.colourFilter(icepackageinfo["icecolorhighlight"], 46.0, True)
            vivaldiwinbgcolprivate = self.colourFilter(icepackageinfo["icecolorhighlight"], 70.0, True)
            
                
            profiletoupdate["vivaldi"]["themes"]["system"][0]["accentOnWindow"] = vivaldiaccentinchrome
            profiletoupdate["vivaldi"]["themes"]["system"][1]["accentOnWindow"] = vivaldiaccentinchrome
            profiletoupdate["vivaldi"]["themes"]["system"][2]["accentOnWindow"] = False
            profiletoupdate["vivaldi"]["themes"]["system"][0]["colorAccentBg"] = vivaldiaccentcol
            profiletoupdate["vivaldi"]["themes"]["system"][1]["colorAccentBg"] = vivaldiaccentcoldark
            profiletoupdate["vivaldi"]["themes"]["system"][2]["colorAccentBg"] = vivaldiaccentcolprivate
            profiletoupdate["vivaldi"]["themes"]["system"][0]["colorHighlightBg"] = vivaldihighlightcol
            profiletoupdate["vivaldi"]["themes"]["system"][1]["colorHighlightBg"] = vivaldihighlightcoldark
            profiletoupdate["vivaldi"]["themes"]["system"][2]["colorHighlightBg"] = vivaldihighlightcol
            if vivaldiwinbgcol != "":
                if self.get_luminant(vivaldiwinbgcol) == False: #Dark BG (in-Preferences default is Light, so no need for Light BG else)
                    profiletoupdate["vivaldi"]["themes"]["system"][0]["colorFg"] = "#FFFFFF"
                profiletoupdate["vivaldi"]["themes"]["system"][0]["colorBg"] = vivaldiwinbgcol
            if vivaldiwinbgcoldark != "":
                if self.get_luminant(vivaldiwinbgcoldark) == True: #Light BG (in-Preferences default is Dark, so no need for Dark BG else)
                    profiletoupdate["vivaldi"]["themes"]["system"][1]["colorFg"] = "#000000"
                profiletoupdate["vivaldi"]["themes"]["system"][1]["colorBg"] = vivaldiwinbgcoldark
            #Private foreground
            if self.get_luminant(vivaldiwinbgcolprivate) == True: #Light BG (in-Preferences default is Dark, so no need for Dark BG else)
                profiletoupdate["vivaldi"]["themes"]["system"][2]["colorFg"] = "#000000"
            profiletoupdate["vivaldi"]["themes"]["system"][2]["colorBg"] = vivaldiwinbgcolprivate
        
        
        
        #Write last updated date to be used in update checks
        try:
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-last-updated" % taskdata["packagename"], 'w') as fp:
                fp.write(datetime.today().strftime('%Y%m%d'))
        except Exception as exceptionstr:
            raise ICEModuleException(_("Failed to update {0}: {1} was encountered when writing the last updated date").format(taskdata["packagename"], exceptionstr))
        
        #Write default browser value to be used for the update process
        try:
            if not os.path.isfile(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-default-browser" % taskdata["packagename"]):
                with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-default-browser" % taskdata["packagename"], 'w') as fp:
                    fp.write(taskdata["source"]) # Used by module during updating to determine your browser
        except Exception as exceptionstr:
            self.task_remove_package(taskdata, None, True) #Remove profile's files/folders on failure
            raise ICEModuleException(_("Failed to update {0}: {1} was encountered when noting the browser selection value").format(taskdata["packagename"], exceptionstr))
        
        
        #Write profile
        try:
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/Default/Preferences" % taskdata["packagename"], 'w') as fp:
                fp.write(json.dumps(profiletoupdate, separators=(',', ':')))
        except Exception as exceptionstr:
            raise ICEModuleException(_("Failed to update {0}: {1} was encountered when writing the Chromium-based profile").format(taskdata["packagename"], exceptionstr))
            
        
        #Update Local State too
        with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromium-profile/Local State", 'r') as fp:
            profiledefaults = json.loads(fp.read())
        try:
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/Local State" % taskdata["packagename"], 'r') as fp:
                profiletoupdate = json.loads(fp.read())
        except Exception as exceptionstr:
            raise ICEModuleException(_("Failed to update {0}: {1} was encountered when reading the browser's local state (is the local state corrupt?)").format(taskdata["packagename"], exceptionstr))
        try:
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/Local State" % taskdata["packagename"], 'w') as fp:
                fp.write(json.dumps(self.storebrain.dict_recurupdate(profiletoupdate, profiledefaults), separators=(',', ':')))
        except Exception as exceptionstr:
            raise ICEModuleException(_("Failed to update {0}: {1} was encountered when writing the Local State").format(taskdata["packagename"], exceptionstr))
        
            
        progress_callback(72)            
            
            
        try:
            with open(os.path.expanduser("~") + "/.local/share/applications/%s.desktop" % windowclassid, 'w') as fp:
                # I mean, this needs no explanation, it's a .desktop file
                fp.write("[Desktop Entry]\n")
                fp.write("Version=1.0\n")
                fp.write("Name={0}\n".format(icepackageinfo["realname"]))
                fp.write("Comment={0}\n".format(_("Website (obtained from Store)")))
                
                fp.write("Exec=/usr/bin/feren-storium-icelaunch {0} {1} {2} {3}\n".format(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s" % taskdata["packagename"], taskdata["source"], '"' + icepackageinfo["website"] + '"', windowclassid))

                fp.write("Terminal=false\n")
                fp.write("X-MultipleArgs=false\n")
                fp.write("Type=Application\n")
                
                if usefallbackicon == True:
                    fp.write("Icon=text-html\n")
                else:
                    fp.write("Icon={0}\n".format(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/icon" % taskdata["packagename"]))

                #Ice stuff will have their own categories to allow for easier sectioning of items in Store overall
                if icepackageinfo["category"] == "ice-accessories":
                    location = "Utility;"
                elif icepackageinfo["category"] == "ice-games":
                    location = "Game;"
                elif icepackageinfo["category"] == "ice-graphics":
                    location = "Graphics;"
                elif icepackageinfo["category"] == "ice-internet":
                    location = "Network;"
                elif icepackageinfo["category"] == "ice-office":
                    location = "Office;"
                elif icepackageinfo["category"] == "ice-programming":
                    location = "Development;"
                elif icepackageinfo["category"] == "ice-multimedia":
                    location = "AudioVideo;"
                elif icepackageinfo["category"] == "ice-system":
                    location = "System;"
                
                fp.write("Categories=GTK;Qt;{0}\n".format(location))
                fp.write("MimeType=text/html;text/xml;application/xhtml_xml;\n")

                fp.write("Keywords=%s\n" % icepackageinfo["keywords"])

                fp.write("StartupWMClass=%s\n" % windowclassid)
                fp.write("StartupNotify=true\n")
        except Exception as exceptionstr:
            raise ICEModuleException(_("Failed to update {0}: {1} was encountered when updating the shortcut in the Applications Menu").format(taskdata["packagename"], exceptionstr))
        
        
        #Remove old extra shortcuts
        for extraid in currenticeextraids:
            try:
                if os.path.isfile(os.path.expanduser("~") + "/.local/share/applications/{0}-{1}.desktop".format(taskdata["packagename"], extraid)):
                    os.remove(os.path.expanduser("~") + "/.local/share/applications/{0}-{1}.desktop".format(taskdata["packagename"], extraid))
            except Exception as exceptionstr:
                raise ICEModuleException(_("Failed to update {0}: {1} was encountered when removing extra shortcuts to replace with new ones").format(taskdata["packagename"], exceptionstr))
            try:
                if os.path.isfile(os.path.expanduser("~") + "/.local/share/feren-storium-ice/{0}/icon-{1}".format(taskdata["packagename"], extraid)):
                    os.remove(os.path.expanduser("~") + "/.local/share/feren-storium-ice/{0}/icon-{1}".format(taskdata["packagename"], extraid))
            except Exception as exceptionstr:
                raise ICEModuleException(_("Failed to update {0}: {1} was encountered when removing extra icons to replace with new ones").format(taskdata["packagename"], exceptionstr))
        
        #Write the new Extra IDs to be used as a backup
        try:
            with open(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s/.storium-extra-ids" % taskdata["packagename"], 'w') as fp:
                fp.write(str(iceextrasids)) # This means that Storium can manage extras later on in time
        except Exception as exceptionstr:
            raise ICEModuleException(_("Failed to update {0}: {1} was encountered when making a note of the SSB's extra shortcuts").format(taskdata["packagename"], exceptionstr))
        
        #Now repeat for extras, if appropriate
        extrascount = 0 #Classic strat for iteration
        if iceextrasids != []:
            import urllib.request #Grabbing files from internet
            import urllib.error
        for extraid in iceextrasids:
            try:
                with open(os.path.expanduser("~") + "/.local/share/applications/{0}-{1}.desktop".format(taskdata["packagename"], extraid), 'w') as fp:
                    # I mean, this needs no explanation, it's a .desktop file
                    fp.write("[Desktop Entry]\n")
                    fp.write("Version=1.0\n")
                    fp.write("Name={0}\n".format(icepackageinfo["realnameextras"][extrascount]))
                    fp.write("Comment={0}\n".format(_("Website (part of %s)" % icepackageinfo["realname"])))
                    
                    fp.write("Exec=/usr/bin/feren-storium-icelaunch {0} {1} {2} {3}\n".format(os.path.expanduser("~") + "/.local/share/feren-storium-ice/%s" % taskdata["packagename"], taskdata["source"], '"' + icepackageinfo["websiteextras"][extrascount] + '"', windowclassid))

                    fp.write("Terminal=false\n")
                    fp.write("X-MultipleArgs=false\n")
                    fp.write("Type=Application\n")
                    
                    try:
                        urllib.request.urlretrieve(icepackageinfo["iconuriextras"][extrascount], (os.path.expanduser("~") + "/.local/share/feren-storium-ice/{0}/icon-{1}".format(taskdata["packagename"], extraid)))
                        fp.write("Icon=%s\n" % (os.path.expanduser("~") + "/.local/share/feren-storium-ice/{0}/icon-{1}".format(taskdata["packagename"], extraid)))
                    except:
                        fp.write("Icon=text-html\n")

                    if icepackageinfo["category"] == "ice-accessories":
                        location = "Utility;"
                    elif icepackageinfo["category"] == "ice-games":
                        location = "Game;"
                    elif icepackageinfo["category"] == "ice-graphics":
                        location = "Graphics;"
                    elif icepackageinfo["category"] == "ice-internet":
                        location = "Network;"
                    elif icepackageinfo["category"] == "ice-office":
                        location = "Office;"
                    elif icepackageinfo["category"] == "ice-programming":
                        location = "Development;"
                    elif icepackageinfo["category"] == "ice-multimedia":
                        location = "AudioVideo;"
                    elif icepackageinfo["category"] == "ice-system":
                        location = "System;"
                    
                    fp.write("Categories=GTK;Qt;{0}\n".format(location))
                    fp.write("MimeType=text/html;text/xml;application/xhtml_xml;\n")

                    fp.write("Keywords=%s\n" % icepackageinfo["keywordsextras"][extrascount])

                    fp.write("StartupNotify=true\n")
            except Exception as exceptionstr:
                raise ICEModuleException(_("Failed to update {0}: {1} was encountered when updating extra shortcuts in the Applications Menu").format(taskdata["packagename"], exceptionstr))
            os.system("chmod +x " + os.path.expanduser("~") + "/.local/share/applications/{0}-{1}.desktop".format(taskdata["packagename"], extraid))
            extrascount += 1
            
        progress_callback(99)
        
        #Otherwise they'll refuse to launch from the Applications Menu (bug seen in Mint's own Ice code fork)
        os.system("chmod +x " + os.path.expanduser("~") + "/.local/share/applications/%s.desktop" % windowclassid)
            
        progress_callback(100)
        
        return True
    
    
    def get_package_changes(self, pkgsinstalled, pkgsupdated, pkgsremoved):
        #Examine the package changes - pkgsinstalled, pkgsupdated and pkgsremoved are lists
        # Just skip it by having empty returns since Ice is exempt
        return [], [], []
    
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
        raise ICEModuleException(_("You cannot manage sources when the 'sources' are just web browsers."))
    
    def disable_appsource(self, appsource):
        #You SHOULD NOT be able to manage Application Sources for websites anyway, so raise an error
        raise ICEModuleException(_("You cannot manage sources when the 'sources' are just web browsers."))

if __name__ == "__main__":
    module = PackageMgmtModule()
