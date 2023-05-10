'''
    Cumination
    Copyright (C) 2022 Team Cumination

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
from resources.lib import utils
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse
import json

site = AdultSite('familypornhd', '[COLOR hotpink]Familypornhd[/COLOR]', 'https://familypornhd.com/', 'https://familypornhd.com/wp-content/uploads/2020/06/Light-normal.png', 'familypornhd')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Channels[/COLOR]', site.url + 'channels/', 'Channels', site.img_cat)
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + 'pornstars', 'Pornstars', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?s=', 'Search', site.img_search)
    List(site.url)
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url)
    if 'You have requested a page or file which doesn\'t exist' in html:
        utils.notify(msg='Nothing found')
        utils.eod()
        return

    html = html.split('>Trending Porn<')[0]
    delimiter = 'article class="entry-tpl-grid'
    re_videopage = 'href="([^"]+)"><'
    re_name = 'title="([^"]+)"'
    re_img = ' src="([^"]+)"'
    utils.videos_list(site, 'familypornhd.Playvid', html, delimiter, re_videopage, re_name, re_img, contextm='familypornhd.Related')

    re_npurl = r'href="([^"]+)">Next'
    re_npnr = r'next" href="[^"]+/page/(\d+)'
    utils.next_page(site, 'familypornhd.List', html, re_npurl, re_npnr, contextm='familypornhd.GotoPage')
    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = url.replace('/page/{}'.format(np), '/page/{}'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('familypornhd.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Channels(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'g1-dark" href="([^"]+)".+?\(([^\)]+)\).+?g1-term-title">([^<]+)<.+?g1-term-count"><strong>(\d+)<', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for caturl, img, name, count in match:
        name = utils.cleantext(name) + '[COLOR hotpink] ({})[/COLOR]'.format(count.strip())
        site.add_dir(name, caturl, 'List', img)
    utils.eod()


@site.register()
def Pornstars(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'class="wp-caption".+?href="([^"]+)".+? src="([^"]+)".+?wp-caption-text">([^<]+)<', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for caturl, img, name in match:
        site.add_dir(name, caturl, 'List', img)
    utils.eod()


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'href="([^"]+)">([^<]+)<', re.IGNORECASE | re.DOTALL).findall(cathtml.split('page-title">Categories<')[-1].split('class="g1-row-background-media"')[0])
    for caturl, name in match:
        site.add_dir(name.title(), caturl, 'List', '')
    utils.eod()


@site.register()
def Search(url, keyword=None):
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        url = "{0}{1}".format(url, keyword.replace(' ', '%20'))
        List(url)


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download, regex='<a href="([^"]+)" target="_blank"')
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videohtml = utils.getHtml(url, site.url)
    match = re.compile('class="embed-container"><iframe.*?src="(https://onetvplus[^"]+)"', re.IGNORECASE | re.DOTALL).findall(videohtml)
    if match:
        iframeurl = match[0]
        iframehtml = utils.getHtml(iframeurl, url)
        match = re.compile(r'FirePlayer\(vhash, ({.+?}), false\);', re.IGNORECASE | re.DOTALL).findall(iframehtml)
        if match:
            j = json.loads(match[0])
            videourl = j["videoUrl"]
            videoserver = j["videoServer"]
            url1 = 'https://onetvplus.xyz' + videourl + '?s={}&d='.format(videoserver)
            hdr = dict(utils.base_hdrs)
            hdr['Accept'] = '*/*'
            html = utils.getHtml(url1, iframeurl, headers=hdr)
            match = re.compile(r'#EXT.+?RESOLUTION=\d+x(\d+)\s*([^#]+)', re.IGNORECASE | re.DOTALL).findall(html)
            if match:
                links = {m[0]: m[1].strip() for m in match}
                videourl = utils.prefquality(links, sort_by=lambda x: int(x), reverse=True)
                if videourl:
                    vp.progress.update(75, "[CR]Loading selected quality[CR]")
                    m3u8html = utils.getHtml(videourl, iframeurl, headers=hdr)
                    myplaylist = utils.TRANSLATEPATH("special://temp/myPlaylist.m3u8")
                    with open(myplaylist, 'w') as f:
                        f.write(m3u8html)
                    myparent = "#EXTM3U\n#EXT-X-VERSION:3\n#EXT-X-STREAM-INF:PROGRAM-ID=1\n{0}".format(myplaylist)
                    videourl = utils.TRANSLATEPATH("special://temp/myParent.m3u8")
                    with open(videourl, 'w') as f:
                        f.write(myparent)
                    vp.play_from_direct_link(videourl)
