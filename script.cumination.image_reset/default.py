import glob
import os
import sqlite3
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs  # Added for modern path translations

def clear_cumination_image_cache():
    # 1. Target images list
    target_images = [
        "cum-cat.png", "cum-channels.png", "cum-downloads.png", "cum-fav.png",
        "cum-favorites.png", "cum-filters.png", "cum-followed.png", "cum-login.png",
        "cum-logout.png", "cum-models.png", "cum-movies.png", "cum-next.png",
        "cum-nophoto.png", "cum-player.png", "cum-refresh.png", "cum-search.png",
        "cum-sites.png", "cum-star.png", "cum-tags.png", "cum-topcams.png"
    ]
    
    # 2. Locate the video addon path (using modern xbmcvfs)
    video_addon_path = ""
    try:
        video_addon = xbmcaddon.Addon("plugin.video.cumination")
        video_addon_path = xbmcvfs.translatePath(video_addon.getAddonInfo('path'))
    except Exception:
        # Fallback: Manually build the path via Kodi's Virtual File System if the object call fails
        xbmc.log("[script.cumination.image_reset] Addon object initialization failed. Trying VFS fallback path.", xbmc.LOGDEBUG)
        fallback_path = xbmcvfs.translatePath("special://home/addons/plugin.video.cumination")
        if os.path.exists(fallback_path):
            video_addon_path = fallback_path

    if not video_addon_path:
        xbmcgui.Dialog().ok("Error", "Cumination Video Addon could not be found.")
        return

    # 3. Locate environment directories
    database_dir = xbmcvfs.translatePath('special://database')
    thumbnails_dir = xbmcvfs.translatePath('special://thumbnails')
    
    # 4. Find all Textures database versions and isolate the HIGHEST numbered one
    search_pattern = os.path.join(database_dir, 'Textures*.db')
    matching_databases = glob.glob(search_pattern)
    
    if not matching_databases:
        xbmcgui.Dialog().ok("Error", "Kodi Textures database not found.")
        return
        
    matching_databases.sort()
    db_path = matching_databases[-1] # Grabs the highest number (e.g. Textures14.db)
    xbmc.log(f"[script.cumination.image_reset] Target database established: {db_path}", xbmc.LOGINFO)

    # 5. Database execution and thumbnail clean up routine
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cleared_count = 0
        
        for image_name in target_images:
            # Recreates the exact target path: ...\plugin.video.cumination\resources\images\filename.png
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
        
        # 6. Fire off the upper corner toast completion notification
        script_addon = xbmcaddon.Addon()
        icon_path = xbmcvfs.translatePath(script_addon.getAddonInfo('icon'))
        
        xbmcgui.Dialog().notification(
            "Cumination Maintenance",
            "Images cleared from Cumination",
            icon_path,
            4000
        )
            
    except Exception as e:
        xbmcgui.Dialog().ok("Error", f"Failed to reset cache:\n{str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    clear_cumination_image_cache()
