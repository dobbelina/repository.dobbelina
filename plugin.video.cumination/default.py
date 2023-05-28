'''
    Cumination
    Copyright (C) 2016 Whitecream

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

import os.path
import sys
import socket
import importlib
import six

from kodi_six import xbmc, xbmcplugin, xbmcaddon, xbmcvfs

from resources.lib import basics
from resources.lib.url_dispatcher import URL_Dispatcher
from resources.lib import utils
from resources.lib import favorites
from resources.lib import pin
from resources.lib.adultsite import AdultSite
from resources.lib.sites import *  # noqa
from resources.lib import exception_logger

socket.setdefaulttimeout(60)

addon = basics.addon
content = 'movies' if addon.getSetting('content') == '0' else 'videos'
xbmcplugin.setContent(basics.addon_handle, content)
addon = xbmcaddon.Addon()
TRANSLATEPATH = xbmcvfs.translatePath if six.PY3 else xbmc.translatePath
progress = utils.progress
dialog = utils.dialog

url_dispatcher = URL_Dispatcher('main')

if addon.getSetting('custom_sites') == 'true':
    sys.path.append(basics.customSitesDir)
    for module_name in favorites.enabled_custom_sites():
        try:
            importlib.import_module(module_name)
        except Exception as e:
            utils.kodilog('{0} {1}: {2}'.format(utils.i18n('err_custom'), module_name, e))
            favorites.disable_custom_site_by_module(module_name)
            title = favorites.get_custom_site_title_by_module(module_name)
            utils.textBox(utils.i18n('disable_custom'), '{0}:[CR]{1}'.format(utils.i18n('custom_msg'), title))


@url_dispatcher.register()
def INDEX():
    url_dispatcher.add_dir('[COLOR white]{}[/COLOR]'.format(utils.i18n('sites')), '', 'site_list',
                           basics.cum_image('cum-sites.png'), '', list_avail=False)
    url_dispatcher.add_dir('[COLOR white]{}[/COLOR]'.format(utils.i18n('fav_videos')), '', 'favorites.List',
                           basics.cum_image('cum-fav.png'), '', list_avail=False)
    download_path = addon.getSetting('download_path')
    if download_path != '' and xbmcvfs.exists(download_path):
        url_dispatcher.add_dir('[COLOR white]{}[/COLOR]'.format(utils.i18n('dnld_folder')), download_path, 'OpenDownloadFolder',
                               basics.cum_image('cum-downloads.png'), '', list_avail=False)

    url_dispatcher.add_dir('[COLOR white]{}[/COLOR]'.format(utils.i18n('custom_list')), '', 'favorites.create_custom_list', Folder=False, list_avail=False)
    for rowid, name in favorites.get_custom_lists():
        url_dispatcher.add_dir(name, str(rowid), 'favorites.load_custom_list', list_avail=False, custom_list=True)
    favorites.load_custom_list('main')
    url_dispatcher.add_dir('[COLOR white]{}[/COLOR]'.format(utils.i18n('clear_cache')), '', 'utils.clear_cache',
                           basics.cuminationicon, '', Folder=False, list_avail=False)

    utils.eod(basics.addon_handle, False)


@url_dispatcher.register()
def site_list():
    custom_listitems = favorites.get_custom_listitems()
    custom_listitems_dict = {}
    for x in custom_listitems:
        custom_listitems_dict[x[0]] = x[1]
    for x in sorted(AdultSite.get_sites(), key=lambda y: y.get_clean_title().lower(), reverse=False):
        if x.custom:
            utils.kodilog('{0}: {1}'.format(utils.i18n('list_custom'), x.title), xbmc.LOGDEBUG)
        title = x.title
        if title in custom_listitems_dict.keys():
            title = '{} [COLOR red]{}[/COLOR]'.format(title, ''.ljust(custom_listitems_dict[title], '*'))
        url_dispatcher.add_dir(title, x.url, x.default_mode, x.image, about=x.about, custom=x.custom)
    utils.eod(basics.addon_handle, False)


@url_dispatcher.register()
def OpenDownloadFolder(url):
    xbmc.executebuiltin('Dialog.Close(busydialog, true)')
    xbmc.sleep(100)
    xbmc.executebuiltin('ActivateWindow(Videos, ' + url + ')')


@url_dispatcher.register()
def smrSettings():
    import resolveurl
    resolveurl.display_settings()


@url_dispatcher.register()
def about_site(name, about, custom):
    heading = '{0} {1}'.format(utils.i18n('about'), name)
    dir = basics.customSitesDir if custom else basics.aboutDir
    with open(TRANSLATEPATH(os.path.join(dir, '{}.txt'.format(about)))) as f:
        announce = f.read()
    utils.textBox(heading, announce)


def change():
    version = addon.getAddonInfo('version')
    if addon.getSetting('changelog_seen_version') == version or not os.path.isfile(basics.changelog):
        return
    addon.setSetting('changelog_seen_version', version)
    heading = '[B][COLOR hotpink]Cumination[/COLOR] [COLOR white]Changelog[/COLOR][/B]'
    with open(basics.changelog) as f:
        cl_lines = f.readlines()
    announce = ''
    for line in cl_lines:
        if not line.strip():
            break
        announce += line
    utils.textBox(heading, announce)


if not addon.getSetting('cuminationage') == 'true':
    age = dialog.yesno(utils.i18n('warn'), utils.i18n('warn_msg'),
                       nolabel=utils.i18n('exit'), yeslabel=utils.i18n('enter'))
    if age:
        addon.setSetting('cuminationage', 'true')
else:
    age = True


def main(argv=None):
    with exception_logger.log_exception():
        if sys.argv:
            argv = sys.argv
        queries = utils.parse_query(argv[2])
        mode = queries.get('mode', None)
        url_dispatcher.dispatch(mode, queries)


if __name__ == '__main__':
    if pin.CheckPin():
        if age:
            change()
            sys.exit(main())
