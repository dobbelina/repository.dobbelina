import os
import sqlite3
import xbmc
import xbmcaddon
import xbmcgui
from utils import TRANSLATEPATH, TEXTURESDB


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
        xbmc.log(f"[plugin.video.cumination] Cache clear error: {str(e)}", xbmc.LOGERROR)
    finally:
        if conn:
            conn.close()


if __name__ == '__main__':
    clear_cumination_image_cache()
