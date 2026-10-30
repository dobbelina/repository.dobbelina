# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Simone Bianchelli
# OptiKlean - Kodi Cleaning and Optimization Addon

import os
import zipfile
import shutil
import json
import time
import stat
from urllib.parse import urlparse
from datetime import datetime

import xbmcvfs
import xbmcgui
import xbmc
import xbmcaddon

# Import common utilities
from . import common_utils

# Import platform in modo sicuro per Kodi
try:
    import platform
    PLATFORM_AVAILABLE = True
except ImportError:
    PLATFORM_AVAILABLE = False
    xbmc.log("OptiKlean: platform module not available, using fallback detection", xbmc.LOGINFO)


addon = xbmcaddon.Addon()
addon_id = addon.getAddonInfo('id')

addon_path = xbmcvfs.translatePath(addon.getAddonInfo("path"))
media_path = f"{addon_path}/resources/media/"
logo_path = f"{media_path}logo.png"

BACKUP_MARKER_FILE = ".optiklean_backup"
NETWORK_PROTOCOLS = frozenset({"smb", "nfs", "ftp", "sftp", "http", "https"})
DATABASE_SPECIAL_PATH = "special://profile/Database/"
HOME_ADDONS_SPECIAL_PATH = "special://home/addons/"
PROFILE_ADDON_DATA_SPECIAL_PATH = "special://profile/addon_data/"
PROFILE_SPECIAL_PATH = "special://profile/"
HOME_SPECIAL_PATH = "special://home/"
USERDATA_SPECIAL_PATH = "special://userdata/"
KEYMAPS_SPECIAL_PATH = "special://userdata/keymaps/"
ADDONS_ARCHIVE_PREFIX = "addons/"
GUI_SETTINGS_FILE = "guisettings.xml"
SOURCES_FILE = "sources.xml"
PROFILES_FILE = "profiles.xml"
ADVANCED_SETTINGS_FILE = "advancedsettings.xml"
PASSWORDS_FILE = "passwords.xml"
SKIN_PREFIX = "skin."
OPTIKLEAN_ADDON_DATA_PATH = f"{PROFILE_ADDON_DATA_SPECIAL_PATH}{addon_id}/"

# Default metadata for legacy backups that have no embedded metadata
_LEGACY_BACKUP_METADATA = {
    "optiklean_backup": True,
    "os_info": "Unknown",
    "architecture": {"arch": "Unknown", "variant": "Unknown", "display": "Unknown"},
    "native_addons": [],
}

def get_kodi_version():
    """Ottiene la versione principale di Kodi (es. 19, 20, 21)"""
    version = common_utils.get_kodi_version()
    return str(version) if version > 0 else "Unknown"
                
def is_flatpak_environment():
    """Rileva se Kodi è in esecuzione in un ambiente Flatpak"""
    flatpak_indicators = [
        os.path.exists('/.flatpak-info'),
        os.environ.get('FLATPAK_ID') is not None,
        os.environ.get('FLATPAK_DEST') is not None,
        '/app/' in os.environ.get('PATH', ''),
        os.path.exists('/var/run/host'),  # Flatpak mount point per host filesystem
        'flatpak' in os.environ.get('container', '').lower()
    ]
    return any(flatpak_indicators)

def is_sandboxed_environment():
    """Rileva se Kodi è in esecuzione in un ambiente sandboxed (Flatpak, Snap, etc.)"""
    sandbox_indicators = [
        is_flatpak_environment(),
        os.environ.get('SNAP') is not None,  # Snap package
        os.environ.get('APPIMAGE') is not None,  # AppImage
        '/snap/' in os.environ.get('PATH', ''),  # Snap in PATH
        os.path.exists('/snap'),  # Snap system
    ]
    return any(sandbox_indicators)

def get_current_os():
    """Rileva il sistema operativo corrente con rilevamento specifico per Android e altri OS"""
    
    # Priorità 1: Rilevamento specifico per Android (sempre, anche se platform è disponibile)
    try:
        # Controllo Android prima di tutto (platform.system() su Android ritorna "Linux" ma non è accurato)
        if os.path.exists('/system/build.prop') or os.path.exists('/android_root'):
            return 'Android'
        
        # Controllo Kodi-specifico per Android
        if xbmc.getCondVisibility("System.Platform.Android"):
            return 'Android'
            
    except (OSError, AttributeError):
        pass
    
    # Priorità 1.5: Controlli Kodi nativi specifici per piattaforma con validazione
    try:
        if xbmc.getCondVisibility("System.Platform.Darwin"):
            return 'macOS'
        elif xbmc.getCondVisibility("System.Platform.IOS"):
            return 'iOS'
        elif xbmc.getCondVisibility("System.Platform.Linux") or xbmc.getCondVisibility("System.Platform.Linux.RaspberryPi"):
            # Tutti i sistemi Linux-based sono trattati semplicemente come 'Linux'
            return 'Linux'
    except (AttributeError, OSError):
        pass
    
    # Priorità 2: Usa platform.system() per rilevamento accurato se disponibile
    if PLATFORM_AVAILABLE:
        detected_os = platform.system()
        
        # Mappa i valori di platform.system() a nomi consistenti
        if detected_os == 'Windows':
            return 'Windows'
        elif detected_os == 'Darwin':  # macOS/macOS X o iOS
            # Controllo per iOS: platform.system() ritorna 'Darwin' ma dobbiamo distinguere
            try:
                # Se è iOS dovrebbe essere stato già rilevato dalla Priorità 1.5
                # Ma facciamo un controllo aggiuntivo per sicurezza
                if hasattr(platform, 'ios_ver'):
                    # iOS ha platform.ios_ver() disponibile
                    return 'iOS'
            except (AttributeError, OSError):
                pass
            
            # Se non è iOS, è macOS - distingui tra versioni
            try:
                mac_version = platform.mac_ver()[0]
                if mac_version:
                    # macOS X era 10.0-10.15, macOS è 11+
                    major_version = int(mac_version.split('.')[0])
                    if major_version >= 11:
                        return 'macOS'
                    else:
                        return 'macOS X'
                else:
                    return 'macOS'
            except (ValueError, AttributeError, OSError):
                return 'macOS'
        elif detected_os == 'Linux':
            # Doppio controllo: platform dice Linux ma potrebbe essere Android non rilevato sopra
            try:
                if os.path.exists('/system/build.prop'):
                    return 'Android'
            except (OSError, IOError):
                pass
            
            # Tutti i sistemi Linux-based sono semplicemente 'Linux'
            return 'Linux'
        else:
            # Altri OS (FreeBSD, etc.) - ritorna quello che dice platform
            return detected_os
    
    # Priorità 3: Fallback detection basato su caratteristiche del filesystem
    else:
        if os.name == 'nt':
            return 'Windows'
        elif os.path.sep == '/':
            try:
                # Controllo per macOS/macOS X o iOS
                if os.path.exists('/System/Library') or os.path.exists('/Applications'):
                    # Controllo se è iOS (iPhone/iPad hanno struttura diversa)
                    if os.path.exists('/System/Library/PrivateFrameworks/MobileDevice.framework'):
                        return 'iOS'
                    
                    # Se non è iOS, è macOS - prova a determinare la versione
                    try:
                        import subprocess
                        version_output = subprocess.check_output(['sw_vers', '-productVersion'], stderr=subprocess.DEVNULL)
                        version = version_output.decode('utf-8').strip()
                        major_version = int(version.split('.')[0])
                        if major_version >= 11:
                            return 'macOS'
                        else:
                            return 'macOS X'
                    except (subprocess.CalledProcessError, ValueError, OSError, AttributeError):
                        return 'macOS'  # Fallback generico
                
                # Tutti i sistemi Unix-like senza /System/Library sono Linux
                else:
                    return 'Linux'
                    
            except OSError:
                # Se non riusciamo ad accedere al filesystem (es. permessi Flatpak restrittivi)
                # assumiamo Linux come fallback sicuro per sistemi Unix-like
                return 'Linux'
        else:
            return 'Unknown'

def get_system_architecture():
    """
    Rileva l'architettura del sistema e la variante OS specifica.
    Ritorna un dizionario con 'arch' (x86_64/ARM) e 'variant' (dettagli specifici)
    """
    
    # Rilevamento architettura base
    arch = 'Unknown'
    variant = 'Unknown'
    
    try:
        # Usa platform.machine() come fonte primaria
        if PLATFORM_AVAILABLE:
            machine = platform.machine().lower()
            
            # Mappatura architetture principali
            if machine in ('x86_64', 'amd64', 'x64'):
                arch = 'x86_64'
            elif machine in ('i386', 'i686', 'x86'):
                arch = 'x86'  # 32-bit x86
            elif machine in ('aarch64', 'arm64', 'arm64-v8a'):
                arch = 'ARM64'
            elif machine in ('armv8l', 'armv7l', 'armv7', 'armeabi-v7a', 'armv6l', 'arm'):
                arch = 'ARM32'
            elif 'aarch64' in machine or 'arm64' in machine:
                arch = 'ARM64'
            elif 'arm' in machine:
                arch = 'ARM32'
            else:
                # Fallback per architetture non standard
                arch = machine
        
        # Fallback usando os.uname() se disponibile
        if arch == 'Unknown':
            try:
                uname = os.uname()
                machine = uname.machine.lower()
                if machine in ('x86_64', 'amd64'):
                    arch = 'x86_64'
                elif machine in ('aarch64', 'arm64', 'arm64-v8a'):
                    arch = 'ARM64'
                elif machine in ('armv8l', 'armv7l', 'armv7', 'armeabi-v7a', 'armv6l', 'arm'):
                    arch = 'ARM32'
                elif 'aarch64' in machine or 'arm64' in machine:
                    arch = 'ARM64'
                elif 'arm' in machine:
                    arch = 'ARM32'
            except (AttributeError, OSError):
                pass
    
    except (AttributeError, OSError):
        pass
    
    # Rilevamento variante OS specifica per ARM (più critica per compatibilità)
    current_os = get_current_os()
    
    if arch in ('ARM32', 'ARM64'):
        # Per sistemi ARM, la variante è critica per compatibilità binari
        if current_os == 'Android':
            variant = 'Android'
        elif current_os == 'Linux':
            # Distingui le principali distribuzioni embedded ARM
            if os.path.exists('/etc/libreelec-release'):
                variant = 'LibreELEC'
            elif os.path.exists('/etc/coreelec-release'):
                variant = 'CoreELEC'  
            elif os.path.exists('/etc/osmc_release'):
                variant = 'OSMC'
            elif os.path.exists('/etc/openelec-release'):
                variant = 'OpenELEC'
            elif os.path.exists('/opt/vc/bin/vcgencmd'):  # Raspberry Pi specific
                variant = 'RaspberryPi'
            else:
                # Linux ARM generico (Ubuntu ARM, Debian ARM, ecc.)
                variant = 'Linux-ARM'
        elif current_os == 'iOS':
            variant = 'iOS'
        else:
            variant = f'{current_os}-ARM'
    
    elif arch == 'x86_64':
        # Per x86_64, la variante è meno critica ma utile per info
        if current_os == 'Windows':
            variant = 'Windows-x64'
        elif current_os == 'macOS':
            variant = 'macOS-x64'
        elif current_os == 'Linux':
            variant = 'Linux-x64'
        else:
            variant = f'{current_os}-x64'
    
    elif arch == 'x86':
        # x86 32-bit (sempre meno comune)
        variant = f'{current_os}-x86'
    
    else:
        # Architettura sconosciuta o non standard
        variant = f'{current_os}-{arch}' if arch != 'Unknown' else current_os
    
    return {
        'arch': arch,
        'variant': variant,
        'display': f'{arch} ({variant})' if variant != 'Unknown' else arch
    }

def check_arm_compatibility(backup_arch, backup_variant, current_arch, current_variant, has_native_addons):
    # Controlla la compatibilità specifica per sistemi ARM secondo le regole
    
    # Se non sono entrambi ARM, non si applica questa logica
    if backup_arch not in ('ARM32', 'ARM64') or current_arch not in ('ARM32', 'ARM64'):
        return None
    
    # Architetture ARM diverse sono sempre incompatibili
    if backup_arch != current_arch:
        return {
            "compatible": False,
            "reason": f"ARM architecture mismatch: {backup_arch} → {current_arch}",
            "category": "architecture_mismatch"
        }
    
    # Stessa architettura ARM - controlla varianti specifiche
    
    # Ecosistemi embedded completamente isolati
    embedded_variants = {'LibreELEC', 'CoreELEC', 'OSMC', 'OpenELEC'}
    
    if backup_variant in embedded_variants or current_variant in embedded_variants:
        if backup_variant == current_variant:
            return {"compatible": True, "reason": f"Same embedded OS: {backup_variant}"}
        else:
            # Embedded OS diversi o embedded vs standard sono incompatibili con addon nativi
            if has_native_addons:
                return {
                    "compatible": False,
                    "reason": f"Embedded OS incompatibility with native addons: {backup_variant} → {current_variant}",
                    "category": "embedded_mismatch"
                }
            else:
                # Senza addon nativi, warning ma possibile
                return {
                    "compatible": True,
                    "reason": f"Embedded OS different but no native addons: {backup_variant} → {current_variant}",
                    "category": "embedded_warning"
                }
    
    # Android è isolato da tutto tranne se stesso
    if backup_variant == 'Android' or current_variant == 'Android':
        if backup_variant == current_variant:
            return {"compatible": True, "reason": "Same Android system"}
        else:
            # Android vs qualsiasi altro è incompatibile con addon nativi
            if has_native_addons:
                return {
                    "compatible": False, 
                    "reason": f"Android incompatibility with native addons: {backup_variant} → {current_variant}",
                    "category": "android_mismatch"
                }
            else:
                return {
                    "compatible": True,
                    "reason": f"Android cross-platform but no native addons: {backup_variant} → {current_variant}",
                    "category": "android_warning"
                }
    
    # Linux ARM generico (RaspberryPi, Linux-ARM) 
    linux_arm_variants = {'RaspberryPi', 'Linux-ARM'}
    
    if backup_variant in linux_arm_variants and current_variant in linux_arm_variants:
        # ARM32: Raspberry Pi OS compatibile solo entro Linux ARM32
        # ARM64: Raspberry Pi OS 64bit/Linux ARM64 compatibili entro Linux ARM64
        return {
            "compatible": True, 
            "reason": f"Linux ARM compatibility: {backup_variant} → {current_variant} on {current_arch}"
        }
    
    # iOS è isolato (solo per completezza, raramente usato)
    if backup_variant == 'iOS' or current_variant == 'iOS':
        if backup_variant == current_variant:
            return {"compatible": True, "reason": "Same iOS system"}
        else:
            return {
                "compatible": False,
                "reason": f"iOS incompatibility: {backup_variant} → {current_variant}",
                "category": "ios_mismatch"
            }
    
    # Fallback: varianti non riconosciute - assumiamo incompatibili se diverse
    if backup_variant != current_variant and has_native_addons:
        return {
            "compatible": False,
            "reason": f"Unknown ARM variants with native addons: {backup_variant} → {current_variant}",
            "category": "unknown_variants"
        }
    
    # Stesse varianti o nessun addon nativo - compatibili
    return {"compatible": True, "reason": f"ARM compatibility check passed: {backup_variant} → {backup_variant}"}

def _xbmcvfs_recursive_delete(path):
    """Recursively delete a path using xbmcvfs (used as fallback when os.path is blind to it)."""
    try:
        dirs, files = xbmcvfs.listdir(path)
        for file in files:
            xbmcvfs.delete(safe_path_join(path, file))
        for dir_name in dirs:
            _xbmcvfs_recursive_delete(safe_path_join(path, dir_name))
        xbmcvfs.rmdir(path)
    except OSError as e:
        xbmc.log(f"OptiKlean: Error in recursive delete: {str(e)}", xbmc.LOGWARNING)

def _cleanup_temp_restore(addon_data_path):
    # Pulizia temp_restore
    temp_extract_path = safe_path_join(addon_data_path, "temp_restore")

    os_exists = os.path.exists(temp_extract_path)
    xbmcvfs_exists = xbmcvfs.exists(temp_extract_path)

    if not os_exists and not xbmcvfs_exists:
        xbmc.log(f"OptiKlean: temp_restore directory does not exist (both checks returned False): {temp_extract_path}", xbmc.LOGINFO)
        return

    if os_exists:
        try:
            xbmc.log(f"OptiKlean: Starting cleanup of temp_restore directory: {temp_extract_path}", xbmc.LOGINFO)
            shutil.rmtree(temp_extract_path)
            xbmc.log("OptiKlean: Successfully cleaned temp_restore using shutil", xbmc.LOGINFO)
        except OSError as e:
            xbmc.log(f"OptiKlean: Error cleaning temp_restore: {str(e)}", xbmc.LOGWARNING)
    else:
        # Fallback: os.path is blind but xbmcvfs sees it
        try:
            xbmc.log(f"OptiKlean: Attempting cleanup with xbmcvfs fallback: {temp_extract_path}", xbmc.LOGINFO)
            _xbmcvfs_recursive_delete(temp_extract_path)
            xbmc.log("OptiKlean: Successfully cleaned temp_restore using xbmcvfs fallback method", xbmc.LOGINFO)
        except OSError as e:
            xbmc.log(f"OptiKlean: Error cleaning temp_restore with xbmcvfs fallback: {str(e)}", xbmc.LOGWARNING)

def is_network_path(path):
    """Check if path is a network/remote path."""
    if not path or not isinstance(path, str):
        return False
    try:
        parsed = urlparse(path.strip())
    except ValueError:
        return False
    if parsed.scheme.lower() not in NETWORK_PROTOCOLS:
        return False
    # Reject embedded credentials to avoid accidental credential exposure
    if parsed.username or parsed.password:
        return False
    return bool(parsed.netloc)

def verify_backup_path_availability(backup_path):
    """
    Verifica se il percorso di backup è disponibile e accessibile.
    Ritorna (success: bool, error_message: str)
    """
    if not backup_path or not backup_path.strip():
        return False, addon.getLocalizedString(30910)
    
    try:
        # Per percorsi di rete, prova a verificare l'accessibilità
        if is_network_path(backup_path):
            xbmc.log(f"OptiKlean: Verifying network backup path: {backup_path}", xbmc.LOGINFO)
            
            # Prova a verificare se la directory esiste o può essere creata
            if xbmcvfs.exists(backup_path):
                xbmc.log(f"OptiKlean: Network path exists: {backup_path}", xbmc.LOGINFO)
                return True, ""
            else:
                # Prova a creare la directory per testare l'accesso
                xbmc.log(f"OptiKlean: Attempting to create network directory: {backup_path}", xbmc.LOGINFO)
                if xbmcvfs.mkdirs(backup_path):
                    xbmc.log(f"OptiKlean: Successfully created network directory: {backup_path}", xbmc.LOGINFO)
                    return True, ""
                else:
                    xbmc.log(f"OptiKlean: Failed to create network directory: {backup_path}", xbmc.LOGWARNING)
                    return False, f"{addon.getLocalizedString(30911)}: {backup_path}"
        else:
            # Per percorsi locali, usa controlli più specifici
            local_path = xbmcvfs.translatePath(backup_path) if backup_path.startswith("special://") else backup_path
            
            # Controllo specifico per unità Windows (lettera di unità)
            if len(local_path) >= 2 and local_path[1] == ':':
                drive_letter = local_path[0].upper()
                
                # Su Windows, controlla se l'unità esiste usando rilevamento unificato
                current_os = get_current_os()
                if current_os == 'Windows':
                    import ctypes
                    try:
                        # GetLogicalDrives ritorna un bitmask delle unità disponibili
                        drives_bitmask = ctypes.windll.kernel32.GetLogicalDrives()
                        drive_index = ord(drive_letter) - ord('A')
                        drive_available = bool(drives_bitmask & (1 << drive_index))
                        
                        if not drive_available:
                            return False, f"{addon.getLocalizedString(30912)}: {drive_letter}:"
                    except Exception as e:
                        xbmc.log(f"OptiKlean: Could not check drive availability: {e}", xbmc.LOGWARNING)
            
            # Controllo standard esistenza percorso
            if os.path.exists(local_path):
                return True, ""
            else:
                # Prova a creare la directory per distinguere tra errori diversi
                try:
                    os.makedirs(local_path, exist_ok=True)
                    return True, ""
                except OSError as e:
                    # Analizza il tipo di errore per messaggi più specifici
                    if e.errno == 3:  # ERROR_PATH_NOT_FOUND
                        if len(local_path) >= 2 and local_path[1] == ':':
                            drive = local_path[0].upper()
                            return False, f"{addon.getLocalizedString(30913)}: {drive}:"
                        else:
                            return False, f"{addon.getLocalizedString(30914)}: {local_path}"
                    elif e.errno == 2:  # ERROR_FILE_NOT_FOUND
                        return False, f"{addon.getLocalizedString(30915)}: {local_path}"
                    else:
                        return False, f"{addon.getLocalizedString(30916)}: {str(e)}"
                except Exception as e:
                    return False, f"{addon.getLocalizedString(30917)}: {str(e)}"
                    
    except Exception as e:
        xbmc.log(f"OptiKlean: Error verifying backup path {backup_path}: {e}", xbmc.LOGERROR)
        return False, f"{addon.getLocalizedString(30918)}: {str(e)}"

def safe_path_join(*paths):
    """Cross-platform path joining using xbmcvfs methods"""
    if not paths:
        return ""
    
    result = str(paths[0])
    for path in paths[1:]:
        if result.endswith('/') or result.endswith('\\'):
            result = result.rstrip('/\\')
        if str(path).startswith('/') or str(path).startswith('\\'):
            path = str(path).lstrip('/\\')
        result = result + '/' + str(path)
    
    return result

def safe_file_size(path):
    """Get file size using xbmcvfs for network compatibility"""
    return common_utils.get_file_size(path)

def safe_copy_file(source, dest):
    """Copy file using xbmcvfs for network compatibility with detailed error logging"""
    try:
        # Log the operation for debugging
        xbmc.log(f"OptiKlean: Attempting to copy from {source} to {dest}", xbmc.LOGDEBUG)
        
        source = source.replace('\\', '/')
        dest = dest.replace('\\', '/')
        
        # Verifica che il file sorgente esista
        source_exists = False
        if source.startswith('/') or (len(source) > 1 and source[1] == ':'):
            # Percorso assoluto locale - usa os.path.exists
            source_local = source.replace('/', os.sep)
            source_exists = os.path.exists(source_local)
        else:
            # Percorso xbmcvfs - usa xbmcvfs.exists
            source_exists = xbmcvfs.exists(source)
        
        if not source_exists:
            xbmc.log(f"OptiKlean: Source file does not exist: {source}", xbmc.LOGWARNING)
            return False
        
        # Ensure destination directory exists
        dest_dir = '/'.join(dest.split('/')[:-1])
        if dest_dir and not xbmcvfs.exists(dest_dir):
            try:
                dest_dir_local = dest_dir.replace('/', os.sep)
                os.makedirs(dest_dir_local, exist_ok=True)
                xbmc.log(f"OptiKlean: Created directory using os.makedirs: {dest_dir_local}", xbmc.LOGDEBUG)
            except Exception as os_error:
                # Fallback a xbmcvfs.mkdirs
                xbmc.log(f"OptiKlean: os.makedirs failed, trying xbmcvfs: {os_error}", xbmc.LOGDEBUG)
                if not xbmcvfs.mkdirs(dest_dir):
                    xbmc.log(f"OptiKlean: Failed to create destination directory: {dest_dir}", xbmc.LOGWARNING)
                    return False
        
        # Gestione permessi file esistente
        dest_local = dest.replace('/', os.sep)
        if os.path.exists(dest_local):
            try:
                # Rimuovi attributo sola lettura su Windows
                current_os = get_current_os()
                if current_os == 'Windows':
                    # Ottieni permessi attuali
                    current_permissions = os.stat(dest_local).st_mode
                    
                    # Se il file è sola lettura, rimuovi il flag
                    if not (current_permissions & stat.S_IWRITE):
                        xbmc.log(f"OptiKlean: Removing read-only flag from {dest_local}", xbmc.LOGDEBUG)
                        # Aggiungi permesso scrittura (mantiene altri permessi)
                        os.chmod(dest_local, current_permissions | stat.S_IWRITE)
                else:
                    # Linux/Unix: assicura permessi scrittura (user)
                    current_permissions = os.stat(dest_local).st_mode
                    os.chmod(dest_local, current_permissions | stat.S_IWUSR)
                    
            except Exception as perm_error:
                xbmc.log(f"OptiKlean: Warning - could not modify permissions for {dest_local}: {perm_error}", xbmc.LOGWARNING)
                # Non interrompiamo - proviamo comunque la copia
        
        # Attempt the copy operation
        copy_result = xbmcvfs.copy(source, dest)
        if copy_result:
            # Verifica che la copia sia andata a buon fine
            if xbmcvfs.exists(dest):
                xbmc.log(f"OptiKlean: Successfully copied {source} to {dest}", xbmc.LOGDEBUG)
                return True
            else:
                xbmc.log(f"OptiKlean: Copy reported success but destination file not found: {dest}", xbmc.LOGWARNING)
                return False
        else:
            xbmc.log(f"OptiKlean: xbmcvfs.copy returned False for {source} to {dest}", xbmc.LOGWARNING)
            return False
            
    except Exception as e:
        xbmc.log(f"OptiKlean: Exception copying file {source} to {dest}: {e}", xbmc.LOGWARNING)
        return False

def remove_readonly_recursive(path):
    """
    Rimuove ricorsivamente l'attributo sola lettura da directory e file.
    Utile per Windows dove addon folders hanno spesso questo flag.
    """
    try:
        current_os = get_current_os()
        
        if current_os != 'Windows':
            # Su Linux/Unix, assicura solo permessi scrittura base
            try:
                os.chmod(path, os.stat(path).st_mode | stat.S_IWUSR)
            except Exception:
                pass
            return True
        
        # Windows: rimuovi attributo sola lettura ricorsivamente
        
        def remove_readonly_windows(root_path):
            """Rimuove ricorsivamente attributo sola lettura su Windows"""
            try:
                for root, dirs, files in os.walk(root_path, topdown=False):
                    # Processa file
                    for name in files:
                        file_path = os.path.join(root, name)
                        try:
                            file_stat = os.stat(file_path)
                            if not (file_stat.st_mode & stat.S_IWRITE):
                                # File sola lettura - aggiungi permesso scrittura
                                os.chmod(file_path, file_stat.st_mode | stat.S_IWRITE)
                        except Exception as e:
                            xbmc.log(f"OptiKlean: Could not modify file {file_path}: {e}", xbmc.LOGDEBUG)
                    
                    # Processa directory
                    for name in dirs:
                        dir_path = os.path.join(root, name)
                        try:
                            dir_stat = os.stat(dir_path)
                            if not (dir_stat.st_mode & stat.S_IWRITE):
                                # Directory sola lettura - aggiungi permesso scrittura
                                os.chmod(dir_path, dir_stat.st_mode | stat.S_IWRITE)
                        except Exception as e:
                            xbmc.log(f"OptiKlean: Could not modify directory {dir_path}: {e}", xbmc.LOGDEBUG)
                
                # Infine, processa la directory root stessa
                try:
                    root_stat = os.stat(root_path)
                    if not (root_stat.st_mode & stat.S_IWRITE):
                        os.chmod(root_path, root_stat.st_mode | stat.S_IWRITE)
                except Exception as e:
                    xbmc.log(f"OptiKlean: Could not modify root {root_path}: {e}", xbmc.LOGDEBUG)
                    
            except Exception as e:
                xbmc.log(f"OptiKlean: Error in recursive readonly removal: {e}", xbmc.LOGWARNING)
                return False
            
            return True
        
        return remove_readonly_windows(path)
        
    except Exception as e:
        xbmc.log(f"OptiKlean: Error removing readonly attribute: {e}", xbmc.LOGWARNING)
        return False

def get_backup_metadata(zip_path):
    """Estrae i metadati dal file di backup per controllo compatibilità"""
    try:
        if is_network_path(zip_path):
            # Per percorsi di rete, copia temporaneamente
            temp_dir = xbmcvfs.translatePath("special://temp/")
            temp_file = safe_path_join(temp_dir, "temp_metadata_check.zip")
            if xbmcvfs.copy(zip_path, temp_file):
                try:
                    with zipfile.ZipFile(xbmcvfs.translatePath(temp_file), 'r') as zipf:
                        if BACKUP_MARKER_FILE in zipf.namelist():
                            marker_content = zipf.read(BACKUP_MARKER_FILE).decode('utf-8')
                            try:
                                return json.loads(marker_content)
                            except json.JSONDecodeError:
                                # Backup legacy - solo stringa semplice
                                return dict(_LEGACY_BACKUP_METADATA)
                finally:
                    xbmcvfs.delete(temp_file)
        else:
            # Percorso locale
            with zipfile.ZipFile(xbmcvfs.translatePath(zip_path), 'r') as zipf:
                if BACKUP_MARKER_FILE in zipf.namelist():
                    marker_content = zipf.read(BACKUP_MARKER_FILE).decode('utf-8')
                    try:
                        return json.loads(marker_content)
                    except json.JSONDecodeError:
                        # Backup legacy - solo stringa semplice
                        return dict(_LEGACY_BACKUP_METADATA)
    except Exception as e:
        xbmc.log(f"OptiKlean: Error reading backup metadata: {e}", xbmc.LOGWARNING)
    
    return None

def check_cross_platform_compatibility(backup_metadata):
    """
    Controlla compatibilità del backup basata su architettura e OS.
    Priorità: architettura CPU > variante OS > addon nativi
    """
    if not backup_metadata:
        return {"status": "unknown", "reason": "No metadata available"}
    
    # Informazioni backup
    backup_os = backup_metadata.get("os_info", "Unknown")
    backup_arch_info = backup_metadata.get("architecture", {"arch": "Unknown", "variant": "Unknown", "display": "Unknown"})
    backup_arch = backup_arch_info.get("arch", "Unknown")
    backup_variant = backup_arch_info.get("variant", "Unknown")
    native_addons = backup_metadata.get("native_addons", [])
    
    # Informazioni sistema corrente
    current_os = get_current_os()
    current_arch_info = get_system_architecture()
    current_arch = current_arch_info.get("arch", "Unknown")
    current_variant = current_arch_info.get("variant", "Unknown")

    # Se ci sono addon nativi e l'architettura non è determinabile, tratta come rischio alto.
    if len(native_addons) > 0 and (backup_arch == "Unknown" or current_arch == "Unknown"):
        return {
            "status": "incompatible_variant_native",
            "reason": "Native addons present but architecture could not be determined safely",
            "backup_info": f"{backup_arch} ({backup_variant})",
            "current_info": f"{current_arch} ({current_variant})",
            "native_addons": native_addons,
            "arm_category": "unknown_architecture"
        }
    
    # 1. CONTROLLO ARCHITETTURA (livello critico)
    if backup_arch != "Unknown" and current_arch != "Unknown":
        if backup_arch != current_arch:
            return {
                "status": "incompatible_architecture",
                "reason": f"Architecture mismatch: backup is {backup_arch}, current system is {current_arch}",
                "backup_info": f"{backup_arch} ({backup_variant})",
                "current_info": f"{current_arch} ({current_variant})"
            }
    
    # 2. CONTROLLO COMPATIBILITÀ ARM SPECIFICA (regole dettagliate)
    if backup_arch in ("ARM32", "ARM64") or current_arch in ("ARM32", "ARM64"):
        arm_compatibility = check_arm_compatibility(
            backup_arch, backup_variant, 
            current_arch, current_variant, 
            len(native_addons) > 0
        )
        
        if arm_compatibility and not arm_compatibility["compatible"]:
            category = arm_compatibility.get("category", "arm_incompatible")
            
            if category in ("architecture_mismatch", "embedded_mismatch", "android_mismatch", "ios_mismatch", "unknown_variants"):
                return {
                    "status": "incompatible_variant_native",
                    "reason": arm_compatibility["reason"],
                    "backup_info": f"{backup_arch} ({backup_variant})",
                    "current_info": f"{current_arch} ({current_variant})",
                    "native_addons": native_addons,
                    "arm_category": category
                }
        elif arm_compatibility and arm_compatibility.get("category") in ("embedded_warning", "android_warning"):
            # Warning per embedded/android ma senza addon nativi - continua con controlli standard
            pass
    
    # 3. CONTROLLO OS TRADIZIONALE (livello secondario)
    if backup_os != "Unknown" and current_os != "Unknown":
        if backup_os == current_os and backup_variant == current_variant:
            return {"status": "compatible", "reason": "Same OS and architecture"}
        elif backup_os != current_os or backup_variant != current_variant:
            if len(native_addons) > 0:
                return {
                    "status": "cross_platform_native",
                    "reason": f"Cross-platform restore with native addons: {backup_variant} → {current_variant}",
                    "backup_info": f"{backup_arch} ({backup_variant})",
                    "current_info": f"{current_arch} ({current_variant})",
                    "native_addons": native_addons
                }
            else:
                return {
                    "status": "cross_platform_safe",
                    "reason": f"Cross-platform restore, no native addons: {backup_variant} → {current_variant}",
                    "backup_info": f"{backup_arch} ({backup_variant})",
                    "current_info": f"{current_arch} ({current_variant})"
                }
    
    # 4. FALLBACK per backup legacy o informazioni incomplete
    if backup_os == "Unknown" or current_os == "Unknown":
        return {"status": "unknown", "reason": "Insufficient information for compatibility check"}
    
    # Default: assumiamo compatibile se arriviamo qui
    return {"status": "compatible", "reason": "No compatibility issues detected"}

def is_valid_optiklean_backup(zip_path):
    try:
        # Handle both local and network paths
        if is_network_path(zip_path):
            # For network paths, copy to temp location first
            temp_dir = xbmcvfs.translatePath("special://temp/")
            temp_file = safe_path_join(temp_dir, "temp_backup_check.zip")
            if xbmcvfs.copy(zip_path, temp_file):
                try:
                    with zipfile.ZipFile(xbmcvfs.translatePath(temp_file), 'r') as zipf:
                        result = BACKUP_MARKER_FILE in zipf.namelist()
                    xbmcvfs.delete(temp_file)
                    return result
                except (zipfile.BadZipFile, zipfile.LargeZipFile, OSError, IOError) as e:
                    xbmc.log(f"OptiKlean: Error reading temp backup file: {e}", xbmc.LOGWARNING)
                    xbmcvfs.delete(temp_file)
                    return False
            return False
        else:
            # Local path - use standard method
            with zipfile.ZipFile(xbmcvfs.translatePath(zip_path), 'r') as zipf:
                return BACKUP_MARKER_FILE in zipf.namelist()
    except (zipfile.BadZipFile, zipfile.LargeZipFile, OSError, IOError) as e:
        xbmc.log(f"OptiKlean: Error validating backup file {zip_path}: {e}", xbmc.LOGWARNING)
        return False

def write_log_local(log_key, content, append=False):
    """Write content to log file with timestamp and rotation for restore logs"""
    log_files = get_log_files()
    
    # Special handling for restore backup log with rotation
    if log_key == "restore_backup":
        common_utils.write_log_with_rotation(log_files, log_key, content, max_entries=8)
    else:
        # Normal log handling
        common_utils.write_log(log_files, log_key, content, append)

def get_log_files():
    """Get log file paths"""
    addon_data_folder = xbmcvfs.translatePath(f"special://profile/addon_data/{addon_id}/")

    if not xbmcvfs.exists(addon_data_folder):
        xbmcvfs.mkdirs(addon_data_folder)

    return {
        "backup_full": safe_path_join(addon_data_folder, "backup_full.log"),
        "backup_addons": safe_path_join(addon_data_folder, "backup_addons.log"),
        "backup_addon_data": safe_path_join(addon_data_folder, "backup_addon_data.log"),
        "backup_addons_and_data": safe_path_join(addon_data_folder, "backup_addons_and_data.log"),
        "backup_databases": safe_path_join(addon_data_folder, "backup_databases.log"),
        "backup_sources": safe_path_join(addon_data_folder, "backup_sources.log"),
        "backup_gui_settings": safe_path_join(addon_data_folder, "backup_gui_settings.log"),
        "backup_profiles": safe_path_join(addon_data_folder, "backup_profiles.log"),
        "backup_advanced_settings": safe_path_join(addon_data_folder, "backup_advanced_settings.log"),
        "backup_skins": safe_path_join(addon_data_folder, "backup_skins.log"),
        "backup_keymaps": safe_path_join(addon_data_folder, "backup_keymaps.log"),
        "backup_playlists": safe_path_join(addon_data_folder, "backup_playlists.log"),
        "backup_passwords": safe_path_join(addon_data_folder, "backup_passwords.log"),
        "restore_backup": safe_path_join(addon_data_folder, "restore_backup.log")
    }

def get_size(path, unit='MB'):
    """Get directory size in specified unit using direct filesystem access for local Kodi paths"""
    return common_utils.get_size(path, unit)

def get_size_mb(path):
    """Compatibility wrapper for get_size in MB"""
    return common_utils.get_size_mb(path)

def get_size_kb(path):
    """Compatibility wrapper for get_size in KB"""
    return common_utils.get_size_kb(path)

def get_free_space_mb(path):
    """Get available free space in MB (returns None for network paths)"""
    try:
        # Check if it's a network path
        if is_network_path(path):
            xbmc.log(f"OptiKlean: Cannot determine free space for network path: {path}", xbmc.LOGINFO)
            return None
        
        # Convert to local path
        local_path = xbmcvfs.translatePath(path)
        
        # Use platform-specific methods based on unified OS detection
        current_os = get_current_os()
        if current_os == 'Windows':
            # Windows method using ctypes - more reliable
            import ctypes
            free_bytes = ctypes.c_ulonglong(0)
            ret = ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                ctypes.c_wchar_p(local_path),
                None,
                None,
                ctypes.byref(free_bytes)
            )
            if ret == 0:
                raise ctypes.WinError()
            return round(free_bytes.value / (1024 * 1024), 2)
        else:
            # Unix/Linux/macOS/iOS method using os.statvfs
            stat = os.statvfs(local_path)
            free_bytes = stat.f_bavail * stat.f_frsize
            return round(free_bytes / (1024 * 1024), 2)
            
    except Exception as e:
        xbmc.log(f"OptiKlean: Failed to get free space for {path}: {e}", xbmc.LOGWARNING)
        return None

def get_backup_size_estimate_details(backup_items):
    """Get backup size estimate with detailed format info"""
    total_bytes = 0
    
    # Compression ratios by file type
    COMPRESSION_RATIOS = {
        'text': 0.2,      # XML, JSON, etc.
        'binary': 0.65,   # Databases, binaries
        'image': 0.9,     # JPG/PNG (already compressed)
        'media': 0.95,    # Videos/music
        'other': 0.7      # Default
    }

    def get_file_type(filepath):
        ext = os.path.splitext(filepath)[1].lower()
        if ext in ('.xml', '.json', '.txt', '.log', '.ini', '.py'):
            return 'text'
        elif ext in ('.db', '.sqlite', '.dat', '.bin'):
            return 'binary'
        elif ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp'):
            return 'image'
        elif ext in ('.mp3', '.mp4', '.mkv', '.avi'):
            return 'media'
        return 'other'

    for source_path, _ in backup_items:
        if not os.path.exists(source_path):
            continue
            
        if os.path.isfile(source_path):
            # Single file
            file_type = get_file_type(source_path)
            file_size = os.path.getsize(source_path)
            total_bytes += file_size * COMPRESSION_RATIOS[file_type]
            
        else:
            # Directory - recursive scan
            for root, dirs, files in os.walk(source_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        file_type = get_file_type(file_path)
                        file_size = os.path.getsize(file_path)
                        total_bytes += file_size * COMPRESSION_RATIOS[file_type]
                    except OSError:
                        continue
    
    # Add 10% buffer
    estimated_bytes = total_bytes * 1.1
    
    # Calculate MB for compatibility (used in space checks)
    estimated_mb = estimated_bytes / (1024 * 1024)
    
    # Return in the most appropriate unit for display
    if estimated_bytes < 1024 * 1024:  # Less than 1MB, display in KB
        display_value = round(estimated_bytes / 1024, 1)
        display_unit = addon.getLocalizedString(31013)
        formatted = f"{display_value} {display_unit}"
    else:
        display_value = round(estimated_mb, 2)
        display_unit = addon.getLocalizedString(31014)
        formatted = f"{display_value} {display_unit}"
    
    return {
        'display_value': display_value,
        'display_unit': display_unit,
        'formatted': formatted,
        'mb_equivalent': round(estimated_mb, 2)  # Always in MB for space calculations
    }

def calculate_backup_size_estimate(backup_items):
    """Legacy compatibility function - returns MB for existing code"""
    details = get_backup_size_estimate_details(backup_items)
    return details['mb_equivalent']

def is_native_addon(addon_id):
    """Identifica se un addon contiene librerie native platform-specific"""
    native_addon_prefixes = [
        "inputstream.",      # InputStream addons (Adaptive, FFmpegDirect, RTMP, etc.)
        "pvr.",             # PVR addons (IPTV Simple, etc.)
        "audiodecoder.",    # Audio decoders
        "audioencoder.",    # Audio encoders
        "imagedecoder.",    # Image decoders
        "peripheral.",      # Peripheral addons (joystick, etc.)
        "vfs.",             # Virtual filesystem
    ]

    if any(addon_id.startswith(prefix) for prefix in native_addon_prefixes):
        return True

    # Fallback robusto: scansione reale dei binari nell'addon.
    try:
        addon_local_path = xbmcvfs.translatePath(f"special://home/addons/{addon_id}")
        if not os.path.exists(addon_local_path):
            return False

        native_ext = ('.so', '.pyd', '.dll', '.dylib', '.jnilib')
        for root, _, files in os.walk(addon_local_path):
            for filename in files:
                if filename.lower().endswith(native_ext):
                    xbmc.log(f"OptiKlean: Native binary detected for addon {addon_id}: {filename}", xbmc.LOGDEBUG)
                    return True
    except Exception as e:
        xbmc.log(f"OptiKlean: Native addon scan failed for {addon_id}: {str(e)}", xbmc.LOGDEBUG)

    return False

def install_native_addons_from_repo(addon_ids, progress_callback=None):
    """
    Installa addon nativi dal repository Kodi ufficiale.
    Funziona cross-platform su tutti i sistemi (Android, Windows, Linux, macOS).
    
    Args:
        addon_ids: Lista di ID addon da installare (es. ["inputstream.adaptive", "pvr.iptvsimple"])
        progress_callback: Funzione opzionale per aggiornare il progresso (percent, message)
    
    Returns:
        dict con:
        - 'success': lista addon installati con successo
        - 'failed': lista tuple (addon_id, reason) per addon falliti
        - 'already_installed': lista addon già presenti
        - 'not_in_repo': lista addon non trovati nel repository
    """
    results = {
        'success': [],
        'failed': [],  # Ora contiene tuple (addon_id, reason)
        'already_installed': [],
        'not_in_repo': []
    }
    
    if not addon_ids:
        return results
    
    total = len(addon_ids)
    
    for i, addon_id in enumerate(addon_ids):
        try:
            if progress_callback:
                progress_callback(
                    int((i / total) * 100),
                    addon.getLocalizedString(31243).format(addon_id=addon_id)  # "Installing {addon_id}..."
                )
            
            # Verifica se l'addon è già installato
            if xbmc.getCondVisibility(f'System.HasAddon({addon_id})'):
                xbmc.log(f"OptiKlean: Addon {addon_id} already installed, skipping", xbmc.LOGINFO)
                results['already_installed'].append(addon_id)
                continue
            
            # Verifica se l'addon è disponibile nei repository configurati
            addon_info_request = json.dumps({
                "jsonrpc": "2.0",
                "method": "Addons.GetAddonDetails",
                "params": {"addonid": addon_id},
                "id": 1
            })
            addon_info_response = json.loads(xbmc.executeJSONRPC(addon_info_request))
            
            # Se l'addon non è nel database locale, potrebbe non essere disponibile
            # Proviamo comunque l'installazione ma tracciamo il caso
            addon_might_not_exist = 'error' in addon_info_response
            
            # Usa InstallAddon builtin - metodo cross-platform ufficiale Kodi
            xbmc.log(f"OptiKlean: Installing native addon from repo: {addon_id}", xbmc.LOGINFO)
            xbmc.executebuiltin(f"InstallAddon({addon_id})")
            
            # Attendi che l'installazione inizi/completi
            # Timeout adattivo: 45 secondi per addon complessi, 30 per altri
            complex_addons = ['inputstream.adaptive', 'inputstream.ffmpegdirect', 'pvr.']
            is_complex = any(addon_id.startswith(prefix) or addon_id == prefix for prefix in complex_addons)
            timeout = 45000 if is_complex else 30000  # millisecondi
            check_interval = 500  # Controlla ogni 500ms
            elapsed = 0
            install_detected = False
            user_cancelled = False
            
            while elapsed < timeout:
                xbmc.sleep(check_interval)
                elapsed += check_interval
                
                # Verifica se l'addon è ora installato
                if xbmc.getCondVisibility(f'System.HasAddon({addon_id})'):
                    xbmc.log(f"OptiKlean: Successfully installed {addon_id} in {elapsed/1000:.1f}s", xbmc.LOGINFO)
                    results['success'].append(addon_id)
                    install_detected = True
                    break
                
                # Aggiorna progresso durante l'attesa e verifica cancellazione
                if progress_callback and elapsed % 2000 == 0:  # Ogni 2 secondi
                    remaining = (timeout - elapsed) // 1000
                    # Restituisce True se l'utente ha annullato (iscanceled)
                    callback_result = progress_callback(
                        int((i / total) * 100),
                        addon.getLocalizedString(31244).format(addon_id=addon_id) + f" ({remaining}s)"
                    )
                    if callback_result:  # L'utente ha annullato
                        xbmc.log(f"OptiKlean: User cancelled during installation of {addon_id}", xbmc.LOGINFO)
                        user_cancelled = True
                        break
            
            if user_cancelled:
                # Aggiungi addon corrente come fallito e interrompi
                results['failed'].append((addon_id, "cancelled"))
                xbmc.log("OptiKlean: Installation cancelled by user, stopping remaining addons", xbmc.LOGINFO)
                break  # Esce dal ciclo for, non installa gli addon rimanenti
            
            if not install_detected:
                # Timeout raggiunto - determina la causa probabile
                if addon_might_not_exist:
                    xbmc.log(f"OptiKlean: Addon {addon_id} not found in any configured repository", xbmc.LOGWARNING)
                    results['not_in_repo'].append(addon_id)
                else:
                    xbmc.log(f"OptiKlean: Timeout installing {addon_id} after {timeout/1000}s - installation may have failed", xbmc.LOGWARNING)
                    results['failed'].append((addon_id, "timeout"))
                
        except Exception as e:
            xbmc.log(f"OptiKlean: Error installing {addon_id}: {str(e)}", xbmc.LOGERROR)
            results['failed'].append((addon_id, str(e)))
    
    # Aggiorna la lista degli addon locali
    xbmc.executebuiltin("UpdateLocalAddons")
    xbmc.sleep(1000)
    
    # Abilita gli addon installati (alcuni potrebbero essere disabilitati di default)
    for addon_id in results['success']:
        try:
            xbmc.executeJSONRPC(json.dumps({
                "jsonrpc": "2.0",
                "method": "Addons.SetAddonEnabled",
                "params": {"addonid": addon_id, "enabled": True},
                "id": 1
            }))
            xbmc.log(f"OptiKlean: Enabled addon {addon_id}", xbmc.LOGINFO)
        except Exception as e:
            xbmc.log(f"OptiKlean: Could not enable {addon_id}: {e}", xbmc.LOGWARNING)
    
    if progress_callback:
        progress_callback(100, addon.getLocalizedString(31245))  # "Native addon installation complete"
    
    return results

def should_exclude_addon_from_backup(folder_name):
    """Determina se un addon deve essere escluso dal backup automatico (non dai backup selettivi)"""
    excluded_prefixes = (
        "xbmc.", "script.common.", "metadata.",
        "resource.language.", "service.xbmc.versioncheck", "service.subtitles.",
        "webinterface.", "visualization.", "screensaver."
    )
    # NOTA: "script.module." NON è escluso perché sono dipendenze Python
    # necessarie per il funzionamento degli addon utente
    # NOTA: "repository." NON è escluso perché i repository sono necessari
    # per reinstallare/aggiornare gli addon dopo un restore
    # Resource generici di sistema da escludere (ma non quelli skin-correlati)
    excluded_resource_patterns = (
        "resource.images.fanart", "resource.images.moviegenreicons.colored",
        "resource.uisounds.confluence"
    )
    excluded_exact = ("script.image.resource.select",)
    
    # Escludi se inizia con un prefisso escluso
    if any(folder_name.startswith(p) for p in excluded_prefixes):
        return True
    # Escludi se è in exact match
    if folder_name in excluded_exact:
        return True
    # Escludi resource generici di sistema ma mantieni quelli skin-correlati
    if folder_name in excluded_resource_patterns:
        return True
    # Mantieni resource.images/uisounds se contengono "skin" nel nome
    if folder_name.startswith(("resource.images.", "resource.uisounds.")):
        if "skin" in folder_name.lower():
            return False  # Mantieni (skin-correlato)
        else:
            return True   # Escludi (sistema generico)
    return False

def collect_database_items_for_backup():
    """Raccoglie tutti i database per il backup"""
    backup_items = []
    backed_up_items = []
    
    db_path = xbmcvfs.translatePath(DATABASE_SPECIAL_PATH)
    
    if xbmcvfs.exists(db_path):
        try:
            _, files = xbmcvfs.listdir(db_path)
            for db_file in files:
                if db_file.endswith('.db'):
                    # Escludi i database delle texture (cache non critica, rigenerata automaticamente)
                    if db_file.lower().startswith('textures'):
                        xbmc.log(f"OptiKlean: Skipping texture database: {db_file} (cache, auto-regenerated)", xbmc.LOGINFO)
                        continue
                    
                    backup_items.append((safe_path_join(db_path, db_file), f"Database/{db_file}"))
                    backed_up_items.append(f"{addon.getLocalizedString(31015)} {db_file}")
        except Exception as e:
            xbmc.log(f"OptiKlean: Error listing databases: {e}", xbmc.LOGWARNING)
    
    return backup_items, backed_up_items

def collect_skin_items_for_backup():
    """Comprehensive skin backup with all component prefixes """
    # Get translated paths
    addons_path = xbmcvfs.translatePath(HOME_ADDONS_SPECIAL_PATH)
    addon_data_path = xbmcvfs.translatePath(PROFILE_ADDON_DATA_SPECIAL_PATH)
    userdata_path = xbmcvfs.translatePath(PROFILE_SPECIAL_PATH)
    
    backup_items = []
    backed_up_items = []

    # Debug: Verify base paths
    xbmc.log(f"OptiKlean: Addons path: {addons_path} (exists: {os.path.exists(addons_path)})", xbmc.LOGINFO)
    xbmc.log(f"OptiKlean: Addon data path: {addon_data_path} (exists: {os.path.exists(addon_data_path)})", xbmc.LOGINFO)

    # 1. Include guisettings.xml with verification
    gui_settings_file = os.path.join(userdata_path, GUI_SETTINGS_FILE)
    if os.path.exists(gui_settings_file):
        try:
            with open(gui_settings_file, 'rb') as f:
                f.read(1)  # Test file access
            backup_items.append((gui_settings_file, GUI_SETTINGS_FILE))
            backed_up_items.append("GUI settings")
            xbmc.log(f"OptiKlean: Verified {GUI_SETTINGS_FILE} for backup", xbmc.LOGINFO)
        except Exception as e:
            xbmc.log(f"OptiKlean: Failed to access {GUI_SETTINGS_FILE}: {str(e)}", xbmc.LOGERROR)

    # 2. Complete list of all skin-related prefixes
    skin_prefixes = (
        # Core skin components
        SKIN_PREFIX,
        "script.skin.",
        "script.skinhelper.",
        "script.skinshortcuts",
        "script.skinvariables",
        
        # Visual elements
        "resource.images.skinbackgrounds.",
        "resource.images.skinicons.",
        "resource.images.skinfanart.",
        "resource.images.skinlogos.",
        "resource.images.skinposters.",
        "resource.images.skinwidgets.",
        
        # Media resources
        "resource.images.studios.",
        "resource.images.moviegenreicons.",
        "resource.images.weathericons.",
        "resource.images.recordlabels.",
        "resource.images.musicgenreicons.",
        "resource.images.countryflags.",
        "resource.images.languageflags.",
        "resource.images.moviecountryicons.",
        "resource.images.tvshowgenreicons.",
        "resource.images.studiopacks.",
        
        # UI elements
        "resource.uisounds.",
        "resource.font.",
        
        # Popular skin frameworks
        "script.embuary.",
        "script.arctic.",
        "script.aura.",
        "script.titan.",
        "script.confluence.",
        "script.estuary.",
        "script.nexus.",
        "script.amber.",
        "script.colorbox.",
        
        # Helper scripts
        "script.skin.helper.",
        "script.skin.widgets.",
        "script.skin.shortcuts.",
        "script.extendedinfo",
        "script.artwork.helper"
    )

    # 3. First scan addons directory and collect skin addons
    skin_addons = set()
    try:
        if os.path.exists(addons_path):
            folders = [f for f in os.listdir(addons_path) 
                      if os.path.isdir(os.path.join(addons_path, f))]
            xbmc.log(f"OptiKlean: Found {len(folders)} folders in addons directory", xbmc.LOGINFO)

            for folder in folders:
                if any(folder.startswith(p) for p in skin_prefixes):
                    skin_addons.add(folder)
                    addon_dir = os.path.join(addons_path, folder)
                    
                    # Verify the addon contains valid files
                    try:
                        test_files = [
                            f for f in os.listdir(addon_dir)
                            if f.endswith(('.xml', '.py', '.json')) or f == 'addon.xml'
                        ]
                        if not test_files:
                            xbmc.log(f"OptiKlean: Skipping {folder} - no valid files found", xbmc.LOGWARNING)
                            continue
                    except Exception as e:
                        xbmc.log(f"OptiKlean: Cannot scan {folder}: {str(e)}", xbmc.LOGWARNING)
                        continue

                    # Add to backup
                    backup_items.append((addon_dir, f"{ADDONS_ARCHIVE_PREFIX}{folder}"))
                    
                    # Classify for logging
                    if folder.startswith(SKIN_PREFIX):
                        item_type = "Skin"
                    elif folder.startswith("script.skinhelper"):
                        item_type = "Skin Helper"
                    elif folder.startswith("resource.images"):
                        item_type = "Skin Resource"
                    elif folder in ("script.skinshortcuts", "script.skinvariables"):
                        item_type = "Skin Utility"
                    else:
                        item_type = "Skin Component"
                    
                    backed_up_items.append(f"{item_type}: {folder}")
                    xbmc.log(f"OptiKlean: Verified {item_type}: {folder}", xbmc.LOGINFO)

    except Exception as e:
        xbmc.log(f"OptiKlean: Error scanning addons directory: {str(e)}", xbmc.LOGERROR)

    # 4. Now scan addon_data directory for standalone skin data folders
    try:
        if os.path.exists(addon_data_path):
            data_folders = [f for f in os.listdir(addon_data_path) 
                           if os.path.isdir(os.path.join(addon_data_path, f))]
            
            for folder in data_folders:
                # Include if:
                # 1. Matches skin pattern AND
                # 2. Either has corresponding addon OR is a skin data folder
                if any(folder.startswith(p) for p in skin_prefixes) and \
                   (folder in skin_addons or folder.startswith(SKIN_PREFIX)):
                    
                    data_dir = os.path.join(addon_data_path, folder)
                    if os.path.exists(data_dir):
                        # Add data folder to backup (don't check if empty)
                        backup_items.append((data_dir, f"addon_data/{folder}"))
                        
                        # Determine if this is standalone data (no corresponding addon)
                        if folder not in skin_addons:
                            backed_up_items.append(f"Standalone Skin Data: {folder}")
                            xbmc.log(f"OptiKlean: Found standalone skin data: {folder}", xbmc.LOGINFO)
                        else:
                            backed_up_items.append(f"Skin Data: {folder}")
                            xbmc.log(f"OptiKlean: Found skin data: {folder}", xbmc.LOGINFO)

    except Exception as e:
        xbmc.log(f"OptiKlean: Error scanning addon_data directory: {str(e)}", xbmc.LOGERROR)

    # Final verification
    xbmc.log(f"OptiKlean: Final backup items count: {len(backup_items)}", xbmc.LOGINFO)
    for src, dest in backup_items:
        if not os.path.exists(src):
            xbmc.log(f"  WARNING: Backup source missing: {src} -> {dest}", xbmc.LOGWARNING)
        else:
            xbmc.log(f"  Verified: {src} -> {dest}", xbmc.LOGDEBUG)

    return backup_items, backed_up_items

def collect_all_user_addons():
    """Raccoglie tutti gli addon utente per il backup completo"""
    addons_path = xbmcvfs.translatePath(HOME_ADDONS_SPECIAL_PATH)
    addon_data_path = xbmcvfs.translatePath(PROFILE_ADDON_DATA_SPECIAL_PATH)
       
    all_user_addons = []
    
    try:
        # First handle regular addons that exist in addons_path (user folder)
        all_folders = sorted(os.listdir(addons_path))
        script_modules_home = [f for f in all_folders if f.startswith("script.module.")]
        xbmc.log(f"OptiKlean: collect_all_user_addons - Found {len(script_modules_home)} script.module.* in home/addons", xbmc.LOGINFO)
        
        for folder in all_folders:
            if folder.lower() in ("temp", "packages"):
                continue
            if should_exclude_addon_from_backup(folder):
                xbmc.log(f"OptiKlean: Excluding from full backup: {folder}", xbmc.LOGDEBUG)
                continue
            
            addon_dir = safe_path_join(addons_path, folder)
            data_dir = safe_path_join(addon_data_path, folder)
            
            has_addon = os.path.isdir(addon_dir)
            has_data = os.path.isdir(data_dir)
            
            if has_addon or has_data:
                all_user_addons.append(folder)
        
        # Also include data folders that don't have corresponding addons
        for data_folder in sorted(os.listdir(addon_data_path)):
            if data_folder in all_user_addons:  # Already processed
                continue
            if should_exclude_addon_from_backup(data_folder):
                continue
            
            data_dir = safe_path_join(addon_data_path, data_folder)
            if os.path.isdir(data_dir):
                all_user_addons.append(data_folder)
                
    except Exception as e:
        xbmc.log(f"OptiKlean: Error collecting user addons: {e}", xbmc.LOGWARNING)
    
    return all_user_addons

def select_addons_for_backup(backup_mode="both"):
    """Select addons for backup based on specified type"""
    addons_path = xbmcvfs.translatePath(HOME_ADDONS_SPECIAL_PATH)
    addon_data_path = xbmcvfs.translatePath(PROFILE_ADDON_DATA_SPECIAL_PATH)

    addon_list = []
    display_list = []

    try:
        # First handle regular addons that exist in addons_path (user folder)
        all_folders = sorted(os.listdir(addons_path))
        script_modules_home = [f for f in all_folders if f.startswith("script.module.")]
        xbmc.log(f"OptiKlean: Found {len(script_modules_home)} script.module.* in home/addons: {script_modules_home[:5]}{'...' if len(script_modules_home) > 5 else ''}", xbmc.LOGINFO)
        
        for folder in all_folders:
            if folder.lower() in ("temp", "packages"):
                continue
            if should_exclude_addon_from_backup(folder):
                xbmc.log(f"OptiKlean: Excluding addon from backup selection: {folder}", xbmc.LOGDEBUG)
                continue
            
            addon_dir = safe_path_join(addons_path, folder)
            data_dir = safe_path_join(addon_data_path, folder)
            
            has_addon = os.path.isdir(addon_dir)
            has_data = os.path.isdir(data_dir)
            
            if (
                (backup_mode == "addons" and not has_addon)
                or (backup_mode == "addon_data" and not has_data)
                or (backup_mode == "both" and not (has_addon or has_data))
            ):
                continue
                
            addon_size_kb = get_size_kb(addon_dir) if has_addon else 0.0
            data_size_kb = get_size_kb(data_dir) if has_data else None
            
            # Format size display - use KB if < 1000KB, otherwise MB
            def format_size(kb):
                if kb < 1000:
                    return f"{kb:.2f} {addon.getLocalizedString(31013)}"
                else:
                    return f"{kb/1024:.2f} {addon.getLocalizedString(31014)}"
            
            data_label = (
                f"{folder} ({format_size(data_size_kb)} {addon.getLocalizedString(31010)})"
                if data_size_kb is not None
                else f"{folder} ({addon.getLocalizedString(31011)})"
            )

            if backup_mode == "addons":
                label = f"{folder} ({format_size(addon_size_kb)})"
            elif backup_mode == "addon_data":
                label = data_label
            else:
                label = f"{folder} ({format_size(addon_size_kb)} {addon.getLocalizedString(31012)}"
                label += (
                    f", {format_size(data_size_kb)} {addon.getLocalizedString(31010)})"
                    if data_size_kb is not None
                    else f", {addon.getLocalizedString(31011)})"
                )
            
            display_list.append(label)
            addon_list.append(folder)

        # Special case: Also include data folders that don't have corresponding addons in home/addons/
        if backup_mode in ("addon_data", "both"):
            for data_folder in sorted(os.listdir(addon_data_path)):
                if data_folder in addon_list:  # Already processed
                    continue
                if should_exclude_addon_from_backup(data_folder):
                    continue
                
                data_dir = safe_path_join(addon_data_path, data_folder)
                if os.path.isdir(data_dir):
                    data_size_kb = get_size_kb(data_dir)
                    label = f"{data_folder} ({format_size(data_size_kb)} {addon.getLocalizedString(31010)})" if data_size_kb is not None else f"{data_folder} ({addon.getLocalizedString(31011)})"
                    display_list.append(label)
                    addon_list.append(data_folder)
            
    except Exception as e:
        xbmc.log(f"OptiKlean: Error listing addons: {e}", xbmc.LOGERROR)
        return None  # Return None to distinguish from empty selection

    # Show selection dialog
    # 31005: "Select addons to back up"
    selected_indices = xbmcgui.Dialog().multiselect(addon.getLocalizedString(31005), display_list)
    
    # Handle dialog return values properly
    if selected_indices is None:  # User pressed Cancel
        xbmc.log("OptiKlean: User cancelled addon selection", xbmc.LOGINFO)
        return None
    elif not selected_indices:  # User pressed OK with no selection
        xbmc.log("OptiKlean: User selected 0 addons", xbmc.LOGINFO)
        return []
    
    # Return the selected addon IDs
    selected_addons = []
    for index in selected_indices:
        if 0 <= index < len(addon_list):  # Safety check
            selected_addons.append(addon_list[index])
    
    xbmc.log(f"OptiKlean: User selected {len(selected_addons)} addons: {selected_addons}", xbmc.LOGINFO)
    return selected_addons

def create_temp_backup(backup_items, progress_callback=None, backup_metadata=None):
    """Create temporary backup ZIP file locally"""
    temp_dir = xbmcvfs.translatePath("special://temp/optiklean/")
    if not xbmcvfs.exists(temp_dir):
        xbmcvfs.mkdirs(temp_dir)
    
    # Controlla spazio disponibile per il backup temporaneo
    estimated_size_mb = calculate_backup_size_estimate(backup_items)
    temp_free_space = get_free_space_mb(temp_dir)
    
    if temp_free_space is not None and estimated_size_mb * 1.5 > temp_free_space:
        # Margine di sicurezza 50% per il file temporaneo non compresso
        xbmc.log(f"OptiKlean: Insufficient temp space. Need ~{estimated_size_mb * 1.5:.1f}MB, available: {temp_free_space:.1f}MB", xbmc.LOGWARNING)
        
        # Mostra dialog di errore informativo
        message = addon.getLocalizedString(30703).format(
            size_required=f"{estimated_size_mb * 1.5:.1f}",
            size_available=f"{temp_free_space:.1f}"
        )
        xbmcgui.Dialog().ok(addon.getLocalizedString(30702), message)
        return None
    
    temp_zip = safe_path_join(temp_dir, f"backup_temp_{int(time.time())}.zip")
    temp_zip_local = xbmcvfs.translatePath(temp_zip)
    cancelled = False
    
    try:
        with zipfile.ZipFile(temp_zip_local, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
            total_items = len(backup_items)
            for i, (source_path, archive_path) in enumerate(backup_items):
                if progress_callback and progress_callback():  # Check for cancellation
                    cancelled = True
                    break
                
                if progress_callback:
                    # 31006: "Backing up: {filename}"
                    progress_callback(
                        int((i / total_items) * 100),
                        addon.getLocalizedString(31006).format(filename=source_path.split('/')[-1])
                    )
                
                # Controlla spazio durante la creazione
                if i % 10 == 0:  # Controlla ogni 10 file per performance
                    try:
                        temp_free_now = get_free_space_mb(temp_dir)
                        if temp_free_now is not None and temp_free_now < 100:  # Meno di 100MB liberi
                            xbmc.log(f"OptiKlean: Low temp space during backup: {temp_free_now:.1f}MB", xbmc.LOGWARNING)
                            
                            # Opzionale: interrompi il backup se lo spazio è troppo poco
                            if temp_free_now < 50:  # Meno di 50MB - situazione critica
                                xbmc.log(f"OptiKlean: Critical temp space shortage: {temp_free_now:.1f}MB", xbmc.LOGERROR)
                                raise RuntimeError(f"Insufficient temporary space: {temp_free_now:.1f}MB remaining")
                    except RuntimeError:
                        raise
                    except Exception:
                        # Non interrompere il backup per errori di controllo spazio (eccetto spazio critico)
                        # Se l'eccezione contiene il messaggio di spazio critico, deve essere rilanciata
                        # ma per semplicità, ignoriamo tutti gli errori del controllo spazio
                        pass
                
                add_to_zip_recursive(backup_zip, source_path, archive_path)

            if cancelled:
                xbmc.log("OptiKlean: Backup creation cancelled by user", xbmc.LOGINFO)
            else:
                # Crea marker file con metadati per compatibilità cross-platform
                if backup_metadata:
                    backup_marker = json.dumps(backup_metadata, indent=2)
                else:
                    # Fallback per backup legacy
                    backup_marker = json.dumps({
                        "optiklean_backup": True,
                        "os_info": get_current_os(),
                        "native_addons": []
                    }, indent=2)
                
                backup_zip.writestr(BACKUP_MARKER_FILE, backup_marker)

        if cancelled:
            if os.path.exists(temp_zip_local):
                os.remove(temp_zip_local)
            elif xbmcvfs.exists(temp_zip):
                xbmcvfs.delete(temp_zip)
            return None
        
        return temp_zip
    except Exception as e:
        xbmc.log(f"OptiKlean: Error creating temp backup: {e}", xbmc.LOGERROR)
        # Clean up on error
        if xbmcvfs.exists(temp_zip):
            xbmcvfs.delete(temp_zip)
        return None

def add_to_zip_recursive(zip_file, source_path, archive_path):
    try:
        # Convert Kodi special paths to local filesystem paths
        local_path = xbmcvfs.translatePath(source_path) if source_path.startswith("special://") else source_path
        
        if not os.path.exists(local_path):
            xbmc.log(f"OptiKlean: Source not found: {local_path}", xbmc.LOGERROR)
            return False

        if os.path.isfile(local_path):
            # Single file - add directly
            zip_file.write(local_path, archive_path)
            return True
        else:
            # Directory - recursive add
            for root, dirs, files in os.walk(local_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, local_path)
                    zip_path = os.path.join(archive_path, rel_path).replace('\\', '/')
                    
                    try:
                        zip_file.write(file_path, zip_path)
                    except Exception as e:
                        xbmc.log(f"OptiKlean: Failed to add {file_path}: {str(e)}", xbmc.LOGWARNING)
            return True

    except Exception as e:
        xbmc.log(f"OptiKlean: ZIP creation error: {str(e)}", xbmc.LOGERROR)
        return False

def perform_backup(mode):
    addon_data_path = xbmcvfs.translatePath(OPTIKLEAN_ADDON_DATA_PATH)
    prompt_status_path = safe_path_join(addon_data_path, "backup_path_prompt_status.json")

    # Define maps at the start for use in both notification and log
    log_key_map = {
        "full": "backup_full",
        "addons": "backup_addons",
        "addon_data": "backup_addon_data", 
        "both": "backup_addons_and_data",
        "skins": "backup_skins",
        "databases": "backup_databases",
        "sources": "backup_sources",
        "gui_settings": "backup_gui_settings",
        "profiles": "backup_profiles",
        "advanced_settings": "backup_advanced_settings",
        "keymaps": "backup_keymaps",
        "playlists": "backup_playlists",
        "passwords": "backup_passwords"
    }
    
    type_label_map = {
        "full": addon.getLocalizedString(30978),              # "Full backup"
        "addons": addon.getLocalizedString(30979),            # "Addons only"
        "addon_data": addon.getLocalizedString(30980),        # "Addon data only"
        "both": addon.getLocalizedString(30981),              # "Addons + data"
        "skins": addon.getLocalizedString(30982),             # "Skins"
        "databases": addon.getLocalizedString(30983),         # "Kodi databases"
        "sources": addon.getLocalizedString(30984),           # "Sources (sources.xml)"
        "gui_settings": addon.getLocalizedString(30985),      # "GUI settings (guisettings.xml)"
        "profiles": addon.getLocalizedString(30986),          # "Profiles (profiles.xml)"
        "advanced_settings": addon.getLocalizedString(30987), # "Advanced settings (advancedsettings.xml)"
        "keymaps": addon.getLocalizedString(30988),           # "Keymaps"
        "playlists": addon.getLocalizedString(30989),         # "Playlists"
        "passwords": addon.getLocalizedString(30990)          # "Network passwords (passwords.xml)"
    }

    # Initialize variables for log
    zip_name = "—"
    dest_zip = "—"  
    size_mb = 0
    result = addon.getLocalizedString(31018)
    backed_up_items = []

    backup_dest = addon.getSetting("backup_path")
    if not backup_dest.strip():
        # Check if we should ask for path or use default
        if xbmcvfs.exists(prompt_status_path):
            try:
                with xbmcvfs.File(prompt_status_path, 'r') as f:
                    data = json.loads(f.read())
                    if data.get("use_default", False):
                        backup_dest = xbmcvfs.translatePath(HOME_SPECIAL_PATH)
                    else:
                        backup_dest = xbmcgui.Dialog().browse(0, addon.getLocalizedString(30304), "files")
                        if not backup_dest:
                            xbmcgui.Dialog().notification("OptiKlean", addon.getLocalizedString(30207), xbmcgui.NOTIFICATION_WARNING, 3000)
                            return
            except (IOError, OSError, json.JSONDecodeError, KeyError) as e:
                xbmc.log(f"OptiKlean: Error reading backup path prompt status: {e}", xbmc.LOGWARNING)
                backup_dest = xbmcvfs.translatePath(HOME_SPECIAL_PATH)
        else:
            # First time - ask user
            choice = xbmcgui.Dialog().yesno(
                addon.getLocalizedString(30704),
                addon.getLocalizedString(30705)
            )
            
            if choice:  # User chose YES - custom folder
                backup_dest = xbmcgui.Dialog().browse(0, addon.getLocalizedString(30304), "files")
                if not backup_dest:
                    xbmcgui.Dialog().notification("OptiKlean", addon.getLocalizedString(30207), xbmcgui.NOTIFICATION_WARNING, 3000)
                    return
                # Save the custom path
                addon.setSetting("backup_path", backup_dest)
            else:  # User chose NO - use default
                backup_dest = xbmcvfs.translatePath(HOME_SPECIAL_PATH)
                # Save preference to not ask again
                try:
                    with xbmcvfs.File(prompt_status_path, 'w') as f:
                        f.write(json.dumps({"use_default": True}))
                except (IOError, OSError, json.JSONDecodeError) as e:
                    xbmc.log(f"OptiKlean: Error writing backup path prompt status: {e}", xbmc.LOGWARNING)

    # Verifica del percorso di backup fino a validazione o cancellazione
    while True:
        path_available, error_message = verify_backup_path_availability(backup_dest)
        if path_available:
            break  # Percorso valido, continua con il backup
            
        xbmc.log(f"OptiKlean: Backup path verification failed: {error_message}", xbmc.LOGERROR)
        
        # Mostra dialog di errore informativo all'utente
        if is_network_path(backup_dest):
            dialog_message = addon.getLocalizedString(31000).format(path=backup_dest)
        else:
            # Messaggio specifico per unità USB/rimovibili
            if "drive" in error_message.lower() and "not available" in error_message.lower():
                dialog_message = addon.getLocalizedString(31001).format(
                    path=backup_dest,
                    error=error_message
                )
            else:
                dialog_message = addon.getLocalizedString(31002).format(
                    path=backup_dest,
                    error=error_message
                )
        
        # Mostra dialog con opzione di aprire le impostazioni
        choice = xbmcgui.Dialog().yesno(
            addon.getLocalizedString(30706),
            dialog_message,
            addon.getLocalizedString(31003),
            addon.getLocalizedString(31004)
        )
        
        if choice:  # User sceglie "Open Settings"
            # Memorizza il percorso originale prima di aprire le impostazioni
            original_backup_dest = backup_dest
            
            xbmc.executebuiltin('Addon.OpenSettings(program.optiklean)')
            
            # Dopo la chiusura delle impostazioni, ricarica la configurazione
            backup_dest = addon.getSetting("backup_path")
            xbmc.log(f"OptiKlean: Reloaded backup path from settings: {backup_dest}", xbmc.LOGINFO)
            
            # Controlla se l'utente ha modificato il percorso
            if backup_dest == original_backup_dest:
                # Il percorso non è cambiato, probabilmente l'utente ha annullato o chiuso senza salvare
                xbmc.log("OptiKlean: Backup path unchanged after settings, assuming user cancelled", xbmc.LOGINFO)
                # Non mostriamo notifica qui - l'utente ha semplicemente chiuso le impostazioni
                result = addon.getLocalizedString(31020)  # "Cancelled by user - No path changes"
                return
            
            # Il percorso è cambiato, continua con la verifica
            # Il loop continuerà automaticamente e ri-verificherà il nuovo percorso
        else:  # User sceglie "Cancel"
            # Mostra notificazione di cancellazione
            xbmcgui.Dialog().notification(
                "OptiKlean", 
                addon.getLocalizedString(30207), 
                logo_path, 
                5000
            )
            result = addon.getLocalizedString(31021)
            return    # Set variables during the process
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    zip_name = f"kodi_backup_{mode}_{timestamp}.zip"
    dest_zip = safe_path_join(backup_dest, zip_name)

    addons_path = xbmcvfs.translatePath(HOME_ADDONS_SPECIAL_PATH)
    db_path = xbmcvfs.translatePath(DATABASE_SPECIAL_PATH)
    userdata_path = xbmcvfs.translatePath(PROFILE_SPECIAL_PATH)

    backup_items = []
    result = addon.getLocalizedString(31017)

    try:
        if mode in ["addons", "addon_data", "both"]:
            selected_addons = select_addons_for_backup(mode)
            
            if selected_addons is None:  # User cancelled
                return
            if not selected_addons:  # Empty selection
                xbmcgui.Dialog().notification("OptiKlean", addon.getLocalizedString(30208), xbmcgui.NOTIFICATION_WARNING, 3000)
                return
            
            # Get Kodi paths (use xbmcvfs for consistency)
            addons_path = xbmcvfs.translatePath(HOME_ADDONS_SPECIAL_PATH)
            addon_data_root = xbmcvfs.translatePath(PROFILE_ADDON_DATA_SPECIAL_PATH)
            
            xbmc.log(f"OptiKlean: Addons path: {addons_path}", xbmc.LOGDEBUG)
            xbmc.log(f"OptiKlean: Addon data path: {addon_data_root}", xbmc.LOGDEBUG)
            
            for addon_id in selected_addons:
                # Handle addon code backup
                if mode in ["addons", "both"]:
                    addon_path = xbmcvfs.translatePath(f"{HOME_ADDONS_SPECIAL_PATH}{addon_id}")
                    
                    xbmc.log(f"OptiKlean: DEBUG - Checking addon path: '{addon_path}'", xbmc.LOGDEBUG)
                    
                    # Use os.path.isdir() like in select_addons_for_backup() for consistency
                    if os.path.isdir(addon_path):
                        # Use forward slashes for archive path (ZIP standard)
                        archive_path = f"{ADDONS_ARCHIVE_PREFIX}{addon_id}"
                        backup_items.append((addon_path, archive_path))
                        backed_up_items.append(f"Addon: {addon_id}")
                        xbmc.log(f"OptiKlean: Found addon: {addon_id}", xbmc.LOGINFO)
                    else:
                        xbmc.log(f"OptiKlean: Addon not found: {addon_id}", xbmc.LOGWARNING)
                
                # Handle addon data backup
                if mode in ["addon_data", "both"]:
                    # Use the same reliable method as select_addons_for_backup()
                    data_path = xbmcvfs.translatePath(f"{PROFILE_ADDON_DATA_SPECIAL_PATH}{addon_id}")
                    xbmc.log(f"OptiKlean: DEBUG - Checking data path: '{data_path}'", xbmc.LOGDEBUG)
                    
                    # Use os.path.isdir() like in select_addons_for_backup() for consistency
                    if os.path.isdir(data_path):
                        archive_path = f"addon_data/{addon_id}"
                        backup_items.append((data_path, archive_path))
                        backed_up_items.append(f"Data: {addon_id}")
                        xbmc.log(f"OptiKlean: Found addon data: {addon_id}", xbmc.LOGINFO)
                    else:
                        xbmc.log(f"OptiKlean: Addon data not found: {data_path}", xbmc.LOGDEBUG)
            
            # Debug output
            xbmc.log(f"OptiKlean: Final backup items count: {len(backup_items)}", xbmc.LOGINFO)
            for item in backup_items:
                xbmc.log(f"OptiKlean: Backup item: {item[0]} -> {item[1]}", xbmc.LOGDEBUG)

        elif mode == "databases":
            # Usa la funzione esistente per raccogliere i database
            db_items, db_backed_up = collect_database_items_for_backup()
            backup_items.extend(db_items)
            backed_up_items.extend(db_backed_up)

        elif mode == "sources":
            sources_file = safe_path_join(userdata_path, SOURCES_FILE)
            if xbmcvfs.exists(sources_file):
                backup_items.append((sources_file, SOURCES_FILE))

        elif mode == "gui_settings":
            gui_settings_file = safe_path_join(userdata_path, GUI_SETTINGS_FILE)
            if xbmcvfs.exists(gui_settings_file):
                backup_items.append((gui_settings_file, GUI_SETTINGS_FILE))

        elif mode == "profiles":
            profiles_file = safe_path_join(userdata_path, PROFILES_FILE)
            if xbmcvfs.exists(profiles_file):
                backup_items.append((profiles_file, PROFILES_FILE))

        elif mode == "advanced_settings":
            advanced_settings_file = safe_path_join(userdata_path, ADVANCED_SETTINGS_FILE)
            if xbmcvfs.exists(advanced_settings_file):
                backup_items.append((advanced_settings_file, ADVANCED_SETTINGS_FILE))
            else:
                xbmcgui.Dialog().notification("OptiKlean", addon.getLocalizedString(30209), logo_path, 3000)
                result = addon.getLocalizedString(31032)
                return

        elif mode == "keymaps":
            keymaps_folder = xbmcvfs.translatePath(KEYMAPS_SPECIAL_PATH)
            if xbmcvfs.exists(keymaps_folder):
                try:
                    dirs, files = xbmcvfs.listdir(keymaps_folder)
                    keymap_count = 0
                    
                    for file in files:
                        if file.endswith('.xml'):
                            keymap_count += 1
                            backed_up_items.append(f"Keymap: {file}")
                    
                    # Check subfolders
                    for dir_name in dirs:
                        subdir_path = safe_path_join(keymaps_folder, dir_name)
                        if xbmcvfs.exists(subdir_path):
                            try:
                                _, subfiles = xbmcvfs.listdir(subdir_path)
                                for subfile in subfiles:
                                    if subfile.endswith('.xml'):
                                        keymap_count += 1
                                        backed_up_items.append(f"Keymap: {dir_name}/{subfile}")
                            except Exception:
                                pass
                    
                    if keymap_count == 0:
                        xbmcgui.Dialog().notification("OptiKlean", addon.getLocalizedString(30210), logo_path, 3000)
                        result = addon.getLocalizedString(31033)
                        return
                    
                    backup_items.append((keymaps_folder, "keymaps"))
                except Exception:
                    xbmcgui.Dialog().notification("OptiKlean", addon.getLocalizedString(30211), xbmcgui.NOTIFICATION_ERROR, 3000)
                    result = addon.getLocalizedString(31034)
                    return
            else:
                xbmcgui.Dialog().notification("OptiKlean", addon.getLocalizedString(30210), logo_path, 3000)
                result = addon.getLocalizedString(31033)
                return

        elif mode == "skins":
            # Automatically collect all skin items
            backup_items, backed_up_items = collect_skin_items_for_backup()
            if not backup_items:
                xbmcgui.Dialog().notification("OptiKlean", addon.getLocalizedString(30212), xbmcgui.NOTIFICATION_WARNING, 3000)
                result = addon.getLocalizedString(31035)
                return

        elif mode == "playlists":
            playlists_folder = xbmcvfs.translatePath("special://userdata/playlists/")
            if xbmcvfs.exists(playlists_folder):
                try:
                    dirs, files = xbmcvfs.listdir(playlists_folder)
                    playlist_count = len([f for f in files if f.endswith(('.m3u', '.pls', '.xsp'))])
                    
                    if playlist_count == 0:
                        xbmcgui.Dialog().notification("OptiKlean", addon.getLocalizedString(30213), logo_path, 3000)
                        result = addon.getLocalizedString(31036)
                        return
                    
                    backup_items.append((playlists_folder, "playlists"))
                    backed_up_items.append(f"Playlists ({playlist_count} files)")
                except Exception:
                    xbmcgui.Dialog().notification("OptiKlean", addon.getLocalizedString(30214), xbmcgui.NOTIFICATION_ERROR, 3000)
                    result = addon.getLocalizedString(31037)
                    return
            else:
                xbmcgui.Dialog().notification("OptiKlean", addon.getLocalizedString(30215), logo_path, 3000)
                result = addon.getLocalizedString(31038)
                return

        elif mode == "passwords":
            passwords_file = safe_path_join(userdata_path, PASSWORDS_FILE)
            if xbmcvfs.exists(passwords_file):
                backup_items.append((passwords_file, PASSWORDS_FILE))
                backed_up_items.append("Network passwords")
            else:
                xbmcgui.Dialog().notification("OptiKlean", addon.getLocalizedString(30216), logo_path, 3000)
                result = addon.getLocalizedString(31039)
                return
        
        elif mode == "full":
            # Full backup using existing functions and expanded logic
            xbmc.log("OptiKlean: Starting full backup (comprehensive system backup)", xbmc.LOGINFO)
            
            # Simula la selezione di TUTTI gli addon utente (senza richiedere input utente)
            # Riusa la logica esistente di select_addons_for_backup() senza dialog
            addons_path = xbmcvfs.translatePath(HOME_ADDONS_SPECIAL_PATH)
            addon_data_path = xbmcvfs.translatePath(PROFILE_ADDON_DATA_SPECIAL_PATH)
            
            try:
                # 1. ADDONS + ADDON DATA
                all_user_addons = collect_all_user_addons()
                
                # Ora aggiungi tutti gli addon selezionati al backup
                for addon_id in all_user_addons:
                    addon_path = xbmcvfs.translatePath(f"{HOME_ADDONS_SPECIAL_PATH}{addon_id}")
                    
                    if os.path.isdir(addon_path):
                        backup_items.append((addon_path, f"{ADDONS_ARCHIVE_PREFIX}{addon_id}"))
                        backed_up_items.append(f"Addon: {addon_id}")
                    
                    # Handle addon data backup
                    data_path = xbmcvfs.translatePath(f"{PROFILE_ADDON_DATA_SPECIAL_PATH}{addon_id}")
                    if os.path.isdir(data_path):
                        backup_items.append((data_path, f"addon_data/{addon_id}"))
                        backed_up_items.append(f"Data: {addon_id}")
                
                xbmc.log(f"OptiKlean: Full backup - Added {len(all_user_addons)} user addons and their data", xbmc.LOGINFO)
            except Exception as e:
                xbmc.log(f"OptiKlean: Error collecting addons for full backup: {e}", xbmc.LOGWARNING)
            
            # 2. DATABASE
            db_items, db_backed_up = collect_database_items_for_backup()
            backup_items.extend(db_items)
            backed_up_items.extend(db_backed_up)
            xbmc.log(f"OptiKlean: Full backup - Added {len(db_backed_up)} databases", xbmc.LOGINFO)
            
            # 3. TUTTI I FILE DI CONFIGURAZIONE - Espanso per includere tutto
            config_files = [
                (SOURCES_FILE, SOURCES_FILE),
                (GUI_SETTINGS_FILE, GUI_SETTINGS_FILE),
                (PROFILES_FILE, PROFILES_FILE),
                (ADVANCED_SETTINGS_FILE, ADVANCED_SETTINGS_FILE),
                (PASSWORDS_FILE, PASSWORDS_FILE),
            ]
            
            for filename, archive_name in config_files:
                file_path = safe_path_join(userdata_path, filename)
                if xbmcvfs.exists(file_path):
                    backup_items.append((file_path, archive_name))
                    backed_up_items.append(f"Config: {filename}")
            
            # 4. KEYMAPS (se esistono) - Riusa logica esistente
            keymaps_folder = xbmcvfs.translatePath(KEYMAPS_SPECIAL_PATH)
            if xbmcvfs.exists(keymaps_folder):
                try:
                    dirs, files = xbmcvfs.listdir(keymaps_folder)
                    keymap_count = len([f for f in files if f.endswith('.xml')])
                    if keymap_count > 0 or dirs:  # Se ci sono file o cartelle
                        backup_items.append((keymaps_folder, "keymaps"))
                        backed_up_items.append(f"Keymaps ({keymap_count} custom files)")
                except Exception as e:
                    xbmc.log(f"OptiKlean: Error collecting keymaps for full backup: {e}", xbmc.LOGWARNING)
            
            # 5. PLAYLISTS (se esistono) - Riusa logica esistente
            playlists_folder = xbmcvfs.translatePath("special://userdata/playlists/")
            if xbmcvfs.exists(playlists_folder):
                try:
                    dirs, files = xbmcvfs.listdir(playlists_folder)
                    playlist_count = len([f for f in files if f.endswith(('.m3u', '.pls', '.xsp'))])
                    if playlist_count > 0:
                        backup_items.append((playlists_folder, "playlists"))
                        backed_up_items.append(f"Playlists ({playlist_count} files)")
                except Exception as e:
                    xbmc.log(f"OptiKlean: Error collecting playlists for full backup: {e}", xbmc.LOGWARNING)
            
            # NOTA: Non aggiungiamo skin separatamente perché sono già inclusi negli addon/addon_data
            # Le skin sono addon, quindi sono già state raccolte nella sezione addon sopra
            
            xbmc.log(f"OptiKlean: Full backup - Total items collected: {len(backup_items)}", xbmc.LOGINFO)
            xbmc.log(f"OptiKlean: Full backup - Components: {len(backed_up_items)} items", xbmc.LOGINFO)

        # Modified empty backup items check with more detailed logging
        if not backup_items:
            xbmc.log("OptiKlean: No valid items found to backup. Possible causes:", xbmc.LOGWARNING)
            xbmc.log(f"- Mode: {mode}", xbmc.LOGWARNING)
            if mode in ["addons", "addon_data", "both"]:
                xbmc.log(f"- Selected addons: {selected_addons if 'selected_addons' in locals() else 'N/A'}", xbmc.LOGWARNING)
                xbmc.log(f"- Addons path exists: {xbmcvfs.exists(addons_path)}", xbmc.LOGWARNING)
                xbmc.log(f"- Addon data path exists: {xbmcvfs.exists(xbmcvfs.translatePath(PROFILE_ADDON_DATA_SPECIAL_PATH))}", xbmc.LOGWARNING)
            
            xbmcgui.Dialog().notification(
                "OptiKlean", 
                addon.getLocalizedString(30217), 
                xbmcgui.NOTIFICATION_WARNING, 
                4000
            )
            result = addon.getLocalizedString(31040)
            return

        # Calculate estimated backup size with smart formatting
        size_details = get_backup_size_estimate_details(backup_items)
        estimated_size_mb = size_details['mb_equivalent']  # For space calculations
        
        # Get available free space
        free_space = get_free_space_mb(backup_dest)
        
        if free_space is None:
            free_space_text = addon.getLocalizedString(30905)
            confirmation_message = (
                f"{addon.getLocalizedString(30900)} {type_label_map.get(mode, mode.replace('_', ' ').title())}[CR]"
                f"{addon.getLocalizedString(30901)} ~{size_details['formatted']}[CR]"
                f"{addon.getLocalizedString(30902)} {free_space_text}[CR][CR]"
                f"{addon.getLocalizedString(30906)}[CR]"
                f"{addon.getLocalizedString(30907)}"
            )
        else:
            if free_space >= 1024:
                free_space_text = f"{free_space / 1024:.1f} {addon.getLocalizedString(31016)}"
            else:
                free_space_text = f"{free_space:.1f} {addon.getLocalizedString(31014)}"
                
            # Check if there's enough space (with 20% safety margin)
            space_warning = ""
            if estimated_size_mb * 1.2 > free_space:
                space_warning = f"[CR][COLOR red]{addon.getLocalizedString(30904)}[/COLOR]"
                
            confirmation_message = (
                f"{addon.getLocalizedString(30900)} {type_label_map.get(mode, mode.replace('_', ' ').title())}[CR]"
                f"{addon.getLocalizedString(30901)} ~{size_details['formatted']}[CR]"
                f"{addon.getLocalizedString(30902)} {free_space_text}{space_warning}[CR][CR]"
                f"{addon.getLocalizedString(30903)}"
            )
        
        # User confirmation
        if not xbmcgui.Dialog().yesno(addon.getLocalizedString(30302), confirmation_message):
            xbmcgui.Dialog().notification(
                "OptiKlean", 
                addon.getLocalizedString(30207), 
                logo_path, 
                3000
            )
            result = addon.getLocalizedString(31019)  # "Cancelled by user"
            return

        # Create backup
        progress = xbmcgui.DialogProgress()
        progress.create("OptiKlean", addon.getLocalizedString(30700))
        
        # Progress callback
        def progress_callback(percent=None, message=None):
            if progress.iscanceled():
                return True
            if percent is not None:
                progress.update(percent, message or "Creating backup...")
            return False
        
        # Raccogli metadati per compatibilità cross-platform
        native_addons = []
        for item_desc in backed_up_items:
            if item_desc.startswith("Addon: "):
                addon_id = item_desc.replace("Addon: ", "")
                if is_native_addon(addon_id):
                    native_addons.append(addon_id)

        def get_kodi_version():
            """Ottiene la versione completa di Kodi"""
            try:
                version = xbmc.getInfoLabel("System.BuildVersion")
                # Estrai solo il numero di versione principale (es. "21.2" da "21.2 Omega (21.2.0) Git:20240101-abcd")
                version_parts = version.split()[0]  # Prende solo "21.2"
                return version_parts
            except Exception as e:
                xbmc.log(f"OptiKlean: Error getting Kodi version: {e}", xbmc.LOGWARNING)
                return "Unknown"
        
        backup_metadata = {
            "optiklean_backup": True,
            "os_info": get_current_os(),
            "architecture": get_system_architecture(),
            "native_addons": native_addons,
            "kodi_version": get_kodi_version()
        }
        
        # Create temporary backup locally with metadata
        temp_zip = create_temp_backup(backup_items, progress_callback, backup_metadata)
        
        if temp_zip is None:
            result = addon.getLocalizedString(31019) if progress.iscanceled() else addon.getLocalizedString(31022)  # "Cancelled by user" or "Error creating backup"
            progress.close()
            return

        # Get size from the temp zip immediately after creation
        try:
            temp_local_path = xbmcvfs.translatePath(temp_zip)
            size_bytes = os.path.getsize(temp_local_path)
            size_mb = max(0.01, round(size_bytes / (1024 * 1024), 2))  # Ensure min 0.01MB display
        except Exception as e:
            xbmc.log(f"OptiKlean: Could not get backup size: {str(e)}", xbmc.LOGWARNING)
            size_mb = 0.00

        progress.update(90, addon.getLocalizedString(30701))
        transfer_success = False

        try:
            if is_network_path(dest_zip):
                # NETWORK TRANSFER (SMB/NFS)
                if safe_copy_file(temp_zip, dest_zip):
                    xbmc.log(f"OptiKlean: Backup copied to {dest_zip}", xbmc.LOGINFO)
                    transfer_success = True
                else:
                    raise OSError(addon.getLocalizedString(31028))
            else:
                # LOCAL TRANSFER - try shutil first
                dest_local = xbmcvfs.translatePath(dest_zip)
                try:
                    shutil.move(temp_local_path, dest_local)
                    xbmc.log(f"OptiKlean: Backup moved to {dest_local}", xbmc.LOGINFO)
                    transfer_success = True
                except OSError as e:
                    # Fallback to xbmcvfs if shutil fails
                    xbmc.log(f"OptiKlean: shutil.move failed, trying xbmcvfs: {str(e)}", xbmc.LOGWARNING)
                    if xbmcvfs.copy(temp_zip, dest_zip):
                        transfer_success = True
                    else:
                        raise OSError(addon.getLocalizedString(31029))

        except Exception as e:
            result = addon.getLocalizedString(31023).format(error=str(e))
            xbmc.log(f"OptiKlean: Backup transfer error: {str(e)}", xbmc.LOGERROR)
        finally:
            # Always cleanup temp file (except when using shutil.move which already moved it)
            try:
                if os.path.exists(temp_local_path):
                    # Only delete if file still exists (shutil.move removes it automatically)
                    if transfer_success and not is_network_path(dest_zip):
                        # For local transfers with shutil.move, file was already moved, no cleanup needed
                        xbmc.log("OptiKlean: Temp file moved successfully by shutil.move", xbmc.LOGDEBUG)
                    else:
                        # For network transfers or failed transfers, delete the temp file
                        os.remove(temp_local_path)
                        xbmc.log(f"OptiKlean: Temp backup file cleaned up: {temp_local_path}", xbmc.LOGDEBUG)
            except OSError as e:
                xbmc.log(f"OptiKlean: Temp cleanup failed: {str(e)}", xbmc.LOGWARNING)
            progress.close()

        if not transfer_success:
            return
        
        # Show notification with accurate size
        item_count = len(backup_items)
        item_text = addon.getLocalizedString(30908) if item_count == 1 else addon.getLocalizedString(30909)
        notification_type = type_label_map.get(mode, mode.replace('_', ' ').title())
        xbmcgui.Dialog().notification(
            "OptiKlean", 
            f"{notification_type}: {item_count} {item_text} ({size_mb} MB)", 
            logo_path, 
            5000
        )

    except Exception as e:
        result = addon.getLocalizedString(31018) + ": " + str(e)
        xbmc.log(f"OptiKlean: Backup error: {str(e)}", xbmc.LOGERROR)

        xbmcgui.Dialog().notification("OptiKlean", addon.getLocalizedString(30964).format(error=str(e)), xbmcgui.NOTIFICATION_ERROR, 5000)
        
    finally:
        log_content = (
            f"{addon.getLocalizedString(30965):<17}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"{addon.getLocalizedString(30966):<17}: {type_label_map.get(mode, addon.getLocalizedString(30977))}\n"
            f"{addon.getLocalizedString(30967):<17}: {zip_name}\n"
            f"{addon.getLocalizedString(30968):<17}: {dest_zip}\n"
            f"{addon.getLocalizedString(30969):<17}: {size_mb} MB\n"
            f"{addon.getLocalizedString(30970):<17}: {result}\n"
        )

        # Add backup contents summary for relevant types
        if mode in ["full", "addons", "addon_data", "both", "databases", "skins", "keymaps"] and backed_up_items:
            log_content += f"\n{addon.getLocalizedString(30971)}:\n"
            for item in backed_up_items:
                log_content += f"• {item}\n"
        
        # Use valid log key as fallback
        log_key = log_key_map.get(mode, "backup_advanced_settings")
        write_log_local(log_key, log_content, append=False)

def perform_restore():
    addon_data_path = xbmcvfs.translatePath(OPTIKLEAN_ADDON_DATA_PATH)
    
    # Inizializza le variabili per il log
    backup_file = "—"
    restore_type = "Unknown"
    size_mb = 0
    result = addon.getLocalizedString(31018)
    items_restored = 0
    failed_files = []
    cleanup_temp_backup = False
    temp_backup_file = None
    backup_file_original = "—"
    safe_backup_display_name = "—"
    restarting_kodi = False
    backup_file_deleted = False
    skip_native_addons = False
    reinstall_native_addons = False  # Nuova flag per reinstallazione automatica
    native_addons_to_reinstall = []  # Lista addon da reinstallare
    native_install_results = None  # Risultati reinstallazione addon nativi
    
    try:
        # Seleziona il file di backup
        backup_file = xbmcgui.Dialog().browse(1, addon.getLocalizedString(30920), "files", ".zip")
        if not backup_file:
            result = addon.getLocalizedString(31019)
            xbmcgui.Dialog().notification("OptiKlean", addon.getLocalizedString(30921), xbmcgui.NOTIFICATION_WARNING, 3000)
            return
        
        backup_file_original = backup_file
        
        if not xbmcvfs.exists(backup_file):
            result = addon.getLocalizedString(31024)
            xbmcgui.Dialog().notification("OptiKlean", addon.getLocalizedString(30922), xbmcgui.NOTIFICATION_ERROR, 3000)
            return
        
        if not is_valid_optiklean_backup(backup_file):
            result = addon.getLocalizedString(31025)
            xbmcgui.Dialog().ok(
                addon.getLocalizedString(30923),
                addon.getLocalizedString(30924)
            )
            return

        size_mb = round(safe_file_size(backup_file) / (1024 * 1024), 2)
        
        temp_backup_file = backup_file
        
        if is_network_path(backup_file):
            temp_dir = xbmcvfs.translatePath("special://temp/optiklean/")
            if not xbmcvfs.exists(temp_dir):
                xbmcvfs.mkdirs(temp_dir)
            
            temp_backup_file = safe_path_join(temp_dir, f"temp_restore_backup_{int(time.time())}.zip")
            xbmc.log(f"OptiKlean: Copying network backup to local temp: {backup_file} -> {temp_backup_file}", xbmc.LOGINFO)
            
            if not xbmcvfs.copy(backup_file, temp_backup_file):
                result = addon.getLocalizedString(31026)
                xbmcgui.Dialog().notification("OptiKlean", addon.getLocalizedString(30925), xbmcgui.NOTIFICATION_ERROR, 3000)
                return
            cleanup_temp_backup = True
        
        # Nota: Non creiamo più temp_extract_path - usiamo estrazione diretta (approccio OpenWizard)

        file_list = []
        backup_metadata = None
        temp_backup_local = xbmcvfs.translatePath(temp_backup_file)

        # FASE 1: Leggi metadati e lista file
        with zipfile.ZipFile(temp_backup_local, 'r') as backup_zip:
            file_list = backup_zip.namelist()
            
            if BACKUP_MARKER_FILE in file_list:
                try:
                    marker_content = backup_zip.read(BACKUP_MARKER_FILE).decode('utf-8')
                    backup_metadata = json.loads(marker_content)
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    xbmc.log(f"OptiKlean: Error reading backup metadata: {e}", xbmc.LOGWARNING)
                    backup_metadata = dict(_LEGACY_BACKUP_METADATA)

        if not backup_metadata:
            backup_metadata = dict(_LEGACY_BACKUP_METADATA)
        
        # Determina il tipo di backup
        has_addons = any(f.startswith(ADDONS_ARCHIVE_PREFIX) for f in file_list)
        has_addon_data = any(f.startswith('addon_data/') for f in file_list)
        has_databases = any(f.startswith('Database/') for f in file_list)
        has_sources = SOURCES_FILE in file_list
        has_gui_settings = GUI_SETTINGS_FILE in file_list
        has_profiles = PROFILES_FILE in file_list
        has_advanced_settings = ADVANCED_SETTINGS_FILE in file_list
        has_passwords = PASSWORDS_FILE in file_list
        has_keymaps = any(f.startswith('keymaps/') for f in file_list)
        
        has_skin_addons = any(f.startswith(f"{ADDONS_ARCHIVE_PREFIX}{SKIN_PREFIX}") for f in file_list)
        has_skin_helpers = any(f.startswith(f"{ADDONS_ARCHIVE_PREFIX}script.skin") for f in file_list)
        has_skin_backgrounds = any(f.startswith(f"{ADDONS_ARCHIVE_PREFIX}resource.images.skinbackgrounds.") for f in file_list)
        has_skin_resources = any(f.startswith(f"{ADDONS_ARCHIVE_PREFIX}resource.images.studios.") or
                               f.startswith(f"{ADDONS_ARCHIVE_PREFIX}resource.images.moviegenreicons.") or
                               f.startswith(f"{ADDONS_ARCHIVE_PREFIX}resource.images.weathericons.") or
                               f.startswith(f"{ADDONS_ARCHIVE_PREFIX}resource.images.recordlabels.") or
                               f.startswith(f"{ADDONS_ARCHIVE_PREFIX}resource.images.musicgenreicons.") or
                               f.startswith(f"{ADDONS_ARCHIVE_PREFIX}resource.images.countryflags.") or
                               f.startswith(f"{ADDONS_ARCHIVE_PREFIX}resource.images.languageflags.") or
                               f.startswith(f"{ADDONS_ARCHIVE_PREFIX}resource.images.moviecountryicons.") or
                               f.startswith(f"{ADDONS_ARCHIVE_PREFIX}resource.images.tvshowgenreicons.") or
                               f.startswith(f"{ADDONS_ARCHIVE_PREFIX}resource.images.studiopacks.") or
                               f.startswith(f"{ADDONS_ARCHIVE_PREFIX}resource.images.skinicons.") or
                               f.startswith(f"{ADDONS_ARCHIVE_PREFIX}resource.images.skinfanart.") or
                               f.startswith(f"{ADDONS_ARCHIVE_PREFIX}resource.images.skinlogos.") or
                               f.startswith(f"{ADDONS_ARCHIVE_PREFIX}resource.images.skinposters.") or
                               f.startswith(f"{ADDONS_ARCHIVE_PREFIX}resource.images.skinwidgets.") or
                               f.startswith(f"{ADDONS_ARCHIVE_PREFIX}resource.uisounds.") or
                               f.startswith(f"{ADDONS_ARCHIVE_PREFIX}resource.font.") for f in file_list)
        has_advanced_skin_scripts = any(f.startswith(f"{ADDONS_ARCHIVE_PREFIX}script.skinhelper.") or
                                      f.startswith(f"{ADDONS_ARCHIVE_PREFIX}script.colorbox.") or
                                      f.startswith(f"{ADDONS_ARCHIVE_PREFIX}script.embuary.") or
                                      f.startswith(f"{ADDONS_ARCHIVE_PREFIX}script.arctic.") or
                                      f.startswith(f"{ADDONS_ARCHIVE_PREFIX}script.aura.") or
                                      f.startswith(f"{ADDONS_ARCHIVE_PREFIX}script.titan.") or
                                      f.startswith(f"{ADDONS_ARCHIVE_PREFIX}script.confluence.") or
                                      f.startswith(f"{ADDONS_ARCHIVE_PREFIX}script.estuary.") or
                                      f.startswith(f"{ADDONS_ARCHIVE_PREFIX}script.nexus.") or
                                      f.startswith(f"{ADDONS_ARCHIVE_PREFIX}script.amber.") for f in file_list)
        has_skin_settings_combo = (GUI_SETTINGS_FILE in file_list and
                                  (has_skin_addons or has_skin_helpers or has_skin_resources or has_advanced_skin_scripts))
        is_skin_backup = has_skin_addons or has_skin_helpers or has_skin_backgrounds or has_skin_resources or has_advanced_skin_scripts or has_skin_settings_combo
        
        is_full_backup = (
            has_addons and has_addon_data and has_databases and 
            has_gui_settings and has_sources
        )

        if is_full_backup:
            restore_type = "Full backup"
        elif has_addons and has_addon_data:
            restore_type = "Addons + data"
        elif has_addons:
            restore_type = "Addons only"
        elif has_addon_data:
            restore_type = "Addon data only"
        elif has_databases:
            restore_type = "Kodi databases"
        elif is_skin_backup:  # ← SPOSTATO QUI (dopo is_full_backup)
            restore_type = "Skins"
        elif has_sources:
            restore_type = "Sources (sources.xml)"
        elif has_gui_settings:
            restore_type = "GUI settings (guisettings.xml)"
        elif has_profiles:
            restore_type = "Profiles (profiles.xml)"
        elif has_advanced_settings:
            restore_type = "Advanced settings (advancedsettings.xml)"
        elif has_passwords:
            restore_type = "Network passwords (passwords.xml)"
        elif has_keymaps:
            restore_type = "Keymaps"
        
        # Controllo compatibilità
        compatibility = check_cross_platform_compatibility(backup_metadata)
        compatibility_status = compatibility.get("status", "unknown")
        
        if compatibility_status in ("incompatible_architecture", "incompatible_variant_native"):
            native_addons = backup_metadata.get("native_addons", [])
            
            if native_addons:
                # Caso con addon nativi - warning più dettagliato
                warning_base = addon.getLocalizedString(30927).format(
                    backup_info=compatibility.get('backup_info', 'Unknown'),
                    current_info=compatibility.get('current_info', 'Unknown'),
                    reason=compatibility.get('reason', 'Architecture mismatch')
                )
                
                # Aggiungi lista addon nativi problematici
                warning_message = warning_base + "\n\n" + addon.getLocalizedString(31233) + "\n"
                for addon_name in native_addons:
                    warning_message += f"• {addon_name}\n"
                
                warning_message += "\n" + addon.getLocalizedString(31234)
                
                # Mostra textviewer con lista completa
                xbmcgui.Dialog().textviewer(
                    addon.getLocalizedString(30928),  # "Backup Compatibility Warning"
                    warning_message
                )
                
                # Chiedi COME procedere (4 opzioni)
                options = [
                    addon.getLocalizedString(30941),  # "Skip native addons"
                    addon.getLocalizedString(31246),  # "Skip and reinstall from repository"
                    addon.getLocalizedString(30942),  # "Restore all addons (may not work)"
                    addon.getLocalizedString(31019)   # "Cancel"
                ]
                
                choice = xbmcgui.Dialog().select(
                    addon.getLocalizedString(30928),
                    options
                )
                
                if choice == -1 or choice == 3:  # Cancel
                    result = addon.getLocalizedString(31019)
                    xbmcgui.Dialog().notification("OptiKlean", addon.getLocalizedString(30218), logo_path, 3000)
                    return
                elif choice == 0:  # Skip native addons
                    skip_native_addons = True
                    xbmc.log(f"OptiKlean: User chose to skip native addons: {native_addons}", xbmc.LOGINFO)
                elif choice == 1:  # Skip and reinstall from repo
                    skip_native_addons = True
                    reinstall_native_addons = True
                    native_addons_to_reinstall = native_addons.copy()
                    xbmc.log(f"OptiKlean: User chose to skip and reinstall native addons: {native_addons}", xbmc.LOGINFO)
                elif choice == 2:  # Restore all
                    skip_native_addons = False
                    xbmc.log("OptiKlean: User chose to restore all addons (native may not work)", xbmc.LOGINFO)
            else:
                # Caso SENZA addon nativi
                simple_warning = addon.getLocalizedString(31235).format(
                    backup_info=compatibility.get('backup_info', 'Unknown'),
                    current_info=compatibility.get('current_info', 'Unknown')
                )
                
                choice = xbmcgui.Dialog().yesno(
                    addon.getLocalizedString(30928),
                    simple_warning + "\n\n" + addon.getLocalizedString(31030)
                )
                
                if not choice:
                    result = addon.getLocalizedString(31019)
                    xbmcgui.Dialog().notification("OptiKlean", addon.getLocalizedString(30218), logo_path, 3000)
                    return

        if has_databases:
            backup_kodi_version = backup_metadata.get("kodi_version", "Unknown")
            
            current_kodi_version = get_kodi_version()
            
            xbmc.log(f"OptiKlean: Backup Kodi version: {backup_kodi_version}, Current: {current_kodi_version}", xbmc.LOGINFO)
            
            if backup_kodi_version != "Unknown" and current_kodi_version != "Unknown":
                # Confronta solo la versione principale (es. "21" vs "20")
                try:
                    backup_major = backup_kodi_version.split('.')[0]
                    current_major = current_kodi_version.split('.')[0]
                    
                    if backup_major != current_major:
                        # Versioni principali diverse - blocca il restore dei database
                        warning_message = addon.getLocalizedString(31230).format(
                            backup_version=backup_kodi_version,
                            current_version=current_kodi_version
                        )
                        
                        xbmcgui.Dialog().ok(
                            addon.getLocalizedString(31231),  # "Database Version Incompatibility"
                            warning_message
                        )
                        
                        result = addon.getLocalizedString(31232)  # "Blocked - Incompatible Kodi versions for databases"
                        return
                except (ValueError, IndexError) as e:
                    xbmc.log(f"OptiKlean: Error parsing Kodi versions: {e}", xbmc.LOGWARNING)
        
        elif compatibility_status == "cross_platform_native":
            native_addons = compatibility.get("native_addons", [])
            
            # Verifica se ci sono effettivamente addon nativi nel backup
            if not native_addons:
                # Nessun addon nativo, procedi normalmente
                xbmc.log("OptiKlean: No native addons in backup, proceeding with restore", xbmc.LOGINFO)
            else:
                # Ci sono addon nativi - mostra dialog di warning con 4 opzioni
                dialog_message = addon.getLocalizedString(30939).format(
                    backup_info=compatibility.get('backup_info', 'Unknown'),
                    current_info=compatibility.get('current_info', 'Unknown')
                ) + "\n\n"
                
                # Aggiungi lista addon nativi
                for addon_name in native_addons:
                    dialog_message += f"• {addon_name}\n"
                
                dialog_message += "\n" + addon.getLocalizedString(30940).format(
                    reason=compatibility.get('reason', 'Cross-platform differences')
                )
                
                # Mostra textviewer prima del select per mostrare il messaggio completo
                xbmcgui.Dialog().textviewer(
                    addon.getLocalizedString(30943),  # Titolo
                    dialog_message
                )
                
                options = [
                    addon.getLocalizedString(30941),  # "Skip native addons"
                    addon.getLocalizedString(31246),  # "Skip and reinstall from repository"
                    addon.getLocalizedString(30942),  # "Restore all addons (may not work)"
                    addon.getLocalizedString(31019)   # "Cancel"
                ]
                
                choice = xbmcgui.Dialog().select(
                    addon.getLocalizedString(30943),  # Titolo
                    options
                )
                
                if choice == -1 or choice == 3:  # Cancel o chiusura dialog
                    result = addon.getLocalizedString(31019)
                    return
                elif choice == 0:  # Skip native addons
                    skip_native_addons = True
                    xbmc.log(f"OptiKlean: User chose to skip native addons: {native_addons}", xbmc.LOGINFO)
                elif choice == 1:  # Skip and reinstall from repo
                    skip_native_addons = True
                    reinstall_native_addons = True
                    native_addons_to_reinstall = native_addons.copy()
                    xbmc.log(f"OptiKlean: User chose to skip and reinstall native addons: {native_addons}", xbmc.LOGINFO)
                elif choice == 2:  # Restore all
                    skip_native_addons = False
                    xbmc.log("OptiKlean: User chose to restore all addons including native ones", xbmc.LOGINFO)
        else:
            skip_native_addons = False
            if compatibility_status == "cross_platform_safe":
                xbmc.log(f"OptiKlean: Cross-platform restore without native addons: {compatibility.get('reason', '')}", xbmc.LOGINFO)
            elif compatibility_status == "unknown":
                xbmc.log(f"OptiKlean: Unknown compatibility, proceeding: {compatibility.get('reason', '')}", xbmc.LOGINFO)
        
        # Controllo spazio
        destination_path = xbmcvfs.translatePath(HOME_SPECIAL_PATH)
        free_space = get_free_space_mb(destination_path)
        
        if free_space is None:
            free_space_text = "Unknown"
            confirmation_message = addon.getLocalizedString(30944).format(
                restore_type=restore_type,
                size=size_mb,
                free_space=free_space_text
            )
        else:
            if free_space >= 1024:
                free_space_text = f"{free_space / 1024:.1f} {addon.getLocalizedString(31016)}"
            else:
                free_space_text = f"{free_space:.1f} {addon.getLocalizedString(31014)}"
                
            confirmation_message = addon.getLocalizedString(30945).format(
                restore_type=restore_type,
                size=size_mb,
                free_space=free_space_text
            )
        
        if not xbmcgui.Dialog().yesno(addon.getLocalizedString(30946), confirmation_message):
            result = addon.getLocalizedString(31019)
            return
        
        # Ripristino
        progress = xbmcgui.DialogProgress()
        progress.create("OptiKlean", addon.getLocalizedString(30947))

        xbmc.log("OptiKlean: Preparing destination directories (removing read-only flags)", xbmc.LOGINFO)

        # Identifica le directory di destinazione principali basate sul contenuto del backup
        destination_dirs_to_prepare = []

        if has_addons:
            addons_base = xbmcvfs.translatePath(HOME_ADDONS_SPECIAL_PATH).replace('/', os.sep)
            destination_dirs_to_prepare.append(addons_base)
            
        if has_addon_data:
            addon_data_base = xbmcvfs.translatePath(PROFILE_ADDON_DATA_SPECIAL_PATH).replace('/', os.sep)
            destination_dirs_to_prepare.append(addon_data_base)
            
        if has_databases:
            db_base = xbmcvfs.translatePath(DATABASE_SPECIAL_PATH).replace('/', os.sep)
            destination_dirs_to_prepare.append(db_base)
            
        if has_keymaps:
            keymaps_base = xbmcvfs.translatePath(KEYMAPS_SPECIAL_PATH).replace('/', os.sep)
            destination_dirs_to_prepare.append(keymaps_base)

        # Rimuovi permessi sola lettura
        for dest_dir in destination_dirs_to_prepare:
            if os.path.exists(dest_dir):
                xbmc.log(f"OptiKlean: Removing read-only flags from {dest_dir}", xbmc.LOGINFO)
                remove_readonly_recursive(dest_dir)

        # Ora procedi con il restore normale
        # Approccio OpenWizard: estrazione diretta nella destinazione (più veloce e robusto)
        total_files = len(file_list)
        restored_count = 0
        failed_files = []
        
        # File di configurazione vanno in userdata (special://profile/)
        userdata_path = xbmcvfs.translatePath(PROFILE_SPECIAL_PATH)

        # FASE 2: Estrazione file - approccio diretto come OpenWizard
        with zipfile.ZipFile(temp_backup_local, 'r') as backup_zip:
            def resolve_safe_target_base(zip_member_path):
                """Resolve allowed extraction base and reject suspicious archive paths."""
                normalized = zip_member_path.replace('\\', '/')
                if normalized.startswith('/'):
                    return None, None

                parts = [p for p in normalized.split('/') if p not in ('', '.')]
                if any(p == '..' for p in parts):
                    return None, None

                if normalized.startswith(ADDONS_ARCHIVE_PREFIX):
                    return xbmcvfs.translatePath(HOME_SPECIAL_PATH), normalized
                if normalized.startswith('addon_data/'):
                    return xbmcvfs.translatePath(PROFILE_SPECIAL_PATH), normalized
                if normalized.startswith('Database/'):
                    return xbmcvfs.translatePath(PROFILE_SPECIAL_PATH), normalized
                if normalized.startswith('keymaps/'):
                    return xbmcvfs.translatePath(USERDATA_SPECIAL_PATH), normalized
                if normalized in [SOURCES_FILE, GUI_SETTINGS_FILE, PROFILES_FILE, ADVANCED_SETTINGS_FILE, PASSWORDS_FILE]:
                    return userdata_path, normalized

                return None, None

            for i, item in enumerate(backup_zip.infolist()):
                file_path = item.filename
                
                # Controlla cancellazione ogni 10 file per performance
                if i % 10 == 0 and progress.iscanceled():
                    result = addon.getLocalizedString(31019)
                    break
                
                # Skip marker file
                if file_path == BACKUP_MARKER_FILE:
                    continue
                
                # Skip directory entries (terminano con /)
                if file_path.endswith('/'):
                    continue
                
                # Skip native addons se richiesto
                if skip_native_addons and file_path.startswith(ADDONS_ARCHIVE_PREFIX):
                    addon_path_parts = file_path.split('/')
                    if len(addon_path_parts) > 1:
                        addon_id = addon_path_parts[1]
                        if addon_id in backup_metadata.get("native_addons", []):
                            xbmc.log(f"OptiKlean: Skipping native addon file: {file_path}", xbmc.LOGDEBUG)
                            continue
                
                progress.update(int((i / total_files) * 100), 
                    addon.getLocalizedString(30948).format(
                        current=i+1,
                        total=total_files,
                        filename=file_path.split('/')[-1]
                    )
                )
                
                try:
                    # Determina la directory di estrazione e valida il path interno dello zip
                    extract_base, safe_member = resolve_safe_target_base(file_path)
                    
                    if extract_base is None:
                        xbmc.log(f"OptiKlean: Skipping unsafe or unknown zip entry: {file_path}", xbmc.LOGWARNING)
                        continue

                    # Verifica finale: il target deve restare sotto la base consentita
                    base_norm = os.path.normpath(extract_base.replace('/', os.sep).replace('\\', os.sep))
                    target_path = os.path.normpath(os.path.join(base_norm, safe_member.replace('/', os.sep)))
                    if os.path.commonpath([base_norm, target_path]) != base_norm:
                        xbmc.log(f"OptiKlean: Path traversal blocked for zip entry: {file_path}", xbmc.LOGWARNING)
                        continue
                    
                    # Normalizza il percorso per il sistema operativo
                    extract_base_local = extract_base.replace('/', os.sep).replace('\\', os.sep)
                    
                    # Estrazione diretta nella destinazione finale
                    # zipfile.extract() sovrascrive automaticamente senza tentare DELETE prima
                    try:
                        backup_zip.extract(item, extract_base_local)
                        restored_count += 1
                        xbmc.log(f"OptiKlean: Extracted {file_path} to {extract_base_local}", xbmc.LOGDEBUG)
                            
                    except PermissionError as pe:
                        # File probabilmente lockato (ancora in uso da Kodi)
                        failed_files.append((file_path, f"Permission denied (file in use): {str(pe)}"))
                        xbmc.log(f"OptiKlean: Permission denied extracting {file_path}: {pe}", xbmc.LOGWARNING)
                    except Exception as extract_error:
                        failed_files.append((file_path, f"Extraction failed: {str(extract_error)}"))
                        xbmc.log(f"OptiKlean: Failed to extract {file_path}: {str(extract_error)}", xbmc.LOGWARNING)
                        
                except Exception as e:
                    failed_files.append((file_path, str(e)))
                    xbmc.log(f"OptiKlean: Error restoring file {file_path}: {str(e)}", xbmc.LOGWARNING)
                    continue
        
        progress.close()
        items_restored = restored_count
        
        if result != addon.getLocalizedString(31019):
            result = addon.getLocalizedString(31017)

            if failed_files:
                result = addon.getLocalizedString(31041).format(
                    items_restored=items_restored,
                    failed_count=len(failed_files)
                )
                
                notification_msg = addon.getLocalizedString(30950).format(
                    items=items_restored,
                    errors=len(failed_files),
                    size=size_mb
                )
                xbmcgui.Dialog().notification("OptiKlean", notification_msg, logo_path, 5000)
            else:
                notification_msg = addon.getLocalizedString(30949).format(
                    items=items_restored,
                    size=size_mb
                )
                xbmcgui.Dialog().notification("OptiKlean", notification_msg, logo_path, 5000)

            # Chiedi cancellazione backup
            backup_filename = backup_file_original.split('/')[-1] if backup_file_original != "—" else "—"
            safe_backup_display_name = str(backup_filename).replace('\x00', '').strip()[:255]

            if items_restored > 0 and xbmcgui.Dialog().yesno(
                addon.getLocalizedString(30951),
                addon.getLocalizedString(30952).format(filename=safe_backup_display_name)
            ):
                try:
                    xbmc.log(f"OptiKlean: Attempting to delete backup file: {backup_file_original}", xbmc.LOGDEBUG)
                    
                    if xbmcvfs.delete(backup_file_original):
                        if not xbmcvfs.exists(backup_file_original):
                            backup_file_deleted = True
                            xbmc.log("OptiKlean: Backup file successfully deleted", xbmc.LOGINFO)
                    
                    xbmcgui.Dialog().notification(
                        "OptiKlean", 
                        addon.getLocalizedString(30953).format(filename=safe_backup_display_name), 
                        logo_path, 
                        4000
                    )
                except Exception as e:
                    xbmc.log(f"OptiKlean: Error deleting backup file: {str(e)}", xbmc.LOGERROR)
                    
                    if result == addon.getLocalizedString(31017):
                        result = addon.getLocalizedString(31042).format(error=str(e))
                    
                    xbmcgui.Dialog().notification(
                        "OptiKlean", 
                        addon.getLocalizedString(30954).format(error=str(e)), 
                        xbmcgui.NOTIFICATION_ERROR, 
                        4000
                    )
                    
        # Gestione addon nativi saltati
        if skip_native_addons and backup_metadata.get("native_addons", []):
            skipped_addons = backup_metadata.get("native_addons", [])
            
            if reinstall_native_addons and native_addons_to_reinstall:
                # Reinstalla automaticamente gli addon nativi dal repository
                xbmc.log(f"OptiKlean: Starting automatic reinstallation of native addons: {native_addons_to_reinstall}", xbmc.LOGINFO)
                
                # Crea progress dialog per l'installazione
                install_progress = xbmcgui.DialogProgress()
                install_progress.create("OptiKlean", addon.getLocalizedString(31247))  # "Installing native addons..."
                
                def update_install_progress(percent, message):
                    """Aggiorna il progress e restituisce True se l'utente ha annullato"""
                    if install_progress.iscanceled():
                        return True  # Segnala cancellazione
                    install_progress.update(percent, message)
                    return False  # Continua normalmente
                
                # Installa gli addon
                install_results = install_native_addons_from_repo(
                    native_addons_to_reinstall,
                    progress_callback=update_install_progress
                )
                
                install_progress.close()
                
                # Mostra risultato installazione
                success_count = len(install_results['success'])
                failed_count = len(install_results['failed'])
                already_count = len(install_results['already_installed'])
                not_in_repo_count = len(install_results['not_in_repo'])
                total_failed = failed_count + not_in_repo_count
                
                result_message = addon.getLocalizedString(31248).format(
                    success=success_count,
                    failed=total_failed,
                    already=already_count
                ) + "\n\n"
                
                if install_results['success']:
                    result_message += addon.getLocalizedString(31249) + "\n"  # "Successfully installed:"
                    for addon_id in install_results['success']:
                        result_message += f"  [OK] {addon_id}\n"
                
                if install_results['already_installed']:
                    result_message += "\n" + addon.getLocalizedString(31250) + "\n"  # "Already installed:"
                    for addon_id in install_results['already_installed']:
                        result_message += f"  [-] {addon_id}\n"
                
                if install_results['not_in_repo']:
                    result_message += "\n" + addon.getLocalizedString(31255) + "\n"  # "Not available in repository:"
                    for addon_id in install_results['not_in_repo']:
                        result_message += f"  [X] {addon_id}\n"
                    result_message += addon.getLocalizedString(31256) + "\n"  # "These addons are not in the official Kodi repository"
                
                if install_results['failed']:
                    result_message += "\n" + addon.getLocalizedString(31251) + "\n"  # "Failed to install:"
                    for addon_id, reason in install_results['failed']:
                        if reason == "timeout":
                            result_message += f"  [X] {addon_id} ({addon.getLocalizedString(31257)})\n"  # "timeout"
                        elif reason == "cancelled":
                            result_message += f"  [X] {addon_id} ({addon.getLocalizedString(31259)})\n"  # "cancelled"
                        else:
                            result_message += f"  [X] {addon_id} ({reason})\n"
                    result_message += "\n" + addon.getLocalizedString(31252)  # "Failed addons may need manual installation"
                
                xbmcgui.Dialog().textviewer(
                    addon.getLocalizedString(31253),  # "Native Addon Installation Results"
                    result_message
                )
                
                # Salva i risultati per il log dettagliato
                native_install_results = install_results
                
                # Aggiungi info al log
                if install_results['success'] or total_failed > 0:
                    result += f" | {addon.getLocalizedString(31254).format(installed=success_count, failed=total_failed)}"
            else:
                # Mostra solo il messaggio di addon saltati (comportamento originale)
                skipped_message = addon.getLocalizedString(30955) + "\n"
                for addon_name in skipped_addons:
                    skipped_message += f"• {addon_name}\n"
                
                skipped_message += "\n" + addon.getLocalizedString(30956)
                xbmcgui.Dialog().ok(addon.getLocalizedString(30957), skipped_message)
        
        # Dialog riavvio Kodi (SEMPRE mostrato se items_restored > 0)
        if items_restored > 0 and xbmcgui.Dialog().yesno(addon.getLocalizedString(30959), addon.getLocalizedString(30958)):
            try:
                safe_backup_original = str(backup_file_original).replace('\x00', '').strip()[:500] if backup_file_original else "—"
                safe_restore_type = str(restore_type).replace('\x00', '').strip()[:100]
                safe_result = str(result).replace('\x00', '').strip()[:200]
                if backup_file_deleted:
                    safe_result += f" {addon.getLocalizedString(30996)}"
                log_content = (
                    f"{addon.getLocalizedString(30972):<17}: {safe_restore_type}\n"
                    f"{addon.getLocalizedString(30973):<17}: {safe_backup_display_name}\n"
                    f"{addon.getLocalizedString(30974):<17}: {safe_backup_original}\n"
                    f"{addon.getLocalizedString(30969):<17}: {size_mb} MB\n"
                    f"{addon.getLocalizedString(30975):<17}: {items_restored}\n"
                    f"{addon.getLocalizedString(30970):<17}: {safe_result}\n"
                )
                if failed_files:
                    log_content += f"\n{addon.getLocalizedString(30976).format(count=len(failed_files))}:\n"
                    for file_path, error in failed_files:
                        safe_file_path = str(file_path).replace('\x00', '').strip()[:200]
                        safe_error = str(error).replace('\x00', '').strip()[:300]
                        log_content += f"• {safe_file_path}: {safe_error}\n"
                # Aggiungi dettagli addon nativi reinstallati
                if native_install_results:
                    log_content += f"\n{addon.getLocalizedString(31258)}:\n"  # "Native addons reinstallation:"
                    if native_install_results['success']:
                        log_content += f"  {addon.getLocalizedString(31249)}\n"  # "Successfully installed:"
                        for addon_id in native_install_results['success']:
                            log_content += f"    [OK] {addon_id}\n"
                    if native_install_results['already_installed']:
                        log_content += f"  {addon.getLocalizedString(31250)}\n"  # "Already installed:"
                        for addon_id in native_install_results['already_installed']:
                            log_content += f"    [-] {addon_id}\n"
                    if native_install_results['not_in_repo']:
                        log_content += f"  {addon.getLocalizedString(31255)}\n"  # "Not available in repository:"
                        for addon_id in native_install_results['not_in_repo']:
                            log_content += f"    [X] {addon_id}\n"
                    if native_install_results['failed']:
                        log_content += f"  {addon.getLocalizedString(31251)}\n"  # "Failed to install:"
                        for addon_id, reason in native_install_results['failed']:
                            log_content += f"    [X] {addon_id} ({reason})\n"
                write_log_local("restore_backup", log_content)
                xbmc.log("OptiKlean: Log written before Kodi restart", xbmc.LOGINFO)
            except Exception as e:
                xbmc.log(f"OptiKlean: Error writing log before restart: {str(e)}", xbmc.LOGWARNING)
            _cleanup_temp_restore(addon_data_path)
            restarting_kodi = True
            xbmc.executebuiltin("RestartApp")
            return
        
    except zipfile.BadZipFile:
        result = addon.getLocalizedString(31027)
        xbmcgui.Dialog().notification("OptiKlean", addon.getLocalizedString(30960), xbmcgui.NOTIFICATION_ERROR, 3000)
        
    except Exception as e:
        error_msg = str(e)
        result = addon.getLocalizedString(31018) + ": " + error_msg
        
        xbmc.log(f"OptiKlean: Restore error: {error_msg}", xbmc.LOGERROR)
        
        if backup_file_deleted and ("No such file or directory" in error_msg or "Errno 2" in error_msg):
            result = addon.getLocalizedString(31017)
            xbmc.log("OptiKlean: Ignoring error as backup file was deleted by user", xbmc.LOGINFO)
        else:
            if not backup_file_deleted:
                xbmcgui.Dialog().notification("OptiKlean", addon.getLocalizedString(30962).format(error=error_msg), xbmcgui.NOTIFICATION_ERROR, 5000)
        
    finally:
        if restarting_kodi:
            xbmc.log("OptiKlean: Skipping cleanup - Kodi is restarting", xbmc.LOGINFO)
        else:
            # Pulizia temp restore
            _cleanup_temp_restore(addon_data_path)

            # Pulizia temp backup file
            if cleanup_temp_backup and temp_backup_file:
                try:
                    if temp_backup_file != backup_file_original and xbmcvfs.exists(temp_backup_file):
                        xbmcvfs.delete(temp_backup_file)
                        xbmc.log("OptiKlean: Cleaned up temporary backup file", xbmc.LOGINFO)
                except Exception as e:
                    xbmc.log(f"OptiKlean: Error cleaning temp backup: {str(e)}", xbmc.LOGWARNING)
            
            # Scrivi log finale
            try:
                safe_backup_original = str(backup_file_original).replace('\x00', '').strip()[:500] if backup_file_original else "—"
                safe_restore_type = str(restore_type).replace('\x00', '').strip()[:100]
                safe_result = str(result).replace('\x00', '').strip()[:200]
                
                if backup_file_deleted:
                    safe_result += f" {addon.getLocalizedString(30996)}"
                
                log_content = (
                    f"{addon.getLocalizedString(30972):<17}: {safe_restore_type}\n"
                    f"{addon.getLocalizedString(30973):<17}: {safe_backup_display_name}\n"
                    f"{addon.getLocalizedString(30974):<17}: {safe_backup_original}\n"
                    f"{addon.getLocalizedString(30969):<17}: {size_mb} MB\n"
                    f"{addon.getLocalizedString(30975):<17}: {items_restored}\n"
                    f"{addon.getLocalizedString(30970):<17}: {safe_result}\n"
                )
                
                if failed_files:
                    log_content += f"\n{addon.getLocalizedString(30976).format(count=len(failed_files))}:\n"
                    for file_path, error in failed_files:
                        log_content += f"• {file_path}: {error}\n"
                
                # Aggiungi dettagli addon nativi reinstallati
                if native_install_results:
                    log_content += f"\n{addon.getLocalizedString(31258)}:\n"  # "Native addons reinstallation:"
                    if native_install_results['success']:
                        log_content += f"  {addon.getLocalizedString(31249)}\n"  # "Successfully installed:"
                        for addon_id in native_install_results['success']:
                            log_content += f"    [OK] {addon_id}\n"
                    if native_install_results['already_installed']:
                        log_content += f"  {addon.getLocalizedString(31250)}\n"  # "Already installed:"
                        for addon_id in native_install_results['already_installed']:
                            log_content += f"    [-] {addon_id}\n"
                    if native_install_results['not_in_repo']:
                        log_content += f"  {addon.getLocalizedString(31255)}\n"  # "Not available in repository:"
                        for addon_id in native_install_results['not_in_repo']:
                            log_content += f"    [X] {addon_id}\n"
                    if native_install_results['failed']:
                        log_content += f"  {addon.getLocalizedString(31251)}\n"  # "Failed to install:"
                        for addon_id, reason in native_install_results['failed']:
                            log_content += f"    [X] {addon_id} ({reason})\n"
                
                write_log_local("restore_backup", log_content)
                xbmc.log("OptiKlean: Restore log written successfully", xbmc.LOGINFO)
            except Exception as e:
                xbmc.log(f"OptiKlean: Error writing restore log: {str(e)}", xbmc.LOGERROR)

def complete_pending_restore(addon_data_path):
    """
    Legacy function: cleans up any pending_db_restore folder from previous versions.
    Database files are now restored directly during the restore process.
    """
    # Normalize path for cross-platform compatibility
    addon_data_path_normalized = addon_data_path.replace('/', os.sep).replace('\\', os.sep)
    pending_db_path = os.path.join(addon_data_path_normalized, "pending_db_restore")
    
    if not os.path.exists(pending_db_path):
        return

    xbmc.log("OptiKlean: Found legacy pending_db_restore folder, cleaning up...", xbmc.LOGINFO)
    
    try:
        # Cleanup pending folder from previous versions
        shutil.rmtree(pending_db_path, ignore_errors=True)
        xbmc.log("OptiKlean: Legacy pending_db_restore folder cleaned up.", xbmc.LOGINFO)
    except Exception as e:
        xbmc.log(f"OptiKlean: Error cleaning up legacy pending_db_restore: {str(e)}", xbmc.LOGWARNING)
