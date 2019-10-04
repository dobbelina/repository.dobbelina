'''
    Ultimate Whitecream
    Copyright (C) 2015 Whitecream

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import sqlite3

import xbmc
import xbmcplugin
from resources.lib import utils
from sites.chaturbate import clean_database as cleanchat
from sites.cam4 import clean_database as cleancam4
from sites.camsoda import clean_database as cleansoda
from sites.naked import clean_database as cleannaked


dialog = utils.dialog
favoritesdb = utils.favoritesdb


conn = sqlite3.connect(favoritesdb)
c = conn.cursor()
try:
    c.executescript("CREATE TABLE IF NOT EXISTS favorites (name, url, mode, image);")
    c.executescript("CREATE TABLE IF NOT EXISTS keywords (keyword);")
except:
    pass
conn.close()


@utils.url_dispatcher.register('901')  
def List():
    if utils.addon.getSetting("chaturbate") == "true":
        cleanchat(False)
        cleancam4(False)
        cleansoda(False)
        cleannaked(False)
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM favorites")
        for (name, url, mode, img) in c.fetchall():
            utils.addDownLink(name, url, int(mode), img, '', '', 'del')
        conn.close()
        xbmcplugin.endOfDirectory(utils.addon_handle)
    except:
        conn.close()
        utils.notify('No Favorites','No Favorites found')
        return


@utils.url_dispatcher.register('900', ['fav','favmode','name','url','img'])  
def Favorites(fav, favmode, name, url, img):
    if fav == "add":
        existing_favorite = select_favorite(url)
        if existing_favorite:
            if existing_favorite[0] == name and existing_favorite[3] == img and existing_favorite[2] == favmode:
                utils.notify('Favorite already exists', 'Video already in favorites')
            else:
                if existing_favorite[2] != favmode:
                    question = 'it'
                if existing_favorite[0] != name:
                    question = 'its name'
                if existing_favorite[3] != img:
                    question = 'its picture'
                if existing_favorite[0] != name and existing_favorite[3] != img:
                    question = 'its name and picture'
                if utils.dialog.yesno('Video already in favorites','This video is already in the favorites with the title', existing_favorite[0], 'Update {}?'.format(question)):
                    update_favorite(favmode, name, url, img)
                    utils.notify('Favorite updated', 'Video updated')
        else:
            addFav(favmode, name, url, img)
            utils.notify('Favorite added', 'Video added to the favorites')
    elif fav == "del":
        delFav(url)
        utils.notify('Favorite deleted', 'Video removed from the list')
        xbmc.executebuiltin('Container.Refresh')
    elif fav == "move_to_end":
        move_fav_to_end(url)
        utils.notify('Favorite moved', 'Video moved to end of the list')
        xbmc.executebuiltin('Container.Refresh')


def select_favorite(url):
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("SELECT * FROM favorites WHERE url = ?", (url,))
    row = c.fetchone()
    conn.close()
    return row


def update_favorite(mode, name, url, img):
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("UPDATE favorites set name = ?, image = ?, mode = ? where url = ?", (name, img, mode, url))
    conn.commit()
    conn.close()


def addFav(mode, name, url, img):
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("INSERT INTO favorites VALUES (?,?,?,?)", (name, url, mode, img))
    conn.commit()
    conn.close()


def delFav(url):
    conn = sqlite3.connect(favoritesdb)
    c = conn.cursor()
    c.execute("DELETE FROM favorites WHERE url = ?", (url,))
    conn.commit()
    conn.close()


def delete_duplicates():
    conn = sqlite3.connect(favoritesdb)
    c = conn.cursor()
    c.execute("DELETE FROM favorites " +
              "WHERE rowid NOT IN " +
              "(SELECT MIN(rowid) as rowid FROM favorites GROUP BY url)")
    conn.commit()
    conn.close()


def move_fav_to_end(url):
    delete_duplicates()
    conn = sqlite3.connect(favoritesdb)
    c = conn.cursor()
    c.execute("UPDATE favorites SET rowid = (SELECT MAX(rowid) FROM favorites) + 1 WHERE url = ?", (url,))
    conn.commit()
    conn.close()

@utils.url_dispatcher.register('912')
def clear_fav():
    if not utils.dialog.yesno('Warning','This will delete all your favorites', 'Continue?', nolabel='No', yeslabel='Yes'):
        return
    conn = sqlite3.connect(favoritesdb)
    c = conn.cursor()
    c.execute("DELETE FROM favorites")
    conn.commit()
    conn.close()
    xbmc.executebuiltin('Container.Refresh')
    utils.notify("Favorites deleted", "")


@utils.url_dispatcher.register('910')
def backup_fav():
    path = utils.xbmcgui.Dialog().browseSingle(0, 'Select directory to place backup' ,'myprograms')
    progress = utils.progress
    progress.create('Backing up', 'Initializing')
    if not path:
        return
    import json
    import gzip
    import datetime
    progress.update(25, "Reading database")
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("SELECT * FROM favorites")
    favorites = [{"name": name, "url": url, "mode": mode, "img": img} for (name, url, mode, img) in c.fetchall()]
    if not favorites:
        progress.close()
        utils.notify("Favorites empty", "No favorites to back up")
        return
    conn.close()
    time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_content = {"meta": {"type": "uwc-favorites", "version": 1, "datetime": time}, "data": favorites}
    if progress.iscanceled():
        progress.close()
        return
    progress.update(75, "Writing backup file")
    filename = "uwc-favorites_" + time + '.bak'
    try:
        with gzip.open(path + filename, "wb") as fav_file:
            json.dump(backup_content, fav_file)
    except IOError:
        progress.close()
        utils.notify("Error: invalid path", "Do you have permission to write to the selected folder?")
        return
    progress.close()
    utils.dialog.ok("Backup complete", "Backup file: {}".format(path + filename))


@utils.url_dispatcher.register('911')
def restore_fav():
    path = utils.dialog.browseSingle(1, 'Select backup file' ,'myprograms')
    if not path:
        return
    import json
    import gzip
    try:
        with gzip.open(path, "rb") as fav_file:
            backup_content = json.load(fav_file)
    except (ValueError, IOError):
        utils.notify("Error", "Invalid backup file")
        return
    if not backup_content["meta"]["type"] == "uwc-favorites":
        utils.notify("Error", "Invalid backup file")
        return
    favorites = backup_content["data"]
    if not favorites:
        utils.notify("Error", "Empty backup")
    added = 0
    skipped = 0
    for favorite in favorites:
        if select_favorite(favorite["url"]):
            skipped += 1
        else:
            addFav(favorite["mode"], favorite["name"], favorite["url"], favorite["img"])
            added += 1
    xbmc.executebuiltin('Container.Refresh')
    utils.dialog.ok("Restore complete", "Restore skips items that are already present in favorites to avoid duplicates", "Added: {}".format(added), "Skipped: {}".format(skipped))
