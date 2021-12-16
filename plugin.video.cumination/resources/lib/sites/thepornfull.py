'''
    Cumination
    Copyright (C) 2021 Team Cumination

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

import re
import xbmc
import xbmcgui
from six.moves import urllib_parse
from resources.lib import utils
from resources.lib.adultsite import AdultSite

site = AdultSite('thepornfull', '[COLOR hotpink]Thepornfull[/COLOR]', 'https://thepornfull.com/', 'https://thepornfull.com/wp-content/uploads/2021/08/Logo-Thepornfull.png', 'thepornfull')


@site.register(default_mode=True)
def thepornfull_main():
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'thepornfull_search', site.img_search)
    thepornfull_list(site.url + 'page/1/?filter=latest')


@site.register()
def thepornfull_list(url):
    listhtml = utils.getHtml(url, site.url)
    match = re.compile('<article.*?href="([^"]+)" title="([^"]+).*?src="([^"]+)"', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for video, name, img in match:
        name = utils.cleantext(name)
        site.add_download_link(name, video, 'thepornfull_play', img, name)

    nextp = re.compile('next" href="([^"]+)"', re.DOTALL | re.IGNORECASE).search(listhtml)
    if nextp:
        site.add_dir('Next Page', nextp.group(1), 'thepornfull_list', site.img_next)
    utils.eod()


@site.register()
def thepornfull_search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'thepornfull_search')
    else:
        title = keyword.replace(' ', '+')
        url += title
        thepornfull_list(url)


@site.register()
def thepornfull_play(url, name, download=None):
    utils.kodilog(url)
    vp = utils.VideoPlayer(name, download=download)
    videohtml = utils.getHtml(url, site.url)
    match = re.compile('iframe src="([^"]+)"', re.IGNORECASE | re.DOTALL).search(videohtml)
    if match:
        iframeurl = match.group(1)
        headers = {'referer': iframeurl}
        iframehtml = utils.getHtml(iframeurl, url)
        iframefile = re.compile('file: "([^"]+)', re.IGNORECASE | re.DOTALL).search(iframehtml)
        if iframefile:
            videourl = iframefile.group(1)
            videourl = "{0}|{1}".format(videourl, urllib_parse.urlencode(headers))
            utils.kodilog(videourl)
            iconimage = xbmc.getInfoImage("ListItem.Thumb")
            subject = xbmc.getInfoLabel("ListItem.Plot")
            listitem = xbmcgui.ListItem(name)
            listitem.setArt({'thumb': iconimage, 'icon': "DefaultVideo.png", 'poster': iconimage})
            listitem.setInfo('video', {'Title': name, 'Genre': 'Porn', 'plot': subject, 'plotoutline': subject})
            listitem.setMimeType('application/vnd.apple.mpegurl')
            listitem.setContentLookup(False)
            xbmc.Player().play(videourl, listitem)