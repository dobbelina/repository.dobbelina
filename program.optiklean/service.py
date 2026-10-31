# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Simone Bianchelli
# OptiKlean - Kodi Cleaning and Optimization Addon

import os
import sys

import xbmc
import xbmcaddon
import xbmcvfs

try:
    from default import run_automatic_maintenance, monitor_settings_changes
except ImportError as e:
    xbmc.log(f"OptiKlean: Error importing from default.py: {str(e)}", xbmc.LOGERROR)
    run_automatic_maintenance = None
    monitor_settings_changes = None

# Get the addon path and add it to the system paths
addon = xbmcaddon.Addon()
addon_id = addon.getAddonInfo('id')
addon_path = xbmcvfs.translatePath(addon.getAddonInfo('path'))
sys.path.append(addon_path)

CLEANING_TYPES = (
    "clear_cache_and_temp",
    "clear_unused_thumbnails",
    "clear_addon_leftovers",
    "clear_kodi_packages",
    "optimize_databases",
)

# Path to addon_data for storing logs
addon_data_folder = xbmcvfs.translatePath(f"special://profile/addon_data/{addon.getAddonInfo('id')}/")


def run_scheduled_maintenance(monitor):
    """Run automatic maintenance once, applying the startup delay only once."""
    if run_automatic_maintenance is None:
        addon_id = addon.getAddonInfo('id')
        xbmc.executebuiltin(f'RunScript({addon_id}, autorun)')
        return not monitor.abortRequested()

    delay_seconds = monitor.addon.getSettingInt("autostart_delay") * 60
    if delay_seconds > 0:
        xbmc.log(f"OptiKlean: Applying startup delay once before automatic maintenance ({delay_seconds} seconds)", xbmc.LOGINFO)
        elapsed = 0
        while elapsed < delay_seconds and not monitor.abortRequested():
            step = min(5, delay_seconds - elapsed)
            if monitor.waitForAbort(step):
                return False
            elapsed += step

    if monitor.abortRequested():
        return False

    run_automatic_maintenance(skip_auto_delay=True)
    return True


class OptiKleanMonitor(xbmc.Monitor):
    def __init__(self):
        super(OptiKleanMonitor, self).__init__()
        self.addon = xbmcaddon.Addon()
        self.startup_complete = False
        self.maintenance_executed = False
        self.check_first_run()

    def check_first_run(self):
        """Check if any enabled option has no JSON file and trigger automatic maintenance if needed"""
        try:
            if run_automatic_maintenance is None:
                return

            if not self._needs_first_run():
                return

            xbmc.log("OptiKlean: first run detected for enabled options", xbmc.LOGINFO)
            if self._wait_for_startup_complete():
                xbmc.log("OptiKlean: starting first automatic maintenance", xbmc.LOGINFO)
                if run_scheduled_maintenance(self):
                    self.maintenance_executed = True

        except Exception as e:
            xbmc.log(f"OptiKlean: Error in check_first_run: {str(e)}", xbmc.LOGERROR)

    def _needs_first_run(self):
        profile_path = xbmcvfs.translatePath(self.addon.getAddonInfo('profile'))
        for cleaning in CLEANING_TYPES:
            if not self.addon.getSettingBool(f"{cleaning}_enable"):
                continue

            last_run_file = os.path.join(profile_path, f"last_{cleaning}.json")
            if not xbmcvfs.exists(last_run_file):
                xbmc.log(f"OptiKlean: First run detected for '{cleaning}' enabled but without JSON file", xbmc.LOGINFO)
                return True
        return False

    def _wait_for_startup_complete(self):
        while not self.abortRequested() and not self.startup_complete:
            if self.waitForAbort(5):
                return False
        return not self.abortRequested()

    def onSettingsChanged(self):
        """Handle settings change"""
        try:
            xbmc.log("OptiKlean: settings changed", xbmc.LOGINFO)

            # Make sure the profile folder exists
            if not xbmcvfs.exists(addon_data_folder):
                xbmcvfs.mkdirs(addon_data_folder)

            # Immediately update the automatic settings state
            if monitor_settings_changes:
                monitor_settings_changes()
            else:
                xbmc.log("OptiKlean: monitor_settings_changes not available", xbmc.LOGWARNING)

            # Check if first run needed for newly enabled cleanings
            self.check_first_run()

        except Exception as e:
            xbmc.log(f"OptiKlean: Error handling settings changed: {str(e)}", xbmc.LOGERROR)

    def onNotification(self, sender, method, data):
        xbmc.log(f"OptiKlean: Notification received - {method}", xbmc.LOGDEBUG)

        if method == "GUI.OnScreensaverDeactivated" or method == "Player.OnPlay":
            self.startup_complete = True
            xbmc.log("OptiKlean: Kodi startup completed", xbmc.LOGINFO)

        if method in ["VideoLibrary.OnScanFinished", "AudioLibrary.OnScanFinished"]:
            self.startup_complete = True
            xbmc.log("OptiKlean: Library scan completed, Kodi is ready", xbmc.LOGINFO)

        if method.startswith("VideoLibrary") or method.startswith("AudioLibrary"):
            self.startup_complete = True
            xbmc.log("OptiKlean: Database activity detected, Kodi is active", xbmc.LOGINFO)

        if method.startswith("Input") or method.startswith("GUI"):
            self.startup_complete = True
            xbmc.log("OptiKlean: User interaction detected", xbmc.LOGDEBUG)


# Main service function
if __name__ == '__main__':
    xbmc.log("OptiKlean: Service started", xbmc.LOGINFO)

    # Safety cleanup for the temp_restore folder at Kodi startup
    try:
        from resources.lib.backup_restore import _cleanup_temp_restore

        xbmc.log("OptiKlean: Performing safety cleanup check for temp_restore folder on startup.", xbmc.LOGINFO)
        _cleanup_temp_restore(addon_data_folder)
    except Exception as e:
        xbmc.log(f"OptiKlean: Error during startup safety cleanup: {str(e)}", xbmc.LOGWARNING)

    monitor = OptiKleanMonitor()
    xbmc.sleep(5000)  # 5 seconds initial wait

    wait_time = 3
    idle_counter = 0
    settings_check_counter = 0  # Counter for settings monitoring (every 10 minutes)

    while not monitor.abortRequested():
        xbmc.log(
            f"OptiKlean: Startup complete: {monitor.startup_complete}, "
            f"Automatic maintenance executed: {monitor.maintenance_executed}",
            xbmc.LOGDEBUG,
        )
        if monitor.waitForAbort(wait_time):
            break

        # Background settings monitoring every 10 minutes (600 seconds)
        settings_check_counter += wait_time
        if settings_check_counter >= 600:
            try:
                if monitor_settings_changes:
                    monitor_settings_changes()
                    xbmc.log("OptiKlean: Periodic settings check completed", xbmc.LOGDEBUG)
            except Exception as e:
                xbmc.log(f"OptiKlean: Error in periodic settings check: {str(e)}", xbmc.LOGERROR)
            settings_check_counter = 0

        if not monitor.maintenance_executed:
            try:
                xbmc.sleep(2000)
                if not xbmc.Player().isPlaying():
                    xbmc.log("OptiKlean: Kodi is ready, checking day intervals for automatic maintenance", xbmc.LOGINFO)
                    if run_scheduled_maintenance(monitor):
                        monitor.maintenance_executed = True
                        wait_time = 60
                else:
                    xbmc.log("OptiKlean: Playback in progress, rescheduling cleanup", xbmc.LOGINFO)
                    idle_counter += 1
                    if idle_counter > 10:
                        xbmc.log("OptiKlean: Idle wait timeout, checking intervals", xbmc.LOGINFO)
                        if run_scheduled_maintenance(monitor):
                            monitor.maintenance_executed = True
                            wait_time = 60
            except Exception as e:
                xbmc.log(f"OptiKlean: Error during automatic maintenance: {str(e)}", xbmc.LOGERROR)
                monitor.maintenance_executed = True
                wait_time = 60

    xbmc.log("OptiKlean: Service terminated", xbmc.LOGINFO)