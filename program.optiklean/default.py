# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Simone Bianchelli
# OptiKlean - Kodi Cleaning and Optimization Addon

import sys
import sqlite3
import os
import errno
import fnmatch
import re
import json
import time
import shutil
from datetime import datetime
from resources.lib import backup_restore
from resources.lib import common_utils

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

try:
    addon_handle = int(sys.argv[1])
except IndexError:
    addon_handle = -1
    
base_url = sys.argv[0]

addon = xbmcaddon.Addon()
# Path to addon_data for storing logs
addon_data_folder = xbmcvfs.translatePath(f"special://profile/addon_data/{addon.getAddonInfo('id')}/")

# Ensure addon_data directory exists
if not xbmcvfs.exists(addon_data_folder):
    xbmcvfs.mkdirs(addon_data_folder)

addon_path = xbmcvfs.translatePath(addon.getAddonInfo("path"))
media_path = f"{addon_path}/resources/media/"
fanart_path = f"{media_path}fanart.jpg"
logo_path = f"{media_path}logo.png"

CLEANING_TYPES = (
    "clear_cache_and_temp",
    "clear_unused_thumbnails",
    "clear_addon_leftovers",
    "clear_kodi_packages",
    "optimize_databases",
)
PROTECTED_TEMP_FILES = (
    'kodi.log',
    'kodi.old.log',
    'commoncache.db',
    'commoncache.socket',
)
PROTECTED_TEMP_FOLDERS = ("temp", "archive_cache")
DEBUG_CANCELLED_MESSAGE = "OptiKlean DEBUG: Operation canceled by user"
AUTOMATIC_LOG_UPDATED_MESSAGE = "OptiKlean: Updated automatic cleaning logs after manual execution"
ERROR_IN_PREFIX = "Error in"
DATABASE_SPECIAL_PATH = "special://database/"
DETAILS_WINDOW_XML = "DetailsWindow.xml"
SIZE_CACHE_TTL_SECONDS = 60
ADDON_NAME = "OptiKlean"


def ensure_path_format(path):
    """
    Ensures consistent path formatting across different platforms,
    especially for Android where path handling can be tricky.
    """
    # Remove any trailing slashes
    path = path.rstrip('/')
    # Ensure we have exactly one trailing slash
    return path + '/'


def _ensure_parent_dir(path):
    """Ensure parent directory exists using os first, then xbmcvfs fallback."""
    parent = os.path.dirname(path)
    if not parent:
        return
    if os.path.exists(parent) or xbmcvfs.exists(parent):
        return
    try:
        os.makedirs(parent, exist_ok=True)
    except Exception:
        xbmcvfs.mkdirs(parent)


def _read_text_file(path):
    """Read text preferring os I/O, with xbmcvfs fallback for edge environments."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        f = None
        try:
            f = xbmcvfs.File(path, 'r')
            return f.read()
        finally:
            if f:
                f.close()


def _write_text_file(path, content):
    """Write text preferring os I/O, with xbmcvfs fallback for edge environments."""
    _ensure_parent_dir(path)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return
    except Exception:
        f = None
        try:
            f = xbmcvfs.File(path, 'w')
            f.write(content)
        finally:
            if f:
                f.close()


def _read_json_file(path, default=None):
    """Read JSON with fallback and default on parse/read errors."""
    try:
        return json.loads(_read_text_file(path))
    except Exception:
        return {} if default is None else default


def _write_json_file(path, data):
    """Write JSON with stable formatting through hybrid I/O."""
    _write_text_file(path, json.dumps(data, indent=2, ensure_ascii=False))


# Defines the paths for the log files
log_files = {
    "clear_kodi_temp_folder": os.path.join(addon_data_folder, "clear_kodi_temp_folder.log"),
    "clear_cache_files_from_addon_data": os.path.join(addon_data_folder, "clear_cache_files_from_addon_data.log"),
    "clear_temp_folders_from_addon_data": os.path.join(addon_data_folder, "clear_temp_folders_from_addon_data.log"),
    "clear_temp_folder_from_addons": os.path.join(addon_data_folder, "clear_temp_folder_from_addons.log"), 
    "clear_unused_thumbnails": os.path.join(addon_data_folder, "clear_unused_thumbnails.log"),
    "clear_older_thumbnails": os.path.join(addon_data_folder, "clear_older_thumbnails.log"),
    "clear_orphan_artwork": os.path.join(addon_data_folder, "clear_orphan_artwork.log"),
    "clear_addon_leftovers": os.path.join(addon_data_folder, "clear_addon_leftovers.log"),
    "clear_kodi_packages": os.path.join(addon_data_folder, "clear_kodi_packages.log"),
    "optimize_databases": os.path.join(addon_data_folder, "optimize_databases.log")
}


def get_file_size(file_path):
    """Returns file size in bytes or 0 if file doesn't exist"""
    return common_utils.get_file_size(file_path)


def get_folder_size(folder_path):
    """Calculates the total size of a folder in bytes (cross-platform)"""
    return common_utils.get_folder_size(folder_path)


def format_size(size_bytes):
    """Formats bytes into a readable string (KB, MB, GB)"""
    return common_utils.format_size(size_bytes)


def _get_datetime_display_format():
    date_format = xbmc.getRegion('dateshort')
    time_format = xbmc.getRegion('time').replace('%H', 'HH').replace('%I', 'hh').replace('%M', 'mm')
    format_map = {
        'DD': '%d', 'MM': '%m', 'YYYY': '%Y',
        'hh': '%I', 'mm': '%M', 'ss': '%S', 'HH': '%H',
        'AP': '%p' if '%p' in xbmc.getRegion('time') else '',
    }

    py_date_format = date_format
    py_time_format = time_format
    for source_token, target_token in format_map.items():
        py_date_format = py_date_format.replace(source_token, target_token)
        py_time_format = py_time_format.replace(source_token, target_token)
    return f"{py_date_format} {py_time_format}"


def _build_next_run_info(cleaning, interval_days, full_format):
    last_run_file = os.path.join(addon_data_folder, f"last_{cleaning}.json")
    if not xbmcvfs.exists(last_run_file):
        return "\n(first run pending)"

    try:
        data = _read_json_file(last_run_file, {})
        last_run_timestamp = data.get('timestamp', 0)
        last_run_human = data.get('human_readable', '')
        if last_run_timestamp > 0:
            last_run_local = datetime.fromtimestamp(last_run_timestamp).strftime(full_format)
            next_run = datetime.fromtimestamp(last_run_timestamp + (interval_days * 86400))
            next_run_local = next_run.strftime(full_format)
            day_label = "day" if interval_days == 1 else "days"
            return (
                f" (set on {last_run_local})\n"
                f"next run time: {next_run_local} (every {interval_days} {day_label})"
            )
        if last_run_human:
            return f" (set on {last_run_human})\nnext run time: unknown"
    except Exception as error:
        xbmc.log(f"OptiKlean: Error reading {last_run_file}: {str(error)}", xbmc.LOGERROR)
    return "\n(last run time unknown)"


def _read_monitored_setting_state(prefix):
    current_enable = addon.getSettingBool(f"{prefix}_enable")
    current_interval = addon.getSettingInt(f"{prefix}_interval")
    last_run_file = os.path.join(addon_data_folder, f"last_{prefix}.json")
    if xbmcvfs.exists(last_run_file):
        data = _read_json_file(last_run_file, {})
        last_enable = data.get("enabled", False)
        last_interval = data.get("interval", 7)
    else:
        last_enable = not current_enable
        last_interval = current_interval + 1
    return current_enable, current_interval, last_enable, last_interval, last_run_file


def _sync_monitored_setting(prefix):
    current_enable, current_interval, last_enable, last_interval, last_run_file = _read_monitored_setting_state(prefix)
    if current_enable == last_enable and current_interval == last_interval:
        return False

    if current_enable:
        update_last_run(prefix)
        return True

    if xbmcvfs.exists(last_run_file):
        xbmcvfs.delete(last_run_file)
        xbmc.log(f"OptiKlean: Deleted file {last_run_file} because it is disabled", xbmc.LOGINFO)
    return True


def _get_progress_percentage(progress_dialog, fallback=0):
    if not progress_dialog:
        return fallback
    try:
        return progress_dialog.getPercentage()
    except AttributeError:
        return fallback


def _update_progress_dialog(progress_dialog, message):
    if progress_dialog:
        progress_dialog.update(_get_progress_percentage(progress_dialog), message)


def _create_results_dict(include_total_size=False):
    results = {
        "deleted": [],
        "locked": [],
        "errors": [],
        "protected": [],
    }
    if include_total_size:
        results["total_size"] = 0
    return results


def _log_debug(message, level=xbmc.LOGINFO):
    xbmc.log(f"OptiKlean DEBUG: {message}", level)


def _format_file_size(size):
    """Format a file size in bytes to a human-readable MB/KB/B string."""
    if size >= 1048576:
        return f"{size / 1048576:.2f}MB"
    if size >= 1024:
        return f"{size / 1024:.2f}KB"
    return f"{size}B"



def _delete_file_once(file_path):
    if xbmcvfs.delete(file_path):
        _log_debug(f"Successfully deleted file: {file_path}")
        return DELETE_SUCCESS, ""
    _log_debug(f"xbmcvfs.delete returned False for {file_path}")
    return DELETE_ERROR, "Failed to delete (unknown error)"


def _handle_delete_file_os_error(error, attempt, retry_count, retry_delay, file_path):
    if error.errno in (errno.EACCES, errno.EPERM, errno.EBUSY, errno.EAGAIN):
        _log_debug(f"File locked (attempt {attempt+1}): {file_path} - {error}")
        if attempt < retry_count:
            time.sleep(retry_delay)
            return None, None, True
        return DELETE_LOCKED, f"File locked: {error}", False
    _log_debug(f"OS error deleting file: {file_path} - {error}")
    return DELETE_ERROR, f"Error: {error}", False
def update_automatic_settings_log():
    """Generates/updates the automatic settings log with status and next run"""

    log_path = os.path.join(addon_data_folder, "automatic_cleaning_settings.log")
    full_format = _get_datetime_display_format()

    log_content = addon.getLocalizedString(31166) + "\n\n"

    for cleaning in CLEANING_TYPES:
        enabled = addon.getSettingBool(f"{cleaning}_enable")
        interval_days = addon.getSettingInt(f"{cleaning}_interval")

        if not enabled:
            log_content += f"Automatic {cleaning.replace('_', ' ')} -> disabled\n"
            continue

        next_run_info = _build_next_run_info(cleaning, interval_days, full_format)
        log_content += f"Automatic {cleaning.replace('_', ' ')} -> enabled{next_run_info}\n\n"

    # Write the log file using xbmcvfs
    try:
        _write_text_file(log_path, log_content)
        xbmc.log("OptiKlean: Updated automatic settings log", xbmc.LOGINFO)
    except Exception as e:
        xbmc.log(f"OptiKlean: Error writing automatic settings log: {str(e)}", xbmc.LOGERROR)


def update_last_run(cleaning_type):
    """
    Updates the JSON file with the current values for a given active option.
    """
    try:
        last_run_file = os.path.join(addon_data_folder, f"last_{cleaning_type}.json")
        data = {
            "enabled": addon.getSettingBool(f"{cleaning_type}_enable"),
            "interval": addon.getSettingInt(f"{cleaning_type}_interval"),
            "timestamp": int(time.time()),
            "human_readable": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        _write_json_file(last_run_file, data)
        xbmc.log(f"OptiKlean: Updated last run info for {cleaning_type}", xbmc.LOGINFO)
    except Exception as e:
        xbmc.log(f"OptiKlean: Failed to update last run for {cleaning_type}: {str(e)}", xbmc.LOGERROR)


def monitor_settings_changes():
    """Monitors changes to the settings and updates the log when they change"""
    try:
        settings_changed = False

        for prefix in CLEANING_TYPES:
            if _sync_monitored_setting(prefix):
                settings_changed = True

        if settings_changed:
            update_automatic_settings_log()
            xbmc.log("OptiKlean: Settings log updated!", xbmc.LOGINFO)

    except Exception as e:
        xbmc.log(f"OptiKlean: Error in monitoring: {str(e)}", xbmc.LOGERROR)
        

def get_autostart_delay():
    """Returns the autostart delay in seconds from settings"""
    delay_minutes = addon.getSettingInt("autostart_delay")
    return delay_minutes * 60  # Convert to seconds


# Function to show the main menu
def show_menu():
    
    # Set fanart for the whole menu (background behind the items)
    xbmcplugin.setPluginFanart(addon_handle, fanart_path)

    # Map actions -> icons
    icons = {
        "clear_cache_and_temp": f"{media_path}cache.png",
        "clear_unused_thumbnails": f"{media_path}thumbnails.png",
        "clear_addon_leftovers": f"{media_path}leftovers.png",
        "clear_kodi_packages": f"{media_path}packages.png",
        "optimize_databases": f"{media_path}databases.png",
        "all_in_one_panel": f"{media_path}AIO.png",
        "backup_and_restore": f"{media_path}backup_restore.png",
        "view_logs": f"{media_path}logs.png",
        "show_support": f"{media_path}help.png",
        "open_addon_settings": f"{media_path}settings.png"
    }

    menu_items = [
        (addon.getLocalizedString(31043), "clear_cache_and_temp"),
        (addon.getLocalizedString(31044), "clear_unused_thumbnails"),
        (addon.getLocalizedString(31045), "clear_addon_leftovers"),
        (addon.getLocalizedString(31046), "clear_kodi_packages"),
        (addon.getLocalizedString(31047), "optimize_databases"),
        (addon.getLocalizedString(31048), "all_in_one_panel"),
        (addon.getLocalizedString(31049), "backup_and_restore"),
        (addon.getLocalizedString(31050), "view_logs"),
        (addon.getLocalizedString(31051), "show_support"),
        (addon.getLocalizedString(31052), "open_addon_settings")
    ]

    for label, action in menu_items:
        li = xbmcgui.ListItem(label)
        li.setArt({
            "icon": icons.get(action, ""),
            "thumb": icons.get(action, ""),
            "poster": logo_path,
            "fanart": fanart_path
        })
        li.setProperty("fanart_image", fanart_path)

        xbmcplugin.addDirectoryItem(
            handle=addon_handle,
            url=f"{base_url}?action={action}",
            listitem=li,
            isFolder=False
        )

    xbmcplugin.endOfDirectory(addon_handle)
    
    # NOTE: monitor_settings_changes() removed from here because it slows down opening the menu.
    # Monitoring is handled by service.py in the background.


# Helper function to write the log
def write_log(log_key, content, append=False):
    """
    Writes content to the specified log file with automatic timestamp footer.
    If append is True, the content will be appended to the file instead of overwriting it.
    """
    common_utils.write_log(log_files, log_key, content, append)


# Constants for the file deletion status
DELETE_SUCCESS = "success"
DELETE_LOCKED = "locked"
DELETE_ERROR = "error"


# Improved helper function to delete files with file lock detection
def delete_file(file_path, retry_count=2, retry_delay=0.5, progress_dialog=None):
    """
    Delete a file with lock detection and retry logic.
    Returns:
        tuple: (status, error_message)
        status can be: "success", "locked", or "error"
    """
    _log_debug(f"Attempting to delete file: {file_path}")
    
    if not xbmcvfs.exists(file_path):
        _log_debug(f"File doesn't exist: {file_path}")
        return DELETE_SUCCESS, ""
    
    if progress_dialog:
        filename = file_path.split('/')[-1] if file_path else ""
        _update_progress_dialog(progress_dialog, f"Processing: {filename}")
    
    for attempt in range(retry_count + 1):
        try:
            _log_debug(f"Delete attempt {attempt+1}/{retry_count+1} for {file_path}")
            return _delete_file_once(file_path)
        except OSError as error:
            status, message, should_retry = _handle_delete_file_os_error(
                error,
                attempt,
                retry_count,
                retry_delay,
                file_path,
            )
            if should_retry:
                continue
            return status, message
        except Exception as error:
            _log_debug(f"Unexpected error deleting file: {file_path} - {error}")
            return DELETE_ERROR, f"Unexpected error: {error}"
    
    _log_debug(f"File appears to be locked after all retry attempts: {file_path}")
    return DELETE_LOCKED, "File appears to be locked by another process"


# Function to check whether it is safe to delete a file
def is_safe_to_delete(file_path, temp_path=None, addon_id=None, critical_cache_addons=None):
    """
    Check if a file can be safely deleted
    :param file_path: Full path to the file
    :param temp_path: Path to temp folder (optional)
    :param addon_id: Addon ID (optional)
    :param critical_cache_addons: List of protected addons (optional)
    :return: True if safe to delete, False if protected
    """
    # Files always protected in temp folder
    temp_protected_files = PROTECTED_TEMP_FILES
    
    # Check if in temp folder
    is_temp_file = temp_path and temp_path in file_path
    
    # 1. Protect specific files in temp folder
    if is_temp_file:
        filename = file_path.split('/')[-1]
        if filename in temp_protected_files:
            return False
        # Skip all other checks for temp folder
        return True
    
    # 2. Protect critical addon caches (only outside temp folder)
    if (
        critical_cache_addons
        and addon_id
        and addon_id in critical_cache_addons
        and (
            "cache" in file_path.lower()
            or "temp" in file_path.lower()
        )
    ):

        return False
    
    # 3. Protect specific extensions (only outside temp folder)
    protected_extensions = ['.db', '.xml', '.json', '.ini', '.cfg']
    if any(file_path.lower().endswith(ext) for ext in protected_extensions):
        return False
        
    return True


# Function to check whether a folder should be excluded from cleaning
def is_excluded_folder(_folder_path):
    """Checks whether a folder should be excluded from cleaning"""
    return False  # placeholder: no folders excluded at this time


# Function to check whether the path is a critical cache to preserve
def is_critical_cache(addon_id, folder_path, critical_cache_addons):
    """Checks whether the path is a critical cache to preserve"""
    if addon_id in critical_cache_addons:
        # For inputstreamhelper, we may want to preserve specific folders
        if addon_id == "script.module.inputstreamhelper":
            # For example, preserve the contents of the "storage" or "download" subfolders
            if "storage" in folder_path or "download" in folder_path:
                return True
        # By default, we preserve all the caches of critical addons
        return True
    return False


# Function to safely delete files and folders recursively
def delete_directory_recursive(directory_path, progress_dialog=None, parent_results=None):
    """
    Recursively deletes a folder and all its contents.
    - Returns True if the folder was deleted or did not exist
    - Returns False if there was a problem during deletion
    """

    # Ensure consistent path format
    directory_path = ensure_path_format(directory_path)
    xbmc.log(f"OptiKlean DEBUG: Entering delete_directory_recursive for {directory_path}", xbmc.LOGINFO)   
 
    # If the folder does not exist, we consider the operation successful
    if not xbmcvfs.exists(directory_path):
        xbmc.log(f"OptiKlean DEBUG: Directory doesn't exist: {directory_path}", xbmc.LOGINFO)
        return True

    # Initialize the results if they were not provided by the caller
    if parent_results is None:
        parent_results = {
            "deleted": [],
            "locked": [],
            "errors": [],
            "protected": []
        }
    
    try:
        # Get lists of files and folders
        xbmc.log(f"OptiKlean DEBUG: Attempting to list contents of {directory_path}", xbmc.LOGINFO)
        dirs, files = xbmcvfs.listdir(directory_path)
        xbmc.log(f"OptiKlean DEBUG: Files found in {directory_path}: {files}", xbmc.LOGINFO)
        xbmc.log(f"OptiKlean DEBUG: Subdirectories found in {directory_path}: {dirs}", xbmc.LOGINFO)
        
        # First delete all files
        for file in files:
            file_path = xbmcvfs.makeLegalFilename(ensure_path_format(directory_path) + file)
            xbmc.log(f"OptiKlean DEBUG: Attempting to delete file: {file_path}", xbmc.LOGINFO)
            
            _update_progress_dialog(progress_dialog, f"Deleting file: {file}")
            
            # Delete the file
            status, error = delete_file(file_path, progress_dialog=progress_dialog)
            if status == DELETE_SUCCESS:
                parent_results["deleted"].append(file_path)
                xbmc.log(f"OptiKlean DEBUG: Successfully deleted file: {file_path}", xbmc.LOGINFO)
            elif status == DELETE_LOCKED:
                parent_results["locked"].append(f"{file_path} (locked)")
                xbmc.log(f"OptiKlean DEBUG: File is locked: {file_path}", xbmc.LOGINFO)
                return False  # We cannot delete the folder if a file is locked
            else:
                parent_results["errors"].append(f"{file_path} ({error})")
                xbmc.log(f"OptiKlean DEBUG: Error deleting file: {file_path} - {error}", xbmc.LOGINFO)
                return False  # We cannot delete the folder if there is an error
        
        # Then recursively delete all subfolders
        for folder in dirs:
            folder_path = xbmcvfs.makeLegalFilename(ensure_path_format(directory_path) + folder)
            xbmc.log(f"OptiKlean DEBUG: Processing subfolder: {folder_path}", xbmc.LOGINFO)
            
            _update_progress_dialog(progress_dialog, f"Processing folder: {folder}")
            
            # Recursive call to delete the subfolder
            subfolder_result = delete_directory_recursive(folder_path, progress_dialog, parent_results)
            xbmc.log(f"OptiKlean DEBUG: Subfolder processing result: {subfolder_result} for {folder_path}", xbmc.LOGINFO)
            if not subfolder_result:
                xbmc.log(f"OptiKlean DEBUG: Failed to process subfolder: {folder_path}", xbmc.LOGINFO)
                return False  # We cannot delete the main folder if a subfolder cannot be deleted
        
        # Finally, delete the folder itself
        xbmc.log(f"OptiKlean DEBUG: Attempting to remove directory: {directory_path}", xbmc.LOGINFO)
        if xbmcvfs.rmdir(directory_path):
            parent_results["deleted"].append(f"Deleted folder: {directory_path}")
            xbmc.log(f"OptiKlean DEBUG: Successfully removed directory: {directory_path}", xbmc.LOGINFO)
            return True
        else:
            parent_results["errors"].append(f"Failed to delete folder: {directory_path}")
            xbmc.log(f"OptiKlean DEBUG: Failed to remove directory: {directory_path}", xbmc.LOGINFO)
            return False
    
    except Exception as e:
        xbmc.log(f"OptiKlean DEBUG: Exception in delete_directory_recursive: {str(e)}", xbmc.LOGERROR)
        parent_results["errors"].append(f"Error processing folder {directory_path}: {str(e)}")
        return False


# Function to safely delete files and folders with a results report
def delete_files_in_folder(
    folder, 
    progress_dialog=None, 
    safe_check=True,
    addon_id=None, 
    temp_path=None, 
    critical_cache_addons=None,
):
    """
    Safely deletes files and folders with a results report
    """
    # Ensure consistent path format
    folder = ensure_path_format(folder)
    xbmc.log(f"OptiKlean DEBUG: Starting delete_files_in_folder for {folder}", xbmc.LOGINFO)
    
    results = {
        "deleted": [],
        "locked": [],
        "errors": [],
        "protected": []
    }

    if not xbmcvfs.exists(folder):
        xbmc.log(f"OptiKlean DEBUG: Folder does not exist: {folder}", xbmc.LOGINFO)
        results["errors"].append(f"Folder does not exist: {folder}")
        return results

    try:
        # Get separate lists of folders and files
        xbmc.log(f"OptiKlean DEBUG: Attempting to list contents of {folder}", xbmc.LOGINFO)
        dirs, files = xbmcvfs.listdir(folder)
        xbmc.log(f"OptiKlean DEBUG: Directories found in {folder}: {dirs}", xbmc.LOGINFO)
        xbmc.log(f"OptiKlean DEBUG: Files found in {folder}: {files}", xbmc.LOGINFO)
        total_items = len(dirs) + len(files)
        
        # Process files first
        for index, item in enumerate(files):
            if progress_dialog and progress_dialog.iscanceled():
                xbmc.log(DEBUG_CANCELLED_MESSAGE, xbmc.LOGINFO)
                break

            item_path = xbmcvfs.makeLegalFilename(ensure_path_format(folder) + item)
            xbmc.log(f"OptiKlean DEBUG: Processing file: {item_path}", xbmc.LOGINFO)
            
            # Update progress
            if progress_dialog:
                percent = int((index / total_items) * 100) if total_items > 0 else 0
                progress_dialog.update(percent, f"Processing file: {item}")

            if safe_check and not is_safe_to_delete(item_path, temp_path):
                xbmc.log(f"OptiKlean DEBUG: File protected (not safe to delete): {item_path}", xbmc.LOGINFO)
                results["protected"].append(item_path)
                continue

            success, error = delete_file(item_path)
            if success == DELETE_SUCCESS:
                xbmc.log(f"OptiKlean DEBUG: Successfully deleted file: {item_path}", xbmc.LOGINFO)
                results["deleted"].append(item_path)
            elif success == DELETE_LOCKED:
                xbmc.log(f"OptiKlean DEBUG: File is locked: {item_path}", xbmc.LOGINFO)
                results["locked"].append(f"{item_path} (locked)")
            else:
                xbmc.log(f"OptiKlean DEBUG: Error deleting file: {item_path} - {error}", xbmc.LOGINFO)
                results["errors"].append(f"{item_path} ({error})")

        # Then process the folders
        for index, item in enumerate(dirs, start=len(files)):
            if progress_dialog and progress_dialog.iscanceled():
                xbmc.log(DEBUG_CANCELLED_MESSAGE, xbmc.LOGINFO)
                break

            item_path = xbmcvfs.makeLegalFilename(ensure_path_format(folder) + item)
            xbmc.log(f"OptiKlean DEBUG: Processing folder: {item_path}", xbmc.LOGINFO)
            
            # Update progress
            if progress_dialog:
                percent = int((index / total_items) * 100) if total_items > 0 else 0
                progress_dialog.update(percent, f"Processing folder: {item}")
            
            # Check whether it is an excluded folder
            if is_excluded_folder(item_path):
                xbmc.log(f"OptiKlean DEBUG: Folder excluded from processing: {item_path}", xbmc.LOGINFO)
                results["protected"].append(f"Excluded folder (protected): {item_path}")
                continue
            
            # Check whether it is a critical cache before proceeding
            if critical_cache_addons and addon_id and is_critical_cache(addon_id, item_path, critical_cache_addons):
                xbmc.log(f"OptiKlean DEBUG: Folder is a critical cache (protected): {item_path}", xbmc.LOGINFO)
                results["protected"].append(f"Protected cache (critical addon): {item_path}")
                continue

            xbmc.log(f"OptiKlean DEBUG: About to process directory recursively: {item_path}", xbmc.LOGINFO)

            # Recursively delete the folder
            folder_deleted = delete_directory_recursive(item_path, progress_dialog, results)
            xbmc.log(f"OptiKlean DEBUG: Result of recursive deletion: {folder_deleted} for {item_path}", xbmc.LOGINFO)

    except Exception as e:
        xbmc.log(f"OptiKlean DEBUG: Exception in delete_files_in_folder: {str(e)}", xbmc.LOGERROR)
        results["errors"].append(f"Error listing {folder}: {str(e)}")

    xbmc.log(f"OptiKlean DEBUG: Completed delete_files_in_folder for {folder}. Results: deleted={len(results['deleted'])}, locked={len(results['locked'])}, errors={len(results['errors'])}, protected={len(results['protected'])}", xbmc.LOGINFO)
    return results


def map_directory_structure(folder_path):
    """
    Recursively maps the directory structure using xbmcvfs.listdir() with try/except
    Returns a dictionary representing the folder structure or None if path is invalid
    """
    folder_path = ensure_path_format(folder_path)
    structure = {
        'path': folder_path,
        'files': [],
        'subfolders': [],
        'accessible': False
    }
    
    try:
        dirs, files = xbmcvfs.listdir(folder_path)
        structure['accessible'] = True
        structure['files'] = files
        
        xbmc.log(f"OptiKlean DEBUG: Mapped {folder_path} - files: {files}", xbmc.LOGINFO)
        
        for dir_name in dirs:
            # Fix: properly join paths without duplicate base paths
            subfolder_path = ensure_path_format(os.path.join(folder_path, dir_name))
            xbmc.log(f"OptiKlean DEBUG: Processing subfolder: {subfolder_path}", xbmc.LOGINFO)
            subfolder_structure = map_directory_structure(subfolder_path)
            if subfolder_structure:
                structure['subfolders'].append(subfolder_structure)
                xbmc.log(f"OptiKlean DEBUG: Added subfolder {subfolder_path} with {len(subfolder_structure['files'])} files and {len(subfolder_structure['subfolders'])} subfolders", xbmc.LOGINFO)
                
    except Exception as e:
        xbmc.log(f"OptiKlean DEBUG: Error mapping directory {folder_path}: {str(e)}", xbmc.LOGERROR)
        structure['accessible'] = False
        
    return structure if structure['accessible'] else None


def _process_temp_subfolder(folder, temp_path, safe_check, progress_dialog, parent_results):
    """Process a subfolder of Kodi temp during clear_kodi_temp_folder."""
    full_path = folder['path']
    xbmc.log(f"OptiKlean DEBUG: Processing folder: {full_path}", xbmc.LOGINFO)
    
    # Skip excluded folders
    if is_excluded_folder(full_path):
        xbmc.log(f"OptiKlean DEBUG: Excluded folder skipped: {full_path}", xbmc.LOGINFO)
        parent_results["protected"].append(f"Excluded folder: {full_path}")
        return True
        
    # Get folder name and relative path
    folder_name = full_path.rstrip('/').split('/')[-1]
          
    if (folder_name in PROTECTED_TEMP_FOLDERS):
        xbmc.log(f"OptiKlean DEBUG: Protected folder in temp - processing contents only: {full_path}", xbmc.LOGINFO)
        
        # Process files in this folder
        for file_name in folder['files']:
            if progress_dialog and progress_dialog.iscanceled():
                return False
                
            file_path = os.path.join(full_path, file_name)
            xbmc.log(f"OptiKlean DEBUG: Processing file: {file_path}", xbmc.LOGINFO)
            
            if safe_check and not is_safe_to_delete(file_path, temp_path):
                xbmc.log(f"OptiKlean DEBUG: Protected file skipped: {file_path}", xbmc.LOGINFO)
                parent_results["protected"].append(file_path)
                continue
            
            # Get file size BEFORE deletion
            file_size = get_file_size(file_path) or 0
                
            status, error = delete_file(file_path, progress_dialog=progress_dialog)
            if status == DELETE_SUCCESS:
                parent_results["deleted"].append((file_path, file_size))  # Store as tuple
                parent_results["total_size"] += file_size
                xbmc.log(f"OptiKlean DEBUG: Successfully deleted file: {file_path} (size: {file_size} bytes)", xbmc.LOGINFO)
            elif status == DELETE_LOCKED:
                parent_results["locked"].append(file_path)
            else:
                parent_results["errors"].append(f"{file_path} ({error})")
        
        # Process all subfolders recursively
        for subfolder in folder['subfolders']:
            _process_temp_subfolder(subfolder, temp_path, safe_check, progress_dialog, parent_results)
        
        return True            

    # Process files in this folder (for non-protected folders)
    for file_name in folder['files']:
        if progress_dialog and progress_dialog.iscanceled():
            return False
            
        file_path = os.path.join(full_path, file_name)
        xbmc.log(f"OptiKlean DEBUG: Processing file: {file_path}", xbmc.LOGINFO)
        
        # Only check protected files if safe_check is True (for non-root files)
        if safe_check and not is_safe_to_delete(file_path, temp_path):
            xbmc.log(f"OptiKlean DEBUG: Protected file skipped: {file_path}", xbmc.LOGINFO)
            parent_results["protected"].append(file_path)
            continue

        # Get file size BEFORE deletion
        file_size = get_file_size(file_path) or 0
        
        status, error = delete_file(file_path, progress_dialog=progress_dialog)

        if status == DELETE_SUCCESS:
            parent_results["deleted"].append((file_path, file_size))  # Store as tuple
            parent_results["total_size"] += file_size
            xbmc.log(f"OptiKlean DEBUG: Successfully deleted file: {file_path} (size: {file_size} bytes)", xbmc.LOGINFO)
        elif status == DELETE_LOCKED:
            parent_results["locked"].append(file_path)
        else:
            parent_results["errors"].append(f"{file_path} ({error})")
    
    # Process all subfolders recursively
    for subfolder in folder['subfolders']:
        _process_temp_subfolder(subfolder, temp_path, safe_check, progress_dialog, parent_results)
        
    # Try to delete the folder itself if empty
    try:
        dirs, files = xbmcvfs.listdir(full_path)
        if not dirs and not files:
            if xbmcvfs.rmdir(full_path):
                parent_results["deleted"].append((f"Deleted folder: {full_path}", 0))  # Store as tuple with size 0
                xbmc.log(f"OptiKlean DEBUG: Successfully deleted folder: {full_path}", xbmc.LOGINFO)
            else:
                parent_results["errors"].append(f"Failed to delete folder: {full_path}")
                xbmc.log(f"OptiKlean DEBUG: Failed to delete folder: {full_path} (may not be empty)", xbmc.LOGINFO)
        else:
            remaining = len(dirs) + len(files)
            parent_results["errors"].append(f"Folder not empty: {full_path} ({remaining} items remaining)")
            xbmc.log(f"OptiKlean DEBUG: Folder not empty, contains {remaining} items: {full_path}", xbmc.LOGINFO)
    except Exception as e:
        parent_results["errors"].append(f"Error deleting folder {full_path}: {str(e)}")
        xbmc.log(f"OptiKlean DEBUG: Exception deleting folder {full_path}: {str(e)}", xbmc.LOGERROR)
        
    return True


def clear_kodi_temp_folder(temp_path, progress_dialog=None, safe_check=True):
    """
    Clears the Kodi temp folder while preserving log files and critical caches
    Returns dictionary with results (deleted, locked, errors, protected)
    """
    results = _create_results_dict(include_total_size=True)

    temp_path = ensure_path_format(temp_path)
    xbmc.log(f"OptiKlean DEBUG: Starting clear_kodi_temp_folder for {temp_path} with safe_check={safe_check}", xbmc.LOGINFO)
    
    try:
        # First map the entire directory structure
        progress_dialog and progress_dialog.update(0, "Mapping temp folder structure...")
        folder_structure = map_directory_structure(temp_path)
        
        if not folder_structure:
            results["errors"].append(f"Could not access temp folder: {temp_path}")
            xbmc.log("OptiKlean DEBUG: Could not map temp folder structure", xbmc.LOGERROR)
            return results
        
        xbmc.log(f"OptiKlean DEBUG: Completed mapping temp folder structure. Root files: {len(folder_structure['files'])}, Subfolders: {len(folder_structure['subfolders'])}", xbmc.LOGINFO)
        
        # Process all files in the root first - ALWAYS protect log files regardless of safe_check
        for file_name in folder_structure['files']:
            if progress_dialog and progress_dialog.iscanceled():
                break
                
            file_path = os.path.join(temp_path, file_name)
            xbmc.log(f"OptiKlean DEBUG: Processing root file: {file_path}", xbmc.LOGINFO)
            
            # First check if this is a protected file (like kodi.log)
            if not is_safe_to_delete(file_path, temp_path):
                xbmc.log(f"OptiKlean DEBUG: Protected file skipped: {file_path}", xbmc.LOGINFO)
                results["protected"].append(file_path)
                continue
            
            # Get file size BEFORE deletion
            file_size = get_file_size(file_path) or 0
                
            status, error = delete_file(file_path, progress_dialog=progress_dialog)
            if status == DELETE_SUCCESS:
                results["deleted"].append((file_path, file_size))  # Store as tuple with size
                results["total_size"] += file_size
                xbmc.log(f"OptiKlean DEBUG: Successfully deleted file: {file_path} (size: {file_size} bytes)", xbmc.LOGINFO)
            elif status == DELETE_LOCKED:
                results["locked"].append(file_path)
            else:
                results["errors"].append(f"{file_path} ({error})")
    

        # Process all top-level folders (this will recursively process their contents)
        for folder in folder_structure['subfolders']:
            if progress_dialog and progress_dialog.iscanceled():
                break
            _process_temp_subfolder(folder, temp_path, safe_check, progress_dialog, results)
        
    except Exception as e:
        results["errors"].append(f"General error in clear_kodi_temp_folder: {str(e)}")
        xbmc.log(f"OptiKlean DEBUG: General error in clear_kodi_temp_folder: {str(e)}", xbmc.LOGERROR)
    
    xbmc.log(f"OptiKlean DEBUG: Completed clear_kodi_temp_folder. Results: deleted={len(results['deleted'])}, locked={len(results['locked'])}, errors={len(results['errors'])}, protected={len(results['protected'])}", xbmc.LOGINFO)
    return results


def _process_addon_temp_folder(folder, addons_temp_path, results, progress):
    """Process one subfolder of the addons temp directory; returns bytes freed."""
    size_freed = 0
    full_path = folder['path']
    xbmc.log(f"OptiKlean DEBUG: Processing folder: {full_path}", xbmc.LOGINFO)

    for file_name in folder['files']:
        if progress.iscanceled():
            return size_freed

        file_path = os.path.join(full_path, file_name)
        xbmc.log(f"OptiKlean DEBUG: Processing file: {file_path}", xbmc.LOGINFO)

        if not is_safe_to_delete(file_path, addons_temp_path):
            xbmc.log(f"OptiKlean DEBUG: Protected file skipped: {file_path}", xbmc.LOGINFO)
            results["protected"].append(file_path)
            continue

        file_size = get_file_size(file_path) or 0
        status, error = delete_file(file_path, progress_dialog=progress)

        if status == DELETE_SUCCESS:
            results["deleted"].append((file_path, file_size))
            results["total_size"] += file_size
            size_freed += file_size
            xbmc.log(f"OptiKlean DEBUG: Successfully deleted file: {file_path} (size: {file_size} bytes)", xbmc.LOGINFO)
        elif status == DELETE_LOCKED:
            results["locked"].append(file_path)
            xbmc.log(f"OptiKlean DEBUG: File is locked: {file_path}", xbmc.LOGINFO)
        else:
            results["errors"].append(f"{file_path} ({error})")
            xbmc.log(f"OptiKlean DEBUG: Error deleting file: {file_path} - {error}", xbmc.LOGERROR)

    for subfolder in folder['subfolders']:
        size_freed += _process_addon_temp_folder(subfolder, addons_temp_path, results, progress)

    return size_freed


def clear_cache_and_temp(auto_mode=False, skip_auto_delay=False):

    # Initialize the cumulative total
    total_freed_all_options = 0

    # Options:
    # 0: Clear Kodi temp folder (preserving log files)
    # 1: Clear cache files from addon data
    # 2: Clear temp folders from addon data
    # 3: Clear temp folder from addons
    choices = [
        addon.getLocalizedString(31070),
        addon.getLocalizedString(31071),
        addon.getLocalizedString(31072),
        addon.getLocalizedString(31073)
    ]
    
    temp_path = ensure_path_format(xbmcvfs.translatePath("special://temp/"))
    addon_data_path = ensure_path_format(xbmcvfs.translatePath("special://profile/addon_data/"))

    if not auto_mode:
        selected = xbmcgui.Dialog().multiselect(addon.getLocalizedString(31053), choices)  # "Select cache/temp to clear"
        if selected is None:
            return
    else:
        # Automatic mode: apply the delay, if set, before starting
        delay_seconds = get_autostart_delay()
        if delay_seconds > 0 and not skip_auto_delay:
            xbmc.log(f"OptiKlean: Automatic cleaning delayed by {delay_seconds} seconds", xbmc.LOGINFO)
            time.sleep(delay_seconds)
        
        selected = [0, 1, 2, 3]
  
    # List of addons with essential caches that must not be deleted
    critical_cache_addons = [
        "script.module.inputstreamhelper",
        "inputstream.adaptive",
        "inputstream.rtmp",
        "script.module.resolveurl",
        "plugin.video.youtube",
        'plugin.video.netflix',
        'plugin.video.amazon',
        'plugin.video.disneyplus',
        'script.common.plugin.cache',
        'pvr.iptvsimple'
    ]
    
    progress = xbmcgui.DialogProgress()
    progress.create(ADDON_NAME, addon.getLocalizedString(31055))  # "Preparing to clear cache..."
    
    try:
        # Option 0: Clear Kodi temp folder (preserving logs)
        if selected and 0 in selected:
            start_time = time.perf_counter()
            progress.update(0, addon.getLocalizedString(31082))  # "Clearing Kodi temp folder (preserving log files)..."
            
            # Log that we are starting the operation
            xbmc.log("OptiKlean: Starting to clear Kodi temp folder", xbmc.LOGINFO)
            xbmc.log(f"OptiKlean: Using temp path: {temp_path}", xbmc.LOGINFO)
            
            # Use safe_check=False to delete all files except protected ones
            results = clear_kodi_temp_folder(temp_path, progress, safe_check=True)
                                          
            total_freed_all_options += results.get("total_size", 0)
            
            # Actual check before marking as completed
            if results and (results.get("deleted") or results.get("total_size", 0) > 0):
                xbmc.log(f"OptiKlean: Temp folder cleanup successful, deleted {len(results.get('deleted', []))} items", xbmc.LOGINFO)
            else:
                xbmc.log("OptiKlean: Temp folder cleanup didn't delete any files", xbmc.LOGINFO)

            log_content = addon.getLocalizedString(31093) + "\n\n"  # "Kodi temp folder cleaning results:"
            
            if results["deleted"]:
                # Separate files and folders, calculate precise total
                deleted_files = []
                deleted_folders = []
                total_bytes = 0
                
                for item in results["deleted"]:
                    if isinstance(item, tuple):
                        file_path, file_size = item
                        if "Deleted folder:" in file_path:  # It's a folder entry
                            _, full_path = file_path.split(":", 1)
                            folder_name = os.path.basename(full_path.strip().rstrip("/"))
                            deleted_folders.append(folder_name)
                        elif file_size > 0:  # It's a file with size
                            deleted_files.append((os.path.basename(file_path), file_size))
                            total_bytes += file_size
                
                # Precise size conversion (bytes → MB)
                total_mb = total_bytes / (1024 * 1024)
                
                # Build log output
                if deleted_files:
                    log_content += addon.getLocalizedString(31098).format(count=len(deleted_files), size=total_mb) + "\n"  # "Files deleted: {count} ({size:.3f} MB freed)"
                    for filename, size in deleted_files:
                        if size >= 1048576:  # ≥1MB
                            log_content += f"  - {filename} ({size/1048576:.3f} MB)\n"
                        elif size >= 1024:  # ≥1KB
                            log_content += f"  - {filename} ({size/1024:.3f} KB)\n"
                        else:
                            log_content += f"  - {filename} ({size} B)\n"
                
                if deleted_folders:
                    log_content += "\n" + addon.getLocalizedString(31099).format(count=len(deleted_folders)) + "\n"  # "Folders deleted: {count}"
                    for folder in deleted_folders:
                        log_content += f"  - {folder}\n"
                
                log_content += "\n"
            
            if results["locked"]:
                log_content += addon.getLocalizedString(31100) + "\n"  # "Files in use (locked):"
                log_content += "  " + "\n  ".join([os.path.basename(f) for f in results["locked"]]) + "\n\n"
            
            if results["errors"]:
                log_content += addon.getLocalizedString(31101) + "\n"  # "Errors:"
                log_content += "  " + "\n  ".join(results["errors"]) + "\n\n"
            
            if results["protected"]:
                log_content += addon.getLocalizedString(31102) + "\n"  # "Protected items (not deleted):"
                protected_items = [os.path.basename(f) for f in results["protected"][:20]]
                log_content += "  " + "\n  ".join(protected_items)
                if len(results["protected"]) > 20:
                    log_content += "\n  " + addon.getLocalizedString(31103).format(count=len(results["protected"]) - 20)  # "... and {count} more items"
                log_content += "\n\n"

            # Log completion
            xbmc.log(f"OptiKlean: Completed clearing Kodi temp folder. Deleted: {len(results['deleted'])}, Protected: {len(results['protected'])}, Errors: {len(results['errors'])}", xbmc.LOGINFO)
            execution_time = round(time.perf_counter() - start_time, 2)
            log_content += addon.getLocalizedString(31104).format(time=execution_time) + "\n"  # "Running time: {time}s"
            write_log("clear_kodi_temp_folder", log_content.rstrip() + "\n")

        # Option 1: Clear cache files from addon data
        if selected and 1 in selected and not progress.iscanceled():
            start_time = time.perf_counter()
            progress.update(0, addon.getLocalizedString(31077))  # "Scanning addon data..."
            
            log_content = addon.getLocalizedString(31094) + "\n\n"  # "Addon cache folders cleaning results:"
            xbmc.log("OptiKlean: Starting addon cache cleaning", xbmc.LOGINFO)
            total_size_freed = 0
            option1_size_freed = 0

            if not xbmcvfs.exists(addon_data_path):
                error_msg = f"Addon data path does not exist: {addon_data_path}"
                xbmc.log(f"OptiKlean: {error_msg}", xbmc.LOGERROR)
                log_content += error_msg + "\n"
            else:
                try:
                    addon_folders, _ = xbmcvfs.listdir(addon_data_path)
                    xbmc.log(f"OptiKlean: Found {len(addon_folders)} addon folders", xbmc.LOGINFO)
                    
                    if not addon_folders:
                        log_content += addon.getLocalizedString(31106) + "\n"
                    else:
                        total_addons = len(addon_folders)
                        has_skips = False

                        for index, addon_id in enumerate(addon_folders):
                            if progress.iscanceled():
                                break
                            
                            progress.update((index * 100) // total_addons, addon.getLocalizedString(31090).format(addon_id=addon_id))  # "Checking {addon_id}..."
                            
                            # Skip critical addons
                            if addon_id in critical_cache_addons:
                                if not has_skips:
                                    log_content += "\n"
                                    has_skips = True
                                log_content += addon.getLocalizedString(31107).format(addon_id=addon_id) + "\n"
                                continue
                            
                            cache_path = xbmcvfs.makeLegalFilename(f"{addon_data_path}/{addon_id}/cache/")
                            
                            if xbmcvfs.exists(cache_path):
                                try:
                                    _, files = xbmcvfs.listdir(cache_path)
                                    addon_deleted = []
                                    addon_size_freed = 0
                                    addon_errors = []
                                    addon_protected = []

                                    for file_name in files:
                                        if progress.iscanceled():
                                            break
                                            
                                        file_path = xbmcvfs.makeLegalFilename(f"{cache_path}/{file_name}")
                                        
                                        # Get file size before deletion
                                        file_size = get_file_size(file_path) or 0
                                        
                                        xbmc.log(f"OptiKlean DEBUG: File {file_path} size: {file_size} bytes", xbmc.LOGDEBUG)
                                        
                                        if is_safe_to_delete(file_path, addon_id=addon_id, 
                                                          critical_cache_addons=critical_cache_addons):
                                            status, error = delete_file(file_path)
                                            
                                            if status == DELETE_SUCCESS:
                                                addon_deleted.append((file_name, file_size))
                                                addon_size_freed += file_size
                                                total_size_freed += file_size
                                                option1_size_freed += file_size
                                                
                                                xbmc.log(f"OptiKlean DEBUG: Successfully deleted {file_path}, added {file_size} bytes to total", xbmc.LOGDEBUG)
                                            elif status == DELETE_LOCKED:
                                                addon_errors.append(f"Locked: {file_name}")
                                            else:
                                                addon_errors.append(f"Error: {file_name} ({error})")
                                        else:
                                            addon_protected.append(file_name)
                                    
                                    # Add results to log
                                    if addon_deleted or addon_errors or addon_protected:
                                        log_content += f"{addon_id} (cache):\n"
                                        
                                        if addon_deleted:
                                            size_kb = addon_size_freed / 1024
                                            log_content += addon.getLocalizedString(31108).format(count=len(addon_deleted), size=size_kb) + "\n"
                                            for file_name, file_size in addon_deleted:
                                                size_str = _format_file_size(file_size)
                                                log_content += f"    - {file_name} ({size_str})\n"
                                        
                                        if addon_protected:
                                            log_content += addon.getLocalizedString(31109).format(count=len(addon_protected)) + "\n"
                                            for file_name in addon_protected:
                                                log_content += f"    - {file_name}\n"
                                        
                                        if addon_errors:
                                            log_content += addon.getLocalizedString(31110).format(count=len(addon_errors)) + "\n"
                                            for error in addon_errors:
                                                log_content += f"    - {error}\n"
                                        
                                        log_content += "\n"
                                
                                except Exception as e:
                                    log_content += f"{addon_id} ERROR: {str(e)}\n"
                    
                except Exception as e:
                    log_content += f"Error listing addon_data: {str(e)}\n"

            xbmc.log(f"OptiKlean DEBUG: Total size freed in option 1: {total_size_freed} bytes ({total_size_freed/1024/1024:.2f} MB)", xbmc.LOGINFO)

            # Add total at the end (after all addon entries)
            if total_size_freed > 0:
                total_mb = total_size_freed / (1024 * 1024)
                log_content += addon.getLocalizedString(31111).format(size=total_mb) + "\n\n"

                total_freed_all_options += option1_size_freed

            execution_time = round(time.perf_counter() - start_time, 2)
            log_content += addon.getLocalizedString(31104).format(time=execution_time) + "\n"
            write_log("clear_cache_files_from_addon_data", log_content.rstrip() + "\n")
            
        # Option 2: Clear temp folders from addon data
        if selected and 2 in selected and not progress.iscanceled():
            start_time = time.perf_counter()
            progress.update(0, addon.getLocalizedString(31078))  # "Preparing to clear addon data temp folders..."
            total_size_freed = 0
            option2_size_freed = 0
            
            log_content = addon.getLocalizedString(31095) + "\n\n"  # "Addon temp folders cleaning results:"
            xbmc.log("OptiKlean: Starting addon temp folders cleaning", xbmc.LOGINFO)
            xbmc.log(f"OptiKlean: Using addon_data path: {addon_data_path}", xbmc.LOGINFO)
            
            if not xbmcvfs.exists(addon_data_path):
                error_msg = f"Addon data path does not exist: {addon_data_path}"
                xbmc.log(f"OptiKlean: {error_msg}", xbmc.LOGERROR)
                log_content += error_msg + "\n"
            else:
                try:
                    addon_folders, _ = xbmcvfs.listdir(addon_data_path)
                    xbmc.log(f"OptiKlean: Found {len(addon_folders)} addon folders", xbmc.LOGINFO)
                    
                    if not addon_folders:
                        log_content += addon.getLocalizedString(31106) + "\n"
                        xbmc.log("OptiKlean: No addon folders found", xbmc.LOGINFO)
                    else:
                        total_addons = len(addon_folders)
                        has_skips = False
                        last_was_skip = False
                        total_size_freed = 0
                        
                        for index, addon_id in enumerate(addon_folders):
                            if progress.iscanceled():
                                break
                            
                            progress.update((index * 100) // total_addons, addon.getLocalizedString(31090).format(addon_id=addon_id))
                            xbmc.log(f"OptiKlean: Processing addon {addon_id}", xbmc.LOGINFO)
                            
                            if addon_id in critical_cache_addons:
                                skip_msg = addon.getLocalizedString(31107).format(addon_id=addon_id)
                                if not has_skips:
                                    log_content = log_content.rstrip() + "\n\n"
                                    has_skips = True
                                log_content += skip_msg + "\n"
                                last_was_skip = True
                                xbmc.log(f"OptiKlean: {skip_msg}", xbmc.LOGINFO)
                                continue
                            
                            last_was_skip = False
                            
                            for temp_folder in ['temp', 'tmp']:
                                temp_path = xbmcvfs.makeLegalFilename(f"{addon_data_path}/{addon_id}/{temp_folder}/")
                                xbmc.log(f"OptiKlean: Checking for {temp_folder} at {temp_path}", xbmc.LOGINFO)
                                
                                if xbmcvfs.exists(temp_path):
                                    try:
                                        _, files = xbmcvfs.listdir(temp_path)
                                        xbmc.log(f"OptiKlean: Found {len(files)} files in {temp_folder}", xbmc.LOGINFO)
                                        
                                        deleted = []
                                        protected = []
                                        errors = []
                                        addon_size_freed = 0
                                        
                                        for file_name in files:
                                            if progress.iscanceled():
                                                break
                                                
                                            file_path = xbmcvfs.makeLegalFilename(f"{temp_path}/{file_name}")
                                            xbmc.log(f"OptiKlean: Processing file {file_path}", xbmc.LOGINFO)
                                            
                                            file_size = get_file_size(file_path) or 0
                                            
                                            if is_safe_to_delete(file_path, addon_id=addon_id, 
                                                              critical_cache_addons=critical_cache_addons):
                                                status, error = delete_file(file_path)
                                                if status == DELETE_SUCCESS:
                                                    if xbmcvfs.exists(file_path):
                                                        error_msg = f"File still exists after deletion: {file_path}"
                                                        xbmc.log(f"OptiKlean: {error_msg}", xbmc.LOGWARNING)
                                                        errors.append(f"Verify failed: {file_name}")
                                                    else:
                                                        xbmc.log(f"OptiKlean: Successfully deleted {file_path} ({file_size} bytes)", xbmc.LOGINFO)
                                                        deleted.append((file_name, file_size))
                                                        addon_size_freed += file_size
                                                        total_size_freed += file_size
                                                        option2_size_freed += file_size
                                                elif status == DELETE_LOCKED:
                                                    error_msg = f"Failed to delete {file_path} (locked)"
                                                    xbmc.log(f"OptiKlean: {error_msg}", xbmc.LOGWARNING)
                                                    errors.append(f"Locked: {file_name}")
                                                else:
                                                    error_msg = f"Failed to delete {file_path} ({error})"
                                                    xbmc.log(f"OptiKlean: {error_msg}", xbmc.LOGERROR)
                                                    errors.append(f"Error: {file_name} ({error})")
                                            else:
                                                xbmc.log(f"OptiKlean: Protected file {file_path}", xbmc.LOGINFO)
                                                protected.append(file_name)
                                        
                                        if has_skips and not last_was_skip and (deleted or protected or errors):
                                            log_content += "\n"
                                        
                                        if deleted or protected or errors:
                                            log_content += f"{addon_id} ({temp_folder}):\n"
                                            
                                            if deleted:
                                                size_kb = addon_size_freed / 1024
                                                log_content += addon.getLocalizedString(31108).format(count=len(deleted), size=size_kb) + "\n"
                                                for file_name, file_size in deleted:
                                                    size_str = _format_file_size(file_size)
                                                    log_content += f"    - {file_name} ({size_str})\n"
                                            
                                            if protected:
                                                log_content += addon.getLocalizedString(31109).format(count=len(protected)) + "\n"
                                                for file_name in protected:
                                                    log_content += f"    - {file_name}\n"
                                            
                                            if errors:
                                                log_content += addon.getLocalizedString(31110).format(count=len(errors)) + "\n"
                                                for error in errors:
                                                    log_content += f"    - {error}\n"
                                            
                                            log_content += "\n"
                                    
                                    except Exception as e:
                                        error_msg = f"Error processing {addon_id} {temp_folder}: {str(e)}"
                                        log_content += f"{addon_id} {temp_folder} ERROR: {error_msg}\n"
                                        xbmc.log(f"OptiKlean: {error_msg}", xbmc.LOGERROR)
                                else:
                                    xbmc.log(f"OptiKlean: No {temp_folder} folder found for {addon_id}", xbmc.LOGINFO)
                    
                    # Move total space freed to the end of the log
                    if total_size_freed > 0:
                        size_mb = total_size_freed / (1024 * 1024)
                        log_content += f"Total space freed: {size_mb:.2f} MB\n\n"
                        
                        total_freed_all_options += option2_size_freed

                except Exception as e:
                    error_msg = f"Error listing addon_data folder: {str(e)}"
                    log_content += error_msg + "\n"
                    xbmc.log(f"OptiKlean: {error_msg}", xbmc.LOGERROR)

            execution_time = round(time.perf_counter() - start_time, 2)
            log_content += addon.getLocalizedString(31104).format(time=execution_time) + "\n"
            write_log("clear_temp_folders_from_addon_data", log_content.rstrip() + "\n")

        # Option 3: Clear temp folder from addons
        if selected and 3 in selected and not progress.iscanceled():
            start_time = time.perf_counter()
            progress.update(0, addon.getLocalizedString(31079))  # "Preparing to clear addons temp folder..."
            option3_size_freed = 0
            
            log_content = addon.getLocalizedString(31096) + "\n\n"  # "Addons temp folder cleaning results:"
            xbmc.log("OptiKlean DEBUG: Starting clear addons temp folder", xbmc.LOGINFO)
            
            addons_temp_path = ensure_path_format(xbmcvfs.translatePath("special://home/addons/temp/"))
            xbmc.log(f"OptiKlean DEBUG: Using addons temp path: {addons_temp_path}", xbmc.LOGINFO)
            
            if not xbmcvfs.exists(addons_temp_path):
                error_msg = f"Addons temp folder does not exist: {addons_temp_path}"
                xbmc.log(f"OptiKlean DEBUG: {error_msg}", xbmc.LOGERROR)
                log_content += error_msg + "\n"
            else:
                # First map the directory structure
                progress.update(10, addon.getLocalizedString(31084))
                folder_structure = map_directory_structure(addons_temp_path)
                
                if not folder_structure:
                    error_msg = f"Could not access addons temp folder: {addons_temp_path}"
                    xbmc.log(f"OptiKlean DEBUG: {error_msg}", xbmc.LOGERROR)
                    log_content += error_msg + "\n"
                else:
                    xbmc.log(f"OptiKlean DEBUG: Found {len(folder_structure['files'])} files and {len(folder_structure['subfolders'])} subfolders in addons temp", xbmc.LOGINFO)
                    
                    results = {
                        "deleted": [],
                        "locked": [],
                        "errors": [],
                        "protected": [],
                        "total_size": 0
                    }
                    

                    
                    # Process all top-level folders
                    for folder in folder_structure['subfolders']:
                        if progress.iscanceled():
                            break
                        option3_size_freed += _process_addon_temp_folder(folder, addons_temp_path, results, progress)
                    
                    # Process files in root folder
                    for file_name in folder_structure['files']:
                        if progress.iscanceled():
                            break
                            
                        file_path = os.path.join(addons_temp_path, file_name)
                        xbmc.log(f"OptiKlean DEBUG: Processing root file: {file_path}", xbmc.LOGINFO)
                        
                        if not is_safe_to_delete(file_path, addons_temp_path):
                            xbmc.log(f"OptiKlean DEBUG: Protected file skipped: {file_path}", xbmc.LOGINFO)
                            results["protected"].append(file_path)
                            continue

                        # Get size BEFORE deletion
                        file_size = get_file_size(file_path) or 0
                        status, error = delete_file(file_path, progress_dialog=progress)
                            
                        if status == DELETE_SUCCESS:
                            results["deleted"].append((file_path, file_size))  # Store as tuple with size
                            results["total_size"] += file_size
                            option3_size_freed += file_size
                            xbmc.log(f"OptiKlean DEBUG: Successfully deleted file: {file_path} (size: {file_size} bytes)", xbmc.LOGINFO)
                        elif status == DELETE_LOCKED:
                            results["locked"].append(file_path)
                            xbmc.log(f"OptiKlean DEBUG: File is locked: {file_path}", xbmc.LOGINFO)
                        else:
                            results["errors"].append(f"{file_path} ({error})")
                            xbmc.log(f"OptiKlean DEBUG: Error deleting file: {file_path} - {error}", xbmc.LOGERROR)
                    
                    # Generate log content
                    if results["deleted"]:
                        size_mb = results["total_size"] / (1024 * 1024)
                        total_freed_all_options += option3_size_freed
                        log_content += addon.getLocalizedString(31175).format(count=len(results['deleted']), size=size_mb) + "\n"
                        for item in results["deleted"]:
                            if isinstance(item, tuple):
                                file_path, file_size = item
                                filename = os.path.basename(file_path)
                                size_str = _format_file_size(file_size)
                                log_content += f"- {filename} ({size_str})\n"
                            else:
                                # Handle folder deletion messages
                                if "Deleted folder:" in item:
                                    folder_name = item.split(":")[1].strip().split('/')[-1]
                                    log_content += f"- [Folder] {folder_name}\n"
                                else:
                                    log_content += f"- {item}\n"
                        log_content += "\n"

                    if results["locked"]:
                        log_content += addon.getLocalizedString(31176).format(count=len(results['locked'])) + "\n"
                        for item in results["locked"]:
                            log_content += f"- {os.path.basename(item)}\n"
                        log_content += "\n"

                    if results["errors"]:
                        log_content += f"Errors ({len(results['errors'])}):\n"
                        for error in results["errors"]:
                            # Try to extract filename from error messages
                            if ERROR_IN_PREFIX in error:
                                path_part = error.split(':')[0].strip()
                                filename = os.path.basename(path_part)
                                log_content += f"- {filename}: {error.split(':', 1)[1].strip()}\n"
                            else:
                                log_content += f"- {error}\n"
                        log_content += "\n"

                    if results["protected"]:
                        log_content += addon.getLocalizedString(31102) + "\n"
                        for item in results["protected"]:
                            log_content += f"- {os.path.basename(item)}\n"
                        log_content += "\n"
                    
                    xbmc.log(f"OptiKlean DEBUG: Addons temp cleanup completed. Deleted: {len(results['deleted'])}, Locked: {len(results['locked'])}, Errors: {len(results['errors'])}, Protected: {len(results['protected'])}", xbmc.LOGINFO)
                        
            execution_time = round(time.perf_counter() - start_time, 2)
            log_content += "\n" + addon.getLocalizedString(31104).format(time=execution_time) + "\n"
            write_log("clear_temp_folder_from_addons", log_content.rstrip() + "\n")
            
        # Show notification if any option was selected and completed
        if selected:
            total_mb = total_freed_all_options / (1024 * 1024)
            notification_msg = addon.getLocalizedString(31056).format(total_mb=total_mb)  # "Clear cache and temp completed! ({total_mb:.2f} MB freed)"
            xbmcgui.Dialog().notification(ADDON_NAME, notification_msg, logo_path, 3000)

            # Update the automatic settings logs only if:
            # 1. Not in automatic mode
            # 2. At least one cleaning was completed successfully
            # 3. Automatic cleaning is enabled in the settings
            if not auto_mode and addon.getSettingBool("clear_cache_and_temp_enable"):
                try:
                    update_last_run("clear_cache_and_temp")
                    update_automatic_settings_log()
                    xbmc.log(AUTOMATIC_LOG_UPDATED_MESSAGE, xbmc.LOGINFO)
                except Exception as e:
                    xbmc.log(f"OptiKlean: Error updating automatic logs: {str(e)}", xbmc.LOGERROR)
        
    except Exception as e:
        error_msg = f"Unexpected error during cleanup: {str(e)}"
        xbmc.log(error_msg, xbmc.LOGERROR)
        xbmcgui.Dialog().notification(ADDON_NAME, addon.getLocalizedString(31057), xbmcgui.NOTIFICATION_ERROR, 5000)  # "Error during cleanup, see log"
                
    finally:
        progress.close()


# Function to find the texture database
def find_texture_database(db_path):
    """
    Dynamically finds the most recent texture database, compatible with all Kodi versions.
    """
    xbmc.log(f"OptiKlean DEBUG: Entering find_texture_database with path: {db_path}", xbmc.LOGINFO)
    
    # Ensure proper path format (no double slashes)
    db_path = db_path.replace('//', '/')
    
    if not xbmcvfs.exists(db_path):
        xbmc.log(f"OptiKlean DEBUG: Database path does not exist: {db_path}", xbmc.LOGINFO)
        return None

    # Pattern to identify the texture databases
    texture_pattern = "Textures*.db"
    xbmc.log(f"OptiKlean DEBUG: Looking for files matching pattern: {texture_pattern}", xbmc.LOGINFO)

    # Search all files in the database directory
    _, files = xbmcvfs.listdir(db_path)
    xbmc.log(f"OptiKlean DEBUG: All files in database directory: {files}", xbmc.LOGINFO)
    
    matching_files = [f for f in files if fnmatch.fnmatch(f, texture_pattern)]
    xbmc.log(f"OptiKlean DEBUG: Matching texture database files: {matching_files}", xbmc.LOGINFO)

    if not matching_files:
        xbmc.log("OptiKlean DEBUG: No texture database files found", xbmc.LOGINFO)
        return None  # No texture database found

    # Convert the file names to numbers and sort by version (Textures13.db, Textures14.db, ...)
    def extract_version(filename):
        match = re.search(r"Textures(\d+)\.db", filename)
        version = int(match.group(1)) if match else 0
        xbmc.log(f"OptiKlean DEBUG: Extracted version {version} from file {filename}", xbmc.LOGINFO)
        return version

    matching_files.sort(key=extract_version, reverse=True)
    xbmc.log(f"OptiKlean DEBUG: Sorted texture database files: {matching_files}", xbmc.LOGINFO)

    # Return the most recent database - Fix path to avoid double slashes
    latest_db = matching_files[0]
    full_path = xbmcvfs.translatePath(f"{db_path}{latest_db}")
    full_path = full_path.replace('//', '/')  # Ensure no double slashes
    xbmc.log(f"OptiKlean DEBUG: Selected latest texture database: {full_path}", xbmc.LOGINFO)
    return full_path


def find_video_database(db_path):
    """
    Dynamically finds the most recent video database, compatible with all Kodi versions.
    """
    xbmc.log(f"OptiKlean DEBUG: Entering find_video_database with path: {db_path}", xbmc.LOGINFO)
    
    # Ensure proper path format (no double slashes)
    db_path = db_path.replace('//', '/')
    
    if not xbmcvfs.exists(db_path):
        xbmc.log(f"OptiKlean DEBUG: Database path does not exist: {db_path}", xbmc.LOGINFO)
        return None

    # Pattern to identify the video databases
    video_pattern = "MyVideos*.db"
    xbmc.log(f"OptiKlean DEBUG: Looking for files matching pattern: {video_pattern}", xbmc.LOGINFO)

    # Search all files in the database directory
    _, files = xbmcvfs.listdir(db_path)
    xbmc.log(f"OptiKlean DEBUG: All files in database directory: {files}", xbmc.LOGINFO)
    
    matching_files = [f for f in files if fnmatch.fnmatch(f, video_pattern)]
    xbmc.log(f"OptiKlean DEBUG: Matching video database files: {matching_files}", xbmc.LOGINFO)

    if not matching_files:
        xbmc.log("OptiKlean DEBUG: No video database files found", xbmc.LOGINFO)
        return None

    # Convert the file names to numbers and sort by version (MyVideos131.db, MyVideos132.db, ...)
    def extract_version(filename):
        match = re.search(r"MyVideos(\d+)\.db", filename)
        version = int(match.group(1)) if match else 0
        xbmc.log(f"OptiKlean DEBUG: Extracted version {version} from file {filename}", xbmc.LOGINFO)
        return version

    matching_files.sort(key=extract_version, reverse=True)
    xbmc.log(f"OptiKlean DEBUG: Sorted video database files: {matching_files}", xbmc.LOGINFO)

    # Return the most recent database
    latest_db = matching_files[0]
    full_path = xbmcvfs.translatePath(f"{db_path}{latest_db}")
    full_path = full_path.replace('//', '/')
    xbmc.log(f"OptiKlean DEBUG: Selected latest video database: {full_path}", xbmc.LOGINFO)
    return full_path


def find_music_database(db_path):
    """
    Dynamically finds the most recent music database, compatible with all Kodi versions.
    """
    xbmc.log(f"OptiKlean DEBUG: Entering find_music_database with path: {db_path}", xbmc.LOGINFO)
    
    # Ensure proper path format (no double slashes)
    db_path = db_path.replace('//', '/')
    
    if not xbmcvfs.exists(db_path):
        xbmc.log(f"OptiKlean DEBUG: Database path does not exist: {db_path}", xbmc.LOGINFO)
        return None

    # Pattern to identify the music databases
    music_pattern = "MyMusic*.db"
    xbmc.log(f"OptiKlean DEBUG: Looking for files matching pattern: {music_pattern}", xbmc.LOGINFO)

    # Search all files in the database directory
    _, files = xbmcvfs.listdir(db_path)
    xbmc.log(f"OptiKlean DEBUG: All files in database directory: {files}", xbmc.LOGINFO)
    
    matching_files = [f for f in files if fnmatch.fnmatch(f, music_pattern)]
    xbmc.log(f"OptiKlean DEBUG: Matching music database files: {matching_files}", xbmc.LOGINFO)

    if not matching_files:
        xbmc.log("OptiKlean DEBUG: No music database files found", xbmc.LOGINFO)
        return None

    # Convert the file names to numbers and sort by version (MyMusic82.db, MyMusic83.db, ...)
    def extract_version(filename):
        match = re.search(r"MyMusic(\d+)\.db", filename)
        version = int(match.group(1)) if match else 0
        xbmc.log(f"OptiKlean DEBUG: Extracted version {version} from file {filename}", xbmc.LOGINFO)
        return version

    matching_files.sort(key=extract_version, reverse=True)
    xbmc.log(f"OptiKlean DEBUG: Sorted music database files: {matching_files}", xbmc.LOGINFO)

    # Return the most recent database
    latest_db = matching_files[0]
    full_path = xbmcvfs.translatePath(f"{db_path}{latest_db}")
    full_path = full_path.replace('//', '/')
    xbmc.log(f"OptiKlean DEBUG: Selected latest music database: {full_path}", xbmc.LOGINFO)
    return full_path


def get_kodi_major_version():
    """
    Gets the major version of Kodi (e.g. 19, 20, 21, 22).
    Returns an integer, or 0 in case of error.
    """
    return common_utils.get_kodi_version()


def _clear_older_thumbnails(db_path, thumb_paths, progress_dialog, start_progress, end_progress, days_threshold=None):
    """
    Deletes thumbnails older than X days using the sizes table of the texture database
    and also removes the corresponding rows from the database.
    If days_threshold is None, reads the user-configured value from settings.
    """
    if days_threshold is None:
        days_threshold = common_utils.get_thumbnail_age_threshold_days()

    # Calculate the threshold timestamp (X days ago)
    threshold_timestamp = int(time.time()) - (days_threshold * 86400)
    # Convert to datetime format for the SQL comparison
    threshold_datetime = datetime.fromtimestamp(threshold_timestamp).strftime("%Y-%m-%d %H:%M:%S")
    
    texture_db = find_texture_database(db_path)
    if not texture_db:
        xbmc.log("OptiKlean DEBUG: Texture database not found for older thumbnails cleanup", xbmc.LOGERROR)
        return [], [], [], 0, 0, 0
    
    deleted = []
    locked = []
    errors = []
    total_size_freed = 0
    deleted_db_sizes = 0
    deleted_db_texture = 0
    
    try:
        # Connect to the texture database
        conn = sqlite3.connect(texture_db)
        cursor = conn.cursor()
        
        # Check the database structure
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        xbmc.log(f"OptiKlean DEBUG: Available tables in texture database: {tables}", xbmc.LOGINFO)
        
        if 'sizes' not in tables or 'texture' not in tables:
            xbmc.log("OptiKlean DEBUG: Required tables (sizes, texture) not found in database", xbmc.LOGERROR)
            conn.close()
            return [], [], [], 0, 0, 0
        
        # Check the table columns
        cursor.execute("PRAGMA table_info(sizes)")
        sizes_columns = [col[1] for col in cursor.fetchall()]
        cursor.execute("PRAGMA table_info(texture)")
        texture_columns = [col[1] for col in cursor.fetchall()]
        
        xbmc.log(f"OptiKlean DEBUG: Sizes table columns: {sizes_columns}", xbmc.LOGINFO)
        xbmc.log(f"OptiKlean DEBUG: Texture table columns: {texture_columns}", xbmc.LOGINFO)
        
        # Check that the required columns exist
        required_sizes_cols = ['idtexture', 'lastusetime']
        required_texture_cols = ['id', 'cachedurl']
        
        if not all(col in sizes_columns for col in required_sizes_cols):
            xbmc.log(f"OptiKlean DEBUG: Missing required columns in sizes table. Required: {required_sizes_cols}, Found: {sizes_columns}", xbmc.LOGERROR)
            conn.close()
            return [], [], [], 0, 0, 0
            
        if not all(col in texture_columns for col in required_texture_cols):
            xbmc.log(f"OptiKlean DEBUG: Missing required columns in texture table. Required: {required_texture_cols}, Found: {texture_columns}", xbmc.LOGERROR)
            conn.close()
            return [], [], [], 0, 0, 0
        
        # Query to find thumbnails older than X days
        # We do a JOIN between sizes and texture to get cachedurl directly
        query = """
            SELECT t.id, t.cachedurl, s.lastusetime
            FROM sizes s
            INNER JOIN texture t ON s.idtexture = t.id
            WHERE s.lastusetime < ?
        """
        
        xbmc.log(f"OptiKlean DEBUG: Executing query with threshold: {threshold_datetime}", xbmc.LOGINFO)
        cursor.execute(query, (threshold_datetime,))
        old_thumbnails = cursor.fetchall()
        
        xbmc.log(f"OptiKlean DEBUG: Found {len(old_thumbnails)} thumbnails older than {days_threshold} days", xbmc.LOGINFO)
        
        if len(old_thumbnails) == 0:
            xbmc.log("OptiKlean DEBUG: No old thumbnails found", xbmc.LOGINFO)
            conn.close()
            return [], [], [], 0, 0, 0
        
        # Process each thumbnail found
        for index, (texture_id, cachedurl, lastusetime) in enumerate(old_thumbnails):
            if progress_dialog and progress_dialog.iscanceled():
                xbmc.log("OptiKlean DEBUG: User canceled old thumbnails cleanup", xbmc.LOGINFO)
                break
                
            # Calculate progress within the assigned range
            progress_range = end_progress - start_progress
            percent = start_progress + int((index / len(old_thumbnails)) * progress_range) if len(old_thumbnails) > 0 else end_progress
            
            if progress_dialog:
                progress_dialog.update(percent, f"Processing old thumbnail {index+1}/{len(old_thumbnails)}")
            
            # Calculate the age in days for the log
            try:
                last_use_dt = datetime.strptime(lastusetime, "%Y-%m-%d %H:%M:%S")
                days_old = (datetime.now() - last_use_dt).days
            except Exception as e:
                xbmc.log(f"OptiKlean DEBUG: Error parsing lastusetime '{lastusetime}': {str(e)}", xbmc.LOGWARNING)
                days_old = -1
            
            xbmc.log(f"OptiKlean DEBUG: Processing thumbnail ID {texture_id}, cachedurl: {cachedurl}, last used: {lastusetime} ({days_old} days ago)", xbmc.LOGINFO)
            
            # Look for the thumbnail file in the possible paths
            thumbnail_found = False
            file_deleted = False
            file_size = 0
            
            for base_path in thumb_paths:
                # Build the full path: base_path + cachedurl
                # cachedurl is already in the format "4/4bfd5855.jpg"
                thumb_file_path = xbmcvfs.makeLegalFilename(f"{base_path}{cachedurl}")
                
                if xbmcvfs.exists(thumb_file_path):
                    thumbnail_found = True
                    xbmc.log(f"OptiKlean DEBUG: Found thumbnail file: {thumb_file_path}", xbmc.LOGINFO)
                    
                    # Get the size before deletion
                    file_size = get_file_size(thumb_file_path) or 0
                    
                    # Delete the file
                    status, error = delete_file(thumb_file_path)
                    
                    if status == DELETE_SUCCESS:
                        deleted.append((thumb_file_path, file_size))
                        total_size_freed += file_size
                        file_deleted = True
                        xbmc.log(f"OptiKlean DEBUG: Deleted old thumbnail: {cachedurl} ({days_old} days old, size: {file_size} bytes)", xbmc.LOGINFO)
                    elif status == DELETE_LOCKED:
                        locked.append(thumb_file_path)
                        xbmc.log(f"OptiKlean DEBUG: Locked old thumbnail: {cachedurl}", xbmc.LOGINFO)
                    else:
                        errors.append(f"{thumb_file_path} ({error})")
                        xbmc.log(f"OptiKlean DEBUG: Error deleting old thumbnail: {cachedurl} - {error}", xbmc.LOGERROR)
                    break
            
            # Delete the rows from the database regardless of whether the physical file was found/deleted
            # This is because the file may have already been deleted manually while the rows remain in the database
            try:
                # Delete from the sizes table
                cursor.execute("DELETE FROM sizes WHERE idtexture=?", (texture_id,))
                deleted_sizes_rows = cursor.rowcount
                deleted_db_sizes += deleted_sizes_rows
                
                # Delete from the texture table
                cursor.execute("DELETE FROM texture WHERE id=?", (texture_id,))
                deleted_texture_rows = cursor.rowcount
                deleted_db_texture += deleted_texture_rows
                
                xbmc.log(f"OptiKlean DEBUG: Deleted database entries for texture ID {texture_id}: {deleted_sizes_rows} from sizes, {deleted_texture_rows} from texture", xbmc.LOGINFO)
                
            except sqlite3.Error as db_error:
                error_msg = f"Database deletion error for texture ID {texture_id}: {str(db_error)}"
                errors.append(error_msg)
                xbmc.log(f"OptiKlean DEBUG: {error_msg}", xbmc.LOGERROR)
            
            if not thumbnail_found:
                xbmc.log(f"OptiKlean DEBUG: Thumbnail file not found on disk: {cachedurl} (database entry will still be removed)", xbmc.LOGDEBUG)
        
        # Commit the database changes and optimize
        try:
            conn.commit()
            xbmc.log("OptiKlean DEBUG: Database changes committed", xbmc.LOGINFO)
            
            # Optimize the database to reduce its physical size
            if progress_dialog:
                progress_dialog.update(end_progress - 5, "Optimizing database...")
            
            cursor.execute("VACUUM")
            xbmc.log("OptiKlean DEBUG: Database vacuumed successfully", xbmc.LOGINFO)
            
        except sqlite3.Error as db_error:
            error_msg = f"Database commit/vacuum error: {str(db_error)}"
            errors.append(error_msg)
            xbmc.log(f"OptiKlean DEBUG: {error_msg}", xbmc.LOGERROR)
        
        conn.close()
        
        xbmc.log(f"OptiKlean DEBUG: Old thumbnails cleanup completed. Files deleted: {len(deleted)}, Locked: {len(locked)}, Errors: {len(errors)}, Size freed: {total_size_freed} bytes, DB entries removed: {deleted_db_sizes} from sizes, {deleted_db_texture} from texture", xbmc.LOGINFO)
        
        return deleted, locked, errors, total_size_freed, deleted_db_sizes, deleted_db_texture
        
    except sqlite3.Error as e:
        if 'conn' in locals():
            conn.close()
        xbmc.log(f"OptiKlean DEBUG: Database error in clear_older_thumbnails_internal: {str(e)}", xbmc.LOGERROR)
        return [], [], [], 0, 0, 0
    except Exception as e:
        if 'conn' in locals():
            conn.close()
        xbmc.log(f"OptiKlean DEBUG: Error in clear_older_thumbnails_internal: {str(e)}", xbmc.LOGERROR)
        return [], [], [], 0, 0, 0


def _clear_orphan_artwork(db_path, thumb_paths, progress_dialog, start_progress, end_progress):
    """
    Finds and deletes orphan artwork from the texture cache.
    An artwork is orphan when it exists in the 'art' table of the video/music database
    but the media it refers to (movie, tvshow, episode, album, artist, etc.) no longer exists.
    Available only for Kodi 22+.
    
    Scans:
    - Video database: movie, tvshow, episode, season, musicvideo, actor, set
    - Music database: album, artist, song
    """
    xbmc.log("OptiKlean DEBUG: Starting orphan artwork cleanup (extended)", xbmc.LOGINFO)
    
    deleted = []
    locked = []
    errors = []
    total_size_freed = 0
    deleted_db_entries = 0
    
    # Find the databases
    video_db = find_video_database(db_path)
    music_db = find_music_database(db_path)
    texture_db = find_texture_database(db_path)
    
    if not video_db and not music_db:
        xbmc.log("OptiKlean DEBUG: No video or music database found for orphan artwork cleanup", xbmc.LOGERROR)
        return [], [], [], 0, 0
    
    if not texture_db:
        xbmc.log("OptiKlean DEBUG: Texture database not found for orphan artwork cleanup", xbmc.LOGERROR)
        return [], [], [], 0, 0
    
    orphan_artwork = []
    
    # ========== PHASE 1: Scan Video Database ==========
    if video_db:
        try:
            video_conn = sqlite3.connect(video_db)
            video_cursor = video_conn.cursor()
            
            # Check that the art table exists
            video_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='art'")
            if video_cursor.fetchone():
                progress_dialog.update(start_progress, addon.getLocalizedString(31270))  # "Scanning video database..."
                
                # Query to find orphan artwork in the video database
                video_orphan_queries = [
                    ("movie", "movie", "idMovie"),
                    ("tvshow", "tvshow", "idShow"),
                    ("episode", "episode", "idEpisode"),
                    ("season", "seasons", "idSeason"),
                    ("musicvideo", "musicvideo", "idMVideo"),
                    ("actor", "actor", "actor_id"),
                    ("set", "sets", "idSet"),
                ]
                
                for media_type, table_name, id_column in video_orphan_queries:
                    try:
                        # Check that the table exists
                        video_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                        if not video_cursor.fetchone():
                            xbmc.log(f"OptiKlean DEBUG: Table {table_name} not found, skipping", xbmc.LOGDEBUG)
                            continue
                        
                        # Find orphan artwork for this media type
                        query = f"""
                            SELECT art.art_id, art.url 
                            FROM art 
                            WHERE art.media_type = ? 
                            AND art.media_id NOT IN (SELECT {id_column} FROM {table_name})
                        """
                        video_cursor.execute(query, (media_type,))
                        results = video_cursor.fetchall()
                        
                        for art_id, url in results:
                            orphan_artwork.append((art_id, url, media_type, "video"))
                            xbmc.log(f"OptiKlean DEBUG: Found video orphan artwork: id={art_id}, type={media_type}", xbmc.LOGDEBUG)
                        
                    except sqlite3.Error as e:
                        xbmc.log(f"OptiKlean DEBUG: Error querying video {media_type}: {str(e)}", xbmc.LOGWARNING)
                        continue
                
                xbmc.log(f"OptiKlean DEBUG: Found {len(orphan_artwork)} orphan artwork entries in video database", xbmc.LOGINFO)
            else:
                xbmc.log("OptiKlean DEBUG: Art table not found in video database", xbmc.LOGINFO)
            
            video_conn.close()
            
        except sqlite3.Error as e:
            xbmc.log(f"OptiKlean DEBUG: Error connecting to video database: {str(e)}", xbmc.LOGWARNING)
            if 'video_conn' in locals():
                video_conn.close()
    
    # ========== PHASE 2: Scan Music Database ==========
    music_orphan_count = 0
    if music_db:
        try:
            music_conn = sqlite3.connect(music_db)
            music_cursor = music_conn.cursor()
            
            # Check that the art table exists in the music database
            music_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='art'")
            if music_cursor.fetchone():
                progress_dialog.update(start_progress + 5, addon.getLocalizedString(31279))  # "Scanning music database..."
                
                # Query to find orphan artwork in the music database
                music_orphan_queries = [
                    ("album", "album", "idAlbum"),
                    ("artist", "artist", "idArtist"),
                    ("song", "song", "idSong"),
                ]
                
                for media_type, table_name, id_column in music_orphan_queries:
                    try:
                        # Check that the table exists
                        music_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                        if not music_cursor.fetchone():
                            xbmc.log(f"OptiKlean DEBUG: Table {table_name} not found in music db, skipping", xbmc.LOGDEBUG)
                            continue
                        
                        # Find orphan artwork for this media type
                        query = f"""
                            SELECT art.art_id, art.url 
                            FROM art 
                            WHERE art.media_type = ? 
                            AND art.media_id NOT IN (SELECT {id_column} FROM {table_name})
                        """
                        music_cursor.execute(query, (media_type,))
                        results = music_cursor.fetchall()
                        
                        for art_id, url in results:
                            orphan_artwork.append((art_id, url, media_type, "music"))
                            music_orphan_count += 1
                            xbmc.log(f"OptiKlean DEBUG: Found music orphan artwork: id={art_id}, type={media_type}", xbmc.LOGDEBUG)
                        
                    except sqlite3.Error as e:
                        xbmc.log(f"OptiKlean DEBUG: Error querying music {media_type}: {str(e)}", xbmc.LOGWARNING)
                        continue
                
                xbmc.log(f"OptiKlean DEBUG: Found {music_orphan_count} orphan artwork entries in music database", xbmc.LOGINFO)
            else:
                xbmc.log("OptiKlean DEBUG: Art table not found in music database", xbmc.LOGINFO)
            
            music_conn.close()
            
        except sqlite3.Error as e:
            xbmc.log(f"OptiKlean DEBUG: Error connecting to music database: {str(e)}", xbmc.LOGWARNING)
            if 'music_conn' in locals():
                music_conn.close()
    
    xbmc.log(f"OptiKlean DEBUG: Total orphan artwork found: {len(orphan_artwork)} (video + music)", xbmc.LOGINFO)
    
    if not orphan_artwork:
        return [], [], [], 0, 0
    
    # ========== PHASE 3: Delete files and database entries ==========
    try:
        progress_dialog.update(start_progress + 10, addon.getLocalizedString(31271))  # "Deleting orphan artwork..."
        
        # Connect to the databases
        texture_conn = sqlite3.connect(texture_db)
        texture_cursor = texture_conn.cursor()
        
        # Reconnect to the video and music databases for the deletions
        video_conn = None
        video_cursor = None
        music_conn = None
        music_cursor = None
        
        if video_db:
            video_conn = sqlite3.connect(video_db)
            video_cursor = video_conn.cursor()
        
        if music_db:
            music_conn = sqlite3.connect(music_db)
            music_cursor = music_conn.cursor()
        
        progress_range = end_progress - start_progress - 20
        processed = 0
        total_orphans = len(orphan_artwork)
        
        for art_id, url, media_type, db_source in orphan_artwork:
            if progress_dialog.iscanceled():
                break
            
            processed += 1
            percent = start_progress + 10 + int((processed / total_orphans) * progress_range)
            progress_dialog.update(percent, f"Processing orphan artwork {processed}/{total_orphans}...")
            
            try:
                # Look for the file in the texture cache
                texture_cursor.execute("SELECT id, cachedurl FROM texture WHERE url = ?", (url,))
                texture_row = texture_cursor.fetchone()
                
                if texture_row:
                    texture_id, cachedurl = texture_row
                    
                    # Find the file in the cache
                    for base_path in thumb_paths:
                        cached_file_path = xbmcvfs.makeLegalFilename(f"{base_path}{cachedurl}")
                        if xbmcvfs.exists(cached_file_path):
                            # Get the size before deleting
                            file_size = get_file_size(cached_file_path) or 0
                            
                            status, error = delete_file(cached_file_path)
                            if status == DELETE_SUCCESS:
                                deleted.append((cached_file_path, file_size))
                                total_size_freed += file_size
                                xbmc.log(f"OptiKlean DEBUG: Deleted orphan artwork file: {cached_file_path}", xbmc.LOGDEBUG)
                            elif status == DELETE_LOCKED:
                                locked.append(cached_file_path)
                            else:
                                errors.append(f"{cached_file_path} ({error})")
                            break
                    
                    # Remove from the texture table
                    try:
                        texture_cursor.execute("DELETE FROM sizes WHERE idtexture = ?", (texture_id,))
                        texture_cursor.execute("DELETE FROM texture WHERE id = ?", (texture_id,))
                    except sqlite3.Error as del_err:
                        xbmc.log(f"OptiKlean DEBUG: Error removing texture entry: {str(del_err)}", xbmc.LOGWARNING)
                
                # Remove from the art table of the correct database (video or music)
                if db_source == "video" and video_cursor:
                    video_cursor.execute("DELETE FROM art WHERE art_id = ?", (art_id,))
                    deleted_db_entries += 1
                elif db_source == "music" and music_cursor:
                    music_cursor.execute("DELETE FROM art WHERE art_id = ?", (art_id,))
                    deleted_db_entries += 1
                
            except Exception as e:
                errors.append(f"Error processing art_id {art_id}: {str(e)}")
                xbmc.log(f"OptiKlean DEBUG: Error processing orphan artwork: {str(e)}", xbmc.LOGERROR)
        
        # Commit and vacuum
        try:
            texture_conn.commit()
            if video_conn:
                video_conn.commit()
            if music_conn:
                music_conn.commit()
            
            texture_cursor.execute("VACUUM")
            if video_cursor:
                video_cursor.execute("VACUUM")
            if music_cursor:
                music_cursor.execute("VACUUM")
            xbmc.log("OptiKlean DEBUG: Databases vacuumed after orphan artwork cleanup", xbmc.LOGINFO)
        except sqlite3.Error as e:
            xbmc.log(f"OptiKlean DEBUG: Error during commit/vacuum: {str(e)}", xbmc.LOGWARNING)
        
        texture_conn.close()
        if video_conn:
            video_conn.close()
        if music_conn:
            music_conn.close()
        
        xbmc.log(f"OptiKlean DEBUG: Orphan artwork cleanup completed. Files deleted: {len(deleted)}, DB entries: {deleted_db_entries}, Size freed: {total_size_freed} bytes", xbmc.LOGINFO)
        
        return deleted, locked, errors, total_size_freed, deleted_db_entries
        
    except sqlite3.Error as e:
        if 'texture_conn' in locals() and texture_conn:
            texture_conn.close()
        if 'video_conn' in locals() and video_conn:
            video_conn.close()
        if 'music_conn' in locals() and music_conn:
            music_conn.close()
        xbmc.log(f"OptiKlean DEBUG: Database error in clear_orphan_artwork_internal: {str(e)}", xbmc.LOGERROR)
        return [], [], [], 0, 0
    except Exception as e:
        if 'texture_conn' in locals() and texture_conn:
            texture_conn.close()
        if 'video_conn' in locals() and video_conn:
            video_conn.close()
        if 'music_conn' in locals() and music_conn:
            music_conn.close()
        xbmc.log(f"OptiKlean DEBUG: Error in clear_orphan_artwork_internal: {str(e)}", xbmc.LOGERROR)
        return [], [], [], 0, 0


def _count_thumbnail_files(folder_path):
    """Recursively counts all files in a thumbnail folder using xbmcvfs."""
    folder_path = ensure_path_format(folder_path)
    count = 0
    try:
        dirs, files = xbmcvfs.listdir(folder_path)
        count += len(files)
        for d in dirs:
            count += _count_thumbnail_files(ensure_path_format(folder_path + d))
    except Exception as e:
        xbmc.log(f"OptiKlean DEBUG: Error counting files in {folder_path}: {str(e)}", xbmc.LOGWARNING)
    return count


def _scan_and_delete_thumbnails(folder_path, valid_thumbs, progress_dialog, total_files, current_index, start_prog, end_prog):
    """
    Recursively scans folder_path and deletes files not in valid_thumbs.
    Returns: (deleted, locked, errors, processed_files, total_size_freed)
      - deleted: list of (file_path, file_size) tuples
      - locked: list of file_path strings
      - errors: list of error message strings
      - processed_files: number of files examined
      - total_size_freed: bytes freed
    """
    folder_path = ensure_path_format(folder_path)
    deleted = []
    locked = []
    errors = []
    processed_files = 0
    total_size_freed = 0

    try:
        dirs, files = xbmcvfs.listdir(folder_path)
    except Exception as e:
        xbmc.log(f"OptiKlean DEBUG: Error listing {folder_path}: {str(e)}", xbmc.LOGWARNING)
        return deleted, locked, errors, processed_files, total_size_freed

    for file_name in files:
        if progress_dialog and progress_dialog.iscanceled():
            return deleted, locked, errors, processed_files, total_size_freed

        file_path = xbmcvfs.makeLegalFilename(f"{folder_path}{file_name}")
        processed_files += 1

        if total_files > 0:
            prog = start_prog + int(((current_index + processed_files) / total_files) * (end_prog - start_prog))
            _update_progress_dialog(progress_dialog, f"Checking {file_name}...")
            if progress_dialog:
                progress_dialog.update(min(prog, end_prog))

        if file_path in valid_thumbs:
            continue

        file_size = get_file_size(file_path) or 0
        status, error = delete_file(file_path, progress_dialog=progress_dialog)

        if status == DELETE_SUCCESS:
            deleted.append((file_path, file_size))
            total_size_freed += file_size
        elif status == DELETE_LOCKED:
            locked.append(file_path)
        else:
            errors.append(f"{ERROR_IN_PREFIX} {file_path}: {error}")

    for dir_name in dirs:
        if progress_dialog and progress_dialog.iscanceled():
            return deleted, locked, errors, processed_files, total_size_freed

        sub_path = ensure_path_format(f"{folder_path}{dir_name}")
        del_, lock_, err_, proc_, size_ = _scan_and_delete_thumbnails(
            sub_path, valid_thumbs, progress_dialog, total_files, current_index + processed_files, start_prog, end_prog
        )
        deleted.extend(del_)
        locked.extend(lock_)
        errors.extend(err_)
        processed_files += proc_
        total_size_freed += size_

    return deleted, locked, errors, processed_files, total_size_freed


# Function to delete thumbnails that are no longer used
def clear_unused_thumbnails(auto_mode=False, skip_auto_delay=False):
    xbmc.log("OptiKlean DEBUG: Starting clear_unused_thumbnails", xbmc.LOGINFO)
    start_time = time.perf_counter()
    threshold_days = common_utils.get_thumbnail_age_threshold_days()
    
    # Check the Kodi version for the orphan artwork feature
    kodi_version = get_kodi_major_version()
    is_kodi_22_or_later = kodi_version >= 22
    
    # If not in automatic mode, show the selection window
    if not auto_mode:
        threshold_days = common_utils.get_thumbnail_age_threshold_days()
        choices = [
            addon.getLocalizedString(31074),  # "Clear unused thumbnails"
            addon.getLocalizedString(31075).format(days=threshold_days)  # "Clear thumbnails older than N days"
        ]
        
        # Add the orphan artwork option only for Kodi 22+
        if is_kodi_22_or_later:
            choices.append(addon.getLocalizedString(31268))  # "Clear orphan artwork (Kodi 22+)"
        
        selected = xbmcgui.Dialog().multiselect(addon.getLocalizedString(31054), choices)  # "Select thumbnail cleaning options"
        if selected is None or len(selected) == 0:
            return
    else:
        # Automatic mode: apply the delay, if set, before starting
        delay_seconds = get_autostart_delay()
        if delay_seconds > 0 and not skip_auto_delay:
            xbmc.log(f"OptiKlean: Automatic thumbnails cleaning delayed by {delay_seconds} seconds", xbmc.LOGINFO)
            time.sleep(delay_seconds)
        
        # In automatic mode, run the enabled cleanings
        # unused (0) + older than 30 days (1) + orphan artwork (2) if Kodi 22+
        if is_kodi_22_or_later:
            selected = [0, 1, 2]
        else:
            selected = [0, 1]
    
    progress = xbmcgui.DialogProgress()
    progress.create(ADDON_NAME, addon.getLocalizedString(31076))  # "Preparing thumbnails cleanup..."
    
    # Initialize common variables
    db_path = ensure_path_format(xbmcvfs.translatePath(DATABASE_SPECIAL_PATH))
    standard_thumb_path = ensure_path_format(xbmcvfs.translatePath("special://userdata/Thumbnails/"))
    alt_thumb_path = ensure_path_format(xbmcvfs.translatePath("special://thumbnails/"))

    skin_base = ensure_path_format(xbmcvfs.translatePath("special://skin/"))
    skin_subfolders = ["thumbnails/", "media/Thumbnails/", "extras/Thumbnails/"]
    skin_thumb_paths = [ensure_path_format(os.path.join(skin_base, sub)) for sub in skin_subfolders]

    thumb_paths = [p for p in [standard_thumb_path, alt_thumb_path] if xbmcvfs.exists(p)] + [
        p for p in skin_thumb_paths if xbmcvfs.exists(p)
    ]

    for p in thumb_paths:
        xbmc.log(f"OptiKlean DEBUG: Thumbnail path added: {p}", xbmc.LOGINFO)

    if not thumb_paths:
        xbmc.log("OptiKlean DEBUG: No valid thumbnail paths found", xbmc.LOGERROR)
        progress.close()
        
        error_msg = addon.getLocalizedString(31058) + "\n"  # "Thumbnails folder not found."
        if 0 in selected:  # Clear unused thumbnails
            execution_time = round(time.perf_counter() - start_time, 2)
            error_msg += f"\n{addon.getLocalizedString(31104).format(time=execution_time)}\n"  # "Running time: {time}s"
            write_log("clear_unused_thumbnails", error_msg)
        
        if 1 in selected:  # Clear older thumbnails
            execution_time = round(time.perf_counter() - start_time, 2)
            error_msg += f"\n{addon.getLocalizedString(31104).format(time=execution_time)}\n"  # "Running time: {time}s"
            write_log("clear_older_thumbnails", error_msg)
        
        xbmcgui.Dialog().notification(ADDON_NAME, addon.getLocalizedString(31058), xbmcgui.NOTIFICATION_ERROR, 3000)  # "Thumbnails folder not found."
        return



    try:
        # Run Clear unused thumbnails if selected
        if 0 in selected:
            xbmc.log("OptiKlean DEBUG: Executing unused thumbnails cleanup", xbmc.LOGINFO)
            
            log_content_unused = "Unused thumbnails cleaning results:\n\n"
            
            texture_db = find_texture_database(db_path)
            xbmc.log(f"OptiKlean DEBUG: Texture database path: {texture_db}", xbmc.LOGINFO)

            if not texture_db:
                xbmc.log("OptiKlean DEBUG: Texture database not found.", xbmc.LOGERROR)
                progress.update(100, addon.getLocalizedString(31203))  # "Texture database not found."
                log_content_unused += "Texture database not found.\n"
                execution_time = round(time.perf_counter() - start_time, 2)
                log_content_unused += f"\nRunning time: {execution_time}s\n"
                write_log("clear_unused_thumbnails", log_content_unused)
                if not auto_mode:
                    xbmcgui.Dialog().notification(ADDON_NAME, addon.getLocalizedString(31156), xbmcgui.NOTIFICATION_ERROR, 3000)
                if len(selected) == 1:  # If it is the only selected option, exit
                    return
            else:
                progress.update(10, addon.getLocalizedString(31157))
                conn = sqlite3.connect(texture_db)
                cursor = conn.cursor()
                cursor.execute("SELECT cachedurl FROM texture")
                rows = cursor.fetchall()
                conn.close()

                valid_thumbs = set()
                missing_thumbs = 0

                for row in rows:
                    full_path = row[0]
                    found = False
                    for base_path in thumb_paths:
                        thumb_path_item = xbmcvfs.makeLegalFilename(f"{base_path}{full_path}")
                        if xbmcvfs.exists(thumb_path_item):
                            valid_thumbs.add(thumb_path_item)
                            found = True
                            break
                    if not found:
                        missing_thumbs += 1
                        xbmc.log(f"OptiKlean DEBUG: Missing thumbnail: {full_path}", xbmc.LOGDEBUG)

                progress.update(20, addon.getLocalizedString(31204))  # "Counting thumbnails..."



                total_files = sum(_count_thumbnail_files(p) for p in thumb_paths)

                # Determine the progress range for this operation
                start_prog = 30
                end_prog = 65 if 1 in selected else 100
                
                progress.update(start_prog, addon.getLocalizedString(31205))  # "Deleting unused thumbnails..."
                deleted, locked, errors, processed_files, total_size_freed = [], [], [], 0, 0



                current_index = 0
                for path in thumb_paths:
                    del_, lock_, err_, proc_, size_ = _scan_and_delete_thumbnails(
                        path, valid_thumbs, progress, total_files, current_index, start_prog, end_prog
                    )
                    deleted.extend(del_)
                    locked.extend(lock_)
                    errors.extend(err_)
                    processed_files += proc_
                    total_size_freed += size_
                    current_index = processed_files

                # Calculate total size freed in MB
                total_mb = total_size_freed / (1024 * 1024)
                
                log_content_unused += f"Deleted: {len(deleted)} ({total_mb:.2f} MB freed)\n"
                log_content_unused += f"Locked: {len(locked)}\n"
                log_content_unused += f"Errors: {len(errors)}\n\n"
                xbmc.log(f"Valid thumbs in DB: {len(valid_thumbs)}", level=xbmc.LOGINFO)
                xbmc.log(f"Missing thumbs: {missing_thumbs}", level=xbmc.LOGINFO)

                if deleted:
                    log_content_unused += addon.getLocalizedString(31158) + "\n"
                    for file_path, file_size in deleted:
                        filename = os.path.basename(file_path)
                        size_str = _format_file_size(file_size)
                        log_content_unused += f"    - {filename} ({size_str})\n"
                    log_content_unused += "\n"

                if locked:
                    log_content_unused += addon.getLocalizedString(31159) + "\n"
                    for file_path in locked:
                        log_content_unused += f"    - {os.path.basename(file_path)}\n"
                    log_content_unused += "\n"

                if errors:
                    log_content_unused += addon.getLocalizedString(31101) + "\n"
                    for error in errors:
                        if ERROR_IN_PREFIX in error:
                            parts = error.split(':')
                            if len(parts) > 1:
                                path_part = parts[0].strip()
                                filename = os.path.basename(path_part)
                                log_content_unused += f"    - {filename}: {':'.join(parts[1:]).strip()}\n"
                            else:
                                log_content_unused += f"    - {error}\n"
                        else:
                            log_content_unused += f"    - {error}\n"
                    log_content_unused += "\n"

                xbmc.log(f"OptiKlean DEBUG: Unused thumbnail cleanup completed. Freed {total_mb:.2f} MB", xbmc.LOGINFO)

            execution_time_unused = round(time.perf_counter() - start_time, 2)
            log_content_unused += "\n" + addon.getLocalizedString(31104).format(time=execution_time_unused) + "\n"
            write_log("clear_unused_thumbnails", log_content_unused)

        # Run Clear thumbnails older than 30 days if selected
        if 1 in selected:
            xbmc.log("OptiKlean DEBUG: Executing older thumbnails cleanup", xbmc.LOGINFO)
            
            log_content_older = addon.getLocalizedString(31160).format(days=threshold_days) + "\n\n"
            
            # Determine the progress range for this operation
            start_prog = 70 if 0 in selected else 30
            end_prog = 100
            
            progress.update(start_prog, addon.getLocalizedString(31206).format(days=threshold_days))  # "Deleting thumbnails older than X days..."
            
            deleted_older, locked_older, errors_older, total_size_freed_older, deleted_db_sizes, deleted_db_texture = _clear_older_thumbnails(
                db_path, thumb_paths, progress, start_prog, end_prog
            )
            
            # Calculate total size freed in MB
            total_mb_older = total_size_freed_older / (1024 * 1024)
            
            log_content_older += addon.getLocalizedString(31161) + "\n"
            log_content_older += addon.getLocalizedString(31162).format(count=len(deleted_older), size=total_mb_older) + "\n"
            log_content_older += addon.getLocalizedString(31163).format(sizes=deleted_db_sizes, texture=deleted_db_texture) + "\n"
            log_content_older += f"Locked: {len(locked_older)}\n"
            log_content_older += f"Errors: {len(errors_older)}\n\n"

            if deleted_older:
                log_content_older += addon.getLocalizedString(31164).format(days=threshold_days) + "\n"
                for file_path, file_size in deleted_older:
                    filename = os.path.basename(file_path)
                    size_str = _format_file_size(file_size)
                    log_content_older += f"    - {filename} ({size_str})\n"
                log_content_older += "\n"

            if locked_older:
                log_content_older += addon.getLocalizedString(31159) + "\n"
                for file_path in locked_older:
                    log_content_older += f"    - {os.path.basename(file_path)}\n"
                log_content_older += "\n"

            if errors_older:
                log_content_older += addon.getLocalizedString(31101) + "\n"
                for error in errors_older:
                    if ERROR_IN_PREFIX in error:
                        parts = error.split(':')
                        if len(parts) > 1:
                            path_part = parts[0].strip()
                            filename = os.path.basename(path_part)
                            log_content_older += f"    - {filename}: {':'.join(parts[1:]).strip()}\n"
                        else:
                            log_content_older += f"    - {error}\n"
                    else:
                        log_content_older += f"    - {error}\n"
                log_content_older += "\n"

            xbmc.log(f"OptiKlean DEBUG: Older thumbnail cleanup completed. Freed {total_mb_older:.2f} MB", xbmc.LOGINFO)
            
            execution_time_older = round(time.perf_counter() - start_time, 2)
            log_content_older += "\n" + addon.getLocalizedString(31104).format(time=execution_time_older) + "\n"
            write_log("clear_older_thumbnails", log_content_older)

        # Run Clear orphan artwork if selected (Kodi 22+ only)
        if 2 in selected and is_kodi_22_or_later:
            xbmc.log("OptiKlean DEBUG: Executing orphan artwork cleanup", xbmc.LOGINFO)
            
            log_content_orphan = addon.getLocalizedString(31269) + "\n\n"  # "Orphan artwork cleaning results:"
            
            # Determine the progress range for this operation
            if 0 in selected and 1 in selected:
                start_prog = 85
            elif 0 in selected or 1 in selected:
                start_prog = 70
            else:
                start_prog = 30
            end_prog = 100
            
            deleted_orphan, locked_orphan, errors_orphan, total_size_freed_orphan, deleted_db_orphan = _clear_orphan_artwork(
                db_path, thumb_paths, progress, start_prog, end_prog
            )
            
            # Calculate total size freed in MB
            total_mb_orphan = total_size_freed_orphan / (1024 * 1024)
            
            log_content_orphan += addon.getLocalizedString(31273).format(count=len(deleted_orphan), size=total_mb_orphan) + "\n"
            log_content_orphan += addon.getLocalizedString(31274).format(count=deleted_db_orphan) + "\n"
            log_content_orphan += f"Locked: {len(locked_orphan)}\n"
            log_content_orphan += f"Errors: {len(errors_orphan)}\n\n"

            if deleted_orphan:
                log_content_orphan += addon.getLocalizedString(31275) + "\n"  # "Deleted orphan artwork files:"
                for file_path, file_size in deleted_orphan:
                    filename = os.path.basename(file_path)
                    size_str = _format_file_size(file_size)
                    log_content_orphan += f"    - {filename} ({size_str})\n"
                log_content_orphan += "\n"

            if locked_orphan:
                log_content_orphan += addon.getLocalizedString(31159) + "\n"
                for file_path in locked_orphan:
                    log_content_orphan += f"    - {os.path.basename(file_path)}\n"
                log_content_orphan += "\n"

            if errors_orphan:
                log_content_orphan += addon.getLocalizedString(31101) + "\n"
                for error in errors_orphan:
                    log_content_orphan += f"    - {error}\n"
                log_content_orphan += "\n"

            xbmc.log(f"OptiKlean DEBUG: Orphan artwork cleanup completed. Freed {total_mb_orphan:.2f} MB", xbmc.LOGINFO)
            
            execution_time_orphan = round(time.perf_counter() - start_time, 2)
            log_content_orphan += "\n" + addon.getLocalizedString(31104).format(time=execution_time_orphan) + "\n"
            write_log("clear_orphan_artwork", log_content_orphan)

        progress.update(100, addon.getLocalizedString(31207))  # "Finishing..."
        
        # Update the automatic settings logs only if:
        # 1. Not in automatic mode
        # 2. Automatic cleaning is enabled in the settings
        # 3. The unused thumbnails cleanup (option 0) was executed
        if not auto_mode and 0 in selected and addon.getSettingBool("clear_unused_thumbnails_enable"):
            try:
                update_last_run("clear_unused_thumbnails")
                update_automatic_settings_log()
                xbmc.log(AUTOMATIC_LOG_UPDATED_MESSAGE, xbmc.LOGINFO)
            except Exception as e:
                xbmc.log(f"OptiKlean: Error updating automatic logs: {str(e)}", xbmc.LOGERROR)

    except Exception as e:
        xbmc.log(f"OptiKlean DEBUG: Critical error in clear_unused_thumbnails: {str(e)}", xbmc.LOGERROR)
        error_content = f"Critical error: {str(e)}"
        if 0 in selected:
            write_log("clear_unused_thumbnails", error_content)
        if 1 in selected:
            write_log("clear_older_thumbnails", error_content)
        if 2 in selected:
            write_log("clear_orphan_artwork", error_content)

    finally:
        progress.close()
        
        # Create notification messages based on what was executed
        # Calculate totals including orphan artwork, if present
        total_deleted_all = 0
        total_mb_all = 0.0
        
        if 'deleted' in locals():
            total_deleted_all += len(deleted)
            total_mb_all += total_size_freed / (1024 * 1024) if 'total_size_freed' in locals() else 0
        if 'deleted_older' in locals():
            total_deleted_all += len(deleted_older)
            total_mb_all += total_size_freed_older / (1024 * 1024) if 'total_size_freed_older' in locals() else 0
        if 'deleted_orphan' in locals():
            total_deleted_all += len(deleted_orphan)
            total_mb_all += total_size_freed_orphan / (1024 * 1024) if 'total_size_freed_orphan' in locals() else 0
        
        # Determine the notification message
        selected_count = len([s for s in selected if s <= 2])
        if selected_count > 1:
            # Multiple operations
            notification_msg = addon.getLocalizedString(31177).format(total_deleted=total_deleted_all, total_mb_combined=total_mb_all)
        elif 0 in selected:
            # Only unused thumbnails
            if 'deleted' in locals() and 'total_mb' in locals():
                notification_msg = addon.getLocalizedString(31178).format(len_deleted=len(deleted), total_mb=total_mb)
            else:
                notification_msg = addon.getLocalizedString(31179)
        elif 1 in selected:
            # Only old thumbnails
            if 'deleted_older' in locals() and 'total_mb_older' in locals():
                notification_msg = addon.getLocalizedString(31180).format(len_deleted_older=len(deleted_older), total_mb_older=total_mb_older)
            else:
                notification_msg = addon.getLocalizedString(31181)
        elif 2 in selected:
            # Only orphan artwork
            if 'deleted_orphan' in locals() and 'total_mb_orphan' in locals():
                notification_msg = addon.getLocalizedString(31278).format(deleted=len(deleted_orphan), size=total_mb_orphan)
            else:
                notification_msg = addon.getLocalizedString(31182)
        else:
            notification_msg = addon.getLocalizedString(31182)
        
        xbmc.log("OptiKlean DEBUG: Finished clear_unused_thumbnails function", xbmc.LOGINFO)
        xbmcgui.Dialog().notification(ADDON_NAME, notification_msg, logo_path, 5000)


def delete_folder(folder_path, progress_dialog=None):
    """
    Delete a folder and all its contents using hybrid xbmcvfs + os approach.
    Returns tuple: (status, locked_files, error_message)
    status can be: DELETE_SUCCESS, DELETE_LOCKED, or DELETE_ERROR
    """
    # Normalize path for all platforms
    folder_path = os.path.normpath(folder_path)
    if not folder_path.endswith(os.sep):
        folder_path += os.sep
    
    xbmc.log(f"OptiKlean DEBUG: Attempting to delete folder: {folder_path}", xbmc.LOGINFO)
    
    # Hybrid existence check
    def path_exists(path):
        # First try xbmcvfs
        if xbmcvfs.exists(path):
            return True
        # Fallback to os.path
        return os.path.exists(path)
    
    if not path_exists(folder_path):
        xbmc.log(f"OptiKlean DEBUG: Folder does not exist: {folder_path}", xbmc.LOGINFO)
        return DELETE_SUCCESS, [], "Folder does not exist"

    locked_files = []
    
    try:
        # Get list of contents using best available method
        def list_contents(path):
            try:
                # First try xbmcvfs
                dirs, files = xbmcvfs.listdir(path)
                return dirs, files
            except Exception as e:
                xbmc.log(f"OptiKlean DEBUG: xbmcvfs.listdir failed: {str(e)}", xbmc.LOGERROR)
                # Fallback to os.listdir
                try:
                    all_items = os.listdir(path)
                    dirs = [d for d in all_items if os.path.isdir(os.path.join(path, d))]
                    files = [f for f in all_items if not os.path.isdir(os.path.join(path, f))]
                    return dirs, files
                except Exception as e:
                    xbmc.log(f"OptiKlean DEBUG: Error listing contents: {str(e)}", xbmc.LOGERROR)
                    raise
        
        # Get ALL contents including hidden files using os.listdir (more reliable on Android)
        def list_all_contents(path):
            """List all files including hidden ones using os module"""
            try:
                path_clean = path.rstrip(os.sep)
                all_items = os.listdir(path_clean)
                dirs = [d for d in all_items if os.path.isdir(os.path.join(path_clean, d))]
                files = [f for f in all_items if os.path.isfile(os.path.join(path_clean, f))]
                return dirs, files
            except Exception as e:
                xbmc.log(f"OptiKlean DEBUG: os.listdir failed: {str(e)}", xbmc.LOGWARNING)
                return [], []

        # Delete files first - use BOTH xbmcvfs and os.listdir to catch hidden files
        dirs, files = list_contents(folder_path)
        os_dirs, os_files = list_all_contents(folder_path)
        
        # Merge file lists (os.listdir catches hidden files that xbmcvfs might miss)
        all_files = list(set(files) | set(os_files))
        all_dirs = list(set(dirs) | set(os_dirs))
        
        xbmc.log(f"OptiKlean DEBUG: Found {len(all_files)} files (xbmcvfs: {len(files)}, os: {len(os_files)}) and {len(all_dirs)} subdirectories", xbmc.LOGINFO)
        
        for file in all_files:
            if progress_dialog and progress_dialog.iscanceled():
                return DELETE_ERROR, [], "Operation cancelled by user"
                
            file_path = os.path.join(folder_path.rstrip(os.sep), file)
            if progress_dialog:
                try:
                    percent = progress_dialog.getPercentage()
                    progress_dialog.update(percent, f"Deleting file: {file}")
                except AttributeError:
                    pass
            
            # Hybrid delete approach
            status = DELETE_ERROR
            error_msg = ""
            
            # First try xbmcvfs
            try:
                if xbmcvfs.delete(file_path):
                    status = DELETE_SUCCESS
                else:
                    # Fallback to os.remove
                    try:
                        os.remove(file_path)
                        status = DELETE_SUCCESS
                    except Exception as e:
                        error_msg = str(e)
                        if getattr(e, 'errno', None) in (errno.EACCES, errno.EPERM, errno.EBUSY):
                            status = DELETE_LOCKED
            except Exception as e:
                error_msg = str(e)
                if getattr(e, 'errno', None) in (errno.EACCES, errno.EPERM, errno.EBUSY):
                    status = DELETE_LOCKED
            
            if status == DELETE_LOCKED:
                locked_files.append(file_path)
                xbmc.log(f"OptiKlean DEBUG: File is locked: {file_path}", xbmc.LOGINFO)
            elif status == DELETE_ERROR:
                xbmc.log(f"OptiKlean DEBUG: Error deleting file: {file_path} - {error_msg}", xbmc.LOGERROR)
        
        # Then delete subdirectories recursively
        for folder in all_dirs:
            if progress_dialog and progress_dialog.iscanceled():
                return DELETE_ERROR, [], "Operation cancelled by user"
                
            subfolder_path = os.path.join(folder_path.rstrip(os.sep), folder)
            if progress_dialog:
                try:
                    percent = progress_dialog.getPercentage()
                    progress_dialog.update(percent, f"Processing subfolder: {folder}")
                except AttributeError:
                    pass
            
            sub_status, sub_locked, sub_error = delete_folder(subfolder_path, progress_dialog)
            if sub_status == DELETE_LOCKED:
                locked_files.extend(sub_locked)
            elif sub_status == DELETE_ERROR:
                xbmc.log(f"OptiKlean DEBUG: Error deleting subfolder: {subfolder_path} - {sub_error}", xbmc.LOGERROR)
        
        # Finally delete the folder itself
        if locked_files:
            return DELETE_LOCKED, locked_files, "Folder contains locked files"
            
        # Hybrid folder deletion
        deleted = False
        folder_path_clean = folder_path.rstrip(os.sep)
        
        try:
            # First try xbmcvfs
            if xbmcvfs.rmdir(folder_path):
                deleted = True
            else:
                # Fallback to os.rmdir
                try:
                    os.rmdir(folder_path_clean)
                    deleted = True
                except OSError as e:
                    if e.errno == errno.ENOTEMPTY:
                        # Folder not empty - check what's really inside (including hidden files)
                        try:
                            remaining_dirs, remaining_files = list_all_contents(folder_path_clean)
                            xbmc.log(f"OptiKlean DEBUG: Folder not empty (os check), contains {len(remaining_files)} files and {len(remaining_dirs)} subfolders", xbmc.LOGINFO)
                            if remaining_files:
                                xbmc.log(f"OptiKlean DEBUG: Hidden/remaining files: {remaining_files}", xbmc.LOGINFO)
                            if remaining_dirs:
                                xbmc.log(f"OptiKlean DEBUG: Hidden/remaining dirs: {remaining_dirs}", xbmc.LOGINFO)
                            
                            # Try shutil.rmtree as last resort (handles hidden files better)
                            if os.path.exists(folder_path_clean):
                                xbmc.log("OptiKlean DEBUG: Attempting shutil.rmtree as fallback", xbmc.LOGINFO)
                                shutil.rmtree(folder_path_clean, ignore_errors=False)
                                deleted = True
                                xbmc.log("OptiKlean DEBUG: shutil.rmtree succeeded", xbmc.LOGINFO)
                        except Exception as rmtree_error:
                            xbmc.log(f"OptiKlean DEBUG: shutil.rmtree failed: {str(rmtree_error)}", xbmc.LOGERROR)
                            error_msg = str(rmtree_error)
                    else:
                        error_msg = str(e)
        except Exception as e:
            error_msg = str(e)
        
        if deleted:
            xbmc.log(f"OptiKlean DEBUG: Successfully deleted folder: {folder_path}", xbmc.LOGINFO)
            return DELETE_SUCCESS, [], ""
        else:
            xbmc.log(f"OptiKlean DEBUG: Failed to delete folder: {folder_path} - {error_msg}", xbmc.LOGERROR)
            return DELETE_ERROR, [], error_msg
    
    except Exception as e:
        xbmc.log(f"OptiKlean DEBUG: Exception in delete_folder: {str(e)}", xbmc.LOGERROR)
        return DELETE_ERROR, [], str(e)


# Function to clean addon leftovers (disabled addons and leftovers of uninstalled addons)
def clear_addon_leftovers(auto_mode=False, skip_auto_delay=False):
    start_time = time.perf_counter()
    progress = xbmcgui.DialogProgress()
    progress.create(ADDON_NAME, addon.getLocalizedString(31197))  # "Reading addon information..."
    log_content = addon.getLocalizedString(31165) + "\n\n"
    xbmc.log("OptiKlean DEBUG: Starting clear_addon_leftovers", xbmc.LOGINFO)

    # Get enabled addons
    progress.update(20, addon.getLocalizedString(31208))  # "Reading enabled addons list..."
    enabled_addons = []
    try:
        json_response = xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Addons.GetAddons", "params":{"enabled":true}, "id":1}')
        response = json.loads(json_response)
        if 'result' in response and 'addons' in response['result']:
            enabled_addons = [addon['addonid'] for addon in response['result']['addons']]
            xbmc.log(f"OptiKlean DEBUG: Found {len(enabled_addons)} enabled addons", xbmc.LOGINFO)
    except Exception as e:
        xbmc.log(f"OptiKlean DEBUG: Error getting enabled addons: {str(e)}", xbmc.LOGERROR)

    # Get disabled addons
    progress.update(30, addon.getLocalizedString(31209))  # "Reading disabled addons list..."
    disabled_addons = []
    try:
        json_response = xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Addons.GetAddons", "params":{"enabled":false}, "id":1}')
        response = json.loads(json_response)
        if 'result' in response and 'addons' in response['result']:
            disabled_addons = [addon['addonid'] for addon in response['result']['addons']]
            xbmc.log(f"OptiKlean DEBUG: Found {len(disabled_addons)} disabled addons", xbmc.LOGINFO)
    except Exception as e:
        xbmc.log(f"OptiKlean DEBUG: Error getting disabled addons: {str(e)}", xbmc.LOGERROR)

    all_installed_addons = set(enabled_addons + disabled_addons)
    disabled_addons_set = set(disabled_addons)
    xbmc.log(f"OptiKlean DEBUG: Total installed addons: {len(all_installed_addons)}", xbmc.LOGINFO)

    # Check addons folder
    addon_dir = xbmcvfs.translatePath("special://home/addons/")
    progress.update(40, addon.getLocalizedString(31210))  # "Finding addon folders..."
    existing_addon_folders = set(xbmcvfs.listdir(addon_dir)[0]) if xbmcvfs.exists(addon_dir) else set()
    xbmc.log(f"OptiKlean DEBUG: Found {len(existing_addon_folders)} addon folders on disk", xbmc.LOGINFO)

    # Check addon_data folder
    addon_data_dir = xbmcvfs.translatePath("special://home/userdata/addon_data/")
    progress.update(50, addon.getLocalizedString(31211))  # "Checking addon data folders..."
    existing_addon_data_folders = set(xbmcvfs.listdir(addon_data_dir)[0]) if xbmcvfs.exists(addon_data_dir) else set()
    xbmc.log(f"OptiKlean DEBUG: Found {len(existing_addon_data_folders)} addon_data folders on disk", xbmc.LOGINFO)

    # Identify leftovers
    orphaned_folders = [folder for folder in existing_addon_folders if folder not in all_installed_addons]
    disabled_folders = [folder for folder in existing_addon_folders if folder in disabled_addons_set]
    orphaned_addon_data = [folder for folder in existing_addon_data_folders if folder not in all_installed_addons]
    disabled_addon_data = [folder for folder in existing_addon_data_folders if folder in disabled_addons_set]
    xbmc.log(f"OptiKlean DEBUG: Found {len(orphaned_folders)} orphaned folders, {len(disabled_folders)} disabled folders, {len(orphaned_addon_data)} orphaned addon_data, {len(disabled_addon_data)} disabled addon_data", xbmc.LOGINFO)
    
    # Log detailed list of orphaned folders for debugging
    if orphaned_folders:
        xbmc.log(f"OptiKlean DEBUG: Orphaned addon folders list: {orphaned_folders}", xbmc.LOGINFO)
    if orphaned_addon_data:
        xbmc.log(f"OptiKlean DEBUG: Orphaned addon_data folders list: {orphaned_addon_data}", xbmc.LOGINFO)

    # Create selection list
    display_list = []
    folder_map = {}
    xbmc.log("OptiKlean DEBUG: Building selection list", xbmc.LOGINFO)

    # Disabled addon folders (in addons)
    for folder in disabled_folders:
        if folder != "packages":  # Skip packages folder
            display_name = f"{addon.getLocalizedString(31226)} {folder} (addons)"
            display_list.append(display_name)
            folder_map[display_name] = xbmcvfs.translatePath(os.path.normpath(os.path.join(addon_dir, folder)))
            xbmc.log(f"OptiKlean DEBUG: Added disabled addon folder: {folder}", xbmc.LOGINFO)

    # Disabled addon_data folders
    for folder in disabled_addon_data:
        if folder != "packages":  # Skip packages folder
            display_name = f"{addon.getLocalizedString(31226)} {folder} (addon_data)"
            display_list.append(display_name)
            folder_map[display_name] = xbmcvfs.translatePath(os.path.normpath(os.path.join(addon_data_dir, folder)))
            xbmc.log(f"OptiKlean DEBUG: Added disabled addon_data folder: {folder}", xbmc.LOGINFO)

    # Orphaned addon folders
    for folder in orphaned_folders:
        if folder != "packages" and folder != "temp":  # Skip packages and temp folders
            display_name = f"{addon.getLocalizedString(31227)} {folder} (addons)"
            display_list.append(display_name)
            folder_map[display_name] = xbmcvfs.translatePath(os.path.normpath(os.path.join(addon_dir, folder)))
            xbmc.log(f"OptiKlean DEBUG: Added orphaned addon folder: {folder}", xbmc.LOGINFO)

    # Orphaned addon_data folders
    for folder in orphaned_addon_data:
        if folder != "packages":  # Skip packages folder
            display_name = f"{addon.getLocalizedString(31227)} {folder} (addon_data)"
            display_list.append(display_name)
            folder_map[display_name] = xbmcvfs.translatePath(os.path.normpath(os.path.join(addon_data_dir, folder)))
            xbmc.log(f"OptiKlean DEBUG: Added orphaned addon_data folder: {folder}", xbmc.LOGINFO)

    progress.close()

    if not display_list:
        xbmc.log("OptiKlean DEBUG: No leftover or disabled addons found", xbmc.LOGINFO)
        progress.close()
        log_content += addon.getLocalizedString(31112) + "\n"
        write_log("clear_addon_leftovers", log_content)
        
        # Update the automatic settings logs even if there are no addons to delete
        xbmc.log(f"OptiKlean DEBUG: auto_mode={auto_mode}, clear_addon_leftovers_enable={addon.getSettingBool('clear_addon_leftovers_enable')}", xbmc.LOGINFO)
        if not auto_mode and addon.getSettingBool("clear_addon_leftovers_enable"):
            try:
                update_last_run("clear_addon_leftovers")
                update_automatic_settings_log()
                xbmc.log(AUTOMATIC_LOG_UPDATED_MESSAGE, xbmc.LOGINFO)
            except Exception as e:
                xbmc.log(f"OptiKlean: Error updating automatic logs: {str(e)}", xbmc.LOGERROR)

        # Show the dialog window only if not in automatic mode
        if not auto_mode:
            xbmcgui.Dialog().ok("OptiKlean", addon.getLocalizedString(31061))
        return

    # User selection
    message = addon.getLocalizedString(31062)
    if not auto_mode:
        selected = xbmcgui.Dialog().multiselect(message, display_list)
        xbmc.log(f"OptiKlean DEBUG: User selected {len(selected) if selected else 0} items", xbmc.LOGINFO)

        if not selected:
            xbmc.log("OptiKlean DEBUG: No items selected for deletion", xbmc.LOGINFO)
            write_log("clear_addon_leftovers", log_content)
            return

        selected_display_names = [display_list[i] for i in selected]
    else:
        # Automatic mode: apply the delay, if set, before starting
        delay_seconds = get_autostart_delay()
        if delay_seconds > 0 and not skip_auto_delay:
            xbmc.log(f"OptiKlean: Automatic addon leftovers cleaning delayed by {delay_seconds} seconds", xbmc.LOGINFO)
            time.sleep(delay_seconds)
        
        selected_display_names = display_list

    # Deletion process
    progress = xbmcgui.DialogProgress()
    progress.create(ADDON_NAME, addon.getLocalizedString(31198))  # "Removing selected addons..."
    total_selected = len(selected_display_names)
    deleted_folders = []
    locked_folders = []
    locked_files = []
    error_folders = []
    total_size_freed = 0  # Track total size of deleted files

    for index, display_name in enumerate(selected_display_names):
        if progress.iscanceled():
            xbmc.log(DEBUG_CANCELLED_MESSAGE, xbmc.LOGINFO)
            break

        folder_path = folder_map[display_name]
        xbmc.log(f"OptiKlean DEBUG: Processing folder {folder_path} ({index+1}/{total_selected})", xbmc.LOGINFO)
        percent = int((index / total_selected) * 100) if total_selected > 0 else 0
        progress.update(percent, addon.getLocalizedString(31212).format(index=index+1, total=total_selected, path=folder_path))

        # Get folder size before deletion
        folder_size = get_folder_size(folder_path)
        xbmc.log(f"OptiKlean DEBUG: Folder size before deletion: {folder_size} bytes", xbmc.LOGINFO)
        
        status, locked_file_list, error_msg = delete_folder(folder_path, progress_dialog=progress)
        if status == DELETE_SUCCESS:
            xbmc.log(f"OptiKlean DEBUG: Successfully deleted folder {folder_path}", xbmc.LOGINFO)
            deleted_folders.append((folder_path, folder_size))
            total_size_freed += folder_size
        elif status == DELETE_LOCKED:
            xbmc.log(f"OptiKlean DEBUG: Folder locked {folder_path}", xbmc.LOGINFO)
            locked_folders.append(folder_path)
            locked_files.extend(locked_file_list)
        else:
            xbmc.log(f"OptiKlean DEBUG: Error deleting folder {folder_path}: {error_msg}", xbmc.LOGERROR)
            error_folders.append(f"{folder_path} ({error_msg})")

    progress.close()

    # Calculate total MB freed
    total_size_freed = sum(size for _, size in deleted_folders)  # Calculate from deleted_folders
    total_mb = total_size_freed / (1024 * 1024) if total_size_freed > 0 else 0  # Initialize here

    # Final log
    xbmc.log(f"OptiKlean DEBUG: Deletion complete. Deleted: {len(deleted_folders)}, Freed: {total_mb:.2f} MB", xbmc.LOGINFO)
    
    # Organize deleted folders by type using existing variables
    deleted_addons = [(f.replace(addon_dir, ""), s) for f, s in deleted_folders if addon_dir in f]
    deleted_addon_data = [(f.replace(addon_data_dir, ""), s) for f, s in deleted_folders if addon_data_dir in f]
    
    if deleted_folders:
        log_content += addon.getLocalizedString(31113) + "\n"
        if deleted_addons:
            log_content += addon.getLocalizedString(31114) + "\n"
            for folder, size in deleted_addons:
                size_mb = size / (1024 * 1024)
                log_content += f"    - {folder} ({size_mb:.2f} MB)\n"
        if deleted_addon_data:
            log_content += addon.getLocalizedString(31115) + "\n"
            for folder, size in deleted_addon_data:
                size_mb = size / (1024 * 1024)
                log_content += f"    - {folder} ({size_mb:.2f} MB)\n"
        log_content += f"\n  Total space freed: {total_mb:.2f} MB\n\n"
    
    if locked_folders:
        cleaned_locked = [f.replace(addon_dir, "").replace(addon_data_dir, "") for f in locked_folders]
        log_content += addon.getLocalizedString(31116) + "\n  " + "\n  ".join(cleaned_locked) + "\n\n"
        if locked_files:
            cleaned_locked_files = [os.path.basename(f) for f in locked_files]
            log_content += addon.getLocalizedString(31117) + "\n  " + "\n  ".join(cleaned_locked_files) + "\n\n"
    if error_folders:
        cleaned_errors = []
        for error in error_folders:
            path, msg = error.split(" (", 1)
            cleaned_path = path.replace(addon_dir, "").replace(addon_data_dir, "")
            cleaned_errors.append(f"{cleaned_path} ({msg}")
        log_content += addon.getLocalizedString(31219) + "\n  " + "\n  ".join(cleaned_errors) + "\n\n"

    execution_time = round(time.perf_counter() - start_time, 2)
    log_content += addon.getLocalizedString(31104).format(time=execution_time) + "\n"
    
    write_log("clear_addon_leftovers", log_content)
    xbmcgui.Dialog().notification(
        "OptiKlean",
        addon.getLocalizedString(31281).format(count=len(deleted_folders), total_mb=total_mb),
        logo_path,
        3000
    )

    # Update the automatic settings logs only if:
    # 1. Not in automatic mode
    # 2. Automatic cleaning is enabled in the settings
    xbmc.log(f"OptiKlean DEBUG: auto_mode={auto_mode}, clear_addon_leftovers_enable={addon.getSettingBool('clear_addon_leftovers_enable')}", xbmc.LOGINFO)
    if not auto_mode and addon.getSettingBool("clear_addon_leftovers_enable"):
        try:
            update_last_run("clear_addon_leftovers")
            update_automatic_settings_log()
            xbmc.log(AUTOMATIC_LOG_UPDATED_MESSAGE, xbmc.LOGINFO)
        except Exception as e:
            xbmc.log(f"OptiKlean: Error updating automatic logs: {str(e)}", xbmc.LOGERROR)

# Function to clean the packages
def clear_kodi_packages(auto_mode=False, skip_auto_delay=False):
    # If in automatic mode, apply the delay, if set, before starting
    if auto_mode:
        delay_seconds = get_autostart_delay()
        if delay_seconds > 0 and not skip_auto_delay:
            xbmc.log(f"OptiKlean: Automatic packages cleaning delayed by {delay_seconds} seconds", xbmc.LOGINFO)
            time.sleep(delay_seconds)
    
    start_time = time.perf_counter()
    progress = xbmcgui.DialogProgress()
    progress.create(ADDON_NAME, addon.getLocalizedString(31199))  # "Preparing to clear packages..."
    
    packages_path = xbmcvfs.translatePath("special://home/addons/packages")
    xbmc.log(f"OptiKlean DEBUG: Using packages path: {packages_path}", xbmc.LOGINFO)
    log_content = addon.getLocalizedString(31097) + "\n\n"  # "Kodi packages cleaning results:"
    
    # Track results
    deleted_items = []
    locked_items = []
    error_items = []
    total_size_freed = 0  # Track total size of deleted packages
    
    xbmc.log(f"OptiKlean DEBUG: Starting package cleanup at path: {packages_path}", xbmc.LOGINFO)
    
    def path_exists(path):
        path = xbmcvfs.translatePath(os.path.normpath(path))
        if xbmcvfs.exists(path):
            xbmc.log(f"OptiKlean DEBUG: Path exists (xbmcvfs): {path}", xbmc.LOGINFO)
            return True
        if os.path.exists(path):
            xbmc.log(f"OptiKlean DEBUG: Path exists (os.path): {path}", xbmc.LOGINFO)
            return True
        xbmc.log(f"OptiKlean DEBUG: Path does not exist: {path}", xbmc.LOGINFO)
        return False
    
    if not path_exists(packages_path):
        error_msg = f"Packages folder does not exist: {packages_path}"
        xbmc.log(f"OptiKlean DEBUG: {error_msg}", xbmc.LOGERROR)
        log_content += error_msg + "\n"
        progress.close()
        write_log("clear_kodi_packages", log_content)
        xbmcgui.Dialog().notification(ADDON_NAME, addon.getLocalizedString(31059), xbmcgui.NOTIFICATION_ERROR, 3000)  # "Packages folder not found"
        return
    
    # Hybrid file listing with robust path handling
    def list_package_files(path):
        norm_path = xbmcvfs.translatePath(os.path.normpath(path))
        try:
            xbmc.log(f"OptiKlean DEBUG: Attempting xbmcvfs.listdir for: {norm_path}", xbmc.LOGINFO)
            _, files = xbmcvfs.listdir(norm_path)
            zip_files = [f for f in files if f.lower().endswith('.zip')]
            xbmc.log(f"OptiKlean DEBUG: Found {len(zip_files)} zip files via xbmcvfs", xbmc.LOGINFO)
            return zip_files
        except Exception as e:
            xbmc.log(f"OptiKlean DEBUG: xbmcvfs.listdir failed, falling back to os.listdir: {str(e)}", xbmc.LOGWARNING)
            try:
                zip_files = [f for f in os.listdir(norm_path) if f.lower().endswith('.zip') and os.path.isfile(
                    xbmcvfs.translatePath(os.path.normpath(os.path.join(norm_path, f))))]
                xbmc.log(f"OptiKlean DEBUG: Found {len(zip_files)} zip files via os.listdir", xbmc.LOGINFO)
                return zip_files
            except Exception as e:
                xbmc.log(f"OptiKlean DEBUG: Failed to list directory contents: {str(e)}", xbmc.LOGERROR)
                return []
    
    package_files = list_package_files(packages_path)
    total_files = len(package_files)
    
    xbmc.log(f"OptiKlean DEBUG: Found {total_files} package files to process", xbmc.LOGINFO)
    
    if total_files == 0:
        progress.close()
        log_content += addon.getLocalizedString(31118) + "\n"  # "No package files found to delete."
        write_log("clear_kodi_packages", log_content)
        xbmcgui.Dialog().notification(ADDON_NAME, addon.getLocalizedString(31060), logo_path, 3000)  # "No packages found"
        # Update the automatic settings logs even if there are no packages
        xbmc.log(f"OptiKlean DEBUG: auto_mode={auto_mode}, clear_kodi_packages_enable={addon.getSettingBool('clear_kodi_packages_enable')}", xbmc.LOGINFO)
        if not auto_mode and addon.getSettingBool("clear_kodi_packages_enable"):
            try:
                update_last_run("clear_kodi_packages")
                update_automatic_settings_log()
                xbmc.log(AUTOMATIC_LOG_UPDATED_MESSAGE, xbmc.LOGINFO)
            except Exception as e:
                xbmc.log(f"OptiKlean: Error updating automatic logs: {str(e)}", xbmc.LOGERROR)
        return
    
    def delete_package_file(file_path):
        norm_path = xbmcvfs.translatePath(os.path.normpath(file_path))
        xbmc.log(f"OptiKlean DEBUG: Attempting to delete: {norm_path}", xbmc.LOGINFO)

        # Get file size before deletion (moved to the beginning)
        try:
            file_size = get_file_size(norm_path)
        except Exception:
            file_size = 0  # Default if the size cannot be obtained

        # First try xbmcvfs
        try:
            if xbmcvfs.delete(norm_path):
                xbmc.log(f"OptiKlean DEBUG: Successfully deleted via xbmcvfs: {norm_path}", xbmc.LOGINFO)
                return DELETE_SUCCESS, file_size  # Return the size instead of ""
            xbmc.log(f"OptiKlean DEBUG: xbmcvfs.delete returned False for: {norm_path}", xbmc.LOGWARNING)
        except Exception as e:
            xbmc.log(f"OptiKlean DEBUG: xbmcvfs.delete exception: {str(e)}", xbmc.LOGWARNING)
        
        # Fallback to os.remove with verification
        try:
            if os.path.exists(norm_path):
                os.remove(norm_path)
                if not os.path.exists(norm_path):
                    xbmc.log(f"OptiKlean DEBUG: Successfully deleted via os.remove: {norm_path}", xbmc.LOGINFO)
                    return DELETE_SUCCESS, file_size
                xbmc.log(f"OptiKlean DEBUG: File still exists after os.remove: {norm_path}", xbmc.LOGERROR)
                return DELETE_ERROR, "File removal failed"
            xbmc.log(f"OptiKlean DEBUG: File disappeared before os.remove: {norm_path}", xbmc.LOGINFO)
            return DELETE_SUCCESS, 0
        except OSError as e:
            if e.errno in (errno.EACCES, errno.EPERM, errno.EBUSY):
                xbmc.log(f"OptiKlean DEBUG: File locked: {norm_path}", xbmc.LOGINFO)
                return DELETE_LOCKED, str(e)
            xbmc.log(f"OptiKlean DEBUG: OS error deleting file: {norm_path} - {str(e)}", xbmc.LOGERROR)
            return DELETE_ERROR, str(e)
        except Exception as e:
            xbmc.log(f"OptiKlean DEBUG: Unexpected error deleting file: {norm_path} - {str(e)}", xbmc.LOGERROR)
            return DELETE_ERROR, str(e)
    
    for index, package_file in enumerate(package_files):
        if progress.iscanceled():
            xbmc.log(DEBUG_CANCELLED_MESSAGE, xbmc.LOGINFO)
            log_content += "\n" + addon.getLocalizedString(31119) + "\n"
            break
            
        percent = int((index / total_files) * 100) if total_files > 0 else 0
        file_path = xbmcvfs.translatePath(os.path.normpath(os.path.join(packages_path, package_file)))
        progress.update(percent, addon.getLocalizedString(31091).format(index=index+1, total=total_files, package_file=package_file))  # "Deleting package ({index}/{total}): {package_file}"
        
        xbmc.log(f"OptiKlean DEBUG: Processing package file {index+1}/{total_files}: {file_path}", xbmc.LOGINFO)
        
        status, result = delete_package_file(file_path)
        if status == DELETE_SUCCESS:
            if isinstance(result, int):  # If we got a file size
                deleted_items.append((file_path, result))
                total_size_freed += result
            else:
                deleted_items.append((file_path, 0))  # Default to 0 if size unknown
        elif status == DELETE_LOCKED:
            locked_items.append(f"{file_path} ({result})")
        else:
            error_items.append(f"{file_path} ({result})")
    
    progress.close()
    
    # Format results
    if deleted_items:
        total_mb = total_size_freed / (1024 * 1024)
        log_content += addon.getLocalizedString(31120).format(count=len(deleted_items), size=total_mb) + "\n"
        for file_path, size in deleted_items:
            filename = os.path.basename(file_path)  # Extract just the filename
            size_kb = size / 1024
            size_mb = size / (1024 * 1024)
            # Show size in appropriate unit (KB or MB)
            if size_mb >= 1:
                log_content += f"  - {filename} ({size_mb:.2f} MB)\n"
            else:
                log_content += f"  - {filename} ({size_kb:.2f} KB)\n"
        log_content += "\n"
    
    if locked_items:
        log_content += addon.getLocalizedString(31121) + "\n"
        for item in locked_items:
            path, reason = item.split(" (", 1) if " (" in item else (item, "")
            filename = os.path.basename(path)
            log_content += f"  - {filename} ({reason}\n"
        log_content += "\n"
    
    if error_items:
        log_content += addon.getLocalizedString(31122) + "\n"
        for item in error_items:
            path, reason = item.split(" (", 1) if " (" in item else (item, "")
            filename = os.path.basename(path)
            log_content += f"  - {filename} ({reason}\n"
        log_content += "\n"

    execution_time = round(time.perf_counter() - start_time, 2)
    log_content += "\n" + addon.getLocalizedString(31104).format(time=execution_time) + "\n"
    write_log("clear_kodi_packages", log_content)
    
    # Show summary notification
    if deleted_items:
        total_mb = total_size_freed / (1024 * 1024)
        summary = addon.getLocalizedString(31153).format(count=len(deleted_items), size=total_mb)
    else:
        summary = addon.getLocalizedString(31154)
    if locked_items:
        summary += f" ({len(locked_items)} locked)"
    xbmcgui.Dialog().notification(ADDON_NAME, summary, logo_path, 3000)
    xbmc.log(f"OptiKlean DEBUG: Package cleanup completed. {summary}", xbmc.LOGINFO)

    # Update the automatic settings logs only if:
    # 1. Not in automatic mode
    # 2. Automatic cleaning is enabled in the settings
    xbmc.log(f"OptiKlean DEBUG: auto_mode={auto_mode}, clear_kodi_packages_enable={addon.getSettingBool('clear_kodi_packages_enable')}", xbmc.LOGINFO)
    if not auto_mode and addon.getSettingBool("clear_kodi_packages_enable"):
        try:
            update_last_run("clear_kodi_packages")
            update_automatic_settings_log()
            xbmc.log(AUTOMATIC_LOG_UPDATED_MESSAGE, xbmc.LOGINFO)
        except Exception as e:
            xbmc.log(f"OptiKlean: Error updating automatic logs: {str(e)}", xbmc.LOGERROR)

# Function to optimize the databases of Kodi and addons
def optimize_databases(auto_mode=False, skip_auto_delay=False):
    # If in automatic mode, apply the delay, if set, before starting
    if auto_mode:
        delay_seconds = get_autostart_delay()
        if delay_seconds > 0 and not skip_auto_delay:
            xbmc.log(f"OptiKlean: Automatic database optimization delayed by {delay_seconds} seconds", xbmc.LOGINFO)
            time.sleep(delay_seconds)
    
    if not auto_mode:
        warning_message = addon.getLocalizedString(30400)
        
        user_choice = xbmcgui.Dialog().yesno(
            addon.getLocalizedString(30300),
            warning_message
        )
        
        if not user_choice:
            xbmc.log("OptiKlean: User cancelled database optimization", xbmc.LOGINFO)
            return

    start_time = time.perf_counter()
    # Base paths
    std_db_path = xbmcvfs.translatePath(DATABASE_SPECIAL_PATH)
    backup_path_setting = addon.getSetting("backup_path")
    # If backup_path is configured → {backup_path}/db_backups/
    # If empty → {addon_profile}/db_backups/
    if backup_path_setting and backup_path_setting.strip():
        backup_path = os.path.join(backup_path_setting, 'db_backups')
    else:
        backup_path = os.path.join(xbmcvfs.translatePath(addon.getAddonInfo('profile')), 'db_backups')
    xbmc.log(f"OptiKlean DEBUG: Using backup path: {backup_path}", xbmc.LOGINFO)
    addon_data_path = xbmcvfs.translatePath("special://userdata/addon_data/").rstrip('/') + '/'

    # Initialize log (without debug)
    log_content = addon.getLocalizedString(31167) + "\n\n"
    
    # Results
    optimized_dbs = []
    locked_dbs = []
    error_dbs = []
    backup_dbs = []
    backup_failed = []
    integrity_checks = []
    backup_cleanup = []
    backup_cleanup_failed = []
    corrupted_databases = []  # New list for corrupted databases

    # Progress dialog
    progress = xbmcgui.DialogProgress()
    progress.create(ADDON_NAME, addon.getLocalizedString(31200))  # "Preparing database optimization..."
    
    # Create backup directory if it doesn't exist
    try:
        if not os.path.exists(backup_path):
            os.makedirs(backup_path)
            xbmc.log(f"OptiKlean DEBUG: Created backup directory: {backup_path}", xbmc.LOGINFO)
    except Exception as e:
        xbmc.log(f"OptiKlean DEBUG: Error creating backup directory: {str(e)}", xbmc.LOGERROR)
        return
    
    def check_directory_exists(dir_path):
        if xbmcvfs.exists(dir_path):
            return True
        test_file = xbmcvfs.makeLegalFilename(dir_path + "/.temp_test")
        try:
            f = xbmcvfs.File(test_file, 'w')
            f.write("test")
            f.close()
            xbmcvfs.delete(test_file)
            return True
        except Exception:
            try:
                xbmcvfs.delete(test_file)
            except Exception as e:
                xbmc.log(f"OptiKlean: Error cleaning test file: {str(e)}", xbmc.LOGDEBUG)
            return False

    def verify_database_integrity(db_path):
        """
        Verifies the integrity of the database using PRAGMA integrity_check
        Returns: (is_valid, error_message)
        """
        try:
            xbmc.log(f"OptiKlean DEBUG: Checking integrity of {db_path}", xbmc.LOGINFO)
            conn = sqlite3.connect(db_path, timeout=5)
            cursor = conn.cursor()
            
            # PRAGMA integrity_check returns "ok" if everything is fine
            cursor.execute("PRAGMA integrity_check;")
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0].lower() == 'ok':
                xbmc.log(f"OptiKlean DEBUG: Database integrity OK: {db_path}", xbmc.LOGINFO)
                return True, "OK"
            else:
                error_msg = result[0] if result else "Unknown integrity error"
                xbmc.log(f"OptiKlean DEBUG: Database integrity FAILED: {db_path} - {error_msg}", xbmc.LOGERROR)
                return False, error_msg
                
        except sqlite3.DatabaseError as e:
            xbmc.log(f"OptiKlean DEBUG: Database error during integrity check: {db_path} - {str(e)}", xbmc.LOGERROR)
            return False, f"Database error: {str(e)}"
        except Exception as e:
            xbmc.log(f"OptiKlean DEBUG: Exception during integrity check: {db_path} - {str(e)}", xbmc.LOGERROR)
            return False, f"Exception: {str(e)}"

    def restore_database_backup(backup_file_path, original_db_path, db_identifier):
        """
        Restores a database from the backup
        Returns: (success, error_message)
        """
        try:
            if not xbmcvfs.exists(backup_file_path):
                return False, "Backup file not found"
            
            # First delete the corrupted database
            if xbmcvfs.exists(original_db_path):
                if not xbmcvfs.delete(original_db_path):
                    return False, "Failed to delete corrupted database"
            
            # Then copy the backup to the original location
            if xbmcvfs.copy(backup_file_path, original_db_path):
                xbmc.log(f"OptiKlean DEBUG: Successfully restored backup for: {db_identifier}", xbmc.LOGINFO)
                return True, ""
            else:
                return False, "Failed to copy backup file"
                
        except Exception as e:
            xbmc.log(f"OptiKlean DEBUG: Exception restoring backup: {db_identifier} - {str(e)}", xbmc.LOGERROR)
            return False, str(e)

    def cleanup_backup_file(backup_file_path, _db_identifier):
        """
        Removes the backup file if it is no longer needed
        Returns: (success, error_message)
        """
        try:
            if xbmcvfs.exists(backup_file_path):
                if xbmcvfs.delete(backup_file_path):
                    xbmc.log(f"OptiKlean DEBUG: Successfully removed backup: {backup_file_path}", xbmc.LOGINFO)
                    return True, ""
                else:
                    xbmc.log(f"OptiKlean DEBUG: Failed to remove backup: {backup_file_path}", xbmc.LOGERROR)
                    return False, "Delete operation failed"
            else:
                xbmc.log(f"OptiKlean DEBUG: Backup file not found: {backup_file_path}", xbmc.LOGINFO)
                return True, "File not found"
        except Exception as e:
            xbmc.log(f"OptiKlean DEBUG: Exception removing backup: {backup_file_path} - {str(e)}", xbmc.LOGERROR)
            return False, str(e)
    
    def process_databases(directory, source_type="standard"):
        db_files = []
        try:
            _, files = xbmcvfs.listdir(directory)
            for file in files:
                if file.lower().endswith((".db", ".sqlite")):
                    db_files.append((directory, file, source_type))
        except Exception as e:
            xbmc.log(f"OptiKlean: Error collecting database files from {source_type}: {str(e)}", xbmc.LOGDEBUG)
        return db_files
    
    # Database collection
    all_db_files = []
    all_db_files.extend(process_databases(std_db_path, "standard"))
    
    if check_directory_exists(addon_data_path):
        addon_dirs, _ = xbmcvfs.listdir(addon_data_path)
        for addon_dir in addon_dirs:
            addon_path = xbmcvfs.makeLegalFilename(addon_data_path + addon_dir)
            if check_directory_exists(addon_path):
                all_db_files.extend(process_databases(addon_path, f"addon:{addon_dir}"))
                try:
                    subdirs, _ = xbmcvfs.listdir(addon_path)
                    for subdir in subdirs:
                        subdir_path = xbmcvfs.makeLegalFilename(addon_path + '/' + subdir)
                        if check_directory_exists(subdir_path):
                            all_db_files.extend(process_databases(subdir_path, f"addon:{addon_dir}:{subdir}"))
                except Exception as e:
                    xbmc.log(f"OptiKlean: Error processing subdirectory in {addon_dir}: {str(e)}", xbmc.LOGDEBUG)
    
    # First phase: Backup and Optimization
    total_files = len(all_db_files)
    if total_files == 0:
        progress.close()
        log_content += addon.getLocalizedString(31123) + "\n"
        write_log("optimize_databases", log_content)
        xbmcgui.Dialog().notification(ADDON_NAME, addon.getLocalizedString(31063), logo_path, 3000)
        return

    # Keep track of the processed databases for the later verification
    processed_databases = []
    
    for index, (dir_path, file, source_type) in enumerate(all_db_files):
        if progress.iscanceled():
            log_content += "\n" + addon.getLocalizedString(31119) + "\n"
            break
            
        percent = int((index / total_files) * 50)  # First half of the progress
        progress.update(percent, addon.getLocalizedString(31086).format(filename=file))

        db_file_path = xbmcvfs.makeLegalFilename(dir_path + '/' + file)
        backup_type_path = xbmcvfs.makeLegalFilename(backup_path + '/' + source_type.replace(":", "_"))
        
        if not xbmcvfs.exists(backup_type_path):
            xbmcvfs.mkdirs(backup_type_path)
        
        backup_file_path = xbmcvfs.makeLegalFilename(backup_type_path + '/' + file + ".bak")
        
        # Backup
        backup_success = False
        try:
            if xbmcvfs.copy(db_file_path, backup_file_path):
                backup_dbs.append(f"{source_type}:{file}")
                backup_success = True
            else:
                backup_failed.append(f"{source_type}:{file}")
        except Exception:
            backup_failed.append(f"{source_type}:{file}")
        
        # Optimization only if the backup succeeded
        optimization_success = False
        optimization_error = None
        if backup_success:
            try:
                conn = sqlite3.connect(db_file_path, timeout=1)
                conn.execute("PRAGMA quick_check;")
                conn.execute("VACUUM;")
                conn.close()
                optimized_dbs.append(f"{source_type}:{file}")
                optimization_success = True
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower():
                    locked_dbs.append(f"{source_type}:{file}")
                    optimization_error = "locked"
                else:
                    error_dbs.append(f"{source_type}:{file}")
                    optimization_error = str(e)
            except Exception as e:
                error_dbs.append(f"{source_type}:{file}")
                optimization_error = str(e)
        
        # Add to the list for later verification if:
        # 1. The backup succeeded (needed for restore)
        # 2. And if the optimization succeeded OR if it failed due to corruption (not due to a lock)
        if backup_success and (optimization_success or (optimization_error and optimization_error != "locked")):
            processed_databases.append({
                'db_path': db_file_path,
                'backup_path': backup_file_path,
                'identifier': f"{source_type}:{file}",
                'optimization_success': optimization_success,
                'optimization_error': optimization_error
            })

    # Second phase: Integrity check and backup management
    if processed_databases and not progress.iscanceled():
        progress.update(50, addon.getLocalizedString(31213))  # "Verifying database integrity..."
        xbmc.log("OptiKlean DEBUG: Starting integrity verification phase", xbmc.LOGINFO)
        
        for index, db_info in enumerate(processed_databases):
            if progress.iscanceled():
                break
                
            percent = 50 + int((index / len(processed_databases)) * 50)  # Second half of the progress
            progress.update(percent, addon.getLocalizedString(31214).format(db_name=os.path.basename(db_info['db_path'])))
            
            # If the optimization failed, consider the database corrupted without checking
            if not db_info['optimization_success']:
                integrity_checks.append(f"✗ {db_info['identifier']} - Optimization failed: {db_info['optimization_error']}")
                corrupted_databases.append(db_info)
                xbmc.log(f"OptiKlean DEBUG: Database failed optimization: {db_info['identifier']} - {db_info['optimization_error']}", xbmc.LOGWARNING)
                continue
            
            # Check integrity only for successfully optimized databases
            is_valid, error_msg = verify_database_integrity(db_info['db_path'])
            
            if is_valid:
                integrity_checks.append(f"✓ {db_info['identifier']}")
                
                # If the integrity is OK, remove the backup
                cleanup_success, cleanup_error = cleanup_backup_file(
                    db_info['backup_path'], 
                    db_info['identifier']
                )
                
                if cleanup_success:
                    backup_cleanup.append(db_info['identifier'])
                else:
                    backup_cleanup_failed.append(f"{db_info['identifier']} ({cleanup_error})")
            else:
                integrity_checks.append(f"✗ {db_info['identifier']} - {error_msg}")
                # Keep the backup if the integrity is not OK and add it to the corrupted ones
                corrupted_databases.append(db_info)
                xbmc.log(f"OptiKlean DEBUG: Database corrupted after optimization: {db_info['identifier']}", xbmc.LOGWARNING)
    
    progress.close()
    
    # Handling of corrupted databases - Restore dialog
    if corrupted_databases and not auto_mode:
        xbmc.log(f"OptiKlean DEBUG: Found {len(corrupted_databases)} corrupted databases", xbmc.LOGWARNING)
        
        # Create the message for the dialog
        corrupted_list = [db['identifier'] for db in corrupted_databases]
        dialog_message = (
            addon.getLocalizedString(31065).format(count=len(corrupted_databases)) + "\n\n"
            + "\n".join([f"• {db_id}" for db_id in corrupted_list])
            + "\n\n" + addon.getLocalizedString(31066) + "\n"
            + addon.getLocalizedString(31067)
        )
        
        # Show confirmation dialog
        restore_choice = xbmcgui.Dialog().yesno(
            addon.getLocalizedString(31068), 
            dialog_message
        )
        
        if restore_choice:
            # The user chose to restore the backups
            xbmc.log("OptiKlean DEBUG: User chose to restore corrupted database backups", xbmc.LOGINFO)
            
            progress = xbmcgui.DialogProgress()
            progress.create(ADDON_NAME, addon.getLocalizedString(31085))
            
            restored_databases = []
            restore_errors = []
            
            for index, db_info in enumerate(corrupted_databases):
                if progress.iscanceled():
                    break
                
                percent = int((index / len(corrupted_databases)) * 100)
                progress.update(percent, addon.getLocalizedString(31092).format(db_name=os.path.basename(db_info['db_path'])))
                
                restore_success, restore_error = restore_database_backup(
                    db_info['backup_path'],
                    db_info['db_path'],
                    db_info['identifier']
                )
                
                if restore_success:
                    restored_databases.append(db_info['identifier'])
                    
                    # After a successful restore, delete the backup
                    cleanup_success, cleanup_error = cleanup_backup_file(
                        db_info['backup_path'],
                        db_info['identifier']
                    )
                    
                    if cleanup_success:
                        backup_cleanup.append(db_info['identifier'])
                    else:
                        backup_cleanup_failed.append(f"{db_info['identifier']} ({cleanup_error})")
                else:
                    restore_errors.append(f"{db_info['identifier']} ({restore_error})")
            
            progress.close()
            
            # Update the lists for the log
            if restored_databases:
                log_content += "\n" + addon.getLocalizedString(31124) + "\n"
                log_content += addon.getLocalizedString(31125).format(count=len(restored_databases)) + "\n"
                log_content += "\n".join(f"• {db}" for db in restored_databases) + "\n\n"
                
                # Remove the restored databases from the corrupted list for the final log
                corrupted_databases = [db for db in corrupted_databases if db['identifier'] not in restored_databases]
            
            if restore_errors:
                log_content += addon.getLocalizedString(31126) + "\n"
                log_content += "\n".join(f"• {error}" for error in restore_errors) + "\n\n"
            
            # Show restore notification
            if restored_databases:
                notification_msg = addon.getLocalizedString(31069).format(count=len(restored_databases))
                if restore_errors:
                    notification_msg += f" ({len(restore_errors)} errors)"
                xbmcgui.Dialog().notification(ADDON_NAME, notification_msg, logo_path, 5000)
        else:
            # The user chose not to restore
            xbmc.log("OptiKlean DEBUG: User chose not to restore corrupted database backups", xbmc.LOGINFO)
            log_content += "\n" + addon.getLocalizedString(31127) + "\n"
            log_content += addon.getLocalizedString(31128) + "\n\n"
    
    elif corrupted_databases and auto_mode:
        # In automatic mode, automatically restore the corrupted databases
        xbmc.log(f"OptiKlean DEBUG: Found {len(corrupted_databases)} corrupted databases in auto mode - restoring automatically", xbmc.LOGWARNING)
        
        restored_databases = []
        restore_errors = []
        
        for db_info in corrupted_databases:
            restore_success, restore_error = restore_database_backup(
                db_info['backup_path'],
                db_info['db_path'],
                db_info['identifier']
            )
            
            if restore_success:
                restored_databases.append(db_info['identifier'])
                
                # After a successful restore, delete the backup
                cleanup_success, cleanup_error = cleanup_backup_file(
                    db_info['backup_path'],
                    db_info['identifier']
                )
                
                if cleanup_success:
                    backup_cleanup.append(db_info['identifier'])
                else:
                    backup_cleanup_failed.append(f"{db_info['identifier']} ({cleanup_error})")
            else:
                restore_errors.append(f"{db_info['identifier']} ({restore_error})")
        
        # Log of the automatic restore results
        if restored_databases:
            log_content += "\n" + addon.getLocalizedString(31129) + "\n"
            log_content += addon.getLocalizedString(31130).format(count=len(restored_databases)) + "\n"
            log_content += "\n".join(f"• {db}" for db in restored_databases) + "\n\n"
            
            xbmc.log(f"OptiKlean: Auto-restored {len(restored_databases)} corrupted databases", xbmc.LOGINFO)
            
            # Remove the restored databases from the corrupted list for the final log
            corrupted_databases = [db for db in corrupted_databases if db['identifier'] not in restored_databases]
        
        if restore_errors:
            log_content += addon.getLocalizedString(31131) + "\n"
            log_content += "\n".join(f"• {error}" for error in restore_errors) + "\n\n"
            
            xbmc.log(f"OptiKlean: Failed to auto-restore {len(restore_errors)} databases", xbmc.LOGERROR)
        
        # If there are still corrupted databases that were not restored
        if corrupted_databases:
            log_content += addon.getLocalizedString(31132) + "\n"
            log_content += addon.getLocalizedString(31133) + "\n"
            log_content += "\n".join(f"• {db['identifier']}" for db in corrupted_databases) + "\n"
            log_content += addon.getLocalizedString(31134) + "\n\n"
    
    # Build the detailed log
    log_content += addon.getLocalizedString(31135).format(count=total_files) + "\n\n"
    
    if backup_dbs:
        log_content += addon.getLocalizedString(31136) + "\n" + "\n".join(f"• {db}" for db in backup_dbs) + "\n\n"
    
    if optimized_dbs:
        log_content += addon.getLocalizedString(31137) + "\n" + "\n".join(f"• {db}" for db in optimized_dbs) + "\n\n"
    
    if integrity_checks:
        log_content += addon.getLocalizedString(31138) + "\n" + "\n".join(f"• {check}" for check in integrity_checks) + "\n\n"
    
    if backup_cleanup:
        log_content += addon.getLocalizedString(31139) + "\n" + "\n".join(f"• {db}" for db in backup_cleanup) + "\n\n"
    
    if locked_dbs:
        log_content += addon.getLocalizedString(31140) + "\n" + "\n".join(f"• {db}" for db in locked_dbs) + "\n\n"
    
    if backup_failed:
        log_content += addon.getLocalizedString(31141) + "\n" + "\n".join(f"• {db}" for db in backup_failed) + "\n\n"
    
    if error_dbs:
        log_content += addon.getLocalizedString(31142) + "\n" + "\n".join(f"• {db}" for db in error_dbs) + "\n\n"
    
    if backup_cleanup_failed:
        log_content += addon.getLocalizedString(31143) + "\n" + "\n".join(f"• {db}" for db in backup_cleanup_failed) + "\n\n"

    # If there are still corrupted databases (not restored), include them in the log
    if corrupted_databases:
        log_content += addon.getLocalizedString(31144) + "\n"
        log_content += "\n".join(f"• {db['identifier']}" for db in corrupted_databases) + "\n\n"

    # Final statistics
    total_optimized = len(optimized_dbs)
    total_cleaned_backups = len(backup_cleanup)
    total_retained_backups = len(backup_dbs) - total_cleaned_backups
    total_corrupted = len(corrupted_databases)
    
    log_content += addon.getLocalizedString(31145) + "\n"
    log_content += addon.getLocalizedString(31146).format(count=total_optimized) + "\n"
    log_content += addon.getLocalizedString(31147).format(count=total_cleaned_backups) + "\n"
    log_content += addon.getLocalizedString(31148).format(count=total_retained_backups) + "\n"
    if total_corrupted > 0:
        log_content += addon.getLocalizedString(31149).format(count=total_corrupted) + "\n"

    execution_time = round(time.perf_counter() - start_time, 2)
    log_content += "\n" + addon.getLocalizedString(31104).format(time=execution_time) + "\n"    
    write_log("optimize_databases", log_content)
    
    # More informative final notification
    if total_optimized > 0:
        if total_cleaned_backups > 0:
            notification_msg = addon.getLocalizedString(31150).format(count=total_optimized)
            if total_corrupted > 0:
                if auto_mode and 'restored_databases' in locals():
                    notification_msg += addon.getLocalizedString(31151).format(count=len(restored_databases))
                else:
                    notification_msg += f", {total_corrupted} corrupted"
            else:
                notification_msg += addon.getLocalizedString(31152).format(count=total_cleaned_backups)
        else:
            notification_msg = addon.getLocalizedString(31150).format(count=total_optimized) + f", {total_retained_backups} backups retained"
            if total_corrupted > 0:
                if auto_mode and 'restored_databases' in locals():
                    notification_msg += addon.getLocalizedString(31151).format(count=len(restored_databases))
                else:
                    notification_msg += f", {total_corrupted} corrupted"
    else:
        notification_msg = addon.getLocalizedString(31080)
    
    xbmcgui.Dialog().notification(ADDON_NAME, notification_msg, logo_path, 5000)

    # Update the automatic settings logs only if:
    # 1. Not in automatic mode
    # 2. Automatic cleaning is enabled in the settings
    if not auto_mode and addon.getSettingBool("optimize_databases_enable"):
        try:
            update_last_run("optimize_databases")
            update_automatic_settings_log()
            xbmc.log(AUTOMATIC_LOG_UPDATED_MESSAGE, xbmc.LOGINFO)
        except Exception as e:
            xbmc.log(f"OptiKlean: Error updating automatic logs: {str(e)}", xbmc.LOGERROR)


def show_backup_dialog():
    choice = xbmcgui.Dialog().select(addon.getLocalizedString(31183), [
        addon.getLocalizedString(31184),  # "Full backup"
        addon.getLocalizedString(31185),  # "Backup only addons"
        addon.getLocalizedString(31186),  # "Backup only addon data"
        addon.getLocalizedString(31187),  # "Backup addons + data"
        addon.getLocalizedString(31188),  # "Backup skins"
        addon.getLocalizedString(31189),  # "Backup Kodi databases"
        addon.getLocalizedString(31190),  # "Backup sources"
        addon.getLocalizedString(31191),  # "Backup GUI settings"
        addon.getLocalizedString(31192),  # "Backup profiles"
        addon.getLocalizedString(31193),  # "Backup advanced settings"
        addon.getLocalizedString(31194),  # "Backup keymaps"
        addon.getLocalizedString(31195),  # "Backup playlists"
        addon.getLocalizedString(31228),  # "Backup network passwords" 
        addon.getLocalizedString(31229)   # "Restore from backup"
    ])
    
    if choice == -1:
        return

    actions = [
        "full", "addons", "addon_data", "both", "skins", "databases",
        "sources", "gui_settings", "profiles", "advanced_settings", 
        "keymaps", "playlists", "passwords", "restore" 
    ]

    mode = actions[choice]
    if mode == "restore":
        backup_restore.perform_restore()
    else:
        backup_restore.perform_backup(mode)


def _show_support_url_dialog(url, heading_id=30307):
    xbmcgui.Dialog().ok(
        heading=addon.getLocalizedString(heading_id),
        message=f"{addon.getLocalizedString(30402)}\n\n{url}"
    )


def show_support():
    """Shows the custom dialog window for support"""
    telegram_url = "https://t.me/ItalianSpaghettiGeeks"
    
    # Create a class for the dialog window
    class SupportDialog(xbmcgui.WindowXMLDialog):
        def __init__(self, *args, **kwargs):
            self.telegram_url = kwargs.get('telegram_url')
            super(SupportDialog, self).__init__(*args, **kwargs)
        
        def onInit(self):
            try:
                # Set only the texts (the QR image is already defined in the XML)
                label_control = self.getControl(9002)
                if label_control:
                    label_control.setLabel(addon.getLocalizedString(30807))  # "Telegram group:"
                
                url_control = self.getControl(9003)
                if url_control:
                    url_control.setLabel(self.telegram_url)
                    
            except Exception as e:
                xbmc.log(f"OptiKlean: Error initializing support dialog - {str(e)}", xbmc.LOGERROR)
        
        def onClick(self, control_id):
            try:
                if control_id == 9000:  # Close button
                    self.close()
                elif control_id == 9003:  # Telegram URL button
                    self.open_telegram_url()
            except Exception as e:
                xbmc.log(f"OptiKlean: Error in support dialog click handler - {str(e)}", xbmc.LOGERROR)
        
        def open_telegram_url(self):
            """Opens the Telegram URL using the browser or the native app"""
            try:
                # On Android, try the Telegram intent first
                if xbmc.getCondVisibility("System.Platform.Android"):
                    xbmc.log("OptiKlean: Attempting to open Telegram via Android intent", xbmc.LOGINFO)
                    try:
                        xbmc.executebuiltin('StartAndroidActivity("org.telegram.messenger","android.intent.action.VIEW",,"tg://resolve?domain=ItalianSpaghettiGeeks")')
                        xbmc.log("OptiKlean: Successfully opened Telegram app", xbmc.LOGINFO)
                        return
                    except Exception as e:
                        xbmc.log(f"OptiKlean: Failed to open Telegram app: {str(e)}", xbmc.LOGWARNING)
                
                # Fallback: open in the web browser
                browser_url = self.telegram_url
                xbmc.log(f"OptiKlean: Opening Telegram URL in browser: {browser_url}", xbmc.LOGINFO)
                
                # Try different methods to open the URL
                if xbmc.getCondVisibility("System.Platform.Windows"):
                    # Windows: use RunPlugin to open the URL
                    xbmc.executebuiltin(f'System.Exec("cmd /c start {browser_url}")')
                elif xbmc.getCondVisibility("System.Platform.Linux"):
                    # Linux: use xdg-open
                    xbmc.executebuiltin(f'System.Exec("xdg-open {browser_url}")')
                elif xbmc.getCondVisibility("System.Platform.OSX"):
                    # macOS: use open
                    xbmc.executebuiltin(f'System.Exec("open {browser_url}")')
                elif xbmc.getCondVisibility("System.Platform.IOS"):
                    # iOS: security limitations - show dialog with URL
                    _show_support_url_dialog(browser_url)
                    return
                elif xbmc.getCondVisibility("System.Platform.Android"):
                    # Android: use browser intent as fallback
                    xbmc.executebuiltin(f'StartAndroidActivity("","android.intent.action.VIEW","","{browser_url}")')
                    return

                # Generic fallback: show a notification with the URL
                _show_support_url_dialog(browser_url)
                return
                
            except Exception as e:
                xbmc.log(f"OptiKlean: Error opening Telegram URL: {str(e)}", xbmc.LOGERROR)
                # Final fallback: show dialog with URL
                xbmcgui.Dialog().ok(
                    heading=addon.getLocalizedString(31218),  # "Error"
                    message=f"{addon.getLocalizedString(30402)}\n\n{self.telegram_url}"  # "Visit support group:" + URL
                )
    
    try:
        # Show the dialog window
        dialog = SupportDialog(
            'SupportDialog.xml',
            xbmcaddon.Addon().getAddonInfo('path'),
            'default',
            '1080i',
            telegram_url=telegram_url
        )
        dialog.doModal()
        del dialog
    except Exception as e:
        xbmc.log(f"OptiKlean: Error showing support dialog - {str(e)}", xbmc.LOGERROR)
        # Fallback to the standard dialog
        _show_support_url_dialog(telegram_url)


# Function to view the logs
def view_logs():
    log_reports = [
        (addon.getLocalizedString(30600), "clear_kodi_temp_folder.log"),
        (addon.getLocalizedString(30601), "clear_cache_files_from_addon_data.log"),
        (addon.getLocalizedString(30602), "clear_temp_folders_from_addon_data.log"),
        (addon.getLocalizedString(30603), "clear_temp_folder_from_addons.log"),
        (addon.getLocalizedString(30604), "clear_unused_thumbnails.log"),
        (addon.getLocalizedString(30605), "clear_older_thumbnails.log"),
        (addon.getLocalizedString(30606), "clear_addon_leftovers.log"),
        (addon.getLocalizedString(30607), "clear_kodi_packages.log"),
        (addon.getLocalizedString(30608), "optimize_databases.log"),
        (addon.getLocalizedString(30609), "automatic_cleaning_settings.log"),

        # Backup logs
        (addon.getLocalizedString(30626), "backup_full.log"),
        (addon.getLocalizedString(30610), "backup_addons.log"),
        (addon.getLocalizedString(30611), "backup_addon_data.log"),
        (addon.getLocalizedString(30612), "backup_addons_and_data.log"),
        (addon.getLocalizedString(30613), "backup_skins.log"),
        (addon.getLocalizedString(30614), "backup_databases.log"),
        (addon.getLocalizedString(30615), "backup_sources.log"),
        (addon.getLocalizedString(30616), "backup_GUI_settings.log"),
        (addon.getLocalizedString(30617), "backup_profiles.log"),
        (addon.getLocalizedString(30618), "backup_advanced_settings.log"),
        (addon.getLocalizedString(30619), "backup_keymaps.log"),
        (addon.getLocalizedString(30620), "backup_playlists.log"),

        # Restore log
        (addon.getLocalizedString(30621), "restore_backup.log")
    ]

    # Create a list of user-friendly names
    display_names = [name for name, _ in log_reports]
    selected = xbmcgui.Dialog().select(addon.getLocalizedString(31196), display_names)  # "Select log to view"

    if selected != -1:
        _, filename = log_reports[selected]
        log_file = os.path.join(addon_data_folder, filename)

        try:
            if os.path.exists(log_file):
                content = _read_text_file(log_file)
                if not content.strip():
                    content = addon.getLocalizedString(31220)  # "Empty content"
            else:
                content = addon.getLocalizedString(31221)  # "Log file not found."
        except Exception as e:
            content = addon.getLocalizedString(31222).format(error=str(e))  # "Error reading log file: {error}"

        xbmcgui.Dialog().textviewer(addon.getLocalizedString(31223).format(log_name=display_names[selected]), content)  # "Log: {log_name}"


def run_automatic_maintenance(skip_auto_delay=False):
    """Runs the automatic maintenance when called from autoexec.py"""
    xbmc.log("OptiKlean: Starting automatic maintenance", xbmc.LOGINFO)
    
    actions_executed = []
    addon = xbmcaddon.Addon()
    
    # Ensure data folder exists
    if not xbmcvfs.exists(addon_data_folder):
        xbmcvfs.mkdirs(addon_data_folder)
        xbmc.log("OptiKlean: Created addon data folder", xbmc.LOGINFO)
    
    def should_run_cleaning(cleaning_type):
        """Determines whether a given cleaning should be run based on the switch and the interval"""
        try:
            # Check whether it is enabled in the settings
            if not addon.getSettingBool(f"{cleaning_type}_enable"):
                xbmc.log(f"OptiKlean: {cleaning_type} not executed because it is disabled", xbmc.LOGDEBUG)
                return False

            interval = addon.getSettingInt(f"{cleaning_type}_interval")
            last_run_file = os.path.join(addon_data_folder, f"last_{cleaning_type}.json")

            if not xbmcvfs.exists(last_run_file):
                return True  # first run

            data = _read_json_file(last_run_file, {})
            last_run = data.get("timestamp", 0)

            if last_run == 0:
                return True

            next_run = last_run + (interval * 86400)
            now = int(time.time())
            return now >= next_run

        except Exception as e:
            xbmc.log(f"OptiKlean: Error in should_run_cleaning: {str(e)}", xbmc.LOGERROR)
            return False


    def run_cleaning(cleaning_name, function, success_message):
        """Runs a cleaning if it is active and should be run"""
        try:
            enabled = addon.getSettingBool(f"{cleaning_name}_enable")
            if not enabled:
                xbmc.log(f"OptiKlean: {cleaning_name} is disabled, skipping cleaning", xbmc.LOGINFO)
                return False

            if should_run_cleaning(cleaning_name):
                xbmc.log(f"OptiKlean: Starting {cleaning_name} cleaning", xbmc.LOGINFO)

                if 'skip_auto_delay' in function.__code__.co_varnames:
                    function(auto_mode=True, skip_auto_delay=skip_auto_delay)
                elif 'auto_mode' in function.__code__.co_varnames:
                    function(auto_mode=True)
                else:
                    function()

                update_last_run(cleaning_name)
                actions_executed.append(success_message)

                xbmc.log(f"OptiKlean: Completed {cleaning_name} cleaning", xbmc.LOGINFO)
                return True
            else:
                xbmc.log(f"OptiKlean: {cleaning_name} not needed at the moment", xbmc.LOGINFO)
                return False

        except Exception as e:
            xbmc.log(f"OptiKlean: Error during {cleaning_name}: {str(e)}", xbmc.LOGERROR)
            return False
    
    # Execute cleanings
    run_cleaning("clear_cache_and_temp", clear_cache_and_temp, "Cache/temp")
    run_cleaning("clear_unused_thumbnails", clear_unused_thumbnails, "Thumbnails")
    run_cleaning("clear_addon_leftovers", clear_addon_leftovers, "Addon leftovers")
    run_cleaning("clear_kodi_packages", clear_kodi_packages, "Packages")
    run_cleaning("optimize_databases", optimize_databases, "Databases")

    # Show notification if any action was executed
    if actions_executed:
        msg = "Auto-clean: " + ", ".join(actions_executed)
        xbmcgui.Dialog().notification(ADDON_NAME, msg, logo_path, 4000)
        xbmc.log(f"OptiKlean: Completed cleanings - {msg}", xbmc.LOGINFO)
        
        # Update the settings log after the cleanings
        try:
            update_automatic_settings_log()
        except Exception as e:
            xbmc.log(f"OptiKlean: Error updating settings log: {str(e)}", xbmc.LOGERROR)
    else:
        xbmc.log("OptiKlean: No cleanings required at this time", xbmc.LOGINFO)


class BaseWindow(xbmcgui.WindowXML):
    """Common base class for the addon windows with shared functions"""
    
    def __init__(self, xml_filename, script_path, default_skin='default', default_res='1080i'):
        super().__init__(xml_filename, script_path, default_skin, default_res)
    
    def onAction(self, action):
        """Handles common actions (such as ESC, Back, etc.)"""
        if action.getId() in (9, 10, 92, 216, 247, 257, 275, 61467, 61448):
            self.close()


class DetailsWindow(BaseWindow):
    """Class to manage the folder details window"""
    
    def __init__(self, xml_filename, script_path, default_skin='default', default_res='1080i'):
        super().__init__(xml_filename, script_path, default_skin, default_res)
        self.folder_path = ""
        self.exclude_folders = []
        self.total_size = 0
        self.folder_sizes = []
    
    def set_folder_path(self, folder_path, exclude_folders=None):
        """Sets the path of the folder to analyze and the folders to exclude"""
        if folder_path:
            self.folder_path = folder_path
        self.exclude_folders = exclude_folders or []
    
    def calculate_folder_sizes(self):
        """Calculates the sizes of all folders/files in the specified directory"""
        self.folder_sizes = []
        self.total_size = 0
        
        try:
            if xbmcvfs.exists(self.folder_path):
                dirs, files = xbmcvfs.listdir(self.folder_path)
                
                # Analyze the folders first
                for dir_name in dirs:
                    if dir_name not in self.exclude_folders:  # Exclude specified folders
                        dir_path = xbmcvfs.makeLegalFilename(os.path.join(self.folder_path, dir_name))
                        size = get_folder_size(dir_path)
                        if size > 0:  # Show only folders with content
                            self.folder_sizes.append((dir_name, size))
                            self.total_size += size
                
                # If there are no significant folders, analyze the individual files
                # (useful for the packages folder, which mainly contains .zip files)
                if len(self.folder_sizes) == 0:
                    for file_name in files:
                        if file_name not in self.exclude_folders:  # Exclude specified files
                            file_path = xbmcvfs.makeLegalFilename(os.path.join(self.folder_path, file_name))
                            try:
                                size = get_file_size(file_path)
                                if size > 0:  # Show only files with content
                                    self.folder_sizes.append((file_name, size))
                                    self.total_size += size
                            except Exception as e:
                                xbmc.log(f"OptiKlean DEBUG: Error getting file size for {file_path}: {str(e)}", xbmc.LOGERROR)
                
                # Sort by size (descending)
                self.folder_sizes.sort(key=lambda x: x[1], reverse=True)
        except Exception as e:
            xbmc.log(f"OptiKlean DEBUG: Error calculating folder sizes: {str(e)}", xbmc.LOGERROR)
    
    def onInit(self):
        """Window initialization"""
        try:
            xbmc.log("OptiKlean: DetailsWindow onInit called", xbmc.LOGINFO)
            # SET THE WINDOW TITLE
            self.getControl(1).setLabel(addon.getLocalizedString(30306))  # "Folder Space Analysis"
            
            # SET THE COLUMN HEADERS
            self.getControl(10).setLabel(addon.getLocalizedString(30802))  # "Percentage"
            self.getControl(11).setLabel(addon.getLocalizedString(30803))  # "Size"
            self.getControl(12).setLabel(addon.getLocalizedString(30804))  # "Folder"
            
            # Load the folder data
            if not self.folder_path:
                xbmc.log("OptiKlean: No folder path set for DetailsWindow", xbmc.LOGWARNING)
                self.getControl(1).setLabel(addon.getLocalizedString(31169))  # "Unable to load folder details"
                return
                
            # Calculate folder sizes
            self.calculate_folder_sizes()
            
            if not self.folder_sizes:
                xbmc.log("OptiKlean: No folder data to display", xbmc.LOGWARNING)
                self.getControl(1).setLabel(addon.getLocalizedString(31169))  # "Unable to load folder details"
                return
            
            # Populate the list with the addon data
            try:
                list_control = self.getControl(5000)
                list_control.reset()  # Clear the list
                
                for folder_name, size in self.folder_sizes:
                    if self.total_size > 0:
                        percentage = (size / self.total_size) * 100
                    else:
                        percentage = 0
                    
                    # Create a ListItem for each folder
                    list_item = xbmcgui.ListItem(folder_name)
                    
                    # Show percentages with one decimal for greater precision
                    if percentage >= 0.1:
                        list_item.setProperty("percentage", f"{percentage:.1f}%")
                    elif percentage >= 0.01:
                        list_item.setProperty("percentage", f"{percentage:.2f}%")
                    else:
                        list_item.setProperty("percentage", "<0.01%")
                    list_item.setProperty("size", format_size(size))
                    
                    # Add the item to the list
                    list_control.addItem(list_item)
                
                xbmc.log(f"OptiKlean: DetailsWindow displayed {len(self.folder_sizes)} folders", xbmc.LOGINFO)
                
            except RuntimeError as e:
                xbmc.log(f"OptiKlean DEBUG: Error setting up list control: {str(e)}", xbmc.LOGERROR)
            
        except Exception as e:
            xbmc.log(f"OptiKlean ERROR: Error in DetailsWindow onInit: {str(e)}", xbmc.LOGERROR)
            # Fallback: show a dialog window with the information
            try:
                self.calculate_folder_sizes()
                
                # Build the message formatted as a table
                message = "Folder Space Analysis\n\n"
                message += f"Total directory size: {format_size(self.total_size)}\n\n"
                message += "Percentage | Size      | Folder\n"
                message += "-" * 50 + "\n"
                
                for folder_name, size in self.folder_sizes[:10]:  # Show only the first 10
                    if self.total_size > 0:
                        percentage = (size / self.total_size) * 100
                    else:
                        percentage = 0
                    
                    # Improved percentage format
                    if percentage >= 0.1:
                        perc_str = f"{percentage:7.1f}%"
                    elif percentage >= 0.01:
                        perc_str = f"{percentage:7.2f}%"
                    else:
                        perc_str = "  <0.01%"
                    
                    message += f"{perc_str}   {format_size(size):>8s}   {folder_name}\n"
                
                if len(self.folder_sizes) > 10:
                    message += f"\n... and {len(self.folder_sizes) - 10} more folders"
                
                xbmcgui.Dialog().textviewer(addon.getLocalizedString(31224), message)  # "Folder Details"
                self.close()
            except Exception as fallback_error:
                xbmc.log(f"OptiKlean ERROR: Fallback error: {str(fallback_error)}", xbmc.LOGERROR)
                xbmcgui.Dialog().ok(addon.getLocalizedString(31168), addon.getLocalizedString(31169))
                self.close()
    
    def onClick(self, control_id):
        """Handles clicks on the controls"""
        if control_id == 9000:  # Close button (X)
            self.close()


class AllInOnePanelWindow(BaseWindow):
    """Class to manage the All in One Panel window"""
    
    def __init__(self, xml_filename, script_path, default_skin='default', default_res='1080i'):
        super().__init__(xml_filename, script_path, default_skin, default_res)
        xbmc.log("OptiKlean: AllInOnePanelWindow initialized", xbmc.LOGINFO)
        
        # Initialize the paths
        self.db_path = xbmcvfs.translatePath(DATABASE_SPECIAL_PATH)
        self.thumbnails_path = xbmcvfs.translatePath("special://profile/thumbnails/")
        self.addon_dir = xbmcvfs.translatePath("special://home/addons/")
        self.addon_data_dir = xbmcvfs.translatePath("special://profile/addon_data/")
        self.packages_path = xbmcvfs.translatePath("special://home/addons/packages/")
        self.temp_path = xbmcvfs.translatePath("special://home/addons/temp/")
        self.temp_folder = xbmcvfs.translatePath("special://temp/")
        self._sizes_cache = None
        self._sizes_cache_time = 0
    
    def calculate_unused_thumbnails_size(self):
        """Calculates the size of unused thumbnails by analyzing the texture database"""
        total_size = 0
        
        # Use the existing find_texture_database function with the path already defined
        texture_db = find_texture_database(self.db_path)
        
        if not texture_db:
            xbmc.log("OptiKlean: Texture database not found for size calculation", xbmc.LOGWARNING)
            return 0
        
        try:
            conn = sqlite3.connect(texture_db)
            cursor = conn.cursor()
            
            # Query to get all thumbnails from the database
            cursor.execute("SELECT cachedurl FROM texture")
            db_thumbs = {row[0] for row in cursor.fetchall()}
            conn.close()
            
            # Check thumbnails on disk (self.thumbnails_path is already special://thumbnails/)
            if xbmcvfs.exists(self.thumbnails_path):
                thumb_base = self.thumbnails_path
                
                # Recursively navigate all subfolders
                for root, dirs, files in os.walk(thumb_base):
                    for file in files:
                        full_path = os.path.join(root, file)
                        # Calculate the relative path for comparison with the DB
                        rel_path = os.path.relpath(full_path, thumb_base).replace('\\', '/')
                        
                        # If it is not in the database, count it as unused
                        if rel_path not in db_thumbs:
                            try:
                                total_size += os.path.getsize(full_path)
                            except (OSError, IOError) as e:
                                # The file may have been deleted or may not be accessible
                                xbmc.log(f"OptiKlean DEBUG: Could not get size for {full_path}: {str(e)}", xbmc.LOGDEBUG)
                            except Exception as e:
                                xbmc.log(f"OptiKlean DEBUG: Unexpected error getting size for {full_path}: {str(e)}", xbmc.LOGWARNING)
            
        except Exception as e:
            xbmc.log(f"OptiKlean: Error calculating unused thumbnails size: {str(e)}", xbmc.LOGERROR)
        
        return total_size
    
    def calculate_addon_leftovers_size(self):
        """Calculates the space used by disabled addons and leftovers"""
        total_size = 0
        
        try:
            # Get enabled and disabled addons
            enabled_addons = []
            disabled_addons = []
            
            try:
                json_response = xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Addons.GetAddons", "params":{"enabled":true}, "id":1}')
                response = json.loads(json_response)
                if 'result' in response and 'addons' in response['result']:
                    enabled_addons = [addon['addonid'] for addon in response['result']['addons']]
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                xbmc.log(f"OptiKlean DEBUG: Error getting enabled addons: {str(e)}", xbmc.LOGWARNING)
            except Exception as e:
                xbmc.log(f"OptiKlean DEBUG: Unexpected error getting enabled addons: {str(e)}", xbmc.LOGERROR)
            
            try:
                json_response = xbmc.executeJSONRPC('{"jsonrpc":"2.0", "method":"Addons.GetAddons", "params":{"enabled":false}, "id":1}')
                response = json.loads(json_response)
                if 'result' in response and 'addons' in response['result']:
                    disabled_addons = [addon['addonid'] for addon in response['result']['addons']]
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                xbmc.log(f"OptiKlean DEBUG: Error getting disabled addons: {str(e)}", xbmc.LOGWARNING)
            except Exception as e:
                xbmc.log(f"OptiKlean DEBUG: Unexpected error getting disabled addons: {str(e)}", xbmc.LOGERROR)
            
            all_installed = set(enabled_addons + disabled_addons)
            
            # Check addon folders for orphaned/disabled
            if os.path.exists(self.addon_dir):
                for folder in os.listdir(self.addon_dir):
                    if folder in ('packages', 'temp'):
                        continue
                    folder_path = os.path.join(self.addon_dir, folder)
                    if os.path.isdir(folder_path):
                        # Count if disabled or orphaned
                        if folder not in all_installed or folder in disabled_addons:
                            total_size += get_folder_size(folder_path)
            
            # Check addon_data folders
            if os.path.exists(self.addon_data_dir):
                for folder in os.listdir(self.addon_data_dir):
                    if folder in ('packages',):
                        continue
                    folder_path = os.path.join(self.addon_data_dir, folder)
                    if os.path.isdir(folder_path):
                        if folder not in all_installed or folder in disabled_addons:
                            total_size += get_folder_size(folder_path)

        except Exception as e:
            xbmc.log(f"OptiKlean: Error calculating addon leftovers size: {str(e)}", xbmc.LOGERROR)
        
        return total_size
    
    def calculate_sizes(self, force_refresh=False):
        """Calculates the sizes of all cleanable components"""
        if force_refresh:
            self._sizes_cache = None
            self._sizes_cache_time = 0
        elif self._sizes_cache and (time.time() - self._sizes_cache_time) < SIZE_CACHE_TTL_SECONDS:
            return dict(self._sizes_cache)

        sizes = {
            'addons': 0,
            'addon_data': 0,
            'packages': 0,
            'thumbnails': 0,
            'total': 0,
            'cache_temp': 0,
            'unused_thumbs': 0,
            'addon_leftovers': 0,
            'kodi_packages': 0,
            'total_recoverable': 0
        }
        
        try:
            # Calculate actual folder sizes
            if os.path.exists(self.addon_dir):
                sizes['addons'] = get_folder_size(self.addon_dir)
            
            if os.path.exists(self.addon_data_dir):
                sizes['addon_data'] = get_folder_size(self.addon_data_dir)
            
            if os.path.exists(self.packages_path):
                sizes['packages'] = get_folder_size(self.packages_path)
            
            if os.path.exists(self.thumbnails_path):
                sizes['thumbnails'] = get_folder_size(self.thumbnails_path)
            
            # Calculate total used
            sizes['total'] = sizes['addons'] + sizes['addon_data'] + sizes['packages'] + sizes['thumbnails']
            
            # Calculate recoverable space (estimates for cleanup tasks)
            # Cache/temp from addon_data
            addon_data_cache_temp = 0
            if os.path.exists(self.addon_data_dir):
                for addon_folder in os.listdir(self.addon_data_dir):
                    addon_path = os.path.join(self.addon_data_dir, addon_folder)
                    if os.path.isdir(addon_path):
                        # Check for cache folders
                        cache_path = os.path.join(addon_path, 'cache')
                        if os.path.exists(cache_path):
                            addon_data_cache_temp += get_folder_size(cache_path)
                        # Check for temp folders
                        temp_path = os.path.join(addon_path, 'temp')
                        if os.path.exists(temp_path):
                            addon_data_cache_temp += get_folder_size(temp_path)
            
            # Temp folder
            temp_folder_size = 0
            if os.path.exists(self.temp_folder):
                temp_folder_size = get_folder_size(self.temp_folder)
            
            sizes['cache_temp'] = addon_data_cache_temp + temp_folder_size
            
            # Unused thumbnails
            sizes['unused_thumbs'] = self.calculate_unused_thumbnails_size()
            
            # Addon leftovers
            sizes['addon_leftovers'] = self.calculate_addon_leftovers_size()
            
            # Packages (all of them are potentially removable)
            sizes['kodi_packages'] = sizes['packages']
            
            # Total recoverable
            sizes['total_recoverable'] = (sizes['cache_temp'] + sizes['unused_thumbs'] + 
                                         sizes['addon_leftovers'] + sizes['kodi_packages'])

        except Exception as e:
            xbmc.log(f"OptiKlean: Error in calculate_sizes: {str(e)}", xbmc.LOGERROR)
        
        # Save to cache
        self._sizes_cache = sizes
        self._sizes_cache_time = time.time()
        
        return sizes

    def refresh_data(self):
        """Recalculates and updates all values in the UI"""
        progress = None
        try:
            progress = xbmcgui.DialogProgress()
            progress.create(ADDON_NAME, addon.getLocalizedString(31202))  # "Refreshing data..."
            
            progress.update(10, addon.getLocalizedString(31215))  # "Preparing to recalculate sizes..."
            
            progress.update(50, addon.getLocalizedString(31216))  # "Calculating updated sizes..."
            sizes = self.calculate_sizes(force_refresh=True)  # Force recalculation ignoring the cache
            
            # Update UI labels with new values
            try:
                # Addons size
                self.getControl(8002).setLabel(format_size(sizes['addons']))
                # Addon data size
                self.getControl(8004).setLabel(format_size(sizes['addon_data']))
                # Packages size
                self.getControl(8006).setLabel(format_size(sizes['packages']))
                # Thumbnails size
                self.getControl(8008).setLabel(format_size(sizes['thumbnails']))
                # Total used
                self.getControl(8010).setLabel(format_size(sizes['total']))
                
                # Recoverable sizes
                self.getControl(8012).setLabel(format_size(sizes['cache_temp']))
                self.getControl(8014).setLabel(format_size(sizes['unused_thumbs']))
                self.getControl(8016).setLabel(format_size(sizes['addon_leftovers']))
                self.getControl(8018).setLabel(format_size(sizes['kodi_packages']))
                self.getControl(8020).setLabel(format_size(sizes['total_recoverable']))
            except Exception as e:
                xbmc.log(f"OptiKlean: Error updating UI controls: {str(e)}", xbmc.LOGERROR)
            
            progress.update(100, addon.getLocalizedString(31217))  # "Data refresh completed!"
            progress.close()
            
        except Exception as e:
            xbmc.log(f"OptiKlean: Error in refresh_data: {str(e)}", xbmc.LOGERROR)
            if progress:
                progress.close()

    def show_addons_details(self):
        """Shows the addons details window"""
        try:
            details_window = DetailsWindow(
                DETAILS_WINDOW_XML,
                addon.getAddonInfo('path'),
                'default',
                '1080i'
            )
            details_window.set_folder_path(self.addon_dir, exclude_folders=['packages', 'temp'])
            details_window.doModal()
            del details_window
            
        except Exception as e:
            xbmc.log(f"OptiKlean: Error showing addons details: {str(e)}", xbmc.LOGERROR)
            xbmcgui.Dialog().notification(
                addon.getLocalizedString(31218),  # "Error"
                addon.getLocalizedString(31169),  # "Unable to load folder details"
                xbmcgui.NOTIFICATION_ERROR,
                3000
            )

    def show_addon_data_details(self):
        """Shows the addon data details window"""
        try:
            details_window = DetailsWindow(
                DETAILS_WINDOW_XML,
                addon.getAddonInfo('path'),
                'default',
                '1080i'
            )
            details_window.set_folder_path(self.addon_data_dir, exclude_folders=['packages'])
            details_window.doModal()
            del details_window
            
        except Exception as e:
            xbmc.log(f"OptiKlean: Error showing addon data details: {str(e)}", xbmc.LOGERROR)
            xbmcgui.Dialog().notification(
                addon.getLocalizedString(31218),  # "Error"
                addon.getLocalizedString(31169),  # "Unable to load folder details"
                xbmcgui.NOTIFICATION_ERROR,
                3000
            )

    def show_packages_details(self):
        """Shows the packages details window"""
        try:
            details_window = DetailsWindow(
                DETAILS_WINDOW_XML,
                addon.getAddonInfo('path'),
                'default',
                '1080i'
            )
            details_window.set_folder_path(self.packages_path)
            details_window.doModal()
            del details_window
            
        except Exception as e:
            xbmc.log(f"OptiKlean: Error showing packages details: {str(e)}", xbmc.LOGERROR)
            xbmcgui.Dialog().notification(
                addon.getLocalizedString(31218),  # "Error"
                addon.getLocalizedString(31169),  # "Unable to load folder details"
                xbmcgui.NOTIFICATION_ERROR,
                3000
            )

    def onInit(self):
        """Window initialization"""
        try:
            # SET THE SECTION TITLES
            self.getControl(1).setLabel(addon.getLocalizedString(30800))  # "Actual used space:"
            self.getControl(2).setLabel(addon.getLocalizedString(30809))  # "Estimated space savings..."
            
            # SET THE FIXED LABELS OF SECTION 1 (Used space)
            self.getControl(10).setLabel(addon.getLocalizedString(30813))  # "Addons:"
            self.getControl(11).setLabel(addon.getLocalizedString(30801))  # "Addons data:"
            self.getControl(12).setLabel(addon.getLocalizedString(30805))  # "Kodi packages:"
            self.getControl(13).setLabel(addon.getLocalizedString(30806))  # "Thumbnails:"
            self.getControl(14).setLabel(addon.getLocalizedString(30808))  # "Total used:"
            
            # SET THE FIXED LABELS OF SECTION 2 (Estimated savings)
            self.getControl(21).setLabel(addon.getLocalizedString(30100))  # "Clear cache and temp"
            self.getControl(22).setLabel(addon.getLocalizedString(30101))  # "Clear unused/older thumbnails"
            self.getControl(23).setLabel(addon.getLocalizedString(30102))  # "Clear addons leftovers"
            self.getControl(24).setLabel(addon.getLocalizedString(30103))  # "Clear packages"
            self.getControl(25).setLabel(addon.getLocalizedString(30810))  # "Total recoverable:"
            
            # SET THE INITIAL LABELS OF THE DYNAMIC VALUES TO "Loading..."
            loading_text = addon.getLocalizedString(31225)  # "Loading..."
            
            # Section 1 - Dynamic values
            self.getControl(110).setLabel(loading_text)
            self.getControl(111).setLabel(loading_text)
            self.getControl(112).setLabel(loading_text)
            self.getControl(113).setLabel(loading_text)
            self.getControl(114).setLabel(loading_text)
            
            # Section 2 - Dynamic values
            self.getControl(121).setLabel(loading_text)
            self.getControl(122).setLabel(loading_text)
            self.getControl(123).setLabel(loading_text)
            self.getControl(124).setLabel(loading_text)
            self.getControl(125).setLabel(loading_text)
            
            # SET THE BUTTON LABELS
            self.getControl(201).setLabel(addon.getLocalizedString(30811))  # "Clean all!"
            self.getControl(202).setLabel(addon.getLocalizedString(30812))  # "Restart Kodi"
            
            # NOW CALCULATE AND UPDATE THE DYNAMIC VALUES
            sizes = self.calculate_sizes()
            
            # Update the calculated values
            # Section 1 - Used space
            self.getControl(110).setLabel(format_size(sizes['addons']))
            self.getControl(111).setLabel(format_size(sizes['addon_data']))
            self.getControl(112).setLabel(format_size(sizes['packages']))
            self.getControl(113).setLabel(format_size(sizes['thumbnails']))
            self.getControl(114).setLabel(format_size(sizes['total']))
            
            # Section 2 - Estimated savings
            self.getControl(121).setLabel(format_size(sizes['cache_temp']))
            self.getControl(122).setLabel(format_size(sizes['unused_thumbs']))
            self.getControl(123).setLabel(format_size(sizes['addon_leftovers']))
            self.getControl(124).setLabel(format_size(sizes['kodi_packages']))
            self.getControl(125).setLabel(format_size(sizes['total_recoverable']))            
        except Exception as e:
            xbmc.log(f"OptiKlean: Error in AllInOnePanelWindow.onInit: {str(e)}", xbmc.LOGERROR)
    
    def onClick(self, control_id):
        """Handles clicks on the controls"""
        try:
            if control_id == 9000:  # Close button
                self.close()
            
            elif control_id == 101:  # Details Addons button (magnifier icon)
                self.show_addons_details()
            elif control_id == 102:  # Details Addon Data button (magnifier icon)
                self.show_addon_data_details()
            elif control_id == 103:  # Details Packages button (magnifier icon)
                self.show_packages_details()
            
            # also keep the old ids if used elsewhere
            elif control_id == 8001:  # Addons details button
                self.show_addons_details()
            elif control_id == 8003:  # Addon data details button
                self.show_addon_data_details()
            elif control_id == 8005:  # Packages details button
                self.show_packages_details()
            
            elif control_id == 201:  # Clean all button
                if xbmcgui.Dialog().yesno(
                    addon.getLocalizedString(31172),  # "Confirmation"
                    addon.getLocalizedString(31201)   # "Running full cleanup..."
                ):
                    # Run all cleanup tasks
                    progress = xbmcgui.DialogProgress()
                    progress.create(ADDON_NAME, addon.getLocalizedString(31201))
                    
                    try:
                        # Execute cleanup functions
                        clear_cache_and_temp(auto_mode=True)
                        if progress.iscanceled():
                            return
                        
                        clear_unused_thumbnails(auto_mode=True)
                        if progress.iscanceled():
                            return
                        
                        clear_addon_leftovers(auto_mode=True)
                        if progress.iscanceled():
                            return
                        
                        clear_kodi_packages(auto_mode=True)
                        if progress.iscanceled():
                            return
                        
                        # Refresh with force_refresh=True to ignore the cache and show updated data
                        self.refresh_data()
                        
                    except Exception as e:
                        xbmc.log(f"OptiKlean: Error during full cleanup: {str(e)}", xbmc.LOGERROR)
                        xbmcgui.Dialog().notification(
                            "OptiKlean",
                            addon.getLocalizedString(31174),  # "Cleanup failed (see log)"
                            xbmcgui.NOTIFICATION_ERROR,
                            5000
                        )
                    finally:
                        if 'progress' in locals() and progress:
                            progress.close()
                            
            elif control_id == 8021:  # Refresh button
                self.refresh_data()
            elif control_id == 202:  # Restart Kodi button
                if xbmcgui.Dialog().yesno(
                    addon.getLocalizedString(31172),  # "Confirmation"
                    addon.getLocalizedString(31173)   # "Would you like to restart Kodi now?"
                ):
                    xbmc.executebuiltin('RestartApp')
                    
        except Exception as e:
            xbmc.log(f"OptiKlean: Error in AllInOnePanelWindow.onClick: {str(e)}", xbmc.LOGERROR)

def show_all_in_one_panel():
    """Opens the custom All in One Panel window"""
    try:
        # Use the addon path correctly
        addon_path = addon.getAddonInfo('path')
        xml_file = "AllInOnePanel.xml"
        
        # Check that the XML file exists
        xml_full_path = os.path.join(addon_path, "resources", "skins", "default", "1080i", xml_file)
        if not xbmcvfs.exists(xml_full_path):
            xbmc.log(f"OptiKlean ERROR: XML file not found: {xml_full_path}", xbmc.LOGERROR)
            xbmcgui.Dialog().notification(ADDON_NAME, addon.getLocalizedString(31170), xbmcgui.NOTIFICATION_ERROR, 5000)
            return
        
        xbmc.log(f"OptiKlean: Opening XML window from: {xml_full_path}", xbmc.LOGINFO)
        
        # Create and show the custom window using the class
        window = AllInOnePanelWindow(xml_file, addon_path, "default", "1080i")
        window.doModal()
        del window
        
    except Exception as e:
        xbmc.log(f"OptiKlean ERROR: Error opening the All in One Panel window: {str(e)}", xbmc.LOGERROR)
        xbmcgui.Dialog().notification(addon.getLocalizedString(31218), addon.getLocalizedString(31171).format(error=str(e)), xbmcgui.NOTIFICATION_ERROR, 5000)


def open_addon_settings():
    # Open the addon settings
    addon.openSettings()


def _parse_action_params():
    if len(sys.argv) <= 2 or not sys.argv[2].startswith('?'):
        return {}
    return {
        pair.split('=')[0]: pair.split('=')[1]
        for pair in sys.argv[2][1:].split('&')
        if '=' in pair
    }


def _run_requested_action(action):
    action_handlers = {
        "clear_cache_and_temp": clear_cache_and_temp,
        "clear_unused_thumbnails": clear_unused_thumbnails,
        "clear_addon_leftovers": clear_addon_leftovers,
        "clear_kodi_packages": clear_kodi_packages,
        "optimize_databases": optimize_databases,
        "all_in_one_panel": show_all_in_one_panel,
        "backup_and_restore": show_backup_dialog,
        "view_logs": view_logs,
        "show_support": show_support,
        "open_addon_settings": open_addon_settings,
    }
    action_handlers.get(action, show_menu)()


def _run_entrypoint():
    # Check for the "autorun" parameter from service.py (fallback)
    is_autorun = len(sys.argv) > 1 and sys.argv[1] == 'autorun'

    if is_autorun:
        xbmc.log("OptiKlean: Detected autorun parameter", xbmc.LOGINFO)
        run_automatic_maintenance()
    else:
        action = _parse_action_params().get("action")
        _run_requested_action(action)


# Handling of parameters to run the selected action
if __name__ == '__main__':
    _run_entrypoint()
