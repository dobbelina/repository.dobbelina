'''
    Cumination
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
import datetime
import os
import re

import xbmc
import six
from resources.lib import basics
from resources.lib import utils
from resources.lib.url_dispatcher import URL_Dispatcher
from resources.lib.adultsite import AdultSite

url_dispatcher = URL_Dispatcher('favorites')

dialog = utils.dialog
favoritesdb = basics.favoritesdb
orders = {'random': 'RANDOM()', 'date added': 'ROWID DESC', 'name': 'NAME COLLATE NOCASE', 'site & date': 'MODE, ROWID DESC', 'site & name': 'MODE, NAME COLLATE NOCASE', 'site & date, in folders': 'MODE, ROWID DESC', 'site & name, in folders': 'MODE, NAME COLLATE NOCASE'}

conn = sqlite3.connect(favoritesdb)
c = conn.cursor()
try:
    c.executescript("CREATE TABLE IF NOT EXISTS favorites (name, url, mode, image, duration, quality);")
    c.executescript("CREATE TABLE IF NOT EXISTS keywords (keyword);")
    c.executescript("CREATE TABLE IF NOT EXISTS custom_sites (author, name, title, url, image, about, version, installed_at, enabled, module_file);")
    c.executescript("CREATE TABLE IF NOT EXISTS custom_lists (name);")
    c.executescript("CREATE TABLE IF NOT EXISTS custom_listitems (name, url, mode, image, list_id);")

    c.execute('PRAGMA table_info(favorites);')
    res = c.fetchall()
    if len(res) == 4:
        addColumn = "ALTER TABLE favorites ADD COLUMN duration"
        c.execute(addColumn)
        addColumn = "ALTER TABLE favorites ADD COLUMN quality"
        c.execute(addColumn)
except:
    pass
conn.close()


@url_dispatcher.register()
def Refresh_images():
    utils.clear_cache()

    connfav = sqlite3.connect(favoritesdb)
    connfav.text_factory = str
    conn = sqlite3.connect(utils.TRANSLATEPATH("special://database/Textures13.db"))
    c = connfav.cursor()
    c.execute('SELECT * FROM favorites')
    for (name, url, mode, img, duration, quality) in c.fetchall():
        try:
            with conn:
                list = conn.execute("SELECT id, cachedurl FROM texture WHERE url = '{}';".format(img))
                for row in list:
                    conn.execute("DELETE FROM sizes WHERE idtexture LIKE '%s';" % row[0])
                    try:
                        os.remove(utils.TRANSLATEPATH("special://thumbnails/" + row[1]))
                    except:
                        pass
                conn.execute("DELETE FROM texture WHERE url LIKE '%%%s%%';" % ".highwebmedia.com")
        except:
            pass
    xbmc.executebuiltin('Container.Refresh')


@url_dispatcher.register()
def List():
    basics.addDir('[COLOR red]Refresh images[/COLOR]', '', 'favorites.Refresh_images', '', Folder=False)
    favorder = utils.addon.getSetting("favorder") or 'date added'
    basics.addDir('[COLOR violet]Sort by: [/COLOR] [COLOR orange]{0}[/COLOR]'.format(favorder), '', 'favorites.Favorder', '', Folder=False)
    if utils.addon.getSetting("chaturbate") == "true":
        for f in AdultSite.clean_functions:
            f(False)
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    try:
        if 'folders' in favorder:
            if basics.addon.getSetting('custom_sites') == 'true':
                sql = "SELECT f.mode, COUNT(*) count FROM favorites f WHERE substr(f.mode, 1, instr(f.mode, '.') - 1) NOT IN (SELECT 'custom_' || cs.name || '_by_' || cs.author FROM custom_sites cs WHERE IFNULL(cs.enabled, 1) != 1) GROUP BY 1 ORDER BY 1"
            else:
                sql = "SELECT f.mode, COUNT(*) count FROM favorites f WHERE mode NOT LIKE 'custom_%' GROUP BY 1 ORDER BY 1"
            c.execute(sql)
            for (mode, count) in c.fetchall():
                site = mode.split('.')[0]
                img = ''
                removed = True
                for s in AdultSite.get_sites():
                    if s.name == site:
                        name = s.title
                        img = s.image
                        removed = False
                        break
                if removed:
                    name = site + ' [COLOR blue](removed)[/COLOR]'
                name = '{} [COLOR thistle][{} favorites][/COLOR]'.format(name, count)
                basics.addDir(name, mode, 'favorites.FavListSite', img)
        else:
            if basics.addon.getSetting('custom_sites') == 'true':
                sql = "SELECT * FROM favorites f WHERE substr(f.mode, 1, instr(f.mode, '.') - 1) NOT IN (SELECT 'custom_' || cs.name || '_by_' || cs.author FROM custom_sites cs WHERE IFNULL(cs.enabled, 1) != 1) ORDER BY {}".format(orders[favorder])
            else:
                sql = "SELECT * FROM favorites f WHERE mode NOT LIKE 'custom_%' ORDER BY {}".format(orders[favorder])
            c.execute(sql)
            for (name, url, mode, img, duration, quality) in c.fetchall():
                duration = '' if duration is None else duration
                quality = '' if quality is None else quality
                if 'site' in favorder:
                    site = mode.split('.')[0]
                    removed = True
                    for s in AdultSite.get_sites():
                        if s.name == site:
                            site = s.title
                            removed = False
                            break
                    if removed:
                        site = site + ' [COLOR blue](removed)[/COLOR]'
                    name = '[COLOR hotpink][{}][/COLOR] {}'.format(site, name)
                basics.addDownLink(name, url, mode, img, desc='', stream='', fav='del', duration=duration, quality=quality)
        conn.close()
        utils.eod(utils.addon_handle)
    except:
        conn.close()
        utils.notify('No Favorites', 'No Favorites found')
        return


@url_dispatcher.register()
def FavListSite(url):
    favorder = utils.addon.getSetting("favorder") or 'date added'
    if utils.addon.getSetting("chaturbate") == "true":
        for f in AdultSite.clean_functions:
            f(False)
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM favorites WHERE mode = '{}' ORDER BY {}".format(url, orders[favorder]))
        for (name, url, mode, img, duration, quality) in c.fetchall():
            duration = '' if duration is None else duration
            quality = '' if quality is None else quality
            basics.addDownLink(name, url, mode, img, desc='', stream='', fav='del', duration=duration, quality=quality)
        conn.close()
        utils.eod(utils.addon_handle)
    except:
        conn.close()
        utils.notify('No Favorites', 'No Favorites found')
        return


@url_dispatcher.register()
def Favorder():
    input = utils.selector('Select sort order by', orders.keys())
    if input:
        favorder = input
        utils.addon.setSetting('favorder', favorder)
        xbmc.executebuiltin('Container.Refresh')


@url_dispatcher.register()
def Favorites(fav, favmode, name, url, img, duration='', quality=''):
    if fav == "add":
        existing_favorite = select_favorite(url)
        if existing_favorite:
            if existing_favorite[0] == name and existing_favorite[3] == img and existing_favorite[2] == favmode and existing_favorite[4] == duration and existing_favorite[5] == quality:
                utils.notify('Favorite already exists', 'Video already in favorites')
            else:
                question = 'it'
                if existing_favorite[2] != favmode:
                    question = 'it'
                if existing_favorite[0] != name:
                    question = 'its name'
                if existing_favorite[3] != img:
                    question = 'its picture'
                if existing_favorite[0] != name and existing_favorite[3] != img:
                    question = 'its name and picture'
                if utils.dialog.yesno('Video already in favorites',
                                      'This video is already in the favorites with the title[CR]'
                                      '{0}[CR]Update {1}?'.format(existing_favorite[0], question)):
                    update_favorite(favmode, name, url, img, duration, quality)
                    utils.notify('Favorite updated', 'Video updated')
        else:
            addFav(favmode, name, url, img, duration, quality)
            utils.notify('Favorite added', 'Video added to the favorites')
        return
    elif fav == "del":
        delFav(url)
        utils.notify('Favorite deleted', 'Video removed from the list')
    elif fav == "move_to_top":
        move_fav_to_top(url)
        utils.notify('Favorite moved', 'Video moved to top of the list')
    elif fav == "move_down":
        move_fav_down(url)
        utils.notify('Favorite moved', 'Video moved down')
    elif fav == "move_up":
        move_fav_up(url)
        utils.notify('Favorite moved', 'Video moved up')
    elif fav == "move_to_bottom":
        move_fav_to_bottom(url)
        utils.notify('Favorite moved', 'Video moved to the bottom of the list')
    xbmc.executebuiltin('Container.Refresh')


def select_favorite(url):
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("SELECT * FROM favorites WHERE url = ?", (url,))
    row = c.fetchone()
    conn.close()
    return row


def update_favorite(mode, name, url, img, duration, quality):
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("UPDATE favorites set name = ?, image = ?, mode = ?, duration = ?, quality = ? where url = ?", (name, img, mode, duration, quality, url))
    conn.commit()
    conn.close()


def addFav(mode, name, url, img, duration, quality):
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("INSERT INTO favorites VALUES (?,?,?,?,?,?)", (name, url, mode, img, duration, quality))
    conn.commit()
    conn.close()


def delFav(url):
    conn = sqlite3.connect(favoritesdb)
    c = conn.cursor()
    conn.text_factory = str
    c.execute("DELETE FROM favorites WHERE url = ?", (url,))
    conn.commit()
    conn.close()


def delete_duplicates():
    conn = sqlite3.connect(favoritesdb)
    c = conn.cursor()
    c.execute("DELETE FROM favorites "
              + "WHERE rowid NOT IN "
              + "(SELECT MIN(rowid) as rowid FROM favorites GROUP BY url)")
    conn.commit()
    conn.close()


def move_fav_to_top(url):
    delete_duplicates()
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("UPDATE favorites SET rowid = (SELECT MAX(rowid) FROM favorites) + 1 WHERE url = ?", (url,))
    conn.commit()
    conn.close()


def move_fav_down(url):
    delete_duplicates()
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    sql = '''DROP TABLE IF EXISTS tmp;
CREATE TEMP TABLE tmp AS
SELECT name,
(SELECT max(ROWID)+1 from favorites) tmp_id,
cli.ROWID id,
coalesce((SELECT max(ROWID) from favorites WHERE ROWID<cli.ROWID), cli.ROWID) prev_id,
coalesce((SELECT min(ROWID) from favorites WHERE ROWID>cli.ROWID), cli.ROWID) next_id
FROM favorites cli
WHERE cli.ROWID = (select ROWID from favorites WHERE url = "{}");
update favorites set ROWID = (SELECT tmp_id FROM tmp) WHERE ROWID = (SELECT prev_id FROM tmp);
update favorites set ROWID = (SELECT prev_id FROM tmp) WHERE ROWID = (SELECT id FROM tmp);
update favorites set ROWID = (SELECT id FROM tmp) WHERE ROWID = (SELECT tmp_id FROM tmp);
DROP TABLE IF EXISTS tmp;'''.format(url)
    c.executescript(sql)
    conn.commit()
    conn.close()
    xbmc.executebuiltin('Container.Refresh')


def move_fav_up(url):
    delete_duplicates()
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    sql = '''DROP TABLE IF EXISTS tmp;
CREATE TEMP TABLE tmp AS
SELECT name,
(SELECT max(ROWID)+1 from favorites) tmp_id,
cli.ROWID id,
coalesce((SELECT max(ROWID) from favorites WHERE ROWID<cli.ROWID), cli.ROWID) prev_id,
coalesce((SELECT min(ROWID) from favorites WHERE ROWID>cli.ROWID), cli.ROWID) next_id
FROM favorites cli
WHERE cli.ROWID = (select ROWID from favorites WHERE url = "{}");
update favorites set ROWID = (SELECT tmp_id FROM tmp) WHERE ROWID = (SELECT next_id FROM tmp);
update favorites set ROWID = (SELECT next_id FROM tmp) WHERE ROWID = (SELECT id FROM tmp);
update favorites set ROWID = (SELECT id FROM tmp) WHERE ROWID = (SELECT tmp_id FROM tmp);
DROP TABLE IF EXISTS tmp;'''.format(url)
    c.executescript(sql)
    conn.commit()
    conn.close()
    xbmc.executebuiltin('Container.Refresh')


def move_fav_to_bottom(url):
    delete_duplicates()
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("UPDATE favorites SET rowid = (SELECT MIN(rowid) FROM favorites) - 1 WHERE url = ?", (url,))
    conn.commit()
    conn.close()


@url_dispatcher.register()
def clear_fav():
    if not utils.dialog.yesno('Warning', 'This will delete all your favorites[CR]Continue?',
                              nolabel='No', yeslabel='Yes'):
        return
    conn = sqlite3.connect(favoritesdb)
    c = conn.cursor()
    c.execute("DELETE FROM favorites")
    conn.commit()
    conn.close()
    xbmc.executebuiltin('Container.Refresh')
    utils.notify("Favorites deleted", "")


@url_dispatcher.register()
def backup_fav():
    path = utils.xbmcgui.Dialog().browseSingle(0, 'Select directory to place backup', 'myprograms')
    progress = utils.progress
    progress.create('Backing up', 'Initializing')
    if not path:
        return
    import json
    import datetime
    progress.update(25, "Reading database")
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("SELECT * FROM favorites")
    favorites = [{"name": name, "url": url, "mode": mode, "img": img, "duration": duration, "quality": quality} for (name, url, mode, img, duration, quality) in c.fetchall()]
    if not favorites:
        progress.close()
        utils.notify("Favorites empty", "No favorites to back up")
        return
    conn.close()
    time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_content = {"meta": {"type": "cumination-favorites", "version": 1, "datetime": time}, "data": favorites}
    if progress.iscanceled():
        progress.close()
        return
    progress.update(75, "Writing backup file")
    filename = "cumination-favorites_" + time + '.bak'
    compressbackup = True if utils.addon.getSetting("compressbackup") == "true" else False
    if compressbackup:
        import gzip
        try:
            if utils.PY3:
                with gzip.open(path + filename, "wt", encoding="utf-8") as fav_file:
                    json.dump(backup_content, fav_file)
            else:
                with gzip.open(path + filename, "wb") as fav_file:
                    json.dump(backup_content, fav_file)
        except IOError:
            progress.close()
            utils.notify("Error: invalid path", "Do you have permission to write to the selected folder?")
            return
    else:
        try:
            if utils.PY3:
                with open(path + filename, "wt", encoding="utf-8") as fav_file:
                    json.dump(backup_content, fav_file)
            else:
                with open(path + filename, "wb") as fav_file:
                    json.dump(backup_content, fav_file)
        except IOError:
            progress.close()
            utils.notify("Error: invalid path", "Do you have permission to write to the selected folder?")
            return
    progress.close()
    utils.dialog.ok("Backup complete", "Backup file: {}".format(path + filename))


@url_dispatcher.register()
def restore_fav():
    path = utils.dialog.browseSingle(1, 'Select backup file', 'myprograms')
    if not path:
        return
    import json
    compressbackup = True if utils.addon.getSetting("compressbackup") == "true" else False
    if compressbackup:
        import gzip
        try:
            if utils.PY3:
                with gzip.open(path, "rt", encoding="utf-8") as fav_file:
                    backup_content = json.load(fav_file)
            else:
                with gzip.open(path, "rb") as fav_file:
                    backup_content = json.load(fav_file)
        except (ValueError, IOError):
            utils.notify("Error", "Invalid backup file")
            return
    else:
        try:
            if utils.PY3:
                with open(path, "rt", encoding="utf-8") as fav_file:
                    backup_content = json.load(fav_file)
            else:
                with open(path, "rb") as fav_file:
                    backup_content = json.load(fav_file)
        except (ValueError, IOError):
            utils.notify("Error", "Invalid backup file")
            return
    if not backup_content["meta"]["type"] == "cumination-favorites":
        if backup_content["meta"]["type"] == "uwc-favorites":
            from resources.lib.convertfav import convertfav
            backup_content = convertfav(backup_content)
        else:
            utils.notify("Error", "Invalid backup file")
            return
    favorites = backup_content["data"]
    if not favorites:
        utils.notify("Error", "Empty backup")
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("select 'custom_' || name || '_by_' || author from custom_sites")
    custom_sites = [cs[0] for cs in c.fetchall()]
    conn.close()
    added = 0
    skipped = 0
    for favorite in favorites:
        if select_favorite(favorite["url"]):
            u = favorite["url"] if six.PY3 else favorite["url"].encode('utf8')
            utils.kodilog('{} is already in favorites, skipping'.format(u))
            skipped += 1
        elif favorite["mode"].startswith('custom_') and favorite["mode"].split('.')[0] not in custom_sites:
            utils.kodilog('{} is not installed, skipping'.format(favorite["mode"].split('.')[0]))
            skipped += 1
        else:
            duration = favorite["duration"] if "duration" in favorite.keys() else ""
            quality = favorite["quality"] if "quality" in favorite.keys() else ""
            addFav(favorite["mode"], favorite["name"], favorite["url"], favorite["img"], duration, quality)
            added += 1
    xbmc.executebuiltin('Container.Refresh')
    utils.dialog.ok("Restore complete",
                    "Restore skips items that are already present in favorites to avoid duplicates[CR]"
                    "and favorites from not installed custom sites[CR]"
                    "Added: {0}[CR]Skipped: {1}".format(added, skipped))


@url_dispatcher.register()
def install_custom_site():
    if not utils.dialog.yesno('WARNING',
                              'Custom sites are not verified by Cumination, and could contain malware.[CR]'
                              'Cumination is not responsible for custom sites. Proceed?'):
        return
    path = utils.dialog.browseSingle(1, 'Select Cumination custom site file', 'myprograms')
    if not path:
        return
    success = process_custom_site_zip(path)
    if not success:
        utils.notify('Error', 'Installation cancelled or invalid file')
    else:
        conn = sqlite3.connect(favoritesdb)
        conn.text_factory = str
        c = conn.cursor()
        c.execute("SELECT title FROM custom_sites ORDER BY ROWID DESC LIMIT 1")
        title = c.fetchone()[0]
        conn.close()
        xbmc.executebuiltin('Container.Refresh')
        utils.notify("{}".format(title), "Site installed")


@url_dispatcher.register()
def install_custom_sites_from_folder():
    if not utils.dialog.yesno('WARNING',
                              'Custom sites are not verified by Cumination, and could contain malware.[CR]'
                              'Cumination is not responsible for custom sites. Proceed?'):
        return
    path = utils.xbmcgui.Dialog().browseSingle(0, 'Select directory containing custom sites', 'myprograms')
    if not path:
        return
    progress = utils.progress
    progress.create('Installing custom sites', 'Searching for files')
    zips = sorted([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and f.endswith('.zip')],
                  key=lambda x: x[0].lower())
    if not zips:
        utils.notify('Error', 'No files found')
        progress.close()
        return
    utils.textBox('Files found', '[CR]'.join(zips))
    if not utils.dialog.yesno('WARNING',
                              'All custom sites from the list will be installed. Proceed?'):
        progress.close()
        return
    successful = []
    unsuccessful = []
    for idx, zip in enumerate(zips):
        progress.update(int(idx / len(zips)), "[CR]Processing {}".format(zip))
        success = process_custom_site_zip(os.path.join(path, zip))
        if success:
            successful.append(zip)
        else:
            unsuccessful.append(zip)
    progress.close()
    text = ''
    if successful:
        text += 'Successful:[CR]{}[CR]'.format('[CR]'.join(successful))
    if unsuccessful:
        text += 'Unsuccessful:[CR]{}'.format('[CR]'.join(unsuccessful))
    utils.textBox('Installation result', text)


def process_custom_site_zip(path):
    import json

    if basics.KODIVER < 19.0:
        from resources.lib import zfile as zipfile
    else:
        import zipfile

    def move(src, target):
        frm = os.path.join(basics.tempDir, src)
        to = os.path.join(basics.customSitesDir, target)
        os.rename(frm, to)

    basics.clean_temp()
    zip = zipfile.ZipFile(path, 'r')
    try:
        with zip.open('meta.json') as metafile:
            meta_data = json.load(metafile)
    except:
        zip.close()
        utils.kodilog('Invalid file')
        return False
    name = meta_data['name']
    original_module = meta_data['module_name']
    author = meta_data['author']
    version = meta_data['version']
    title = meta_data['title']
    url = meta_data['url']
    original_image = meta_data.get('image')
    original_about = meta_data.get('about')
    if original_about and not original_about.endswith('.txt'):
        zip.close()
        utils.kodilog('About file must have .txt extension')
        return False
    if original_module and not original_module.endswith('.py'):
        zip.close()
        utils.kodilog('Module file must have .py extension')
        return False
    checkable = (author, name)
    checkable_file_names = (original_module, original_about, original_image)
    invalid_chars = ['\\', '/', ':', '<', '>', '|', '"', '?', '*']
    for c in checkable_file_names:
        if not c:
            continue
        for i in invalid_chars:
            if i in c:
                zip.close()
                utils.kodilog('Invalid character ({}) in value of meta data: {}'.format(i, c))
                return False
    invalid_chars.append('.')
    for c in checkable:
        if not c:
            continue
        for i in invalid_chars:
            if i in c:
                zip.close()
                utils.kodilog('Invalid character ({}) in value of meta data: {}'.format(i, c))
                return False
    extractable = (original_module, original_image, original_about)
    extracted = []
    for e in extractable:
        if e:
            if e not in zip.namelist():
                zip.close()
                utils.kodilog('File not found in archive: {}'.format(e))
                basics.clean_temp()
                return False
            zipfile.ZipFile.extract(zip, e, basics.tempDir)
            extracted.append(e)
    zip.close()
    if len(extracted) == 0:
        basics.clean_temp()
        return False
    already_installed = select_custom_sites_attributes((author, name), 'title', 'version')
    if already_installed:
        old_title = already_installed[0][0]
        old_version = already_installed[0][1]
        utils.textBox('Site already installed', 'Custom site is already installed[CR]Title: {}[CR]Version: {}[CR][CR]'
                                                'New title: {}[CR]New version: {}[CR]'.format(old_title, old_version,
                                                                                              title, version))
        if not utils.dialog.yesno('Site already installed', 'Replace version {} with {}?'.format(old_version, version)):
            basics.clean_temp()
            return False
        keep_favorites = utils.dialog.yesno('Site already installed',
                                            'Old favorites and custom list items'
                                            ' could be incompatible with the new version. Keep them?')
        delete_custom_site(author, name, keep_favorites)
    id = get_new_site_id()
    new_module = "custom_{}.py".format(id)
    new_image = "{}_{}_img.{}".format(author, name, original_image.split('.')[-1]) if original_image else None
    new_about = "{}_{}_about.txt".format(author, name) if original_about else None
    add_custom_site(author, name, title, url, new_image, new_about.split('.')[0] if new_about else None,
                    version, new_module.split('.')[0])
    move(original_module, new_module)
    if original_image:
        move(original_image, new_image)
    if original_about:
        move(original_about, new_about)
    basics.clean_temp()
    return True


@url_dispatcher.register()
def uninstall_custom_site():
    sites = select_custom_sites_attributes(None, 'author', 'name', 'title')
    if not sites:
        utils.notify('No custom sites installed')
        return
    sites = {'{} by {}'.format(title, author): [author, name, title] for author, name, title in sites}
    chosen = utils.selector("Select site to uninstall", sites, show_on_one=True)
    if not chosen:
        return
    author, name, title = chosen
    delete_custom_site(author, name)
    xbmc.executebuiltin('Container.Refresh')
    utils.notify("{}".format(title), "Site uninstalled")


@url_dispatcher.register()
def list_custom_sites():
    def create_text_block(sites):
        block = ''
        for site in sites:
            block += '{}, version {}, created by {}[CR]'.format(site[2], site[3], site[0])
        return block
    sites = select_custom_sites_attributes(None, 'author', 'name', 'title', 'version', 'enabled')
    if not sites:
        utils.notify('No custom sites installed')
    enabled_sites = sorted([site for site in sites if site[4] == 1], key=lambda x: x[2].lower())
    disabled_sites = sorted([site for site in sites if site[4] == 0], key=lambda x: x[2].lower())
    text = ''
    if enabled_sites:
        text += 'Enabled sites:[CR]'
        text += create_text_block(enabled_sites) + '[CR]'
    if disabled_sites:
        text += 'Disabled sites:[CR]'
        text += create_text_block(disabled_sites)
    utils.textBox('Installed custom sites', text.strip())


@url_dispatcher.register()
def enable_custom_site():
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("SELECT author, name, title FROM custom_sites WHERE enabled = 0")
    rows = c.fetchall()
    conn.close()
    if not rows:
        utils.notify('No disabled custom sites found')
        return
    if not utils.dialog.yesno('WARNING',
                              'Custom sites are not verified by Cumination, and could contain malware.[CR]'
                              'Only enable sites from trusted sources. Proceed?'):
        return
    sites = {'{} by {}'.format(title, author): [author, name, title] for author, name, title in rows}
    chosen = utils.selector("Select site to enable", sites, show_on_one=True)
    author, name, title = chosen
    if not utils.dialog.yesno('WARNING',
                              'Custom sites are not verified by Cumination, and could contain malware.[CR]'
                              '{} will be enabled.[CR]Continue?'.format(title)):
        return
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("UPDATE custom_sites SET enabled = 1 WHERE author = ? and name = ?", (author, name))
    conn.commit()
    conn.close()
    xbmc.executebuiltin('Container.Refresh')
    utils.notify("{}".format(title), "Site enabled")


@url_dispatcher.register()
def disable_custom_site():
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("SELECT author, name, title FROM custom_sites WHERE enabled = 1")
    rows = c.fetchall()
    conn.close()
    if not rows:
        utils.notify('No enabled custom sites found')
        return
    sites = {'{} by {}'.format(title, author): [author, name, title] for author, name, title in rows}
    chosen = utils.selector("Select site to enable", sites, show_on_one=True)
    author, name, title = chosen
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("UPDATE custom_sites SET enabled = 0 WHERE author = ? and name = ?", (author, name))
    conn.commit()
    conn.close()
    xbmc.executebuiltin('Container.Refresh')
    utils.notify("{}".format(title), "Site disabled")


@url_dispatcher.register()
def enable_all_custom_sites():
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("SELECT author, name, title FROM custom_sites WHERE enabled = 0")
    rows = c.fetchall()
    conn.close()
    if not rows:
        utils.notify('No disabled custom sites found')
        return
    if not utils.dialog.yesno('WARNING',
                              'Custom sites are not verified by Cumination, and could contain malware.[CR]'
                              'Only enable sites from trusted sources. Proceed?'):
        return
    text = ''
    for author, _, title in rows:
        text += '{} by {}[CR]'.format(title, author)
    utils.textBox('Sites to enable', text.strip())
    if not utils.dialog.yesno('WARNING',
                              'Custom sites are not verified by Cumination, and could contain malware.[CR]'
                              'All custom sites will be enabled.[CR]Continue?'):
        return
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("UPDATE custom_sites SET enabled = 1 WHERE enabled = 0")
    conn.commit()
    conn.close()
    xbmc.executebuiltin('Container.Refresh')
    utils.notify("All custom sites enabled")


@url_dispatcher.register()
def disable_all_custom_sites():
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("SELECT author, name, title FROM custom_sites WHERE enabled = 1")
    rows = c.fetchall()
    conn.close()
    if not rows:
        utils.notify('No enabled custom sites found')
        return
    text = ''
    for author, _, title in rows:
        text += '{} by {}[CR]'.format(title, author)
    utils.textBox('Sites to disable', text.strip())
    if not utils.dialog.yesno('WARNING',
                              'All custom sites will be disabled.[CR]Continue?'):
        return
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("UPDATE custom_sites SET enabled = 0 WHERE enabled = 1")
    conn.commit()
    conn.close()
    xbmc.executebuiltin('Container.Refresh')
    utils.notify("All custom sites disabled")


def select_custom_sites_attributes(author_and_name, *args):
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    if author_and_name:
        c.execute("SELECT {} FROM custom_sites where author = ? and name = ?".format(", ".join(args)),
                  (author_and_name[0], author_and_name[1]))
    else:
        c.execute("SELECT {} FROM custom_sites".format(", ".join(args)))
    rows = c.fetchall()
    conn.close()
    return rows


def delete_custom_site(author, name, keep_favorites=False):
    site_elements = select_custom_sites_attributes((author, name), 'module_file', 'image', 'about', 'title')[0]
    removable = (site_elements[0] + '.py', site_elements[0] + '.pyo', site_elements[1], site_elements[2] + '.txt' if site_elements[2] else None)
    for r in removable:
        if r:
            try:
                os.remove(os.path.join(basics.customSitesDir, r))
            except OSError:
                pass
    mode_name = 'custom_{}_by_{}'.format(name, author)
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("DELETE FROM custom_sites WHERE author = ? and name = ?", (author, name))
    if not keep_favorites:
        c.execute("DELETE FROM favorites WHERE substr(mode, 1, instr(mode, '.') - 1) = ?", (mode_name,))
        # c.execute("DELETE FROM favorite_sites WHERE name = ?", (mode_name,))
        c.execute("DELETE FROM custom_listitems WHERE substr(mode, 1, instr(mode, '.') - 1) = ?", (mode_name,))
    conn.commit()
    conn.close()


def get_new_site_id():
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("SELECT max(rowid) FROM custom_sites")
    max_id = c.fetchone()[0]
    conn.close()
    max_id = 0 if not max_id else max_id
    return max_id + 1


def add_custom_site(author, name, title, url, image, about, version, module_file):
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("INSERT INTO custom_sites VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (author, name, title, url, image, about,
                                                                                version, datetime.datetime.now(),
                                                                                False, module_file))
    conn.commit()
    conn.close()


def enabled_custom_sites():
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("SELECT module_file FROM custom_sites WHERE enabled = ?", (True,))
    rows = c.fetchall()
    conn.close()
    sites = [site[0] for site in rows]
    return sites


def get_custom_data(author, name):
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("SELECT title, image, about, url FROM custom_sites WHERE author = ? AND name = ?", (author, name))
    row = c.fetchone()
    conn.close()
    return row if row else (None, None, None, None)


def disable_custom_site_by_module(module_file):
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("UPDATE custom_sites SET enabled = 0 WHERE module_file =  ?", (module_file,))
    conn.commit()
    conn.close()


def get_custom_site_title_by_module(module_file):
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("SELECT title FROM custom_sites WHERE module_file = ?", (module_file,))
    row = c.fetchone()
    conn.close()
    return row[0]


@url_dispatcher.register()
def create_custom_list():
    name = utils._get_keyboard(heading="Input the name for the list")
    if not name:
        return
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("INSERT INTO custom_lists VALUES (?)", (name,))
    conn.commit()
    conn.close()
    xbmc.executebuiltin('Container.Refresh')


def get_custom_lists():
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("SELECT rowid, name FROM custom_lists")
    rows = c.fetchall()
    conn.close()
    return rows


def get_custom_listitems():
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("SELECT name, count(*) count FROM custom_listitems WHERE list_id in (SELECT 'main' union SELECT ROWID from custom_lists) group by name")
    rows = c.fetchall()
    conn.close()
    return rows


@url_dispatcher.register()
def load_custom_list(url):
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    if basics.addon.getSetting('custom_sites') == 'true':
        c.execute("select cli.rowid, cli.name, cli.url, cli.mode, cli.image from custom_listitems cli "
                  + "LEFT JOIN custom_sites cs on 'custom_' || cs.name || '_by_' ||"
                  + " cs.author = substr(cli.mode, 1, instr(cli.mode, '.') - 1)"
                  + " WHERE ifnull(cs.enabled, 1) = 1 and cli.list_id = ?", (url,))
    else:
        c.execute("select cli.rowid, cli.name, cli.url, cli.mode, cli.image from custom_listitems cli"
                  + " LEFT JOIN custom_sites cs on 'custom_' || cs.name || '_by_' ||"
                  + " cs.author = substr(cli.mode, 1, instr(cli.mode, '.') - 1)"
                  + " WHERE cs.name IS NULL and cli.list_id = ?", (url,))
    for (rowid, name, url, mode, img) in c.fetchall():
        if not img.startswith('http'):
            custom = 'custom_sites' in img
            img = img if img.lower().startswith('http') else img.split('/')[-1].split('\\')[-1]
            img = basics.cum_image(img, custom)
        keyword_match = re.compile(r'\[COLOR [a-z]*\](.*?)\[\/COLOR\]', re.IGNORECASE).search(name)
        keyword = keyword_match.group(1) if keyword_match else ''
        ins = AdultSite.get_site_by_name(mode.split('.')[0])
        if ins:
            if ins.default_mode == mode:
                custom = ins.custom
                about = ins.about
            else:
                name = ins.title + ' - ' + name
                custom = False
                about = None
            basics.addDir(name, url, mode, img, about=about, custom=custom, list_avail=False, listitem_id=rowid, keyword=keyword)
    conn.close()
    if 'main' not in url:
        utils.eod(utils.addon_handle)


@url_dispatcher.register()
def add_listitem(favmode, name, url, img):
    name = name.split(' [COLOR red]*')[0]
    custom_lists = get_custom_lists()
    custom_lists = {row[1]: str(row[0]) for row in custom_lists}
    custom_lists['Main menu'] = 'main'
    selected_id = utils.selector('Add this item to', custom_lists, sort_by=lambda x: x[1], show_on_one=True)
    conn = sqlite3.connect(favoritesdb)
    conn.text_factory = str
    c = conn.cursor()
    c.execute("INSERT INTO custom_listitems VALUES (?,?,?,?,?)", (name, url, favmode, img, selected_id))
    conn.commit()
    conn.close()
    xbmc.executebuiltin('Container.Refresh')


@url_dispatcher.register()
def remove_listitem(listitem_id):
    conn = sqlite3.connect(favoritesdb)
    c = conn.cursor()
    c.execute("DELETE FROM custom_listitems WHERE rowid = ?", (listitem_id,))
    conn.commit()
    conn.close()
    xbmc.executebuiltin('Container.Refresh')


@url_dispatcher.register()
def move_listitem(listitem_id):
    custom_lists = get_custom_lists()
    custom_lists = {row[1]: str(row[0]) for row in custom_lists}
    custom_lists['Main menu'] = 'main'
    selected_id = utils.selector('Move this item to', custom_lists, sort_by=lambda x: x[1], show_on_one=True)
    if selected_id:
        conn = sqlite3.connect(favoritesdb)
        c = conn.cursor()
        c.execute("UPDATE custom_listitems set list_id = ? WHERE rowid = ?", (selected_id, listitem_id,))
        conn.commit()
        conn.close()
        xbmc.executebuiltin('Container.Refresh')


@url_dispatcher.register()
def remove_list(rowid):
    conn = sqlite3.connect(favoritesdb)
    c = conn.cursor()
    c.execute("DELETE FROM custom_lists WHERE rowid = ?", (int(rowid),))
    c.execute("DELETE FROM custom_listitems WHERE list_id = ?", (rowid,))
    conn.commit()
    conn.close()
    xbmc.executebuiltin('Container.Refresh')


@url_dispatcher.register()
def edit_list(rowid):
    name = utils._get_keyboard(heading="Input the new name for the list")
    if not name:
        return
    conn = sqlite3.connect(favoritesdb)
    c = conn.cursor()
    c.execute("UPDATE custom_lists set name = ? WHERE rowid = ?", (name, int(rowid),))
    conn.commit()
    conn.close()
    xbmc.executebuiltin('Container.Refresh')


@url_dispatcher.register()
def moveup_listitem(listitem_id):
    conn = sqlite3.connect(favoritesdb)
    c = conn.cursor()
    sql = '''DROP TABLE IF EXISTS tmp;
CREATE TEMP TABLE tmp AS
SELECT name,
(SELECT max(ROWID)+1 from custom_listitems) tmp_id,
cli.ROWID id,
coalesce((SELECT max(ROWID) from custom_listitems WHERE list_id = cli.list_id and ROWID<cli.ROWID), cli.ROWID) prev_id,
coalesce((SELECT min(ROWID) from custom_listitems WHERE list_id = cli.list_id and ROWID>cli.ROWID), cli.ROWID) next_id
FROM custom_listitems cli
WHERE cli.ROWID = {};
update custom_listitems set ROWID = (SELECT tmp_id FROM tmp) WHERE ROWID = (SELECT prev_id FROM tmp);
update custom_listitems set ROWID = (SELECT prev_id FROM tmp) WHERE ROWID = (SELECT id FROM tmp);
update custom_listitems set ROWID = (SELECT id FROM tmp) WHERE ROWID = (SELECT tmp_id FROM tmp);
DROP TABLE IF EXISTS tmp;'''.format(listitem_id)
    c.executescript(sql)
    conn.commit()
    conn.close()
    xbmc.executebuiltin('Container.Refresh')


@url_dispatcher.register()
def movedown_listitem(listitem_id):
    conn = sqlite3.connect(favoritesdb)
    c = conn.cursor()
    sql = '''DROP TABLE IF EXISTS tmp;
CREATE TEMP TABLE tmp AS
SELECT name,
(SELECT max(ROWID)+1 from custom_listitems) tmp_id,
cli.ROWID id,
coalesce((SELECT max(ROWID) from custom_listitems WHERE list_id = cli.list_id and ROWID<cli.ROWID), cli.ROWID) prev_id,
coalesce((SELECT min(ROWID) from custom_listitems WHERE list_id = cli.list_id and ROWID>cli.ROWID), cli.ROWID) next_id
FROM custom_listitems cli
WHERE cli.ROWID = {};
update custom_listitems set ROWID = (SELECT tmp_id FROM tmp) WHERE ROWID = (SELECT next_id FROM tmp);
update custom_listitems set ROWID = (SELECT next_id FROM tmp) WHERE ROWID = (SELECT id FROM tmp);
update custom_listitems set ROWID = (SELECT id FROM tmp) WHERE ROWID = (SELECT tmp_id FROM tmp);
DROP TABLE IF EXISTS tmp;'''.format(listitem_id)
    c.executescript(sql)
    conn.commit()
    conn.close()
    xbmc.executebuiltin('Container.Refresh')


@url_dispatcher.register()
def moveup_list(rowid):
    conn = sqlite3.connect(favoritesdb)
    c = conn.cursor()
    sql = '''DROP TABLE IF EXISTS tmp;
CREATE TEMP TABLE tmp AS
SELECT name,
(SELECT max(ROWID)+1 from custom_lists) tmp_id,
cli.ROWID id,
coalesce((SELECT max(ROWID) from custom_lists WHERE ROWID<cli.ROWID), cli.ROWID) prev_id,
coalesce((SELECT min(ROWID) from custom_lists WHERE ROWID>cli.ROWID), cli.ROWID) next_id
FROM custom_lists cli
WHERE cli.ROWID = {};
update custom_lists set ROWID = (SELECT tmp_id FROM tmp) WHERE ROWID = (SELECT prev_id FROM tmp);
update custom_listitems set list_id = cast((SELECT tmp_id FROM tmp) as text) WHERE list_id = cast((SELECT prev_id FROM tmp) as text);
update custom_lists set ROWID = (SELECT prev_id FROM tmp) WHERE ROWID = (SELECT id FROM tmp);
update custom_listitems set list_id = cast((SELECT prev_id FROM tmp) as text) WHERE list_id = cast((SELECT id FROM tmp) as text);
update custom_lists set ROWID = (SELECT id FROM tmp) WHERE ROWID = (SELECT tmp_id FROM tmp);
update custom_listitems set list_id = cast((SELECT id FROM tmp) as text) WHERE list_id = cast((SELECT tmp_id FROM tmp) as text);
DROP TABLE IF EXISTS tmp;'''.format(rowid)
    c.executescript(sql)
    conn.commit()
    conn.close()
    xbmc.executebuiltin('Container.Refresh')


@url_dispatcher.register()
def movedown_list(rowid):
    conn = sqlite3.connect(favoritesdb)
    c = conn.cursor()
    sql = '''DROP TABLE IF EXISTS tmp;
CREATE TEMP TABLE tmp AS
SELECT name,
(SELECT max(ROWID)+1 from custom_lists) tmp_id,
cli.ROWID id,
coalesce((SELECT max(ROWID) from custom_lists WHERE ROWID<cli.ROWID), cli.ROWID) prev_id,
coalesce((SELECT min(ROWID) from custom_lists WHERE ROWID>cli.ROWID), cli.ROWID) next_id
FROM custom_lists cli
WHERE cli.ROWID = {};
update custom_lists set ROWID = (SELECT tmp_id FROM tmp) WHERE ROWID = (SELECT next_id FROM tmp);
update custom_listitems set list_id = cast((SELECT tmp_id FROM tmp) as text) WHERE list_id = cast((SELECT next_id FROM tmp) as text);
update custom_lists set ROWID = (SELECT next_id FROM tmp) WHERE ROWID = (SELECT id FROM tmp);
update custom_listitems set list_id = cast((SELECT next_id FROM tmp) as text) WHERE list_id = cast((SELECT id FROM tmp) as text);
update custom_lists set ROWID = (SELECT id FROM tmp) WHERE ROWID = (SELECT tmp_id FROM tmp);
update custom_listitems set list_id = cast((SELECT id FROM tmp) as text) WHERE list_id = cast((SELECT tmp_id FROM tmp) as text);
DROP TABLE IF EXISTS tmp;'''.format(rowid)
    c.executescript(sql)
    conn.commit()
    conn.close()
    xbmc.executebuiltin('Container.Refresh')
