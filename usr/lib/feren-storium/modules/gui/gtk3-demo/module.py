#!/usr/bin/python3

import gi

gi.require_version('WebKit2', '4.0')
gi.require_version('Gtk', '3.0')

import sys
import urllib.request #Grabbing files from internet
import urllib.error
import locale #Translations go brrr
import gettext #Translations go brrr
import getpass #Used for finding username
import colorsys #Used for page recolourisation

import os

from gi.repository import WebKit2, Gtk, Gio, Gdk, GLib, Pango, GObject, GdkPixbuf
from threading import Thread
from queue import Queue, Empty
from notify2 import Notification, init as NotifyInit



####Application Details Header
class AppDetailsHeader(Gtk.VBox):

    def __init__(self):
        
        Gtk.Box.__init__(self)
        
        self.app_icon = Gtk.Image()
        self.app_icon.set_from_icon_name("deb", Gtk.IconSize.DND)
        
        self.app_title = Gtk.Label()
        self.app_title.set_label("APPLICATION TITLE")
        
        self.app_shortdesc = Gtk.Label()
        self.app_shortdesc.set_label("APPLICATION SHORT DESCRIPTION")
        
        self.pack_start(self.app_icon, False, False, 4)
        self.pack_start(self.app_title, True, False, 4)
        self.pack_start(self.app_shortdesc, True, False, 4)
        
        pass



####AppView (the website)
class AppView(WebKit2.WebView):

    def __init__(self):
        WebKit2.WebView.__init__(self)

        self.connect('load-changed', self._load_changed_cb)
        self.connect('context-menu', self._context_menu_cb)
        self.connect('notify::status', self.on_load_status_change)
        
        self.status_btn = None
        self.back_btn = None

        #For the back button
        #TODO: Check this more rigorously
        self.back_button_history = ["home.html"]

        self.back_signal_handler = None
        
        self.current_package = ""
    
        
    def on_load_status_change(download, status):
        print(download, status)
        
        #self._push_config()
        
    def refresh_gtk_colors(self):
        """
        Updates the CSS on the page to use the colours from GTK.
        """
        window = Gtk.Window()
        style_context = window.get_style_context()

        def _rgba_to_hex(color):
           """
           Return hexadecimal string for :class:`Gdk.RGBA` `color`.
           """
           return "#{0:02x}{1:02x}{2:02x}".format(
                                            int(color.red   * 255),
                                            int(color.green * 255),
                                            int(color.blue  * 255))

        def _get_color(style_context, preferred_color, fallback_color):
            color = _rgba_to_hex(style_context.lookup_color(preferred_color)[1])
            if color == "#000000":
                color = _rgba_to_hex(style_context.lookup_color(fallback_color)[1])
            return color

        def _get_hex_variant(string, offset):
            """
            Converts hex input #RRGGBB to RGB and HLS to increase lightness independently
            """
            string = string.lstrip("#")
            rgb = list(int(string[i:i+2], 16) for i in (0, 2 ,4))

            # colorsys module converts to HLS to brighten/darken
            hls = colorsys.rgb_to_hls(rgb[0], rgb[1], rgb[2])
            newbright = hls[1] + offset
            newbright = min([255, max([0, newbright])])
            hls = (hls[0], newbright, hls[2])

            # Re-convert to rgb and hex
            newrgb = colorsys.hls_to_rgb(hls[0], hls[1], hls[2])

            def _validate(value):
                value = int(value)
                if value > 255:
                    return 255
                elif value < 0:
                    return 0
                return value

            newrgb = [_validate(newrgb[0]), _validate(newrgb[1]), _validate(newrgb[2])]
            newhex = '#%02x%02x%02x' % (newrgb[0], newrgb[1], newrgb[2])
            return newhex

        bg_color = _get_color(style_context, "theme_base_color_breeze", "theme_base_color")
        text_color = _get_color(style_context, "theme_fg_color_breeze", "theme_fg_color")
        selected_bg_color = _get_color(style_context, "theme_selected_bg_color_breeze", "theme_selected_bg_color")
        selected_text_color = _get_color(style_context, "theme_selected_fg_color_breeze", "theme_selected_fg_color")
        button_bg_color = _get_color(style_context, "theme_button_background_normal_breeze", "theme_bg_color")

        css = []
        css.append("--bg: " + bg_color)
        css.append("--text: " + text_color)
        css.append("--selected_bg: " + selected_bg_color)
        css.append("--selected_text: " + selected_text_color)
        css.append("--button_bg: linear-gradient(to bottom, {0}, {1})".format(
                                          _get_hex_variant(button_bg_color, 8),
                                          _get_hex_variant(button_bg_color, -8)))

        app.update_page("body", "append", "<style>:root {" + ";".join(css) + "}</style>")

        # For High Contrast theme
        if bg_color in ["#000", "#000000"]:
            app.update_page("body", "addClass", "bg-is-black")

    def toggle_back(self, newstate):
        backbtnthread = Thread(target=self._toggle_back,
                            args=(newstate,))
        backbtnthread.start()
    
    def _toggle_back(self, newstate):
        GLib.idle_add(self.__toggle_back, newstate)
    
    def __toggle_back(self, newstate):
        self.back_btn.set_sensitive(newstate)

    def _back_action(self, data):
        self.toggle_back(False)
        #Remove from back history
        self.back_button_history = self.back_button_history[:-1]
        self.run_javascript('gotopage("'+self.back_button_history[-1]+'")')
        
    def _goto_page(self, page):
        #file = os.path.abspath(os.path.join(translations.get_pages_path(), page+".html"))
        file = os.path.abspath(os.path.join("/usr/share/feren-storium/"+page+".html"))
        uri = 'file://' + urllib.request.pathname2url(file)
        self.load_uri(uri)
        
    def _goto_packageview(self, packagename):
        #file = os.path.abspath(os.path.join(translations.get_pages_path(), "packagepage.html"))
        self.run_javascript('gotopackage("'+packagename+'")')

    def _btn_goto_packageview(self, btn, packagename):
        self._goto_packageview(packagename)

    def _generate_apps_list(self, category):
        pass

    def _generate_websites_list(self, category):
        pass

    def update_insite_information(self, packagename, packagetype):
        pass
            
    def packagepagestuff(self):
        pass

    def _push_config(self):
        # TODO: push notification should be connected to angularjs and use a
        # broadcast event any suitable controllers will be able to listen and
        # respond accordingly, for now we just use jQuery to manually toggle
        current_page = app.current_page
                
        #Toggle block buttons first
        self.StoreGUI.gohome_btn.handler_block(self.StoreGUI.gohome_handle_id)
        self.StoreGUI.status_btn.handler_block(self.StoreGUI.status_handle_id)
        #Do their toggles and then unblock
        self.StoreGUI.gohome_btn.set_active(False)
        self.StoreGUI.status_btn.set_active(False)
        self.StoreGUI.gohome_btn.handler_unblock(self.StoreGUI.gohome_handle_id)
        self.StoreGUI.status_btn.handler_unblock(self.StoreGUI.status_handle_id)

        ### Index Page ###
        if current_page == 'statuspage.html':
            pass

        if current_page.startswith('packagepage.html'):
            pass

    def _load_changed_cb(self, view, frame):
        self.refresh_gtk_colors()
        uri = str(self.get_uri())
        
        #By making this only run on a fully loaded page we prevent this thing running multiple times in one page load
        if self.get_estimated_load_progress() == 1.0:
            self.toggle_back(uri.rsplit('/', 1)[1] != "home.html")
            #Add page to history if it isn't the latest page in history
            if self.back_button_history[-1] != uri.rsplit('/', 1)[1] and uri.rsplit('/', 1)[1] != "splash.html":
                self.back_button_history.append(uri.rsplit('/', 1)[1])
                

            if uri.rsplit('/', 1)[1] == "splash.html":
                self.back_button_history = ["home.html"]
                self.run_javascript('gotopage("'+self.StoreGUI._start_page+'")')
                return
            else:
                self.mainwindowstack.set_visible_child(self.mainwindow)
            app.current_page = uri.rsplit('/', 1)[1]
            self._push_config()

    def _context_menu_cb(self, webview, menu, event, htr, user_data=None):
        # Disable context menu.
        return True



####Store Window
class StoreWindow(object):
    def __init__(self):

        self.current_page = ""

        #systemstate.first_run = self._check_first_run()
        #systemstate.first_run = True

        self._start_page = 'home.html'

        self._build_app()

    def build_app_post_splashscreen(self, mainwindow, maintoolbar, mv, b):
        GLib.idle_add(self._build_app_post_splashscreen, mainwindow, maintoolbar, mv, b)

    def _build_app_post_splashscreen(self, mainwindow, maintoolbar, mv, b):
        # build rest of window
        box_application_header = AppDetailsHeader()
        #box_application_header.set_visible(False)
        box_application_header.parent_window = self.w
        # add the box to the parent window and show
        mainwindow.pack_start(maintoolbar, False, True, 0)
        mainwindow.pack_start(box_application_header, False, True, 0)
        mainwindow.pack_end(b, True, True, 0)
        file = os.path.abspath("/usr/share/feren-storium/home.html")
        uri = 'file://' + urllib.request.pathname2url(file)
        mv.load_uri(uri)
        mv.AppDetailsHeader = box_application_header
        self.w.show_all()

    def _build_app(self):
        # build window
        self.w = Gtk.Window()
        self.w.set_position(Gtk.WindowPosition.CENTER)
        self.w.set_title("Store")
        self.w.set_default_size(850, 640)
        self.w.set_size_request(850, 540)
        #self.w.set_resizable(False)

        #This allows Store to be natively recognised as an application associated with its .desktop file
        GLib.set_prgname('/usr/bin/feren-storium')
        
        back_img = Gtk.Image()
        back_img.set_from_icon_name("go-previous-symbolic", Gtk.IconSize.BUTTON);

        back_btn = Gtk.Button(image=back_img)
        back_btn.set_sensitive(False)
        back_btn.set_name("back-btn")
        
        status_img = Gtk.Image()
        status_img.set_from_icon_name("folder-download-symbolic", Gtk.IconSize.BUTTON);
        self.status_btn = Gtk.ToggleButton(image=status_img)
        self.status_btn.set_name("status-btn")
        self.status_btn.set_always_show_image(True)
        self.status_handle_id = self.status_btn.connect("clicked", self._status_pressed)
        
        search_img = Gtk.Image()
        search_img.set_from_icon_name("edit-find-symbolic", Gtk.IconSize.BUTTON);
        search_btn = Gtk.ToggleButton(image=search_img)
        search_btn.set_name("search-btn")
        
        mainmenu = Gio.Menu()
        mainmenu.append("hello")
        mainmenu.append("world")
        menu_btn_img = Gtk.Image()
        menu_btn_img.set_from_icon_name("open-menu-symbolic", Gtk.IconSize.BUTTON);
        menu_btn = Gtk.MenuButton(image=menu_btn_img)
        menu_btn.set_use_popover(False)
        menu_btn.set_menu_model(mainmenu)
        
        self.gohome_btn = Gtk.ToggleButton(label=("Items Page"))
        self.gohome_btn.set_name("gohome-btn")
        self.gohome_handle_id = self.gohome_btn.connect("clicked", self._gohome_pressed)
        
        #For the splash screen
        mainwindowstack = Gtk.Stack()
        mainwindowstack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        #Use a titlebar-toolbar approach
        mainwindow = Gtk.VBox()
        mainwindow.set_spacing(0)
        maintoolbar = Gtk.Toolbar()
        maintoolbar.get_style_context().add_class(Gtk.STYLE_CLASS_PRIMARY_TOOLBAR)
        maintoolbarcontents = Gtk.ToolItem()
        maintoolbarcontents.set_expand(True)
        maintoolbar.insert(maintoolbarcontents, 0)
        header = Gtk.Box()
        #maintoolbarcontents.set_border_width(2)
        maintoolbarcontents.add(header)
        header.set_spacing(6)
        toolbarspacer=Gtk.Alignment()
        
        #Logo
        logoimageandbox = Gtk.Box(spacing=8)
        logotypebox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        store_logoimg = Gtk.Image()
        store_logoimg.set_from_icon_name("softwarecenter", Gtk.IconSize.DND);
        
        store_logotype1 = Gtk.Label(label=("Feren Storium"))
        
        store_logotype1_box = Gtk.Box()
        store_logotype1_box.pack_start(store_logotype1, False, False, 0)
        
        logotypebox.pack_start(store_logotype1_box, False, False, 0)
        logoimageandbox.pack_start(store_logoimg, False, False, 0)
        logoimageandbox.pack_end(logotypebox, False, False, 0)
            
        header.pack_start(back_btn, False, True, 0)
        header.pack_start(logoimageandbox, False, True, 0)
        header.pack_start(toolbarspacer, True, True, 0)
        
        buttoncentering = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        buttoncenteringbtns = Gtk.Box(spacing=4)
        buttoncentering.set_center_widget(buttoncenteringbtns)
        
        buttoncenteringbtns.pack_start(self.gohome_btn, False, True, 0)
        buttoncenteringbtns.pack_start(self.status_btn, False, True, 0)
        buttoncenteringbtns.pack_start(search_btn, False, True, 0)
        buttoncenteringbtns.pack_start(menu_btn, False, True, 0)
        
        header.pack_end(buttoncentering, False, False, 0)
        
        # build tasks page
        taskspage = Gtk.VBox(spacing=8)
        
        taskslabel_box = Gtk.Box()
        taskslabel = Gtk.Label(label="Currently working on these tasks:")
        taskslabel_box.pack_start(taskslabel, False, False, 0)
        
        self.tasksitems = Gtk.FlowBox()
        self.tasksitems.set_margin_top(4)
        self.tasksitems.set_margin_bottom(4)
        self.tasksitems.set_min_children_per_line(1)
        self.tasksitems.set_max_children_per_line(1)
        self.tasksitems.set_row_spacing(4)
        self.tasksitems.set_homogeneous(True)
        self.tasksitems.set_valign(Gtk.Align.START)
        
        updateslabel_box = Gtk.Box()
        updateslabel = Gtk.Label(label="Updates are available for:")
        updateslabel_box.pack_start(updateslabel, False, False, 0)
        
        self.updatesitems = Gtk.FlowBox()
        self.updatesitems.set_margin_top(4)
        self.updatesitems.set_margin_bottom(4)
        self.updatesitems.set_min_children_per_line(1)
        self.updatesitems.set_max_children_per_line(1)
        self.updatesitems.set_row_spacing(4)
        self.updatesitems.set_homogeneous(True)
        self.updatesitems.set_valign(Gtk.Align.START)
        
        installedlabel_box = Gtk.Box()
        installedlabel = Gtk.Label(label="Currently installed:")
        installedlabel_box.pack_start(installedlabel, False, False, 0)
        
        self.installeditems = Gtk.FlowBox()
        self.installeditems.set_margin_top(4)
        self.installeditems.set_margin_bottom(4)
        self.installeditems.set_min_children_per_line(1)
        self.installeditems.set_max_children_per_line(1)
        self.installeditems.set_row_spacing(4)
        self.installeditems.set_homogeneous(True)
        self.installeditems.set_valign(Gtk.Align.START)
                
        taskspage.pack_start(taskslabel_box, False, True, 0)
        taskspage.pack_start(self.tasksitems, False, True, 0)
        taskspage.pack_start(updateslabel_box, False, True, 0)
        taskspage.pack_start(self.updatesitems, False, True, 0)
        taskspage.pack_start(installedlabel_box, False, True, 0)
        taskspage.pack_start(self.installeditems, False, True, 0)
        
        
        # build 404 page
        self.nfpage = Gtk.VBox(spacing=8)
        
        nfpage_box = Gtk.VBox()
        nfpagelabel = Gtk.Label(label="Not Available")
        nfpagelabel2 = Gtk.Label(label="This item is currently not available or does not exist.")
        nfpage_box.pack_start(nfpagelabel, False, False, 5)
        nfpage_box.pack_end(nfpagelabel2, False, False, 5)
        self.nfpage.set_center_widget(nfpage_box)
        
        mainwindowstack.add_named(mainwindow, "window")
        
        # build webkit container
        mv = AppView()
        mv.get_style_context().add_class(Gtk.STYLE_CLASS_VIEW)
        mv.set_zoom_level(1.0)

        mv.back_btn = back_btn
        mv.back_signal_handler = mv.back_btn.connect("clicked", mv._back_action)
        mv.header = header
        
        mv.StoreGUI = self
        
        #handle_id is needed to block events as otherwise the button active state changes cause button press events to occur (for whatever stupid reason) which ultimately leads to a Stack Overflow as the event code retriggers the event by triggering the button press yet again looping the cycle indefinitely

        # build scrolled window widget and add our appview stack
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        
        # build another scrolled window widget and add our tasks view
        sw2 = Gtk.ScrolledWindow()
        sw2.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sw2.get_style_context().add_class(Gtk.STYLE_CLASS_VIEW)
        
        self.pages = Gtk.Stack()
        self.pages.get_style_context().add_class(Gtk.STYLE_CLASS_VIEW)
        self.pages.add_named(sw, "webkit")
        self.pages.add_named(sw2, "tasks")
        self.pages.add_named(self.nfpage, "404")
        taskspage.set_margin_bottom(8)
        taskspage.set_margin_top(8)
        taskspage.set_margin_left(10)
        taskspage.set_margin_right(10)
        
        sw.add(mv)
        sw2.add(taskspage)

        # build a an autoexpanding box and add our scrolled window
        b = Gtk.Box(homogeneous=False, spacing=0)
        b.pack_start(self.pages, expand=True, fill=True, padding=0)
        
        self.w.add(mainwindowstack)
        
        self.w.connect('delete-event', self.close)

        self._window = self.w
        self.webkit = mv

        self.w.show_all()
        
        #Add more variables to mv
        mv.sw = sw
        mv.sw2 = sw2
        mv.pages = self.pages
        mv.mainwindow = mainwindow
        mv.mainwindowstack = mainwindowstack
        
        thread = Thread(target=self.build_app_post_splashscreen,
                        args=(mainwindow, maintoolbar, mv, b))
        thread.daemon = True
        thread.start()

    def run(self):
        Gtk.main()

    def _gohome_pressed(self, gtk_widget):
        self.webkit._goto_page("home")

    def _status_pressed(self, gtk_widget):
        self.webkit._goto_page("statuspage")

    def close(self, p1 = None, p2 = None):
        try:
            os.file.remove(pidfile)
        except:
            pass
        Gtk.main_quit(p1, p2)

    def update_page(self, element, function, parm1=None, parm2=None):
        """ Runs a JavaScript jQuery function on the page,
            ensuring correctly parsed quotes. """
        if parm1 and parm2:
            self.run_javascript('$("' + element + '").' + function + "('" + parm1.replace("'", '\\\'') + "', '" + parm2.replace("'", '\\\'') + "')")
        if parm1:
            if not function == 'src':
                self.run_javascript('$("' + element + '").' + function + "('" + parm1.replace("'", '\\\'') + "')")
            else:
                #Image replacing requires a special code modification
                self.run_javascript('$("' + element + '").attr' + "('src', '" + parm1.replace("'", '\\\'') + "')")
        else:
            self.run_javascript('$("' + element + '").' + function + '()')

    def run_javascript(self, script):
        thread = Thread(target=self._run_javascript,
                        args=(script,))
        thread.start()

    def _run_javascript(self, script):
        """
        Runs a JavaScript function on the page, regardless of which thread it is called from.
        GTK+ operations must be performed on the same thread to prevent crashes.
        """
        GLib.idle_add(self.__run_javascript, script)

    def __run_javascript(self, script):
        """
        Runs a JavaScript script on the page when invoked from run_javascript()
        """
        self.webkit.run_javascript(script)
        return GLib.SOURCE_REMOVE

    def _check_first_run(self):
        pass
    

class Module():
    def init(self):
        global app
        app = StoreWindow()
        app.run()