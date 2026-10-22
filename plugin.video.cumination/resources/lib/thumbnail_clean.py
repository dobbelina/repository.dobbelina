import glob
import os
import sqlite3
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

def clear_cumination_image_cache():
    target_images = [
        "cum-cat.png", "cum-channels.png", "cum-downloads.png", "cum-fav.png",
        "cum-favorites.png", "cum-filters.png", "cum-followed.png", "cum-login.png",
        "cum-logout.png", "cum-models.png", "cum-movies.png", "cum-next.png",
        "cum-nophoto.png", "cum-player.png", "cum-refresh.png", "cum-search.png",
        "cum-sites.png", "cum-star.png", "cum-tags.png", "cum-topcams.png"
    ]
    
    # Dynamically find the main addon path by stepping up from resources/lib/
    # This ensures perfect compatibility with your Kodi 21 Portable layout
    current_dir = os.path.dirname(__file__)  # resources/lib
    resources_dir = os.path.dirname(current_dir)  # resources
    video_addon_path = os.path.dirname(resources_dir)  # plugin.video.cumination root

    database_dir = xbmcvfs.translatePath('special://database')
    thumbnails_dir = xbmcvfs.translatePath('special://thumbnails')
    
    # Find all Textures database versions and isolate the HIGHEST numbered one
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
        
        # Fire off the upper corner toast completion notification
        video_addon = xbmcaddon.Addon('plugin.video.cumination')
        icon_path = xbmcvfs.translatePath(video_addon.getAddonInfo('icon'))
        
        xbmcgui.Dialog().notification(
            "Cumination Maintenance",
            "Thumbnails cleared from Cumination",
            icon_path,
            4000
        )
            
    except Exception as e:
        xbmc.log(f"[plugin.video.cumination] Cache clear error: {str(e)}", xbmc.LOGERROR)
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    clear_cumination_image_cache()
