from __future__ import absolute_import
from . import _
from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Components.PluginComponent import PluginDescriptor
from Components.config import config, ConfigSubsection, ConfigText, ConfigYesNo, ConfigSelection, ConfigNumber, ConfigFloat
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from twisted.web.client import getPage
from Screens.Console import Console
import six
import logging
import os
import json
from Tools.Directories import fileExists

from .e2_utils import isFullHD
from .subtitles import E2SubsSeeker, SubsSearch, initGeneralSettings, initSubsSettings, \
    SubsSetupGeneral, SubsSearchSettings, SubsSetupExternal, SubsSetupEmbedded
from .subtitlesdvb import SubsSupportDVB, SubsSetupDVBPlayer

VER = "1.7.0.29"
log = logging.getLogger("SubsSupport")


def openSubtitlesSearch(session, **kwargs):
    settings = initSubsSettings().search
    eventList = []
    eventNow = session.screen["Event_Now"].getEvent()
    eventNext = session.screen["Event_Next"].getEvent()
    if eventNow:
        eventList.append(eventNow.getEventName())
    if eventNext:
        eventList.append(eventNext.getEventName())
    
    # If no events found, try to use the channel name as fallback
    if not eventList:
        try:
            from enigma import iPlayableService
            service = session.nav.getCurrentService()
            info = service and service.info()
            if info:
                channel_name = info.getName()
                if channel_name:
                    eventList.append(channel_name)
                    print(f"[SubsSupport] Using channel name as fallback: {channel_name}")
        except Exception as e:
            print(f"[SubsSupport] Error getting channel name: {e}")
    
    session.open(SubsSearch, E2SubsSeeker(session, settings), settings, searchTitles=eventList, standAlone=True)


def openSubtitlesPlayer(session, **kwargs):
    SubsSupportDVB(session)


def openSubsSupportSettings(session, **kwargs):
    settings = initSubsSettings()
    session.open(SubsSupportSettings, settings, settings.search, settings.external, settings.embedded, config.plugins.subsSupport.dvb)


class SubsSupportSettings(Screen):
    if isFullHD():
        skin = """
            <screen position="center,center" size="710,378">
                <widget source="menuList" render="Listbox" scrollbarMode="showOnDemand" position="10,10" size="692,362" zPosition="3" transparent="1" >
                    <convert type="TemplatedMultiContent">
                        {"templates":
                            {"default": (50, [
                                MultiContentEntryText(pos=(0, 0), size=(530, 45), font=0, flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER|RT_WRAP, text=0, color=0xFFFFFF)
                            ], True, "showOnDemand"),
                            },
                        "fonts": [gFont("Regular", 38)],
                        "itemHeight": 50
                        }
                    </convert>
                </widget>
            </screen>
            """
    else:
        skin = """
            <screen position="center,center" size="370,200">
                <widget source="menuList" render="Listbox" scrollbarMode="showOnDemand" position="10,10" size="340,180" zPosition="3" transparent="1" >
                    <convert type="TemplatedMultiContent">
                        {"templates":
                            {"default": (30, [
                                MultiContentEntryText(pos=(0, 0), size=(340, 30), font = 0, flags=RT_HALIGN_LEFT|RT_VALIGN_CENTER|RT_WRAP, text=0, color=0xFFFFFF)
                            ], True, "showOnDemand"),
                            },
                        "fonts": [gFont("Regular", 23)],
                        "itemHeight": 30
                        }
                    </convert>
                </widget>
            </screen>
            """

    def __init__(self, session, generalSettings, searchSettings, externalSettings, embeddedSettings, dvbSettings):
        Screen.__init__(self, session)
        self.generalSettings = generalSettings
        self.searchSettings = searchSettings
        self.externalSettings = externalSettings
        self.embeddedSettings = embeddedSettings
        self.dvbSettings = dvbSettings
        self.new_version = None
        self.new_description = None
        
        # Get backup path from config - with proper error handling
        try:
            self.settings_backup_path = self.generalSettings.settingsBackupPath.getValue()
            self.settings_backup_file = os.path.join(self.settings_backup_path, "settings_backup.json")
        except AttributeError:
            # Fallback to default path if setting is missing
            log.error("settingsBackupPath not found in generalSettings, using default")
            self.settings_backup_path = "/etc/enigma2/subssupport"
            self.settings_backup_file = os.path.join(self.settings_backup_path, "settings_backup.json")
            
        menu_items = [
            (_("General settings"), "general"),
            (_("External subtitles settings"), "external"),
            (_("Embedded subtitles settings"), "embedded"),
            (_("Search settings"), "search"),
            (_("DVB player settings"), "dvb"),
            (_("Backup settings"), "backup"),
            (_("Restore settings"), "restore")
        ]
        
        self["menuList"] = List(menu_items)
        self["actionmap"] = ActionMap(["OkCancelActions", "DirectionActions"],
        {
            "up": self["menuList"].selectNext,
            "down": self["menuList"].selectPrevious,
            "ok": self.confirmSelection,
            "cancel": self.close,
        })
        self.onLayoutFinish.append(self.setWindowTitle)
        self.onFirstExecBegin.append(self.checkUpdates)

    def setWindowTitle(self):
        self.setup_title = _("SubsSupport settings")
        self.setTitle(f"{self.setup_title} v{VER}")

    def confirmSelection(self):
        selection = self["menuList"].getCurrent()[1]
        if selection == "general":
            self.openGeneralSettings()
        elif selection == "external":
            self.openExternalSettings()
        elif selection == "embedded":
            self.openEmbeddedSettings()
        elif selection == "search":
            self.openSearchSettings()
        elif selection == "dvb":
            self.openDVBPlayerSettings()
        elif selection == "backup":
            self.backupSettings()
        elif selection == "restore":
            self.restoreSettings()  # Changed from _confirmRestore to restoreSettings

    def openGeneralSettings(self):
        self.session.open(SubsSetupGeneral, self.generalSettings)

    def openSearchSettings(self):
        seeker = E2SubsSeeker(self.session, self.searchSettings, True)
        self.session.open(SubsSearchSettings, self.searchSettings, seeker, True)

    def openExternalSettings(self):
        self.session.open(SubsSetupExternal, self.externalSettings)

    def openEmbeddedSettings(self):
        try:
            from Screens.AudioSelection import QuickSubtitlesConfigMenu
        except ImportError:
            self.session.open(SubsSetupEmbedded, self.embeddedSettings)
        else:
            self.session.open(MessageBox, _("Please change embedded subtitles settings in Settings / System / Subtitles settings"), MessageBox.TYPE_INFO)

    def openDVBPlayerSettings(self):
        self.session.open(SubsSetupDVBPlayer, self.dvbSettings)

    def backupSettings(self):
        try:
            # Get the backup path from config
            backup_path = self.generalSettings.settingsBackupPath.getValue()
            backup_file = os.path.join(backup_path, "settings_backup.json")
            
            # Create backup directory if it doesn't exist
            if not os.path.exists(backup_path):
                os.makedirs(backup_path)
            
            # Verify we can write to the directory
            test_file = os.path.join(backup_path, "test.tmp")
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
            except IOError as e:
                raise Exception(_("Cannot write to backup directory: %s") % str(e))
            
            # Extract all subtitlesSupport settings
            settings_file = '/etc/enigma2/settings'
            if not fileExists(settings_file):
                raise Exception(_("Settings file not found"))
            
            # Extract all settings for our plugin
            with open(settings_file, 'r') as f, open(backup_file, 'w') as backup:
                for line in f:
                    if line.startswith('config.plugins.subtitlesSupport.'):
                        backup.write(line)
            
            # Verify backup was created
            if not fileExists(backup_file):
                raise Exception(_("Backup file creation failed"))
            if os.path.getsize(backup_file) == 0:
                raise Exception(_("Backup file is empty - no settings found"))
            
            self.session.open(MessageBox, _("Settings backup completed successfully!"), MessageBox.TYPE_INFO)
        except Exception as e:
            log.error("Backup failed: %s", str(e), exc_info=True)
            self.session.open(MessageBox, _("Backup failed!") + "\n" + str(e), MessageBox.TYPE_ERROR)

    def restoreSettings(self):
        backup_path = self.generalSettings.settingsBackupPath.getValue()
        backup_file = os.path.join(backup_path, "settings_backup.json")
        
        if not fileExists(backup_file):
            self.session.open(MessageBox, _("No backup file found at: %s") % backup_file, MessageBox.TYPE_ERROR)
            return
        
        message = _("Are you sure you want to restore settings from:\n%s\n\nEnigma2 will restart to apply changes.") % backup_file
        self.session.openWithCallback(self._performRestore, MessageBox, message, MessageBox.TYPE_YESNO)

    def _performRestore(self, answer):
        if not answer:
            return
        
        backup_path = self.generalSettings.settingsBackupPath.getValue()
        backup_file = os.path.join(backup_path, "settings_backup.json")
        
        try:
            if not fileExists(backup_file):
                self.session.open(MessageBox, _("Backup file no longer exists!"), MessageBox.TYPE_ERROR)
                return
            
            # Create a restore script
            restore_script = f"""#!/bin/sh
    # Stop Enigma2
    init 4
    sleep 2

    # Backup current settings
    cp /etc/enigma2/settings /etc/enigma2/settings.bak

    # Remove existing plugin settings
    grep -v '^config.plugins.subtitlesSupport.' /etc/enigma2/settings > /tmp/settings.tmp

    # Add our backed up settings
    cat "{backup_file}" >> /tmp/settings.tmp

    # Replace settings file
    mv /tmp/settings.tmp /etc/enigma2/settings
    rm -f /tmp/settings.tmp

    # Restart Enigma2
    sleep 1
    init 3
    """
            
            script_path = '/tmp/subssupport_restore.sh'
            with open(script_path, 'w') as f:
                f.write(restore_script)
            os.chmod(script_path, 0o755)
            
            # Execute the restore through Console
            self.session.open(
                Console,
                title=_("Restoring Settings..."),
                cmdlist=[script_path],
                closeOnSuccess=False
            )
            self.close()
            
        except Exception as e:
            log.error("Restore failed: %s", str(e), exc_info=True)
            self.session.open(MessageBox, _("Restore failed!") + "\n" + str(e), MessageBox.TYPE_ERROR)


    def checkUpdates(self):
        try:
            url = b"https://raw.githubusercontent.com/popking159/ssupport/main/version.txt"
            getPage(url, timeout=10).addCallback(self.parseUpdateData).addErrback(self.updateError)
        except Exception as e:
            log.error("Update check error: %s", str(e))

    def updateError(self, error):
        log.error("Failed to check for updates: %s", str(error))

    def parseUpdateData(self, data):
        if six.PY3:
            data = data.decode("utf-8")
        else:
            data = data.encode("utf-8")
        
        if data:
            lines = data.split("\n")
            for line in lines:
                if line.startswith("version="):
                    self.new_version = line.split("'")[1] if "'" in line else line.split('"')[1]
                if line.startswith("description="):
                    self.new_description = line.split("'")[1] if "'" in line else line.split('"')[1]
                    break
        
        if self.new_version and self.new_version != VER:
            message = _("New version %s is available.\n\n%s\n\nDo you want to install now?") % (self.new_version, self.new_description)
            self.session.openWithCallback(
                self.installUpdate, 
                MessageBox, 
                message, 
                MessageBox.TYPE_YESNO,
                timeout=10
            )

    def installUpdate(self, answer=False):
        if answer:
            cmd = 'wget -q "--no-check-certificate" https://github.com/popking159/ssupport/raw/main/subssupport-install.sh -O - | /bin/sh'
            self.session.open(Console, title=_("Installing update..."), cmdlist=[cmd], closeOnSuccess=False)


def Plugins(**kwargs):
    from enigma import getDesktop
    screenwidth = getDesktop(0).size().width()
    if screenwidth and screenwidth == 1920:
        iconSET = 'ss_set_FHD.png'
        iconDWN = 'ss_dwn_FHD.png'
        iconPLY = 'ss_ply_FHD.png'
    else:
        iconSET = 'ss_set_HD.png'
        iconDWN = 'ss_dwn_HD.png'
        iconPLY = 'ss_ply_HD.png'

    return [
        PluginDescriptor(name=_('SubsSupport settings'), icon=iconSET, description=_('Change subssupport settings'), where=PluginDescriptor.WHERE_PLUGINMENU, fnc=openSubsSupportSettings),
        PluginDescriptor(name=_('SubsSupport downloader'), icon=iconDWN, description=_('Download subtitles for your videos'), where=PluginDescriptor.WHERE_PLUGINMENU, fnc=openSubtitlesSearch),
        PluginDescriptor(name=_('SubsSupport DVB player'), icon=iconPLY, description=_('watch DVB broadcast with subtitles'), where=PluginDescriptor.WHERE_PLUGINMENU, fnc=openSubtitlesPlayer),
        PluginDescriptor(name=_('SubsSupport settings'), where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=openSubsSupportSettings),
        PluginDescriptor(name=_('SubsSupport downloader'), where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=openSubtitlesSearch),
        PluginDescriptor(name=_('SubsSupport DVB player'), where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=openSubtitlesPlayer)
           ]