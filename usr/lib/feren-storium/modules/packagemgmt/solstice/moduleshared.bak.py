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
from gi.repository import GLib
import colorsys
from urllib import parse
import collections.abc


class ICEModuleSharedException(Exception): # Name this according to the module to allow easier debugging
    pass


class main():
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
    

    def __init__(self):
        gettext.install("feren-storium-ice", "/usr/share/locale", names="ngettext")
        self.applications_directory = os.path.expanduser("~") + "/.local/share/applications"
        self.default_ice_directory = os.path.expanduser("~") + "/.local/share/feren-storium-ice"
        
        
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
        
        
    ####COLOR CHECKS
    #Is the color light or dark?
    def get_is_light(self, hexcode):
        #string
        
        #Returns:
        # True: Light
        # False: Dark
        redc, greenc, bluec = tuple(int(hexcode[i:i+2], 16) for i in (1, 3, 5)) #Dodge the # character
        lumi = colorsys.rgb_to_hls(redc, greenc, bluec)[1]
        
        if lumi > 127.5:
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
                lumi = lumi * (1.0 + amount) #Conversion to make the 'lumi * amount' darken instead of brightening
            else:
                if (lumi + amount) < 0.0:
                    lumi = 0.0
                else:
                    lumi -= amount
        else: #Positive means lightening, and 0.0 means no change
            if multiply == True:
                lumi = lumi * (1.0 + amount) #Add 1.0 to the amount to lighten it instead of darkening it
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


    #### CHROMIUM PROFILE CREATION
    #Default Settings
    def set_default_settings_chromi(self, preferencesfile, website, realname, iconuri):
        #dict, string, string, string
        
        newpreferences = preferencesfile #For patching, return later
        
        with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromiums/Preferences", 'r') as fp:
            defaultpreferences = json.loads(fp.read())
        newpreferences = self.dict_recurupdate(newpreferences, defaultpreferences)
        
        #Set important settings unique to each SSB
        newpreferences["homepage"] = website
        newpreferences["custom_links"]["list"][0]["title"] = realname
        newpreferences["custom_links"]["list"][0]["url"] = website
        newpreferences["session"]["startup_urls"] = [website]
        newpreferences["download"]["default_directory"] = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD) + "/" + _("{0} Downloads").format(realname)
        newpreferences["profile"]["name"] = realname
        newpreferences["ntp"]["custom_background_dict"]["attribution_line_1"] = _("Website Application - {0}").format(realname)
        newpreferences["vivaldi"]["tabs"]["new_page"]["custom_url"] = "https://feren-os.github.io/start-page/ice?ice-text="+(_("Website Application - {0}").format(realname))+"&home-url={0}".format(parse.quote(website, safe=""))+"&home-icon={0}".format(parse.quote(iconuri, safe=""))
        newpreferences["vivaldi"]["homepage"] = website
        newpreferences["vivaldi"]["homepage_cache"] = website
        
        #Set the permissions for websites in this SSB
        shortenedurl = self.get_shortened_url(website)
        for permtype in ["ar", "autoplay", "automatic_downloads", "background_sync", "clipboard", "file_handling", "font_access", "midi_sysex", "notifications", "payment_handler", "sensors", "sound", "sleeping-tabs", "window_placement", "vr"]:
            newpreferences["profile"]["content_settings"]["exceptions"][permtype] = {}
            newpreferences["profile"]["content_settings"]["exceptions"][permtype]["[*.]"+shortenedurl+",*"] = {"expiration": "0", "model": 0, "setting": 1}
            newpreferences["profile"]["content_settings"]["exceptions"][permtype][shortenedurl+",*"] = {"expiration": "0", "model": 0, "setting": 1}
            
        #Return the new Preferences
        return newpreferences
    
    #Default Settings for extra shortcuts
    def append_default_extras_settings_chromi(self, preferencesfile, extraids=[], extrawebsites=[], extrarealnames=[]):
        #dict, list, list, list
        
        newpreferences = preferencesfile #For patching, return later
        
        shortenedurl = self.get_shortened_url(website)
        for permtype in ["ar", "autoplay", "automatic_downloads", "background_sync", "clipboard", "file_handling", "font_access", "midi_sysex", "notifications", "payment_handler", "sensors", "sound", "sleeping-tabs", "window_placement", "vr"]:
            extrascount = 0
            for extraid in extraids:
                shortenedurl = self.get_shortened_url(extrawebsites[extrascount])
                try:
                    shortenedurl = shortenedurl.split("/")[0]
                except:
                    pass
                newpreferences["profile"]["content_settings"]["exceptions"][permtype]["[*.]"+shortenedurl+",*"] = {"expiration": "0", "model": 0, "setting": 1}
                newpreferences["profile"]["content_settings"]["exceptions"][permtype][shortenedurl+",*"] = {"expiration": "0", "model": 0, "setting": 1}
                extrascount += 1
        
        #Return the new Preferences
        return newpreferences
    
    def set_default_settings_gecko(self, prefsjs, userjs, website, realname, iconuri, needsreset=True):
        #list, list, string, string, string, bool
        
        pass #TODO
    
    #Vivaldi and Brave settings
    def set_ice_privacy_chromi(self, preferencesfile, allowhistory=True, allowgooglesignon=False, allowgooglehangouts=False):
        #dict, bool, bool, bool
        
        newpreferences = preferencesfile #For patching, return later
        #First, open the Preferences file
        with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromiums/preferences.json", 'r') as fp:
            preferencesjson = json.loads(fp.read())
                
        if not allowgooglesignon: #Disable Google sign-on if unneeded
            newpreferences = self.dict_recurupdate(newpreferences, preferencesjson["disable-googlesignon"])
        if not allowgooglehangouts: #Disable Google Hangouts if unneeded
            newpreferences = self.dict_recurupdate(newpreferences, preferencesjson["disable-googlehangouts"])
        if not allowhistory: #Disable History if the SSB provides History itself
            newpreferences = self.dict_recurupdate(newpreferences, preferencesjson["disable-history"])
            
        #Return the new Preferences
        return newpreferences
            
    #Firefox settings
    def set_ice_privacy_gecko(self, prefsjs, userjs, allowhistory=True):
        #list, list, bool
        
        pass #TODO
    
    #Bonuses
    def append_ice_extras_chromi(self, preferencesfile, extras=[]):
        #dict, list
        
        newpreferences = preferencesfile #For patching, return later
        #First, open the Extras file
        with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromiums/extras.json", 'r') as fp:
            extrasjson = json.loads(fp.read())
        
        #First, add the extras that are supplied
        for item in extras:
            if item in extrasjson:
                #Check that the extension isn't already installed
                for extensionid in extrasjson[item]["extensions"]["settings"]:
                    if extensionid in newpreferences["extensions"]["settings"]:
                        #If it is, clear out stuff that would uninstall the extra if installed
                        extrasjson[item]["extensions"]["settings"][extensionid].pop("path", None)
                        extrasjson[item]["extensions"]["settings"][extensionid]["manifest"].pop("name", None)
                        extrasjson[item]["extensions"]["settings"][extensionid]["manifest"].pop("version", None)
                #Now that is done, install extra to profile
                newpreferences = self.dict_recurupdate(newpreferences, extrasjson[item])
        #Second, we remove extras no longer selected
        for item in extrasjson:
            if not item in extras:
                for extensionid in extrasjson[item]["extensions"]["settings"]:
                    newpreferences["extensions"]["settings"].pop(extensionid, None)
        #Now, return the new Preferences
        return newpreferences
    
    
    #Theme colouring
    def append_theme_colours(self, preferencesfile, icecolor, icehighlightcolor, icecolordark):
        #dict, string, string, string
        
        newpreferences = preferencesfile #For patching, return later
        
        #TODO: Figure out doing themes for Chrome to colour the windows by their website colours
        vivaldihighlightcol = icehighlightcolor
        if self.get_colours_different(icecolor, icehighlightcolor): #Suitable background colour used
            vivaldiaccentcol = icehighlightcolor
            vivaldiaccentcoldark = icehighlightcolor
            vivaldiwinbgcol = icecolor
            vivaldiwinbgcoldark = icecolordark
            vivaldiaccentinchrome = False
        else: #Otherwise use fallback colours
            vivaldiaccentcol = icecolor
            vivaldiaccentcoldark = icecolordark
            vivaldiwinbgcol = ""
            vivaldiwinbgcoldark = ""
            vivaldiaccentinchrome = True 
        vivaldiaccentcolprivate = self.color_filter(icehighlightcolor, -46.0)
        vivaldiwinbgcolprivate = self.color_filter(icehighlightcolor, -70.0)
        
        #Now apply all the values for the themes in Vivaldi
        newpreferences["vivaldi"]["themes"]["system"][0]["accentOnWindow"] = vivaldiaccentinchrome
        newpreferences["vivaldi"]["themes"]["system"][1]["accentOnWindow"] = vivaldiaccentinchrome
        newpreferences["vivaldi"]["themes"]["system"][2]["accentOnWindow"] = False
        newpreferences["vivaldi"]["themes"]["system"][0]["colorAccentBg"] = vivaldiaccentcol
        newpreferences["vivaldi"]["themes"]["system"][1]["colorAccentBg"] = vivaldiaccentcoldark
        newpreferences["vivaldi"]["themes"]["system"][2]["colorAccentBg"] = vivaldiaccentcolprivate
        newpreferences["vivaldi"]["themes"]["system"][0]["colorHighlightBg"] = vivaldihighlightcol
        newpreferences["vivaldi"]["themes"]["system"][1]["colorHighlightBg"] = vivaldihighlightcol
        newpreferences["vivaldi"]["themes"]["system"][2]["colorHighlightBg"] = vivaldihighlightcol
        #Now set text colours where appropriate
        # Normal foregrounds
        if vivaldiwinbgcol != "":
            if self.get_is_light(vivaldiwinbgcol) == False: #Dark BG (in-Preferences default is Light, so no need for Light BG else)
                newpreferences["vivaldi"]["themes"]["system"][0]["colorFg"] = "#FFFFFF"
            newpreferences["vivaldi"]["themes"]["system"][0]["colorBg"] = vivaldiwinbgcol
        if vivaldiwinbgcoldark != "":
            if self.get_is_light(vivaldiwinbgcoldark) == True: #Light BG (in-Preferences default is Dark, so no need for Dark BG else)
                newpreferences["vivaldi"]["themes"]["system"][1]["colorFg"] = "#000000"
            newpreferences["vivaldi"]["themes"]["system"][1]["colorBg"] = vivaldiwinbgcoldark
        # Private foregrounds
        if self.get_is_light(vivaldiwinbgcolprivate) == True: #Light BG (in-Preferences default is Dark, so no need for Dark BG else)
            newpreferences["vivaldi"]["themes"]["system"][2]["colorFg"] = "#000000"
        newpreferences["vivaldi"]["themes"]["system"][2]["colorBg"] = vivaldiwinbgcolprivate
        
        #Return the new Preferences
        return newpreferences
    
    def set_local_state(self, localstatefile):
        #dict
        
        newpreferences = localstatefile #For patching, return later
        
        with open("/usr/share/feren-storium/modules/packagemgmt-ice/chromiums/Local State", 'r') as fp:
            defaultpreferences = json.loads(fp.read())
        newpreferences = self.dict_recurupdate(newpreferences, defaultpreferences)
        
        #Return the new Local State
        return newpreferences
    
    #Finishing touches
    def profile_finishing_touches(self, profilepath, source, allowhistory=True, extras=[]):
        #string, string, bool, list
        
        #Load defaults first for Local State
        with open("%s/.storium-extra-ids" % profilepath, 'w') as fp:
            fp.write(str(extras)) # This means that Store can manage extras later on in time
        if not allowhistory:
            with open("%s/.storium-nohistory" % profilepath, 'w') as fp:
                pass
        with open("%s/.storium-last-updated" % profilepath, 'w') as fp:
            fp.write(datetime.today().strftime('%Y%m%d'))
        with open("%s/.storium-default-browser" % profilepath, 'w') as fp:
            fp.write(source) # Used by module during updating to determine your browser
        with open("%s/First Run" % profilepath, 'w') as fp:
            pass #Skips the initial Welcome to Google Chrome dialog
        with open("%s/Default/Bookmarks" % profilepath, 'w') as fp:
            pass #Skips the initial Welcome to Google Chrome dialog
    

    ####SHORTCUT CREATION
    def create_shortcuts(self, realname, packagename, useicon, source, website, category, keywords, windowclass):
        #string, string, bool, string, string, string, string, string
        
        with open(self.applications_directory + "/%s.desktop" % windowclass, 'w') as fp:
            # I mean, this needs no explanation, it's a .desktop file
            fp.write("[Desktop Entry]\n")
            fp.write("Version=1.0\n")
            fp.write("Name={0}\n".format(realname))
            fp.write("Comment={0}\n".format(_("Website (obtained from Store)")))
            
            fp.write("Exec=/usr/bin/feren-storium-icelaunch {0} {1} {2} {3}\n".format(self.default_ice_directory + "/%s" % packagename, source, '"' + website + '"', windowclass))

            fp.write("Terminal=false\n")
            fp.write("X-MultipleArgs=false\n")
            fp.write("Type=Application\n")
            
            if useicon:
                fp.write("Icon={0}\n".format(self.default_ice_directory + "/%s/icon" % packagename))
            else:
                fp.write("Icon=text-html\n")

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

            fp.write("Keywords=%s\n" % keywords)

            fp.write("StartupWMClass=%s\n" % windowclass)
            fp.write("StartupNotify=true\n")
        
        os.system("chmod +x " + self.applications_directory + "/%s.desktop" % windowclass)
        #Otherwise it will refuse to launch from the Applications Menu
    
    def create_extra_shortcuts(self, realname, packagename, source, category, windowclass, extraids=[], extrawebsites=[], extrarealnames=[], extraiconuris=[], extrakeywords=[]):
        #string, string, string, string, string, list, list, list, list, list
        
        extrascount = 0 #Classic strat for iteration
        if extraids != []:
            import urllib.request #Grabbing files from internet
            import urllib.error
        for extraid in extraids:
            try:
                with open(self.applications_directory + "/{0}-{1}.desktop".format(packagename, extraid), 'w') as fp:
                    # I mean, this needs no explanation, it's a .desktop file
                    fp.write("[Desktop Entry]\n")
                    fp.write("Version=1.0\n")
                    fp.write("Name={0}\n".format(extrarealnames[extrascount]))
                    fp.write("Comment={0}\n".format(_("Website (part of %s)" % realname)))
                    
                    fp.write("Exec=/usr/bin/feren-storium-icelaunch {0} {1} {2} {3}\n".format(self.default_ice_directory + "/%s" % packagename, source, '"' + extrawebsites[extrascount] + '"', windowclass))

                    fp.write("Terminal=false\n")
                    fp.write("X-MultipleArgs=false\n")
                    fp.write("Type=Application\n")
                    
                    try:
                        urllib.request.urlretrieve(extraiconuris[extrascount], (self.default_ice_directory + "/{0}/icon-{1}".format(packagename, extraid)))
                        fp.write("Icon=%s\n" % (self.default_ice_directory + "/{0}/icon-{1}".format(packagename, extraid)))
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
                raise ICEModuleException(_("Failed to update {0}: {1} was encountered when updating extra shortcuts in the Applications Menu").format(packagename, exceptionstr))
            os.system("chmod +x " + self.applications_directory + "/{0}-{1}.desktop".format(packagename, extraid))
            extrascount += 1
