# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Simone Bianchelli
# OptiKlean - Kodi Cleaning and Optimization Addon

"""
Common utility functions shared across multiple modules.
This module provides reusable functions for file operations, logging, and system detection.
"""

import os
import time
import xbmc
import xbmcvfs
import xbmcaddon
from datetime import datetime

addon = xbmcaddon.Addon()
addon_id = addon.getAddonInfo('id')


def _translate_if_special(path):
    return xbmcvfs.translatePath(path) if path.startswith("special://") else path


def _get_path_size_bytes(local_path):
    if os.path.isfile(local_path):
        return os.path.getsize(local_path)
    if not os.path.isdir(local_path):
        return 0

    total_bytes = 0
    for root, _, files in os.walk(local_path):
        for file_name in files:
            try:
                total_bytes += os.path.getsize(os.path.join(root, file_name))
            except (OSError, IOError):
                continue
    return total_bytes


def _split_rotated_entries(current_content):
    entries = []
    parts = current_content.split(f'\n{addon.getLocalizedString(31009)}')
    for index, part in enumerate(parts):
        if index == 0 and part.strip():
            entries.append(part.strip())
        elif part.strip():
            entries.append(f"{addon.getLocalizedString(31009)}{part.strip()}")
    return entries


def get_kodi_version():
    """
    Get Kodi's major version number (e.g., 19, 20, 21, 22).
    Returns an integer or 0 on error.
    """
    try:
        version_string = xbmc.getInfoLabel("System.BuildVersion")
        major_version = int(version_string.split('.')[0])
        xbmc.log(f"OptiKlean: Detected Kodi major version: {major_version}", xbmc.LOGINFO)
        return major_version
    except Exception as e:
        xbmc.log(f"OptiKlean: Error getting Kodi version: {e}", xbmc.LOGWARNING)
        return 0


def get_file_size(file_path):
    """
    Get file size in bytes. Returns 0 if file doesn't exist.
    Uses xbmcvfs first, falls back to os.path.
    """
    try:
        if xbmcvfs.exists(file_path):
            file = xbmcvfs.File(file_path)
            size = file.size()
            file.close()
            return size
            
        # Fallback to os.path if xbmcvfs fails
        if os.path.exists(file_path):
            return os.path.getsize(file_path)

    except Exception as e:
        xbmc.log(f"OptiKlean: Error getting size for {file_path}: {str(e)}", xbmc.LOGERROR)
    return 0


def get_folder_size(folder_path):
    """
    Calculate total size of a folder in bytes (cross-platform).
    Uses xbmcvfs for compatibility, falls back to os.walk.
    """
    total_size = 0
    
    # Try with xbmcvfs first (works on all systems)
    try:
        dirs, files = xbmcvfs.listdir(folder_path)
        for file in files:
            file_path = xbmcvfs.makeLegalFilename(os.path.join(folder_path, file))
            file_size = get_file_size(file_path)
            total_size += file_size
        
        for dir_name in dirs:
            dir_path = xbmcvfs.makeLegalFilename(os.path.join(folder_path, dir_name))
            total_size += get_folder_size(dir_path)
            
    except Exception as e:
        xbmc.log(f"OptiKlean: Error calculating folder size with xbmcvfs: {str(e)}", xbmc.LOGERROR)
        # Fallback to os.walk if xbmcvfs fails
        try:
            for root, dirs, files in os.walk(folder_path):
                for f in files:
                    fp = os.path.join(root, f)
                    total_size += os.path.getsize(fp)
        except Exception as e:
            xbmc.log(f"OptiKlean: Error calculating folder size with os.walk: {str(e)}", xbmc.LOGERROR)
    
    return total_size


def get_size(path, unit='MB'):
    """
    Get directory/file size in specified unit using direct filesystem access.
    
    Args:
        path: Path to file or directory
        unit: 'KB' or 'MB' for kilobytes or megabytes
    
    Returns:
        Size in specified unit (float)
    """
    try:
        local_path = _translate_if_special(path)
        
        if not os.path.exists(local_path):
            return 0.0
        
        total_bytes = _get_path_size_bytes(local_path)
        divisor = 1024 if unit.upper() == 'KB' else (1024 * 1024)
        return round(total_bytes / divisor, 2)
        
    except Exception as e:
        xbmc.log(f"OptiKlean: Error calculating size for {path}: {e}", xbmc.LOGWARNING)
        return 0.0


def get_size_mb(path):
    """Compatibility wrapper for get_size in MB"""
    return get_size(path, 'MB')


def get_size_kb(path):
    """Compatibility wrapper for get_size in KB"""
    return get_size(path, 'KB')


def format_size(bytes_value):
    """
    Format bytes into a human-readable string (KB, MB, GB).
    
    Args:
        bytes_value: Size in bytes
    
    Returns:
        Formatted string (e.g., "1.50 MB")
    """
    if bytes_value >= 1024 * 1024 * 1024:
        return f"{bytes_value / (1024 * 1024 * 1024):.2f} GB"
    elif bytes_value >= 1024 * 1024:
        return f"{bytes_value / (1024 * 1024):.2f} MB"
    elif bytes_value >= 1024:
        return f"{bytes_value / 1024:.2f} KB"
    else:
        return f"{bytes_value} B"


def get_localized_datetime():
    """
    Get current datetime formatted according to Kodi's regional settings.
    Falls back to ISO format if regional formatting fails.
    
    Returns:
        Formatted datetime string
    """
    try:
        # Get Kodi's time format (12h vs 24h)
        time_format = xbmc.getRegion('time').replace('%H', 'HH').replace('%I', 'hh').replace('%M', 'mm')
        
        # Get date format based on region
        date_format = xbmc.getRegion('dateshort')
        
        # Convert to Python datetime format
        format_map = {
            'DD': '%d', 'MM': '%m', 'YYYY': '%Y',
            'hh': '%I', 'mm': '%M', 'ss': '%S', 'HH': '%H',
            'AP': '%p' if '%p' in xbmc.getRegion('time') else ''
        }
        
        for k, v in format_map.items():
            date_format = date_format.replace(k, v)
            time_format = time_format.replace(k, v)
        
        full_format = f"{date_format} {time_format}"
        return time.strftime(full_format)
    except Exception as e:
        # Fallback to safe ISO format if regional formatting fails
        xbmc.log(f"OptiKlean: Error with localized datetime, using fallback: {e}", xbmc.LOGWARNING)
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def write_log(log_files_dict, log_key, content, append=False):
    """
    Write content to the specified log file with automatic timestamp footer.
    
    Args:
        log_files_dict: Dictionary mapping log keys to file paths
        log_key: Key identifying which log file to write to
        content: Content to write to the log
        append: If True, append to existing content instead of overwriting
    """
    log_path = log_files_dict.get(log_key)
    if not log_path:
        xbmc.log(f"OptiKlean: Log key '{log_key}' not found", xbmc.LOGERROR)
        return
    
    mode = "a" if append else "w"
    
    try:
        with open(log_path, mode, encoding="utf-8") as f:
            f.write(content)
            if not content.endswith('\n'):
                f.write('\n')
            f.write(f"\n{addon.getLocalizedString(31009)} {get_localized_datetime()}\n")
    except Exception as e:
        xbmc.log(f"OptiKlean: Error writing log file {log_path}: {e}", xbmc.LOGERROR)


def write_log_with_rotation(log_files_dict, log_key, content, max_entries=8):
    """
    Write content to log file with rotation support (keeps only last N entries).
    Used primarily for restore logs.
    
    Args:
        log_files_dict: Dictionary mapping log keys to file paths
        log_key: Key identifying which log file to write to
        content: Content to write to the log
        max_entries: Maximum number of entries to keep (default: 8)
    """
    log_path = log_files_dict.get(log_key)
    if not log_path:
        xbmc.log(f"OptiKlean: Log key '{log_key}' not found", xbmc.LOGERROR)
        return
    
    # Ensure directory exists
    log_dir = os.path.dirname(log_path)
    if log_dir and not xbmcvfs.exists(log_dir):
        try:
            xbmcvfs.mkdirs(log_dir)
            xbmc.log(f"OptiKlean: Created log directory {log_dir}", xbmc.LOGINFO)
        except Exception as e:
            xbmc.log(f"OptiKlean: Failed to create log directory {log_dir}: {str(e)}", xbmc.LOGERROR)
            return
    
    entries = []

    if xbmcvfs.exists(log_path):
        try:
            with xbmcvfs.File(log_path, 'r') as f:
                entries = _split_rotated_entries(f.read())
        except Exception as e:
            xbmc.log(f"OptiKlean: Error reading existing log: {str(e)}", xbmc.LOGWARNING)
    
    # Add new entry
    new_entry = content.strip()
    if not new_entry.endswith('\n'):
        new_entry += '\n'
    new_entry += f"\n{addon.getLocalizedString(31009)} {get_localized_datetime()}\n"
    
    entries.append(new_entry)
    
    # Keep only last max_entries
    if len(entries) > max_entries:
        entries = entries[-max_entries:]
    
    # Write rotated content
    try:
        with xbmcvfs.File(log_path, 'w') as f:
            for i, entry in enumerate(entries):
                if i > 0:
                    f.write('\n' + '='*50 + '\n\n')
                f.write(entry)
        xbmc.log(f"OptiKlean: Log rotated, kept {len(entries)} entries", xbmc.LOGINFO)
    except Exception as e:
        xbmc.log(f"OptiKlean: Error writing rotated log: {str(e)}", xbmc.LOGERROR)


def get_thumbnail_age_threshold_days():
    """
    Returns the configured thumbnail age threshold in days.
    Falls back to 30 if the setting is missing or invalid.
    """
    try:
        threshold = int(addon.getSetting("thumbnail_age_threshold") or 30)
        return threshold if threshold >= 1 else 30
    except (ValueError, TypeError):
        return 30