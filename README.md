# Feren Storium

Modular Package Management Backend

This is essentially going to be the base of New Feren OS Store with the goal of letting Feren OS Store exist to its full goals and full potential, but also allow the codebase to individually be contributed to and be adapted by others across the Linux space, with modularity in mind.


As such, this will essentially eventually be the New Feren OS Store but stripped of its GUI principles and pages and essentially turned back into a tech demonstration to be adapted upon.


Currently a very huge work-in-progress and currently barely functional in functionality. Pending a lot of further development before it's considered ready.

---

Mockups:

https://github.com/feren-OS/Bug-Reporting-Center/issues/128#issuecomment-651418078

---

<h1>TODO</h1>

Background Process:

- [ ] Userland: Run on login, ready to accept signals for stuff like update completion, etc.
- [ ] Userland: Upon Store launching by user, show the GUI and get the current Tasks situation from System's background process
- [ ] Userland: When Store's closed, continue running userland Tasks in current process, but once that's done unlock the 'instance' file, start a new Store background process, and then quit the current process (thus reducing resource usage)
- [ ] System: Run on bootup, ready to accept system-wide tasks
- [ ] System: Based on configuration, perform automatic updates when necessary
- [ ] System: Receive signal when system is shutting down or restarting to exit on tasks completion (or immediately if there's no tasks)
- [ ] System: If configured to, when auto-updating or manually updating only download packages, then schedule a new systemd target next boot to run system process only in 'finish update' mode
- [ ] System: In 'finish update' mode, switch Plymouth to updating screen, and then when done restore the systemd target, and restart the system
- [ ] System Exit Holdup: If a task or update tasks are currently occurring, and the system begins shutdown or restart, show a Plymouth status saying what's finishing (and progress) in terms of tasks if it's not updates, or switch to updates Plymouth if it is updates-tasks (otherwise just quit immediately)

Tasks and Updates:

- [ ] Make Tasks system perform tasks in its newer form
- [x] Restructure Tasks System from original Storium
- [ ] Add means of cancelling Tasks (callback?)
- [ ] Add in Confirmation dialog code
- [ ] Finish running tasks and move scheduled tasks into Staged, unless they're updates, upon logging out or whatever
- [ ] Updates: Offset performing of updates to a separate superuser-ran process
- [ ] Updates: Figure out how to get statuses from the superuser-ran process
- [ ] Updates: 'Downgrade' packages when current versions are no longer available
- [ ] Updates: Send progress to 'shutdown holdup' process once 'shutdown holdup' process sends signal to start receiving progress and statuses
- [ ] Updates: Provide a way to perform updates on startup (probably using 'shutdown holdup' process, but instead to hold up booting) - probably abusing systemd service
- [ ] Updates: Add notification for completed updates, including automatics
- [ ] Updates: On system-ran auto-update process, send a signal when done so that Store can receive it in userland to notify that updates were completed in the background?

Drivers:

- [ ] Place drivers in updates page
- [ ] Add notification when no 3rd-party drivers are installed but some are available
- [ ] Cache the known drivers in a config storage thingy when a driver's installed, so that a notification appears if the list of drivers gets new additions
- [ ] Upon notifications for newer drivers, update said storage thingy immediately to prevent new notifications

API and Modules:

- [x] Make modules able to declare if they should be loaded or not
- [x] Allow modules to determine whether or not to allow being used (aka having runtime checks)
- [ ] Figure out how we want to go about adding a task for adding an application source when installing something that needs one
- [ ] Add ability to refresh task progress
- [ ] Add ability to invalidate package install status cache

Package Management Modules:

- [ ] Add call that lists package changes, and available bonuses, so they can be fed to the Confirm? dialog
- [ ] Merge Package File Management modules code into Package Management modules
- [ ] Add in a 'drivers' section to the available updates data returned to the API
- [ ] APT: Off-set tasks execution to systemland process (and send language too)
- [ ] APT: Wait for process completion, and use exit code as indication of completion or failure
- [ ] APT: Send a signal containing an error message to Store if the task fails
- [ ] APT: Hold up shutdown/reboot until current task completes
- [ ] APT: Disable cancelling once downloading is finished
- [ ] APT: Add support for .deb files
- [ ] Flatpak: Actually do the module's package management capabilities
- [ ] Flatpak: Add support for .flatpakref and .flatpak files
- [ ] Snap: Complete the module
- [ ] Snap: Add support for .snap files?
- [ ] Snap: ONLY allow Snaps that are known to be maintained by their official developers to be shown in the Store
- [ ] ICE: Finish the split of code
- [ ] ICE (post-release idea): Firefox support
- [ ] ICE: Add a GUI for choosing and managing profiles
- [ ] ICE: Change ICE profiles data so that multiple profiles can be made
- [ ] ICE: Add support for switching browsers between Chromium-based browsers and Firefox-based browsers, depending on current browser preference, if the current browser is no longer present
- [ ] (post-release idea) Module that allows listing ALL AppStream items and installing all of the items?
- [ ] (post-release idea) Support for KDE Store?

Demo GUI Module:

- [ ] When opening files with Store, if the default module chosen to manage the package file indicates the package's name = any Store item's respective package name, continue loading but switch to an FYI dialog about the package being in Store
- [ ] Program in Tasks list support and buttons running any appropriate callbacks
- [ ] Allow installation of programs that don't have their application sources enabled, but rename their Install buttons to 'Install...'
- [ ] Program in Updates, Drivers and Installed sections in the Tasks page
- [ ] Notify on successful installs
- [ ] Notify on available updates (when automatic is disabled)
- [ ] Notify on automatic updates starting
- [ ] Add category for other non-curated Stores

Commands and MITM:

- [ ] Add MITM wrappers to apt, etc. to add bonus features like application source management

Settings:

- [ ] Program in all options from the official mockups
- [ ] Allow exporting and importing of 'application playlists' (a file that, when exported lists all of the things you installed in there, and then imported adds everything in that list that is current available to that same installation tasks-queue)
- [ ] 'Noob Mode' where the sources dropdown next to Install buttons is hidden to prevent any confusion

Misc.:

- [ ] EXE files: EXE inspection thing that checks file details(?) and recommends software in Store based on the EXE in use, otherwise skips to WINE usage
- [ ] EXE files: Open up WINE in Store
- [ ] WINE disclaimer in WINE info page for reasons
- [ ] (post-release idea) Add options for beta-testing certain applications?