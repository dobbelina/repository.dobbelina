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

site = AdultSite('palimas', '[COLOR hotpink]Palimas[/COLOR]', 'https://palimas.org/', 'palimas.png', 'palimas')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Pornstars[/COLOR]', site.url + 'pornstars?view=top-rated', 'Categories', site.img_cat)
    # site.add_dir('[COLOR hotpink]Channels[/COLOR]', site.url + 'channels', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + '?q=', 'Search', site.img_search)
    List(site.url + '?view=latest&when=all-time')
    utils.eod()


@site.register()
def List(url):
    html = utils.getHtml(url, '')
    if 'Oops! Sorry, no results were found' in html:
        utils.notify(msg='Nothing found')
        utils.eod()
        return

    delimiter = '''class=['"]video-cube['"]'''
    re_videopage = r'''href=['"]([^'"]+)['"]\s+title'''
    re_name = '''title=['"]([^'"]+)['"]'''
    re_img = r'''img\s+src=['"]([^'"]+)['"]'''
    re_quality = '''class=['"]vquality['"]>([^<]+)<'''
    re_duration = '''class=['"]vmin['"]>([^<]+)<'''

    cm = []
    cm_lookupinfo = (utils.addon_sys + "?mode=" + str('palimas.Lookupinfo') + "&url=")
    cm.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + cm_lookupinfo + ')'))
    cm_related = (utils.addon_sys + "?mode=" + str('palimas.Related') + "&url=")
    cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')'))

    utils.videos_list(site, 'palimas.Playvid', html, delimiter, re_videopage, re_name, re_img, re_quality=re_quality, re_duration=re_duration, contextm=cm)

    re_npurl = 'href="([^"]+)">Next'
    re_npnr = r'page=(\d+)">Next'
    re_lpnr = r'>Showing\s*\d+-\d+\s*of\s*(\d+)<'
    utils.next_page(site, 'palimas.List', html, re_npurl, re_npnr, re_lpnr=re_lpnr, videos_per_page=30, contextm='palimas.GotoPage')
    utils.eod()


@site.register()
def GotoPage(list_mode, url, np, lp):
    dialog = xbmcgui.Dialog()
    pg = dialog.numeric(0, 'Enter Page number')
    if pg:
        url = url.replace('page={}'.format(np), 'page={}'.format(pg))
        if int(lp) > 0 and int(pg) > int(lp):
            utils.notify(msg='Out of range!')
            return
        contexturl = (utils.addon_sys + "?mode=" + str(list_mode) + "&url=" + urllib_parse.quote_plus(url))
        xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('palimas.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url).replace("'", '"')
    match = re.compile(r'class=(?:"catt"|"pornstar-cube"|"channel-cube")><a href="([^"]+)"><img src="([^"]+)"\s*alt="([^"]+)".+?<h3>([\d,]+)', re.IGNORECASE | re.DOTALL).findall(cathtml)
    for caturl, img, name, count in match:
        name = utils.cleantext(name) + '[COLOR hotpink] ({} videos)[/COLOR]'.format(count)
        caturl = utils.fix_url(caturl, site.url)
        img = utils.fix_url(img, site.url)
        site.add_dir(name, caturl, 'List', img)
    if 'class="pagination"' in cathtml:
        re_npurl = 'href="([^"]+)">Next'
        re_npnr = r'page=(\d+)">Next'
        re_lpnr = r'>Showing\s*\d+-\d+\s*of\s*(\d+)<'
        baseurl = url.split('?')[0]
        utils.next_page(site, 'palimas.Categories', cathtml, re_npurl, re_npnr, re_lpnr=re_lpnr, videos_per_page=30, contextm='palimas.GotoPage', baseurl=baseurl)
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
    vp = utils.VideoPlayer(name, download, regex=r"\).src\s*=\s*'([^']+)'", direct_regex=None)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    videolinks = {}
    directlinks = {}
    for i in range(1, 5):
        videohtml = utils.getHtml(url, site.url, data='video-player={}'.format(i))
        vp.progress.update(25 + i * 16, "[CR]Loading video page[CR]")
        links = re.compile(r"\).src\s*=\s*'([^']+)'", re.IGNORECASE | re.DOTALL).findall(videohtml)
        if links:
            link = links[0]
            if '?url=' in link:
                link = link.split('?url=')[-1]
                name = link.split('/')[2]
                html = utils.getHtml(link)
                match = re.compile(r"<a href='([^']+)'", re.IGNORECASE | re.DOTALL).findall(html)
                if match:
                    directlinks[name] = 'https:' + match[-1]
            elif vp.resolveurl.HostedMediaFile(link).valid_url():
                videolinks[link.split('/')[2]] = link
            elif link.endswith('.mp4'):
                link = link + '|Referer={0}&verifypeer=false'.format(url)
                directlinks[link.split('/')[2]] = link
            elif link == 'h':
                match = re.compile(r'video id.+?<source src="([^"]+)"', re.IGNORECASE | re.DOTALL).findall(videohtml)
                if match:
                    link = match[0]
                    directlinks[link.split('/')[2]] = link
    links = directlinks.copy()
    links.update(videolinks)
    videourl = utils.selector('Select server', links, setting_valid=False)
    if not videourl:
        vp.progress.close()
        return
    vp.progress.update(90, "[CR]Loading video page[CR]")
    if videourl in directlinks.values():
        vp.play_from_direct_link(videourl)
    if videourl in videolinks.values():
        vp.play_from_link_to_resolve(videourl)


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Cat", '/(categories/[^"]+)">([^<]+)<', ''),
        ("Model", ["<label>Pornstars:.*?<label>", '/(pornstar[^"]+)">([^<]+)</a>'], '')
    ]

    lookupinfo = utils.LookupInfo(site.url, url, 'palimas.List', lookup_list)
    lookupinfo.getinfo()