# Feren Storium

Modular Package Management Backend

This is essentially going to be the base of New Feren OS Store with the goal of letting Feren OS Store exist to its full goals and full potential, but also allow the codebase to individually be contributed to and be adapted by others across the Linux space, with modularity in mind.


As such, this will essentially eventually be the New Feren OS Store but stripped of its GUI principles and pages and essentially turned back into a tech demonstration to be adapted upon.


Currently a very huge work-in-progress and currently barely functional in functionality. Pending a lot of further development before it's considered ready.

---

Mockups:

https://github.com/feren-OS/Bug-Reporting-Center/issues/128#issuecomment-651418078

---

Ideas I want to implement into this application:

- [x] Make modules able to declare if they should be loaded or not
- [ ] APT support
- [ ] .deb support
- [ ] Flatpak support
- [ ] .flatpakref support
- [x] Snap support
- [x] ICE SSBs Support
- [x] Add custom messages to command-not-found (nevermind, just used MITMs) (not yet in repo)
- [ ] Add FYI dialog when opening DEBs for packages already in the Store
- [ ] Support for KDE Store?
- [ ] Separate Games and Themes sections
- [ ] Updates section in Tasks/Installed
- [ ] Notifications for successful installs, updates now being available, installing system-wide automatic updates, etc.
- [ ] Tasks management for queuing multiple install/remove/update/etc tasks at once
- [ ] Pre-defined application lists on the Home page for different topics
- [ ] Settings: Allow toggling of automatic updates
- [ ] Settings: Allow toggling and management of application sources
- [ ] Allow installation of programs that don't have their application sources enabled, but rename their Install buttons to 'Install...' and treat the application source as an extra '(pre-)dependency'
- [ ] Settings: Allow exporting and importing of 'application playlists' (a file that, when exported lists all of the things you installed in the Feren Store, and then imported adds everything in that list that is current available to that same installation queue)
- [ ] Restore Editors' Picks
- [ ] 'Noob Mode' where the sources dropdown next to Install buttons is hidden to prevent any confusion
- [ ] Add category for other non-curated Stores
- [ ] Add options for beta-testing certain applications (switch over to Beta)
- [ ] Allow easy control of important unattended-upgrades settings
- [ ] Snaps: ONLY allow Snaps that are known to be maintained by their official developers to be shown in the Store
- [ ] 'Advanced Mode' where all dependencies are mentioned in the confirmation dialog
- [ ] EXE files: EXE inspection thing that checks file details(?) and recommends software in Store based on the EXE in use, otherwise skips to WINE usage
- [ ] EXE files: Open up WINE in Store
- [ ] Info/Warning module: WINE disclaimer in WINE info page for reasons


Scrapped ideas:
- [ ] Allow the user, in an advanced setting, to turn the Store from curated only into show all available packages (low priority idea here)
- [ ] If this is on, any non-curated applications should have a persistent warning saying something along the lines of "This application is not curated by us. Feren OS's developers take no responsibility for any damage this package may do to your system. There is also no assurance that this application is officially maintained by its original developers. Please take caution when installing this application."
- [ ] ICE Module: Option to use normal browser profile (disables bonuses) (scrapped because browsers have in-built PWAs functionality now which do this anyway)