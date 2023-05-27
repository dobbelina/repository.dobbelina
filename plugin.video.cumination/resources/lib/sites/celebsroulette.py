'''
    Cumination
    Copyright (C) 2023 Cumination

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
from resources.lib import utils
from resources.lib.decrypters.kvsplayer import kvs_decode
from resources.lib.adultsite import AdultSite
from six.moves import urllib_parse
import xbmc

site = AdultSite('celebsroulette', '[COLOR hotpink]CelebsRoulette[/COLOR]', 'https://celebsroulette.com/', 'https://celebsroulette.com/images/logo.png', 'celebsroulette')


@site.register(default_mode=True)
def Main():
    site.add_dir('[COLOR hotpink]Categories[/COLOR]', site.url + 'categories/', 'Categories', site.img_cat)
    site.add_dir('[COLOR hotpink]Models[/COLOR]', site.url + 'models/1/', 'Models', site.img_cat)
    site.add_dir('[COLOR hotpink]Tags[/COLOR]', site.url + 'tags/', 'Tags', site.img_cat)
    site.add_dir('[COLOR hotpink]Playlists[/COLOR]', site.url + 'playlists/?mode=async&function=get_block&block_id=list_playlists_common_playlists_list&sort_by=&from=01', 'Playlist', site.img_cat)
    site.add_dir('[COLOR hotpink]Search[/COLOR]', site.url + 'search/?mode=async&function=get_block&block_id=list_videos_videos_list_search_result&category_ids=&sort_by=&from_videos=01&q=', 'Search', site.img_search)
    List(site.url + 'latest-updates/')
    utils.eod()


@site.register()
def List(url):
    listhtml = utils.getHtml(url)
    if '/models/' in url or '/categories/' in url or '/tags/' in url:
        listhtml = listhtml.split('New Naked Celebs Scenes')[0]
    match = re.compile(r'class="item.+?href="([^"]+)"\s+title="([^"]+)".+?data-original="([^"]+)".+?</strong>', re.DOTALL | re.IGNORECASE).findall(listhtml)

    for videopage, name, img in match:
        name = utils.cleantext(name)

        cm = []
        cm_lookupinfo = (utils.addon_sys + "?mode=" + str('celebsroulette.Lookupinfo') + "&url=" + urllib_parse.quote_plus(videopage))
        cm.append(('[COLOR deeppink]Lookup info[/COLOR]', 'RunPlugin(' + cm_lookupinfo + ')'))
        cm_related = (utils.addon_sys + "?mode=" + str('celebsroulette.Related') + "&url=" + urllib_parse.quote_plus(videopage))
        cm.append(('[COLOR deeppink]Related videos[/COLOR]', 'RunPlugin(' + cm_related + ')'))

        site.add_download_link(name, videopage, 'Playvid', img, name, contextm=cm)

    nextp = re.compile(r':(\d+)">Next', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if nextp:
        np = nextp[0]
        pg = int(np) - 1
        r = re.search(r'/\d+/', url)
        if r:
            next_page = re.sub(r'/\d+/', '/{0}/'.format(np), url)
        elif 'from_videos={0:02d}'.format(pg) in url:
            next_page = url.replace('from_videos={0:02d}'.format(pg), 'from_videos={0:02d}'.format(int(np)))
        else:
            next_page = url + '{0}/'.format(np)
        lp = re.compile(r':(\d+)">Last', re.DOTALL | re.IGNORECASE).findall(listhtml)
        lp = '/' + lp[0] if lp else ''
        site.add_dir('Next Page (' + np + lp + ')', next_page, 'List', site.img_next)

    utils.eod()


@site.register()
def ListPL(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'class="item.+?item="([^"]+).+?original="([^"]+).+?title">\s*([^<\n]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for video, img, name in match:
        name = utils.cleantext(name)
        site.add_download_link(name, video, 'Playvid', img, name)

    nextp = re.compile(r':(\d+)">Next', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if nextp:
        np = nextp[0]
        pg = int(np) - 1
        if 'from={0:02d}'.format(pg) in url:
            next_page = url.replace('from={0:02d}'.format(pg), 'from={0:02d}'.format(int(np)))
        else:
            next_page = url + '{0}/'.format(np)
        lp = re.compile(r':(\d+)">Last', re.DOTALL | re.IGNORECASE).findall(listhtml)
        lp = '/' + lp[0] if lp else ''
        site.add_dir('Next Page (' + np + lp + ')', next_page, 'ListPL', site.img_next)

    utils.eod()


@site.register()
def Playlist(url):
    listhtml = utils.getHtml(url)
    match = re.compile(r'class="item.+?href="([^"]+).+?data-original="([^"]+).+?title">\s*([^<\n]+).+?videos">([^<]+)', re.DOTALL | re.IGNORECASE).findall(listhtml)
    for lpage, img, name, count in match:
        name = utils.cleantext(name) + "[COLOR deeppink] {0}[/COLOR]".format(count)
        lpage += '?mode=async&function=get_block&block_id=playlist_view_playlist_view&sort_by=&from=01'
        site.add_dir(name, lpage, 'ListPL', img)

    nextp = re.compile(r':(\d+)">Next', re.DOTALL | re.IGNORECASE).findall(listhtml)
    if nextp:
        np = nextp[0]
        pg = int(np) - 1
        if 'from={0:02d}'.format(pg) in url:
            next_page = url.replace('from={0:02d}'.format(pg), 'from={0:02d}'.format(int(np)))
        else:
            next_page = url + '{0}/'.format(np)
        lp = re.compile(r':(\d+)">Last', re.DOTALL | re.IGNORECASE).findall(listhtml)
        lp = '/' + lp[0] if lp else ''
        site.add_dir('Next Page (' + np + lp + ')', next_page, 'Playlist', site.img_next)

    utils.eod()


@site.register()
def Search(url, keyword=None):
    searchUrl = url
    if not keyword:
        site.search_dir(url, 'Search')
    else:
        title = keyword.replace(' ', '-')
        searchUrl = searchUrl + title
        List(searchUrl)


@site.register()
def Tags(url):
    html = utils.getHtml(url)
    match = re.compile(r'<li>\s*<a\s*href="([^"]+)">([^<]+)</a>\s*</li>', re.DOTALL | re.IGNORECASE).findall(html)
    for tagpage, name in match:
        name = utils.cleantext(name)
        site.add_dir(name, tagpage, 'List')
    utils.eod()


@site.register()
def Categories(url):
    cathtml = utils.getHtml(url)
    match = re.compile(r'<a\s*class="item"\s*href="([^"]+)"\s*title="([^"]+)">.+?src="([^"]+)".+?class="videos">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(cathtml)
    for catpage, name, img, videos in match:
        name = utils.cleantext(name) + " [COLOR deeppink]" + videos + "[/COLOR]"
        site.add_dir(name, catpage, 'List', img)
    utils.eod()


@site.register()
def Models(url):
    html = utils.getHtml(url)
    match = re.compile(r'class="item"\s*href="([^"]+)".+?(?:src="([^"]+)"|>no image<).+?class="title">([^<]+)<.+?"videos">([^<]+)<', re.DOTALL | re.IGNORECASE).findall(html)
    for murl, img, name, videos in match:
        name = utils.cleantext(name) + " [COLOR deeppink]" + videos + "[/COLOR]"
        site.add_dir(name, murl, 'List', img)

    nextp = re.compile(r'class="pagination".+?next".+?(\d+)"', re.DOTALL | re.IGNORECASE).search(html)
    if nextp:
        np = nextp.group(1)
        next_page = re.sub(r'/\d+/', '/{0}/'.format(np), url)
        lp = re.compile(r'class="pagination".+?last".+?(\d+)"', re.DOTALL | re.IGNORECASE).findall(html)[0]
        site.add_dir('Next Page ( ' + np + ' / ' + lp + ' )', next_page, 'Models', site.img_next)

    utils.eod()


@site.register()
def Playvid(url, name, download=None):
    vp = utils.VideoPlayer(name, download)
    vp.progress.update(25, "[CR]Loading video page[CR]")
    html = utils.getHtml(url)
    surl = re.search(r"video_url:\s*'([^']+)'", html)
    if surl:
        surl = surl.group(1)
        if surl.startswith('function/'):
            license = re.findall(r"license_code:\s*'([^']+)", html)[0]
            surl = kvs_decode(surl, license)
            surl = utils.getVideoLink(surl)
            surl += '|Referer=' + site.url
    else:
        vp.progress.close()
        return
    vp.progress.update(75, "[CR]Video found[CR]")
    vp.play_from_direct_link(surl)


@site.register()
def Lookupinfo(url):
    lookup_list = [
        ("Model", '(models/[^"]+)">([^<]+)<', ''),
        ("Categorie", '(categories/[^"]+)">([^<]+)<', ''),
        ("Tag", '(tags/[^"]+)">([^<]+)<', '')
    ]
    lookupinfo = utils.LookupInfo(site.url, url, 'celebsroulette.List', lookup_list)
    lookupinfo.getinfo()


@site.register()
def Related(url):
    contexturl = (utils.addon_sys + "?mode=" + str('celebsroulette.List') + "&url=" + urllib_parse.quote_plus(url))
    xbmc.executebuiltin('Container.Update(' + contexturl + ')')
