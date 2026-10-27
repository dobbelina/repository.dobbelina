import os
import sys
import sqlite3
import xbmc
import xbmcaddon
import xbmcgui
from resources.lib.utils import TRANSLATEPATH, TEXTURESDB

def clear_cumination_image_cache():
    target_images = [
        "cum-cat.png", "cum-channels.png", "cum-downloads.png", "cum-fav.png",
        "cum-favorites.png", "cum-filters.png", "cum-followed.png", "cum-login.png",
        "cum-logout.png", "cum-models.png", "cum-movies.png", "cum-next.png",
        "cum-nophoto.png", "cum-player.png", "cum-refresh.png", "cum-search.png",
        "cum-sites.png", "cum-star.png", "cum-tags.png", "cum-topcams.png"
    ]
    
    video_addon = xbmcaddon.Addon('plugin.video.cumination')
    video_addon_path = TRANSLATEPATH(video_addon.getAddonInfo('path'))
    thumbnails_dir = TRANSLATEPATH('special://thumbnails')
    db_path = TEXTURESDB

    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cleared_count = 0
        
        for image_name in target_images:
            full_image_path = os.path.join(video_addon_path, "resources", "images", image_name)
            cursor.execute("SELECT url, cachedurl FROM texture WHERE url = ?;", (full_image_path,))
            rows = cursor.fetchall()
            
            for url, cached_filename in rows:
                # UNIVERSAL SAFE CAST: Forces variables to standard strings depending on Python version
                if sys.version_info[0] < 3:
                    cached_filename = str(cached_filename)
                    url = str(url)

                cached_file_path = os.path.join(thumbnails_dir, cached_filename)
                if os.path.exists(cached_file_path):
                    try:
                        os.remove(cached_file_path)
                    except Exception:
                        pass
                
                cursor.execute("DELETE FROM texture WHERE url = ?;", (url,))
                cleared_count += 1
                
        conn.commit()
        
        icon_path = TRANSLATEPATH(video_addon.getAddonInfo('icon'))
        xbmcgui.Dialog().notification(
            "Cumination Maintenance",
            "Images cleared from Cumination",
            icon_path,
            4000
        )
            
    except Exception as e:
        xbmc.log("[plugin.video.cumination] Cache clear error: " + str(e), xbmc.LOGERROR)
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    clear_cumination_image_cache()
