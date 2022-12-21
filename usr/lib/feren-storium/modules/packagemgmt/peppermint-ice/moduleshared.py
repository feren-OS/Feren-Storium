import configparser
import os
import subprocess
import gettext
import gi


#Dependencies
import json
import locale
import shutil
from datetime import datetime
import ast
import signal
import time
from gi.repository import GLib
import colorsys
from urllib import parse
import collections.abc
from threading import Thread
gettext.install("feren-storium-ice-shared", "/usr/share/locale", names="ngettext")


#Developer options
applications_directory = os.path.expanduser("~") + "/.local/share/applications"
default_ice_directory = os.path.expanduser("~") + "/.local/share/feren-storium-ice"
icevivaldiprefix = "vivaldistoriumice:"


class ICEModuleSharedException(Exception): # Name this according to the module to allow easier debugging
    pass


class main():
    #### Useful callbacks
    def dict_recurupdate(self, d, u): # I'm sure it's a recursive dictionary updater function, from what I can read of this function
        for k, v in u.items():
            if isinstance(v, collections.abc.Mapping):
                d[k] = self.dict_recurupdate(d.get(k, {}), v)
            else:
                d[k] = v
        return d
    
    def get_shortened_url(self, website):
        shortenedurl = website.split("://")[1:] #Remove the HTTPS portion
        shortenedurl = ''.join(shortenedurl) #Rejoin list into string
        try:
            shortenedurl = shortenedurl.split("/")[0] #Shorten to just domain
        except:
            pass
        return shortenedurl

    def boolean_to_jsonbool(self, boole):
        if boole == True:
            return "true"
        else:
            return "false"
    
    #### Initialisation and memory refreshing
    def __init__(self):
        gettext.install("feren-storium-ice", "/usr/share/locale", names="ngettext")
        self.refresh_memory()

    def refresh_memory(self): # Function to refresh some memory values
        self.json_storage = {}

        for i in ["package-info/peppermint-ice"]:
            with open("/usr/share/feren-storium/curated/" + i + "/data.json", 'r') as fp:
                self.json_storage[i] = json.loads(fp.read())
            if os.path.isfile("/usr/share/feren-storium/curated/" + locale.getlocale()[0] + "/" + i + "/data.json"):
                with open("/usr/share/feren-storium/curated/" + locale.getlocale()[0] + "/" + i + "/data.json", 'r') as fp: #Also overwrite with language-specifics if they exist
                    self.json_storage[i] = self.dict_recurupdate(self.json_storage[i], json.loads(fp.read()))


        with open("/usr/share/feren-storium/curated/package-sources-info/peppermint-ice/data.json", 'r') as fp:
            self.sources_storage = json.loads(fp.read())
        if os.path.isfile("/usr/share/feren-storium/curated/" + locale.getlocale()[0] + "/package-sources-info/peppermint-ice/data.json"):
            with open("/usr/share/feren-storium/curated/" + locale.getlocale()[0] + "/package-sources-info/peppermint-ice/data.json", 'r') as fp: #Also overwrite with language-specifics if they exist
                self.sources_storage = self.dict_recurupdate(self.sources_storage, json.loads(fp.read()))


    #### ITEM INFORMATION
    def getInfo(self, itemid, sourceid, subsourceid):
        result = {}
        #Get information on a package using the JSON data
        try:
            result = self.json_storage["package-info/peppermint-ice"][itemid]
            result["iconlocal"] = ""
            if not "shortdescription" in result:
                result["shortdescription"] = _("Website Application")
            #Fallback defaults for browser options
            if not "icenohistory" in result:
                result["icenohistory"] = False
            if not "icegoogleinteg" in result:
                result["icegoogleinteg"] = False
            if not "icegooglehangouts" in result:
                result["icegooglehangouts"] = False
            if not "iceaccentwindow" in result:
                result["iceaccentwindow"] = True
            return result
        except:
            pass
        raise ICEModuleSharedException(_("%s's information failed to be obtained - perhaps the item doesn't exist on this source?") % itemid)

        
    #### INSPIRE TITLEBAR THEME ADDITIONS
    def inspire_tbar_iding(self, hexcode, windowclass, hexcodehighlight="#006aff"):
        #string, string, string
        
        #TODO: Add IDs for Feren OS Titlebar Theme, to add titlebar branding colours
        #redc, greenc, bluec = tuple(int(hexcode[i:i+2], 16) for i in (1, 3, 5)) #Dodge the # character
        #lumi = colorsys.rgb_to_hls(redc, greenc, bluec)[1]
        #foregroundc = ""
        #if lumi > 127.5:
            #foregroundc = "0,0,0"
        #else:
            #foregroundc = "255,255,255"
        
        #redacc, greenacc, blueacc = tuple(int(hexcodehighlight[i:i+2], 16) for i in (1, 3, 5))
        ##lumiacc = colorsys.rgb_to_hls(redacc, greenacc, blueacc)[1]
        ##foregroundacc = ""
        ##if lumiacc > 127.5:
            ##foregroundacc = "0,0,0"
        ##else:
        #foregroundacc = "255,255,255"
        
        pass
        
        
    #### COLOUR CHECKS
    #Is the color light or dark?
    def get_is_light(self, hexcode):
        #string
        
        #Returns:
        # True: Light
        # False: Dark
        redc, greenc, bluec = tuple(int(hexcode[i:i+2], 16) for i in (1, 3, 5)) #Dodge the # character
        lumi = colorsys.rgb_to_hls(redc, greenc, bluec)[1]
        
        if lumi > 168:
            return True
        else:
            return False
    
    #Apply a brightness filter to a color
    def color_filter(self, hexcode, amount, multiply=False):
        #string, float, bool
        
        #Returns:
        # Darkened/Lightened colour
        redc, greenc, bluec = tuple(int(hexcode[i:i+2], 16) for i in (1, 3, 5)) #Dodge the # character
        hue, lumi, sat = colorsys.rgb_to_hls(redc, greenc, bluec)
        
        if amount < 0.0: #Negative means darkening
            if multiply == True:
                lumi = lumi * (1.0 + amount) #1.0 + -amount, amount is negative, thus it darkens it during multiplication
            else:
                if (lumi + amount) < 0.0:
                    lumi = 0.0
                else:
                    lumi += amount
        else: #Positive means lightening, and 0.0 means no change
            if multiply == True:
                lumi = lumi * (1.0 + amount) #Add 1.0 to the amount to lighten it instead of darkening it during multiplication
            else:
                if (lumi + amount) > 255.0:
                    lumi = 255.0
                else:
                    lumi += amount

        redc, greenc, bluec = colorsys.hls_to_rgb(hue, lumi, sat) #Convert to RGB
        redc, greenc, bluec = int(redc), int(greenc), int(bluec) #Convert back to integers
        return '#%02x%02x%02x' % (redc, greenc, bluec) #Returns conversion to hexcode
    
    #Are colours different enough? (do RGBs of both colors not match one-another within a 20-20 leeway)
    def get_colours_different(self, hexcode1, hexcode2):
        #string, string
        
        #Returns:
        # True: Yes
        # False: No
        red1, green1, blue1 = tuple(int(hexcode1[i:i+2], 16) for i in (1, 3, 5))
        red2, green2, blue2 = tuple(int(hexcode2[i:i+2], 16) for i in (1, 3, 5))
        
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


    #### RUNNING PROFILE
    def run_profile(self, itemid, profileid, browser, browsertype, website, wmclass, nohistory=False, closecallback=None):
        #string, string, string, string, bool
        profiledir = "{0}/{1}/{2}".format(default_ice_directory, itemid, profileid)

        if browser in self.sources_storage["browsers"]:
            commandtorun = self.sources_storage["browsers"][browser]["command"]
            piececount = 0 #for loop right below
            while piececount < len(commandtorun):
                #Translate arguments
                commandtorun[piececount] = commandtorun[piececount].replace(
                    "%WEBSITEURL%", website).replace(
                    "%WINCLASS%", wmclass).replace(
                    "%PROFILEDIR%", profiledir)
                piececount += 1

            ssbproc = subprocess.Popen(commandtorun, close_fds=True)
        else:
            raise ICEModuleSharedException(_("Cannot find information about the specified browser to launch"))

        #Check there's a note about a process having ran, and if so if the process is running
        if os.path.isfile(profiledir + "/.storium-active-pid"):
            with open(profiledir + "/.storium-active-pid", 'r') as pidfile:
                lastpid = pidfile.readline()
            try:
                lastpid = int(lastpid)
                try:
                    os.kill(lastpid, 0) #Send a You There? to the PID identified
                except:
                    os.remove(profiledir + "/.storium-active-pid") #The PID doesn't exist
            except:
                os.remove(profiledir + "/.storium-active-pid")
        #Tell Storium that the process's running (prevents updates while running, and prevents uninstallation leftovers with Storium module)
        if not os.path.isfile(profiledir + "/.storium-active-pid"):
            with open(profiledir + "/.storium-active-pid", 'w') as pidfile:
                pidfile.write(str(ssbproc.pid))

        if nohistory == True:
            if not closecallback == None:
                closecallback()

            #FIXME: We need a better way of doing this.
            time.sleep(16)
            if browsertype == "chromium":
                if os.path.isfile(profiledir + "/Default/History"):
                    os.remove(profiledir + "/Default/History")
                if os.path.isfile(profiledir + "/Default/History-journal"):
                    os.remove(profiledir + "/Default/History-journal")
                if os.path.isdir(profiledir + "/Default/Sessions"):
                    shutil.rmtree(profiledir + "/Default/Sessions")
            elif browsertype == "firefox":
                pass #TODO



    #### INITIAL INSTALLATION
    def get_profiles_folder(self, itemid): #string
        return default_ice_directory + "/%s" % itemid


    def create_profiles_folder(self, itemid):
        #string

        if not os.path.isdir(default_ice_directory): #Make sure the profiles directory even exists
            try:
                os.mkdir(default_ice_directory)
            except Exception as exceptionstr:
                raise ICEModuleException(_("{1} was encountered when trying to create the profiles location")).format(exceptionstr)
        if not os.path.isdir(default_ice_directory + "/%s" % itemid): #Now create the directory for this website application's profiles to go
            try:
                os.mkdir(default_ice_directory + "/%s" % itemid)
            except Exception as exceptionstr:
                raise ICEModuleException(_("{1} was encountered when trying to create the profile's folder")).format(exceptionstr)


    def create_appsmenu_shortcuts(self, itemid, browser, package_information, bonusids):
        #string, string, dict

        windowclassid = itemid
        if browser == "vivaldi": #FIXME: Temporary until Vivaldi adds proper shadows support
            windowclassid = icevivaldiprefix + windowclassid

        with open(applications_directory + "/{0}.desktop".format(windowclassid), 'w') as fp:
            # I mean, this needs no explanation, it's a .desktop file
            fp.write("[Desktop Entry]\n")
            fp.write("Version=1.0\n")
            fp.write("Name={0}\n".format(package_information["realname"]))
            fp.write("Comment={0}\n".format(package_information["shortdescription"]))
            if "iconname" in package_information:
                fp.write("Icon={0}\n".format(package_information["iconname"]))
            else:
                fp.write("Icon=ice\n")

            fp.write("Exec=/usr/bin/feren-storium-ice {0}\n".format('"' + applications_directory + "/{0}.desktop".format(windowclassid) + '"'))

            #Ice stuff will have their own categories to allow for easier sectioning of items in Store overall
            if package_information["category"] == "ice-accessories":
                location = "Utility;"
            elif package_information["category"] == "ice-games":
                location = "Game;"
            elif package_information["category"] == "ice-graphics":
                location = "Graphics;"
            elif package_information["category"] == "ice-internet":
                location = "Network;"
            elif package_information["category"] == "ice-office":
                location = "Office;"
            elif package_information["category"] == "ice-programming":
                location = "Development;"
            elif package_information["category"] == "ice-multimedia":
                location = "AudioVideo;"
            elif package_information["category"] == "ice-system":
                location = "System;"
            fp.write("Categories=GTK;Qt;{0}\n".format(location))

            #fp.write("MimeType=text/html;text/xml;application/xhtml_xml;\n")

            fp.write("Keywords=%s\n" % package_information["keywords"])

            fp.write("Terminal=false\n")
            fp.write("X-MultipleArgs=false\n")
            fp.write("Type=Application\n")
            fp.write("StartupWMClass=%s\n" % windowclassid)
            fp.write("StartupNotify=true\n")

            #Now to write the information for ICE to use
            fp.write("\n")
            fp.write("X-FerenIce-BrowserType=%s\n" % self.sources_storage["browsers"][browser]["type"])
            fp.write("X-FerenIce-Browser=%s\n" % browser)
            fp.write("X-FerenIce-ID=%s\n" % itemid)
            fp.write("X-FerenIce-Website=%s\n" % package_information["icewebsite"])
            fp.write("X-FerenIce-ExtraIDs=%s\n" % package_information["extrasids"])
            fp.write("X-FerenIce-NoHistory=%s\n" % self.boolean_to_jsonbool(package_information["icenohistory"]))
            fp.write("X-FerenIce-Google=%s\n" % self.boolean_to_jsonbool(package_information["icegoogleinteg"]))
            fp.write("X-FerenIce-GoogleHangouts=%s\n" % self.boolean_to_jsonbool(package_information["icegooglehangouts"]))
            fp.write("X-FerenIce-BonusIDs=%s\n" % str(bonusids))
            fp.write("X-FerenIce-BG=%s\n" % package_information["icebackground"])
            fp.write("X-FerenIce-BG-Dark=%s\n" % package_information["icebackground-dark"])
            fp.write("X-FerenIce-Accent=%s\n" % package_information["iceaccent"])
            fp.write("X-FerenIce-Accent-Dark=%s\n" % package_information["iceaccent-dark"])
            fp.write("X-FerenIce-Color=%s\n" % package_information["icecolor"])
            fp.write("X-FerenIce-AccentWindow=%s\n" % self.boolean_to_jsonbool(package_information["iceaccentwindow"]))
            fp.write("X-FerenIce-LastUpdate=%s\n" % package_information["icelastupdated"])


        #Finally, make it executable so it launches fine from the Applications Menu:
        os.system("chmod +x " + applications_directory + "/{0}.desktop".format(windowclassid))

        #Now repeat for the rest of them
        for extraid in package_information["extrasids"]:
            targetid = itemid + "-" + extraid #for reference
            targetidinfo = self.getInfo(targetid, "", "") #no source is given in here, and Ice is 'source-agnostic'

            windowclassid = targetid
            if browser == "vivaldi": #FIXME: Temporary until Vivaldi adds proper shadows support
                windowclassid = icevivaldiprefix + windowclassid

            with open(applications_directory + "/{0}.desktop".format(windowclassid), 'w') as fp:
                # I mean, this needs no explanation, it's a .desktop file
                fp.write("[Desktop Entry]\n")
                fp.write("Version=1.0\n")
                fp.write("Name={0}\n".format(targetidinfo["realname"]))
                fp.write("Comment={0}\n".format(targetidinfo["shortdescription"]))
                if "iconname" in targetidinfo:
                    fp.write("Icon={0}\n".format(targetidinfo["iconname"]))
                else:
                    fp.write("Icon=ice\n")

                fp.write("Exec=/usr/bin/feren-storium-ice {0}\n".format('"' + applications_directory + "/{0}.desktop".format(windowclassid) + '"'))

                #Ice stuff will have their own categories to allow for easier sectioning of items in Store overall
                if targetidinfo["category"] == "ice-accessories":
                    location = "Utility;"
                elif targetidinfo["category"] == "ice-games":
                    location = "Game;"
                elif targetidinfo["category"] == "ice-graphics":
                    location = "Graphics;"
                elif targetidinfo["category"] == "ice-internet":
                    location = "Network;"
                elif targetidinfo["category"] == "ice-office":
                    location = "Office;"
                elif targetidinfo["category"] == "ice-programming":
                    location = "Development;"
                elif targetidinfo["category"] == "ice-multimedia":
                    location = "AudioVideo;"
                elif targetidinfo["category"] == "ice-system":
                    location = "System;"
                fp.write("Categories=GTK;Qt;{0}\n".format(location))

                #fp.write("MimeType=text/html;text/xml;application/xhtml_xml;\n")

                fp.write("Keywords=%s\n" % targetidinfo["keywords"])

                fp.write("Terminal=false\n")
                fp.write("X-MultipleArgs=false\n")
                fp.write("Type=Application\n")
                fp.write("StartupWMClass=%s\n" % windowclassid)
                fp.write("StartupNotify=true\n")

                #Now to write the information for ICE to use
                fp.write("\n")
                fp.write("X-FerenIce-ParentID=%s\n" % targetidinfo["parentitemid"])
                fp.write("X-FerenIce-Website=%s\n" % targetidinfo["icewebsite"])


            #Finally, make it executable so it launches fine from the Applications Menu:
            os.system("chmod +x " + applications_directory + "/{0}.desktop".format(windowclassid))



    ####PROFILE CREATION
    def profileid_generate(self, itemid, profilename):
        result = profilename.replace(" ", "").replace("\\", "").replace("/", "").replace("?", "").replace("*", "").replace("+", "").replace("%", "").lower()

        print("{0}/{1}/{2}".format(default_ice_directory, itemid, result))
        if os.path.isdir("{0}/{1}/{2}".format(default_ice_directory, itemid, result)): #Duplication prevention
            numbertried = 2
            while os.path.isdir("{0}/{1}/{2}{3}".format(default_ice_directory, itemid, result, numbertried)):
                numbertried += 1
            result = result + str(numbertried) #Append duplication prevention number

        return result

    def create_profile_folder(self, itemid, profileid, browsertype):
        if not os.path.isdir(default_ice_directory + "/%s" % itemid): #Make sure profiles directory exists beforehand
            self.create_profiles_folder(itemid)

        if os.path.isdir("{0}/{1}/{2}".format(default_ice_directory, itemid, profileid)): #Fail if profile exists
            raise ICEModuleSharedException(_("Cannot create new profile as %s already exists") % profileid)
        else:
            os.mkdir("{0}/{1}/{2}".format(default_ice_directory, itemid, profileid))

        if browsertype == "chromium": #Chromium-specific profile structure
            os.mkdir("{0}/{1}/{2}/Default".format(default_ice_directory, itemid, profileid))
        elif browsertype == "firefox": #Firefox-specific profile structure
            os.mkdir("{0}/{1}/{2}/chrome".format(default_ice_directory, itemid, profileid))

        #The rest is left up to self.update_profile_settings to do.


    def update_profile_settings(self, iteminfo, profilename, profileid, darkmode):
        if not os.path.isdir(default_ice_directory + "/%s" % iteminfo["id"]): #Make sure profiles directory exists beforehand
            self.create_profiles_folder(iteminfo["id"])
        if iteminfo["browsertype"] == "chromium":
            expectedfolder = "Default"
        elif iteminfo["browsertype"] == "firefox":
            expectedfolder = "chrome"
        if not os.path.isdir("{0}/{1}/{2}/{3}".format(default_ice_directory, iteminfo["id"], profileid, expectedfolder)): #Make sure this profile's directory exists beforehand
            self.create_profile_folder(iteminfo["id"], profileid, iteminfo["browsertype"])

        #Make note of the profile name and last updated configs
        profileconfs = {}
        if os.path.isfile("{0}/{1}/{2}/.ice-settings".format(default_ice_directory, iteminfo["id"], profileid)):
            with open("{0}/{1}/{2}/.ice-settings".format(default_ice_directory, iteminfo["id"], profileid), 'r') as fp:
                profileconfs = json.loads(fp.read())

        #Set user's human-readable name
        profileconfs["readablename"] = profilename

        #Note user's dark-mode preference
        profileconfs["darkmode"] = darkmode

        #Chromium-specific configs
        if iteminfo["browsertype"] == "chromium":
            PreferencesFile = "{0}/{1}/{2}/Default/Preferences".format(default_ice_directory, iteminfo["id"], profileid)

            result = {}
            if os.path.isfile(PreferencesFile): #Load old Preferences into variable if one exists
                with open(PreferencesFile, 'r') as fp:
                    result = json.loads(fp.read())
            with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromiums/Preferences", 'r') as fp: #Also load default preferences, so we can patch
                result = self.dict_recurupdate(result, json.loads(fp.read()))

            #Set important settings unique to each SSB
            result["homepage"] = iteminfo["website"]
            result["custom_links"]["list"][0]["title"] = iteminfo["name"]
            result["custom_links"]["list"][0]["url"] = iteminfo["website"]
            result["session"]["startup_urls"] = [iteminfo["website"]]
            result["download"]["default_directory"] = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD) + "/" + _("{0} Downloads").format(iteminfo["name"])
            result["profile"]["name"] = _("{0} - {1}").format(profilename, iteminfo["name"])
            result["ntp"]["custom_background_dict"]["attribution_line_1"] = _("{0} - {1}").format(profilename, iteminfo["name"])
            result["vivaldi"]["homepage"] = iteminfo["website"]
            result["vivaldi"]["homepage_cache"] = iteminfo["website"]

            #Set permissions for the initial website
            result = self.chromi_set_sitepermissions(result, iteminfo["id"], iteminfo["website"], iteminfo["extraids"])

            #Toggle features for the SSB
            result = self.chromi_set_privacyfeatures(result, iteminfo["nohistory"], iteminfo["googleinteg"], iteminfo["googlehangouts"])

            #Add bonuses to SSB
            result = self.chromi_set_bonuses(result, iteminfo["bonusids"])

            #Add theme colours to SSB (Vivaldi)
            result = self.chromi_set_colors(result, iteminfo["bg"], iteminfo["bgdark"], iteminfo["accent"], iteminfo["accentdark"], iteminfo["color"], iteminfo["accentonwindow"])

            #Add the Start Page Bookmark
            self.chromi_add_startpage(iteminfo["id"], profileid, iteminfo["name"], iteminfo["website"])

            #Save to the Preferences fileonusIDs
            try:
                with open(PreferencesFile, 'w') as fp:
                    fp.write(json.dumps(result, separators=(',', ':'))) # This dumps minified json (how convenient), which is EXACTLY what Chrome uses for Preferences, so it's literally pre-readied
            except Exception as exceptionstr:
                raise ICESharedModuleException(_("Failed to write to Preferences"))

            #Finally, configure Local State
            self.chromi_update_local_state(iteminfo["id"], profileid, darkmode)

            #and finish off with this:
            self.chromi_finishing_touches(iteminfo["id"], profileid)

        #Firefox-specific configs
        elif iteminfo["browsertype"] == "firefox":
            targetfolder = "{0}/{1}/{2}/".format(default_ice_directory, iteminfo["id"], profileid)
            #First, copy config files over
            for cfile in ["handlers.json", "user.js"]:
                shutil.copy("/usr/share/feren-storium/modules/packagemgmt-ice/firefox/" + cfile, targetfolder + cfile)

            #Depending on file existence, either direct-copy or update browser configs
            try:
                if not os.path.isfile(targetfolder + "prefs.js"):
                    shutil.copy("/usr/share/feren-storium/modules/packagemgmt-ice/firefox/prefs.js", targetfolder + "prefs.js")

                with open(targetfolder + "prefs.js", 'r') as fp:
                    result = fp.read().splitlines()
                # else:
                #     with open(targetfolder + "prefs.js", 'r') as fp:
                #         result = fp.read().splitlines()
                #     with open("/usr/share/feren-storium/modules/packagemgmt-ice/firefox/prefs.js", 'r') as fp:
                #         defaultprefs = fp.read().splitlines()
                #     #Now update the prefs
                #     for line in defaultprefs:
                #         if line.startswith("user_pref"):
                #             currentpref = line.split()[0]
                #             prefpresent = False
                #             linescounted = 0
                #             for currline in result:
                #                 if line.startswith(currentpref):
                #                     result[linescounted] = line #Overwrite with default value
                #                     prefpresent = True
                #                     break
                #                 linescounted += 1
                #             if prefpresent == False:
                #                 result.add(line) #Add preference if it isn't present

                linescounted = 0
                for line in result:
                    #Replace certain keywords if they're present in the new configurations
                    result[linescounted] = result[linescounted].replace("WEBSITEHERE", iteminfo["website"]).replace("NAMEHERE", iteminfo["name"])
                    linescounted += 1

                #(over)Write the new prefs.js
                with open(targetfolder + "prefs.js", 'w') as fp:
                    fp.write('\n'.join(result))
            except Exception as exceptionstr:
                raise ICESharedModuleException(_("Failed to write to prefs.js"))

            #Values for user.js: preparation
            if iteminfo["nohistory"] == True:
                nohistory = "true"
            else:
                nohistory = "false"

            #Repeat for user.js, too
            try:
                with open(targetfolder + "user.js", 'r') as fp:
                    result = fp.read().splitlines()
                linescounted = 0
                for line in result:
                    result[linescounted] = result[linescounted].replace("WEBSITEHERE", iteminfo["website"]).replace("NAMEHERE", iteminfo["name"]).replace("CLEARHISTORY", nohistory)
                    linescounted += 1

                with open(targetfolder + "user.js", 'w') as fp:
                    fp.write('\n'.join(result))
            except Exception as exceptionstr:
                raise ICESharedModuleException(_("Failed to write to user.js"))

            #Finish it off by adding UI
            for cfile in ["userContent.css", "userChrome.css", "ferenChrome.css", "ice.css"]:
                shutil.copy("/usr/share/feren-storium/modules/packagemgmt-ice/firefox/chrome/" + cfile, targetfolder + "chrome/" + cfile)

            #...and colourise the UI
            if self.get_is_light(iteminfo["color"]) == True:
                foreground = "black"
            else:
                foreground = "white"

            with open(targetfolder + "chrome/ice.css", 'r') as fp:
                result = fp.read().splitlines()
            linescounted = 0
            for line in result:
                result[linescounted] = result[linescounted].replace("ACCENTBG", iteminfo["color"]).replace("ACCENTFG", foreground)
                linescounted += 1

            with open(targetfolder + "chrome/ice.css", 'w') as fp:
                fp.write('\n'.join(result))

        #If Flatpak, grant access to the profile's directory
        if "flatpak" in self.sources_storage["browsers"][iteminfo["browser"]]:
            os.system("/usr/bin/flatpak override --user {0} --filesystem={1}/{2}/{3}".format(self.sources_storage["browsers"][iteminfo["browser"]]["flatpak"], default_ice_directory, iteminfo["id"], profileid))

        #Finally, save new last updated date and save to .ice-settings
        profileconfs["lastupdated"] = datetime.today().strftime('%Y%m%d')

        try:
            with open("{0}/{1}/{2}/.ice-settings".format(default_ice_directory, iteminfo["id"], profileid), 'w') as fp:
                fp.write(json.dumps(profileconfs, separators=(',', ':')))
        except Exception as exceptionstr:
            raise ICESharedModuleException(_("Failed to write to .ice-settings"))












    #### CHROMIUM PROFILE CREATION
    #Default Settings
    def chromi_set_sitepermissions(self, preferencedict, itemid, ogwebsite, extraids):
        #dict, string, list

        #Set the permissions for default website in this SSB
        shortenedurl = self.get_shortened_url(ogwebsite)
        for permtype in ["ar", "autoplay", "automatic_downloads", "background_sync", "clipboard", "file_handling", "font_access", "midi_sysex", "notifications", "payment_handler", "sensors", "sound", "sleeping-tabs", "window_placement", "vr"]:
            preferencedict["profile"]["content_settings"]["exceptions"][permtype] = {}
            preferencedict["profile"]["content_settings"]["exceptions"][permtype]["[*.]"+shortenedurl+",*"] = {"expiration": "0", "model": 0, "setting": 1}
            preferencedict["profile"]["content_settings"]["exceptions"][permtype][shortenedurl+",*"] = {"expiration": "0", "model": 0, "setting": 1}

        #Set the permissions for extra websites in this SSB
        for extraid in extraids:
            targetid = itemid + "-" + extraid #for reference
            targetidinfo = self.getInfo(targetid, "", "") #no source is given in here, and Ice is 'source-agnostic'

            shortenedurl = self.get_shortened_url(targetidinfo["icewebsite"])
            try:
                shortenedurl = shortenedurl.split("/")[0]
            except:
                pass
            for permtype in ["ar", "autoplay", "automatic_downloads", "background_sync", "clipboard", "file_handling", "font_access", "midi_sysex", "notifications", "payment_handler", "sensors", "sound", "sleeping-tabs", "window_placement", "vr"]:
                preferencedict["profile"]["content_settings"]["exceptions"][permtype]["[*.]"+shortenedurl+",*"] = {"expiration": "0", "model": 0, "setting": 1}
                preferencedict["profile"]["content_settings"]["exceptions"][permtype][shortenedurl+",*"] = {"expiration": "0", "model": 0, "setting": 1}
            
        #Return the modified Preferences
        return preferencedict
    
    #Vivaldi and Brave settings
    def chromi_set_privacyfeatures(self, preferencedict, nohistory=False, allowgooglesignon=False, allowgooglehangouts=False):
        #dict, bool, bool, bool
        
        #First, open the Preferences file
        with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromiums/preferences.json", 'r') as fp:
            preferencesjson = json.loads(fp.read())
                
        if not allowgooglesignon: #Disable Google sign-on if unneeded
            preferencedict = self.dict_recurupdate(preferencedict, preferencesjson["disable-googlesignon"])
        if not allowgooglehangouts: #Disable Google Hangouts if unneeded
            preferencedict = self.dict_recurupdate(preferencedict, preferencesjson["disable-googlehangouts"])
        if nohistory: #Disable History if the SSB provides History itself
            preferencedict = self.dict_recurupdate(preferencedict, preferencesjson["disable-history"])
            
        #Return the modified Preferences
        return preferencedict
            
    #Firefox settings
    def set_ice_privacy_gecko(self, prefsjs, userjs, allowhistory=True):
        #list, list, bool
        
        pass #TODO
    
    #Bonuses
    def chromi_set_bonuses(self, preferencedict, bonuses=[]):
        #dict, list
        
        #First, open the Extras file
        with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromiums/extras.json", 'r') as fp:
            bonusesjson = json.loads(fp.read())
        
        #First, add the bonuses that were chosen
        for item in bonuses:
            if item in bonusesjson:
                #Check that the extension isn't already installed
                for extensionid in bonusesjson[item]["extensions"]["settings"]:
                    if extensionid in preferencedict["extensions"]["settings"]:
                        #If it is, clear out stuff that would uninstall the extra if installed
                        bonusesjson[item]["extensions"]["settings"][extensionid].pop("path", None)
                        bonusesjson[item]["extensions"]["settings"][extensionid]["manifest"].pop("name", None)
                        bonusesjson[item]["extensions"]["settings"][extensionid]["manifest"].pop("version", None)
                #Now that is done, install extra to profile
                preferencedict = self.dict_recurupdate(preferencedict, bonusesjson[item])
        #Second, we remove bonuses no longer selected
        for item in bonusesjson:
            if not item in bonuses:
                for extensionid in bonusesjson[item]["extensions"]["settings"]:
                    preferencedict["extensions"]["settings"].pop(extensionid, None)

        #Now, return the modified Preferences
        return preferencedict
    
    
    #Theme colouring
    def chromi_set_colors(self, preferencedict, bg, bgdark, accent, accentdark, color, accentonwindow):
        #dict, string, string, string, string, string, bool
        
        #TODO: Figure out doing themes for Chrome to colour the windows by their website colours

        #Vivaldi
        bgprivate = self.color_filter(color, -70.0)
        preferencedict["vivaldi"]["themes"]["system"][0]["accentOnWindow"] = accentonwindow
        preferencedict["vivaldi"]["themes"]["system"][1]["accentOnWindow"] = accentonwindow
        preferencedict["vivaldi"]["themes"]["system"][2]["accentOnWindow"] = False
        preferencedict["vivaldi"]["themes"]["system"][0]["colorAccentBg"] = accent
        preferencedict["vivaldi"]["themes"]["system"][1]["colorAccentBg"] = accentdark
        preferencedict["vivaldi"]["themes"]["system"][2]["colorAccentBg"] = self.color_filter(color, -46.0)
        preferencedict["vivaldi"]["themes"]["system"][0]["colorBg"] = bg
        preferencedict["vivaldi"]["themes"]["system"][1]["colorBg"] = bgdark
        preferencedict["vivaldi"]["themes"]["system"][2]["colorBg"] = bgprivate
        preferencedict["vivaldi"]["themes"]["system"][0]["colorHighlightBg"] = color
        preferencedict["vivaldi"]["themes"]["system"][1]["colorHighlightBg"] = color
        preferencedict["vivaldi"]["themes"]["system"][2]["colorHighlightBg"] = color
        #Now set text colours where appropriate
        # Normal foregrounds
        if self.get_is_light(bg) == False: #Dark BG (predefined colour is black so no else)
            preferencedict["vivaldi"]["themes"]["system"][0]["colorFg"] = "#FFFFFF"
        if self.get_is_light(bgdark) == True: #Light BG (predefined colour is white so no else)
            preferencedict["vivaldi"]["themes"]["system"][1]["colorFg"] = "#000000"
        # Private foregrounds
        if self.get_is_light(bgprivate) == True: #Light BG (predefined colour is white so no else)
            preferencedict["vivaldi"]["themes"]["system"][2]["colorFg"] = "#000000"
        
        #Return the modified Preferences
        return preferencedict
    
    def chromi_update_local_state(self, itemid, profileid, darkmode):
        #string, string, bool
        
        LocalStateFile = "{0}/{1}/{2}/Local State".format(default_ice_directory, itemid, profileid)

        result = {}
        if os.path.isfile(LocalStateFile): #Load old Preferences into variable if one exists
            with open(LocalStateFile, 'r') as fp:
                result = json.loads(fp.read())
        with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromiums/Local State", 'r') as fp: #Also load default local state, so we can patch
            result = self.dict_recurupdate(result, json.loads(fp.read()))

        #Enable dark mode if on
        if darkmode == True and not "enable-force-dark@1" in result["browser"]["enabled_labs_experiments"] and not "enable-force-dark@2" in result["browser"]["enabled_labs_experiments"] and not "enable-force-dark@3" in result["browser"]["enabled_labs_experiments"] and not "enable-force-dark@4" in result["browser"]["enabled_labs_experiments"] and not "enable-force-dark@5" in result["browser"]["enabled_labs_experiments"] and not "enable-force-dark@6" in result["browser"]["enabled_labs_experiments"] and not "enable-force-dark@7" in result["browser"]["enabled_labs_experiments"]:
            result["browser"]["enabled_labs_experiments"].append("enable-force-dark@1")

        #Save to the Local State
        try:
            with open(LocalStateFile, 'w') as fp:
                fp.write(json.dumps(result, separators=(',', ':'))) # Also a minified json
        except Exception as exceptionstr:
            raise ICESharedModuleException(_("Failed to write to Local State"))


    #Start Page
    def chromi_add_startpage(self, itemid, profileid, name, website):
        #dict, string, string

        #First, open default Bookmarks file
        with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromiums/Bookmarks", 'r') as fp:
            result = json.loads(fp.read())

        #Then tweak the values
        result["roots"]["bookmark_bar"]["children"][0]["children"][0]["meta_info"]["Thumbnail"] = "https://via.placeholder.com/256" #TODO
        result["roots"]["bookmark_bar"]["children"][0]["children"][0]["name"] = name
        result["roots"]["bookmark_bar"]["children"][0]["children"][0]["url"] = website

        #Then write to Bookmarks
        try:
            with open("{0}/{1}/{2}/Default/Bookmarks".format(default_ice_directory, itemid, profileid), 'w') as fp:
                fp.write(json.dumps(result, separators=(',', ':'))) # Also a minified json
        except Exception as exceptionstr:
            raise ICESharedModuleException(_("Failed to write to Bookmarks"))

    
    #Finishing touches
    def chromi_finishing_touches(self, itemid, profileid):
        #string, string
        
        with open("{0}/{1}/{2}/First Run".format(default_ice_directory, itemid, profileid), 'w') as fp:
            pass #Skips the initial Welcome to Google Chrome dialog
