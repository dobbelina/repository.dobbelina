import glob
import os
import sqlite3
import xbmc
import xbmcaddon
import xbmcgui

# Universal path translator fallback logic
# This checks for both missing modules and missing functions across ALL Kodi versions
try:
    import xbmcvfs
    if hasattr(xbmcvfs, 'translatePath'):
        TRANSLATEPATH = xbmcvfs.translatePath
    else:
        TRANSLATEPATH = xbmc.translatePath
except (ImportError, AttributeError):
    # Safe fallback for legacy Python 2 / Kodi 18 platforms
    TRANSLATEPATH = xbmc.translatePath

def clear_cumination_image_cache():
    target_images = [
        "cum-cat.png", "cum-channels.png", "cum-downloads.png", "cum-fav.png",
        "cum-favorites.png", "cum-filters.png", "cum-followed.png", "cum-login.png",
        "cum-logout.png", "cum-models.png", "cum-movies.png", "cum-next.png",
        "cum-nophoto.png", "cum-player.png", "cum-refresh.png", "cum-search.png",
        "cum-sites.png", "cum-star.png", "cum-tags.png", "cum-topcams.png"
    ]
    
    # 2. Get the active add-on path dynamically
    video_addon = xbmcaddon.Addon('plugin.video.cumination')
    video_addon_path = TRANSLATEPATH(video_addon.getAddonInfo('path'))

    # 3. Locate environment directories universally
    database_dir = TRANSLATEPATH('special://database')
    thumbnails_dir = TRANSLATEPATH('special://thumbnails')
    
    # 4. Find all Textures database versions and isolate the HIGHEST numbered one
    search_pattern = os.path.join(database_dir, 'Textures*.db')
    matching_databases = glob.glob(search_pattern)
    
    if not matching_databases:
        return
        
    matching_databases.sort()
    db_path = matching_databases[-1] # Grabs the highest version (e.g. Textures14.db)

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cleared_count = 0
        
        for image_name in target_images:
            # Recreates your exact path down to the resources subfolder
            full_image_path = os.path.join(video_addon_path, "resources", "images", image_name)
            
            # Query the database mapping row
            cursor.execute("SELECT url, cachedurl FROM texture WHERE url = ?;", (full_image_path,))
            rows = cursor.fetchall()
            
            for url, cached_filename in rows:
                cached_file_path = os.path.join(thumbnails_dir, cached_filename)
                
                # Delete physical cache file if it exists
                if os.path.exists(cached_file_path):
                    try:
                        os.remove(cached_file_path)
                    except Exception:
                        pass
                
                # Wipe the database row tracking it
                cursor.execute("DELETE FROM texture WHERE url = ?;", (url,))
                cleared_count += 1
                
        conn.commit()
        
        # 5. Fire off the upper corner toast completion notification
        icon_path = TRANSLATEPATH(video_addon.getAddonInfo('icon'))
        
        xbmcgui.Dialog().notification(
            "Cumination Maintenance",
            "Images cleared from Cumination",
            icon_path,
            4000
        )
            
    except Exception as e:
        # FIXED: Removed the f-string syntax to make it completely safe for Python 2 (Kodi 18.9)
        xbmc.log("[plugin.video.cumination] Cache clear error: " + str(e), xbmc.LOGERROR)
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    clear_cumination_image_cache()
