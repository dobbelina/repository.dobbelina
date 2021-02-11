import os.path
import sqlite3
import six
from six.moves import urllib_parse
import shutil
from kodi_six import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs
import os
import sys

__scriptname__ = "Cumination"
__author__ = "Cumination"
__scriptid__ = "plugin.video.cumination"

addon_handle = int(sys.argv[1])
addon_sys = sys.argv[0]
addon = xbmcaddon.Addon()
TRANSLATEPATH = xbmcvfs.translatePath if six.PY3 else xbmc.translatePath

rootDir = addon.getAddonInfo('path')
if rootDir[-1] == ';':
    rootDir = rootDir[0:-1]
rootDir = TRANSLATEPATH(rootDir)
resDir = os.path.join(rootDir, 'resources')
imgDir = os.path.join(resDir, 'images')
aboutDir = os.path.join(resDir, 'about')
profileDir = addon.getAddonInfo('profile')
profileDir = TRANSLATEPATH(profileDir)
cookiePath = os.path.join(profileDir, 'cookies.lwp')
favoritesdb = os.path.join(profileDir, 'favorites.db')
customSitesDir = os.path.join(profileDir, 'custom_sites')
tempDir = os.path.join(profileDir, 'temp')

cuminationicon = TRANSLATEPATH(os.path.join(rootDir, 'icon.png'))
changelog = TRANSLATEPATH(os.path.join(rootDir, 'changelog.txt'))

if not os.path.exists(profileDir):
    os.makedirs(profileDir)

if not os.path.exists(customSitesDir):
    os.makedirs(customSitesDir)

if not os.path.exists(tempDir):
    os.makedirs(tempDir)

kodiver = xbmc.getInfoLabel("System.BuildVersion").split(".")[0]


def cum_image(filename, custom=False):
    if filename.startswith('http'):
        return filename
    else:
        img = os.path.join(customSitesDir if custom else imgDir, filename)
        return img


def eod(handle=addon_handle, cache=True):
    if addon.getSetting('customview') == 'true':
        skin = xbmc.getSkinDir().lower()
        viewtype = 55 if 'estuary' in skin else 50
        setview = addon.getSetting('setview')
        if ';' in setview:
            currentskin, viewno = setview.split(';')
            if currentskin == skin:
                viewtype = viewno
        xbmc.executebuiltin("Container.SetViewMode(%s)" % str(viewtype))
    xbmcplugin.endOfDirectory(handle, cacheToDisc=cache)


def addDownLink(name, url, mode, iconimage, desc='', stream=None, fav='add', noDownload=False, contextm=None, fanart=None):
    contextMenuItems = []
    favtext = "Remove from" if fav == 'del' else "Add to"  # fav == 'add' or 'del'
    u = (sys.argv[0]
         + "?url=" + urllib_parse.quote_plus(url)
         + "&mode=" + str(mode)
         + "&name=" + urllib_parse.quote_plus(name))
    dwnld = (sys.argv[0]
             + "?url=" + urllib_parse.quote_plus(url)
             + "&mode=" + str(mode)
             + "&download=" + str(1)
             + "&name=" + urllib_parse.quote_plus(name))
    favorite = (sys.argv[0]
                + "?url=" + urllib_parse.quote_plus(url)
                + "&fav=" + fav
                + "&favmode=" + str(mode)
                + "&mode=" + str('favorites.Favorites')
                + "&img=" + urllib_parse.quote_plus(iconimage)
                + "&name=" + urllib_parse.quote_plus(name))
    ok = True
    if not iconimage:
        iconimage = cuminationicon
    liz = xbmcgui.ListItem(name)
    liz.setArt({'thumb': iconimage, 'icon': "DefaultVideo.png", 'poster': iconimage})
    if not fanart:
        fanart = os.path.join(rootDir, 'fanart.jpg')
        if addon.getSetting('posterfanart') == 'true':
            fanart = iconimage
    liz.setArt({'fanart': fanart})
    if stream:
        liz.setProperty('IsPlayable', 'true')
    if desc:
        liz.setInfo(type="Video", infoLabels={"Title": name, "plot": desc, "plotoutline": desc})
    else:
        liz.setInfo(type="Video", infoLabels={"Title": name})
    video_streaminfo = {'codec': 'h264'}
    liz.addStreamInfo('video', video_streaminfo)
    if contextm:
        if isinstance(contextm, list):
            for i in contextm:
                if isinstance(i, tuple):
                    contextMenuItems.append(i)
        else:
            if isinstance(contextm, tuple):
                contextMenuItems.append(contextm)
    contextMenuItems.append(('[COLOR hotpink]' + favtext + ' favorites[/COLOR]', 'RunPlugin(' + favorite + ')'))
    if fav == 'del':
        favorite_move_to_end = (sys.argv[0]
                                + "?url=" + urllib_parse.quote_plus(url)
                                + "&fav=" + 'move_to_end'
                                + "&favmode=" + str(mode)
                                + "&mode=" + str('favorites.Favorites')
                                + "&img=" + urllib_parse.quote_plus(iconimage)
                                + "&name=" + urllib_parse.quote_plus(name))
        contextMenuItems.append(('[COLOR hotpink]Move favorite to Top[/COLOR]', 'RunPlugin(' + favorite_move_to_end + ')'))
        favorite_move_up = (sys.argv[0]
                            + "?url=" + urllib_parse.quote_plus(url)
                            + "&fav=" + 'move_up'
                            + "&favmode=" + str(mode)
                            + "&mode=" + str('favorites.Favorites')
                            + "&img=" + urllib_parse.quote_plus(iconimage)
                            + "&name=" + urllib_parse.quote_plus(name))
        contextMenuItems.append(('[COLOR hotpink]Move favorite Up[/COLOR]', 'RunPlugin(' + favorite_move_up + ')'))
        favorite_move_down = (sys.argv[0]
                              + "?url=" + urllib_parse.quote_plus(url)
                              + "&fav=" + 'move_down'
                              + "&favmode=" + str(mode)
                              + "&mode=" + str('favorites.Favorites')
                              + "&img=" + urllib_parse.quote_plus(iconimage)
                              + "&name=" + urllib_parse.quote_plus(name))
        contextMenuItems.append(('[COLOR hotpink]Move favorite Down[/COLOR]', 'RunPlugin(' + favorite_move_down + ')'))

    if not noDownload:
        contextMenuItems.append(('[COLOR hotpink]Download Video[/COLOR]', 'RunPlugin(' + dwnld + ')'))
    settings_url = (sys.argv[0]
                    + "?mode=" + str('utils.openSettings'))
    contextMenuItems.append(
        ('[COLOR hotpink]Addon settings[/COLOR]', 'RunPlugin(' + settings_url + ')'))
    setview = (sys.argv[0]
               + "?mode=" + str('utils.setview'))
    contextMenuItems.append(
        ('[COLOR hotpink]Set this view as default[/COLOR]', 'RunPlugin(' + setview + ')'))
    liz.addContextMenuItems(contextMenuItems, replaceItems=False)
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=u, listitem=liz, isFolder=False)
    return ok


def addDir(name, url, mode, iconimage=None, page=None, channel=None, section=None, keyword='', Folder=True, about=None,
           custom=False, list_avail=True, listitem_id=None, custom_list=False, contextm=None):
    u = (sys.argv[0]
         + "?url=" + urllib_parse.quote_plus(url)
         + "&mode=" + str(mode)
         + "&page=" + str(page)
         + "&channel=" + str(channel)
         + "&section=" + str(section)
         + "&keyword=" + urllib_parse.quote_plus(keyword)
         + "&name=" + urllib_parse.quote_plus(name))
    ok = True
    if not iconimage:
        iconimage = cuminationicon
    liz = xbmcgui.ListItem(name)
    fanart = os.path.join(rootDir, 'fanart.jpg')
    art = {'thumb': iconimage, 'icon': "DefaultFolder.png", 'fanart': fanart}
    if addon.getSetting('posterfanart') == 'true':
        fanart = iconimage
        art.update({'poster': iconimage})
    liz.setArt(art)
    liz.setInfo(type="Video", infoLabels={"Title": name})

    contextMenuItems = []
    if contextm:
        if isinstance(contextm, list):
            for i in contextm:
                if isinstance(i, tuple):
                    contextMenuItems.append(i)
        else:
            if isinstance(contextm, tuple):
                contextMenuItems.append(contextm)
    if about:
        about_url = (sys.argv[0]
                     + "?mode=" + str('main.about_site')
                     + "&img=" + urllib_parse.quote_plus(iconimage)
                     + "&name=" + urllib_parse.quote_plus(name)
                     + "&about=" + str(about)
                     + "&custom=" + str(custom))
        contextMenuItems.append(
            ('[COLOR hotpink]About site[/COLOR]', 'RunPlugin(' + about_url + ')'))
    if len(keyword) >= 1:
        keyw = (sys.argv[0]
                + "?mode=" + str('utils.delKeyword')
                + "&keyword=" + urllib_parse.quote_plus(keyword))
        contextMenuItems.append(('[COLOR hotpink]Remove keyword[/COLOR]', 'RunPlugin(' + keyw + ')'))
    if list_avail:
        list_item_name = 'Add item to ...'
        list_url = (sys.argv[0]
                    + "?url=" + urllib_parse.quote_plus(url)
                    + "&favmode=" + str(mode)
                    + "&mode=" + str('favorites.add_listitem')
                    + "&img=" + urllib_parse.quote_plus(iconimage)
                    + "&name=" + urllib_parse.quote_plus(name))
        contextMenuItems.append(('[COLOR hotpink]%s[/COLOR]' % list_item_name, 'RunPlugin(' + list_url + ')'))
    if listitem_id:
        move_listitem_url = (sys.argv[0]
                             + "?mode=" + str('favorites.move_listitem')
                             + "&listitem_id=" + str(listitem_id))
        contextMenuItems.append(('[COLOR hotpink]Move item to ...[/COLOR]', 'RunPlugin(' + move_listitem_url + ')'))
        listitem_url = (sys.argv[0]
                        + "?mode=" + str('favorites.remove_listitem')
                        + "&listitem_id=" + str(listitem_id))
        contextMenuItems.append(('[COLOR hotpink]Remove from list[/COLOR]', 'RunPlugin(' + listitem_url + ')'))
        moveupitem_url = (sys.argv[0]
                          + "?mode=" + str('favorites.moveup_listitem')
                          + "&listitem_id=" + str(listitem_id))
        contextMenuItems.append(('[COLOR hotpink]Move item Up[/COLOR]', 'RunPlugin(' + moveupitem_url + ')'))
        movedownitem_url = (sys.argv[0]
                            + "?mode=" + str('favorites.movedown_listitem')
                            + "&listitem_id=" + str(listitem_id))
        contextMenuItems.append(('[COLOR hotpink]Move item Down[/COLOR]', 'RunPlugin(' + movedownitem_url + ')'))

    if custom_list:
        editlist_url = (sys.argv[0]
                        + "?mode=" + str('favorites.edit_list')
                        + "&rowid=" + str(url))
        contextMenuItems.append(('[COLOR hotpink]Edit name[/COLOR]', 'RunPlugin(' + editlist_url + ')'))
        dellist_url = (sys.argv[0]
                       + "?mode=" + str('favorites.remove_list')
                       + "&rowid=" + str(url))
        contextMenuItems.append(('[COLOR hotpink]Remove list[/COLOR]', 'RunPlugin(' + dellist_url + ')'))
        moveuplist_url = (sys.argv[0]
                          + "?mode=" + str('favorites.moveup_list')
                          + "&rowid=" + str(url))
        contextMenuItems.append(('[COLOR hotpink]Move list Up[/COLOR]', 'RunPlugin(' + moveuplist_url + ')'))
        movedownlist_url = (sys.argv[0]
                            + "?mode=" + str('favorites.movedown_list')
                            + "&rowid=" + str(url))
        contextMenuItems.append(('[COLOR hotpink]Move list Down[/COLOR]', 'RunPlugin(' + movedownlist_url + ')'))

    settings_url = (sys.argv[0]
                    + "?mode=" + str('utils.openSettings'))
    contextMenuItems.append(
        ('[COLOR hotpink]Addon settings[/COLOR]', 'RunPlugin(' + settings_url + ')'))
    setview = (sys.argv[0]
               + "?mode=" + str('utils.setview'))
    contextMenuItems.append(
        ('[COLOR hotpink]Set this view as default[/COLOR]', 'RunPlugin(' + setview + ')'))
    liz.addContextMenuItems(contextMenuItems, replaceItems=False)
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=u, listitem=liz, isFolder=Folder)
    return ok


def searchDir(url, mode, page=None):
    addDir('[COLOR hotpink]Add Keyword[/COLOR]', url, 'utils.newSearch', cum_image('cum-search.png'), '', mode,
           Folder=False)
    conn = sqlite3.connect(favoritesdb)
    c = conn.cursor()

    if addon.getSetting('keywords_sorted') == 'true':
        addDir('[COLOR hotpink]Unsorted Keywords[/COLOR]', url, 'utils.setUnsorted', cum_image('cum-search.png'), '', mode, Folder=False)
    else:
        addDir('[COLOR hotpink]Sorted Keywords[/COLOR]', url, 'utils.setSorted', cum_image('cum-search.png'), '', mode, Folder=False)

    try:
        if addon.getSetting('keywords_sorted') == 'true':
            c.execute("SELECT * FROM keywords order by keyword")
        else:
            c.execute("SELECT * FROM keywords ORDER BY rowid DESC")
        for (keyword,) in c.fetchall():
            name = '[COLOR deeppink]' + urllib_parse.unquote_plus(keyword) + '[/COLOR]'
            addDir(name, url, mode, cum_image('cum-search.png'), page=page, keyword=keyword)
    except:
        pass
    conn.close()
    eod()


def clean_temp():
    shutil.rmtree(tempDir)
    os.makedirs(tempDir)
